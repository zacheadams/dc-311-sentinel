#!/usr/bin/env python3
"""
High-throughput parallel OBJECTID-window fetcher for DC 311 City Service Requests
across 2025 (Layer 18) and 2026 (Layer 21) from Open Data DC ArcGIS FeatureServer.

Because OBJECTID is an integer primary key and maxRecordCount is 1000, querying
contiguous 1000-ID windows (OBJECTID >= lo AND OBJECTID <= lo + 999) without
ORDER BY uses a direct B-tree index range scan (~150ms per batch) and mathematically
cannot exceed 1000 records per request.

Includes the full DETAILS column and stores Zstandard-compressed Parquet files
in data/raw/sr_2025.parquet and data/raw/sr_2026.parquet.

Strictly adheres to:
- Strictly zero emojis across code, logs, and outputs
"""

import concurrent.futures
import gzip
import http.client
import json
import os
import ssl
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import pyarrow as pa
import pyarrow.parquet as pq

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

LAYER_MAP = {
    2025: 18,
    2026: 21,
}

OUT_FIELDS = ",".join([
    "OBJECTID",
    "SERVICEREQUESTID",
    "SERVICECODE",
    "SERVICECODEDESCRIPTION",
    "SERVICETYPECODEDESCRIPTION",
    "ORGANIZATIONACRONYM",
    "SERVICECALLCOUNT",
    "ADDDATE",
    "RESOLUTIONDATE",
    "SERVICEDUEDATE",
    "SERVICEORDERDATE",
    "INSPECTIONFLAG",
    "INSPECTIONDATE",
    "SERVICEORDERSTATUS",
    "STATUS_CODE",
    "PRIORITY",
    "DETAILS",
    "STREETADDRESS",
    "ZIPCODE",
    "WARD",
    "LATITUDE",
    "LONGITUDE",
    "MARADDRESSREPOSITORYID",
    "EDITED",
])

PARQUET_SCHEMA = pa.schema([
    ("OBJECTID", pa.int64()),
    ("SERVICEREQUESTID", pa.string()),
    ("SERVICECODE", pa.string()),
    ("SERVICECODEDESCRIPTION", pa.string()),
    ("SERVICETYPECODEDESCRIPTION", pa.string()),
    ("ORGANIZATIONACRONYM", pa.string()),
    ("SERVICECALLCOUNT", pa.int32()),
    ("ADDDATE", pa.int64()),
    ("RESOLUTIONDATE", pa.int64()),
    ("SERVICEDUEDATE", pa.int64()),
    ("SERVICEORDERDATE", pa.int64()),
    ("INSPECTIONFLAG", pa.string()),
    ("INSPECTIONDATE", pa.int64()),
    ("SERVICEORDERSTATUS", pa.string()),
    ("STATUS_CODE", pa.string()),
    ("PRIORITY", pa.string()),
    ("DETAILS", pa.string()),
    ("STREETADDRESS", pa.string()),
    ("ZIPCODE", pa.string()),
    ("WARD", pa.string()),
    ("LATITUDE", pa.float64()),
    ("LONGITUDE", pa.float64()),
    ("MARADDRESSREPOSITORYID", pa.int64()),
    ("EDITED", pa.int64()),
])

HOST = "maps2.dcgis.dc.gov"
HEADERS = {
    "User-Agent": "DC-311-Sentinel-Pipeline/1.0",
    "Accept-Encoding": "gzip",
    "Connection": "keep-alive",
}

_tls = threading.local()


def get_conn():
    conn = getattr(_tls, "conn", None)
    if conn is None:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(HOST, timeout=45, context=ctx)
        _tls.conn = conn
    return conn


def reset_conn():
    conn = getattr(_tls, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
    _tls.conn = None


def fetch_json_keepalive(path_and_query, max_retries=5):
    for attempt in range(max_retries):
        try:
            conn = get_conn()
            conn.request("GET", path_and_query, headers=HEADERS)
            resp = conn.getresponse()
            raw = resp.read()
            if resp.status != 200:
                reset_conn()
                raise RuntimeError(f"HTTP {resp.status}")
            if resp.getheader("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            data = json.loads(raw.decode("utf-8"))
            if "error" in data:
                err = data["error"]
                raise RuntimeError(
                    f"ArcGIS error {err.get('code')}: {err.get('message')} {err.get('details')}"
                )
            return data
        except Exception as e:
            reset_conn()
            if attempt == max_retries - 1:
                raise
            wait_s = min(20, 1.5 ** attempt)
            time.sleep(wait_s)


def get_layer_bounds_and_count(layer_id):
    base_path = f"/dcgis/rest/services/DCGIS_DATA/ServiceRequests/FeatureServer/{layer_id}/query"
    count_res = fetch_json_keepalive(f"{base_path}?where=1%3D1&returnCountOnly=true&f=json")
    total_count = int(count_res.get("count", 0))

    stats = json.dumps([
        {"statisticType": "min", "onStatisticField": "OBJECTID", "outStatisticFieldName": "min_oid"},
        {"statisticType": "max", "onStatisticField": "OBJECTID", "outStatisticFieldName": "max_oid"},
    ])
    bounds_res = fetch_json_keepalive(
        f"{base_path}?where=1%3D1&outStatistics={urllib.parse.quote(stats)}&f=json"
    )
    attrs = bounds_res["features"][0]["attributes"]
    min_oid = int(attrs.get("MIN_OID") or attrs.get("min_oid") or 1)
    max_oid = int(attrs.get("MAX_OID") or attrs.get("max_oid") or total_count)
    return total_count, min_oid, max_oid


def normalize_record(attrs):
    def to_int(val):
        if val is None or val == "":
            return None
        try:
            return int(val)
        except Exception:
            return None

    def to_float(val):
        if val is None or val == "":
            return None
        try:
            return float(val)
        except Exception:
            return None

    def to_str(val):
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None

    return {
        "OBJECTID": to_int(attrs.get("OBJECTID")),
        "SERVICEREQUESTID": to_str(attrs.get("SERVICEREQUESTID")),
        "SERVICECODE": to_str(attrs.get("SERVICECODE")),
        "SERVICECODEDESCRIPTION": to_str(attrs.get("SERVICECODEDESCRIPTION")),
        "SERVICETYPECODEDESCRIPTION": to_str(attrs.get("SERVICETYPECODEDESCRIPTION")),
        "ORGANIZATIONACRONYM": to_str(attrs.get("ORGANIZATIONACRONYM")),
        "SERVICECALLCOUNT": to_int(attrs.get("SERVICECALLCOUNT")),
        "ADDDATE": to_int(attrs.get("ADDDATE")),
        "RESOLUTIONDATE": to_int(attrs.get("RESOLUTIONDATE")),
        "SERVICEDUEDATE": to_int(attrs.get("SERVICEDUEDATE")),
        "SERVICEORDERDATE": to_int(attrs.get("SERVICEORDERDATE")),
        "INSPECTIONFLAG": to_str(attrs.get("INSPECTIONFLAG")),
        "INSPECTIONDATE": to_int(attrs.get("INSPECTIONDATE")),
        "SERVICEORDERSTATUS": to_str(attrs.get("SERVICEORDERSTATUS")),
        "STATUS_CODE": to_str(attrs.get("STATUS_CODE")),
        "PRIORITY": to_str(attrs.get("PRIORITY")),
        "DETAILS": to_str(attrs.get("DETAILS")),
        "STREETADDRESS": to_str(attrs.get("STREETADDRESS")),
        "ZIPCODE": to_str(attrs.get("ZIPCODE")),
        "WARD": to_str(attrs.get("WARD")),
        "LATITUDE": to_float(attrs.get("LATITUDE")),
        "LONGITUDE": to_float(attrs.get("LONGITUDE")),
        "MARADDRESSREPOSITORYID": to_int(attrs.get("MARADDRESSREPOSITORYID")),
        "EDITED": to_int(attrs.get("EDITED")),
    }


def fetch_window(layer_id, lo_oid, hi_oid):
    base_path = f"/dcgis/rest/services/DCGIS_DATA/ServiceRequests/FeatureServer/{layer_id}/query"
    where = f"OBJECTID >= {lo_oid} AND OBJECTID <= {hi_oid}"
    params = urllib.parse.urlencode({
        "where": where,
        "outFields": OUT_FIELDS,
        "returnGeometry": "false",
        "f": "json",
    })
    data = fetch_json_keepalive(f"{base_path}?{params}")
    feats = data.get("features", [])
    rows = []
    for f in feats:
        attrs = f.get("attributes")
        if attrs and attrs.get("OBJECTID") is not None:
            rows.append(normalize_record(attrs))
    return rows


def fetch_year(year, full_fetch=False, num_workers=10):
    layer_id = LAYER_MAP[year]
    out_parquet = os.path.join(RAW_DIR, f"sr_{year}.parquet")
    os.makedirs(RAW_DIR, exist_ok=True)

    total_count, min_oid, max_oid = get_layer_bounds_and_count(layer_id)
    print(f"Year {year} (Layer {layer_id}): Server count={total_count:,}, OID range=[{min_oid}, {max_oid}]")

    if os.path.exists(out_parquet) and not full_fetch:
        existing_table = pq.read_table(out_parquet)
        existing_count = existing_table.num_rows
        if abs(existing_count - total_count) <= max(50, int(total_count * 0.001)):
            print(f"Year {year} Parquet already complete ({existing_count:,} rows). Skipping full re-download.")
            return existing_count
        if year == 2026 and existing_count > 0:
            existing_rows = {r["OBJECTID"]: r for r in existing_table.to_pylist() if r["OBJECTID"] is not None}
            max_existing_oid = max(existing_rows.keys())
            print(f"Incremental 2026 update from OBJECTID > {max_existing_oid}...")
            windows = []
            cur = max_existing_oid + 1
            while cur <= max_oid:
                windows.append((cur, min(max_oid, cur + 999)))
                cur += 1000
            new_count = 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as pool:
                for batch in pool.map(lambda w: fetch_window(layer_id, w[0], w[1]), windows):
                    for r in batch:
                        existing_rows[r["OBJECTID"]] = r
                        new_count += 1
            merged = list(existing_rows.values())
            merged.sort(key=lambda x: x["OBJECTID"])
            table = pa.Table.from_pylist(merged, schema=PARQUET_SCHEMA)
            pq.write_table(table, out_parquet, compression="zstd")
            print(f"Saved updated {year} Parquet: {len(merged):,} rows ({new_count:,} new)")
            return len(merged)

    # Build 1,000-ID windows
    windows = []
    cur = min_oid
    while cur <= max_oid:
        windows.append((cur, min(max_oid, cur + 999)))
        cur += 1000

    print(f"Fetching {len(windows):,} index windows across {num_workers} keep-alive workers...")
    t0 = time.time()
    all_rows_by_oid = {}
    completed_windows = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as pool:
        futures = [pool.submit(fetch_window, layer_id, lo, hi) for (lo, hi) in windows]
        for fut in concurrent.futures.as_completed(futures):
            batch = fut.result()
            for r in batch:
                all_rows_by_oid[r["OBJECTID"]] = r
            completed_windows += 1
            if completed_windows % 100 == 0 or completed_windows == len(windows):
                elapsed = time.time() - t0
                print(
                    f"  [Year {year}] {completed_windows}/{len(windows)} windows "
                    f"({len(all_rows_by_oid):,} rows, {elapsed:.1f}s)"
                )

    deduped = list(all_rows_by_oid.values())
    deduped.sort(key=lambda x: x["OBJECTID"])
    elapsed = time.time() - t0
    print(
        f"Year {year} fetch complete in {elapsed:.1f}s: {len(deduped):,} unique rows "
        f"(server count: {total_count:,})"
    )

    table = pa.Table.from_pylist(deduped, schema=PARQUET_SCHEMA)
    pq.write_table(table, out_parquet, compression="zstd")
    size_mb = os.path.getsize(out_parquet) / (1024 * 1024)
    print(f"Wrote {out_parquet} ({size_mb:.2f} MB)")
    return len(deduped)


def main():
    full = "--full" in sys.argv
    counts = {}
    for yr in (2025, 2026):
        counts[yr] = fetch_year(yr, full_fetch=full)

    manifest_path = os.path.join(RAW_DIR, "fetch_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "counts": counts,
            },
            f,
            indent=2,
        )
    print(f"Saved manifest to {manifest_path}")


if __name__ == "__main__":
    main()
