#!/usr/bin/env python3
"""
Build the analytical DuckDB warehouse (data/warehouse.duckdb) from raw 2025 and 2026
311 service request Parquet files, joining:
- 2023 ANC and 2022 Ward spatial boundaries via bounding-box-indexed point-in-polygon
- Service category family taxonomy from data/config.json
- Daily DC weather observations (rain, snow, temperature, and 3-day rolling totals)

Strictly adheres to:
- Strictly zero emojis across code, logs, and outputs
"""

import json
import os
import re
import time
from collections import defaultdict

import duckdb
import pyarrow as pa

from spatial_utils import get_bbox, get_poly_rings_list, is_point_in_poly

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_2025 = os.path.join(BASE_DIR, "data", "raw", "sr_2025.parquet")
RAW_2026 = os.path.join(BASE_DIR, "data", "raw", "sr_2026.parquet")
RAW_WEATHER = os.path.join(BASE_DIR, "data", "raw", "dc_weather_daily.parquet")
WAREHOUSE_DB = os.path.join(BASE_DIR, "data", "warehouse.duckdb")
ANC_GEOJSON = os.path.join(BASE_DIR, "data", "dc_ancs.geojson")
WARD_GEOJSON = os.path.join(BASE_DIR, "data", "dc_wards.geojson")
SMD_GEOJSON = os.path.join(BASE_DIR, "data", "dc_smds.geojson")
CONFIG_JSON = os.path.join(BASE_DIR, "data", "config.json")


def load_polygon_index(geojson_path, id_field):
    with open(geojson_path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    items = []
    for feat in gj.get("features", []):
        props = feat.get("properties", {})
        poly_id = str(props.get(id_field, "")).strip()
        rings_list = get_poly_rings_list(feat.get("geometry", {}))
        if not poly_id or not rings_list:
            continue
        bbox = get_bbox(rings_list)
        items.append((poly_id, bbox, rings_list))

    # Build a 0.01-degree (~1km) grid index for fast candidate lookup
    grid = defaultdict(list)
    for item in items:
        poly_id, (min_x, min_y, max_x, max_y), rings_list = item
        gx0 = int(min_x * 100)
        gx1 = int(max_x * 100)
        gy0 = int(min_y * 100)
        gy1 = int(max_y * 100)
        for gx in range(gx0, gx1 + 1):
            for gy in range(gy0, gy1 + 1):
                grid[(gx, gy)].append(item)

    return items, grid


def lookup_polygon(lon, lat, grid, all_items):
    cell = (int(lon * 100), int(lat * 100))
    candidates = grid.get(cell, all_items)
    for poly_id, (min_x, min_y, max_x, max_y), rings_list in candidates:
        if min_x <= lon <= max_x and min_y <= lat <= max_y:
            for poly_rings in rings_list:
                if is_point_in_poly(lon, lat, poly_rings):
                    return poly_id
    return None


def classify_service_category(desc, rules):
    if not desc:
        return "Government Info & Admin"
    desc_lower = desc.lower()
    for rule in rules:
        for kw in rule["keywords"]:
            if kw.lower() in desc_lower:
                return rule["category"]
    return "Government Info & Admin"


def normalize_ward_str(val):
    if not val:
        return None
    s = str(val).strip()
    if s.lower() in ("null", "none", ""):
        return None
    m = re.search(r"([1-8])", s)
    return m.group(1) if m else None


def build_warehouse():
    t0 = time.time()
    for path in (RAW_2025, RAW_2026, RAW_WEATHER, ANC_GEOJSON, WARD_GEOJSON, CONFIG_JSON):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required input file missing: {path}")

    with open(CONFIG_JSON, "r", encoding="utf-8") as f:
        config = json.load(f)
    category_rules = config.get("category_rules", [])

    if os.path.exists(WAREHOUSE_DB):
        os.remove(WAREHOUSE_DB)

    con = duckdb.connect(WAREHOUSE_DB)
    con.execute("SET TimeZone='America/New_York';")

    print("Loading raw 2025 and 2026 Parquet files into DuckDB staging...")
    con.execute(
        f"""
        CREATE TABLE raw_requests AS
        SELECT * FROM read_parquet(['{RAW_2025}', '{RAW_2026}'])
        WHERE ADDDATE IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY COALESCE(SERVICEREQUESTID, CAST(OBJECTID AS VARCHAR))
            ORDER BY COALESCE(EDITED, ADDDATE) DESC
        ) = 1
        """
    )
    raw_count = con.execute("SELECT COUNT(*) FROM raw_requests").fetchone()[0]
    print(f"Loaded {raw_count:,} deduplicated service requests.")

    # Build category lookup table for all distinct SERVICECODE + SERVICECODEDESCRIPTION pairs
    distinct_codes = con.execute(
        """
        SELECT DISTINCT
            COALESCE(SERVICECODE, 'UNKNOWN') AS service_code,
            COALESCE(SERVICECODEDESCRIPTION, 'Unknown Service Request') AS service_desc
        FROM raw_requests
        """
    ).fetchall()

    cat_rows = []
    for scode, sdesc in distinct_codes:
        cat = classify_service_category(sdesc, category_rules)
        cat_rows.append({"service_code": scode, "service_desc": sdesc, "category": cat})

    cat_table = pa.Table.from_pylist(cat_rows)
    con.register("cat_lookup_arrow", cat_table)
    con.execute("CREATE TABLE service_taxonomy AS SELECT * FROM cat_lookup_arrow")

    # Deduplicate coordinates for fast ANC, SMD & Ward point-in-polygon assignment
    print("Assigning 2023 ANC, SMD, and 2022 Ward boundaries to unique coordinate pairs...")
    anc_items, anc_grid = load_polygon_index(ANC_GEOJSON, "ANC_ID")
    smd_items, smd_grid = load_polygon_index(SMD_GEOJSON, "SMD_ID")
    ward_items, ward_grid = load_polygon_index(WARD_GEOJSON, "WARD")

    unique_coords = con.execute(
        """
        SELECT DISTINCT
            ROUND(LONGITUDE, 4) AS lon4,
            ROUND(LATITUDE, 4) AS lat4
        FROM raw_requests
        WHERE LONGITUDE IS NOT NULL
          AND LATITUDE IS NOT NULL
          AND LONGITUDE BETWEEN -77.15 AND -76.89
          AND LATITUDE BETWEEN 38.78 AND 39.01
        """
    ).fetchall()

    coord_rows = []
    for lon4, lat4 in unique_coords:
        anc_id = lookup_polygon(lon4, lat4, anc_grid, anc_items)
        smd_id = lookup_polygon(lon4, lat4, smd_grid, smd_items)
        ward_id = lookup_polygon(lon4, lat4, ward_grid, ward_items)
        if not ward_id and anc_id:
            m = re.match(r"^([1-8])", anc_id)
            if m:
                ward_id = m.group(1)
        coord_rows.append({
            "lon4": lon4,
            "lat4": lat4,
            "spatial_anc": anc_id,
            "spatial_smd": smd_id,
            "spatial_ward": ward_id,
        })

    coord_table = pa.Table.from_pylist(coord_rows)
    con.register("coord_lookup_arrow", coord_table)
    con.execute("CREATE TABLE coord_lookup AS SELECT * FROM coord_lookup_arrow")
    print(f"Mapped {len(coord_rows):,} unique coordinate cells to ANC and Ward polygons.")

    # Load daily weather table
    con.execute(
        f"""
        CREATE TABLE weather_daily AS
        SELECT
            CAST(date AS DATE) AS weather_date,
            temp_max_f,
            temp_min_f,
            temp_mean_f,
            precip_in,
            rain_in,
            snow_in,
            rain_3d_in,
            precip_3d_in,
            snow_3d_in,
            is_rainy_day,
            is_heavy_rain_day,
            is_snow_day,
            is_freeze_day,
            is_heat_day
        FROM read_parquet('{RAW_WEATHER}')
        """
    )

    # Create final enriched requests table
    print("Building enriched requests table in DuckDB...")
    con.execute(
        """
        CREATE TABLE requests AS
        WITH base AS (
            SELECT
                r.OBJECTID AS object_id,
                r.SERVICEREQUESTID AS service_request_id,
                COALESCE(r.SERVICECODE, 'UNKNOWN') AS service_code,
                COALESCE(r.SERVICECODEDESCRIPTION, 'Unknown Service Request') AS service_desc,
                COALESCE(r.SERVICETYPECODEDESCRIPTION, 'Other') AS service_type_desc,
                COALESCE(r.ORGANIZATIONACRONYM, 'UNKNOWN') AS agency,
                COALESCE(r.SERVICECALLCOUNT, 1) AS call_count,
                timezone('America/New_York', to_timestamp(r.ADDDATE / 1000.0)) AS add_ts,
                CAST(timezone('America/New_York', to_timestamp(r.ADDDATE / 1000.0)) AS DATE) AS add_date,
                CASE WHEN r.RESOLUTIONDATE IS NOT NULL AND r.RESOLUTIONDATE > 0
                     THEN timezone('America/New_York', to_timestamp(r.RESOLUTIONDATE / 1000.0))
                     ELSE NULL END AS resolution_ts,
                CASE WHEN r.SERVICEDUEDATE IS NOT NULL AND r.SERVICEDUEDATE > 0
                     THEN timezone('America/New_York', to_timestamp(r.SERVICEDUEDATE / 1000.0))
                     ELSE NULL END AS due_ts,
                COALESCE(r.SERVICEORDERSTATUS, 'UNKNOWN') AS order_status,
                COALESCE(r.STATUS_CODE, 'UNKNOWN') AS status_code,
                COALESCE(r.PRIORITY, 'STANDARD') AS priority,
                r.DETAILS AS details,
                r.STREETADDRESS AS street_address,
                r.ZIPCODE AS zipcode,
                NULLIF( regexp_extract(COALESCE(r.WARD, ''), '([1-8])', 1), '' ) AS raw_ward,
                r.LATITUDE AS latitude,
                r.LONGITUDE AS longitude,
                ROUND(r.LONGITUDE, 4) AS lon4,
                ROUND(r.LATITUDE, 4) AS lat4,
                r.MARADDRESSREPOSITORYID AS mar_id
            FROM raw_requests r
        )
        SELECT
            b.object_id,
            b.service_request_id,
            b.service_code,
            b.service_desc,
            t.category,
            b.service_type_desc,
            b.agency,
            b.call_count,
            b.add_ts,
            b.add_date,
            EXTRACT(YEAR FROM b.add_date) AS req_year,
            EXTRACT(MONTH FROM b.add_date) AS req_month,
            EXTRACT(DAYOFYEAR FROM b.add_date) AS req_doy,
            EXTRACT(ISODOW FROM b.add_date) AS req_isodow,
            EXTRACT(HOUR FROM b.add_ts) AS req_hour,
            DATE_TRUNC('week', b.add_date) AS req_week,
            b.resolution_ts,
            b.due_ts,
            CASE
                WHEN b.resolution_ts IS NOT NULL AND b.resolution_ts >= b.add_ts
                THEN ROUND(EXTRACT(EPOCH FROM (b.resolution_ts - b.add_ts)) / 3600.0, 2)
                ELSE NULL
            END AS resolution_hours,
            CASE
                WHEN b.resolution_ts IS NOT NULL OR UPPER(b.status_code) IN ('CLOSED', 'RESOLVED') OR UPPER(b.order_status) LIKE 'CLOSED%'
                THEN TRUE
                ELSE FALSE
            END AS is_closed,
            CASE
                WHEN b.due_ts IS NOT NULL AND b.resolution_ts IS NOT NULL
                THEN (b.resolution_ts <= b.due_ts)
                ELSE NULL
            END AS sla_met,
            b.order_status,
            b.status_code,
            b.priority,
            b.details,
            b.street_address,
            b.zipcode,
            COALESCE(b.raw_ward, c.spatial_ward) AS ward,
            c.spatial_anc AS anc,
            c.spatial_smd AS smd,
            b.latitude,
            b.longitude,
            b.mar_id,
            w.temp_max_f,
            w.temp_min_f,
            w.temp_mean_f,
            w.precip_in,
            w.rain_in,
            w.snow_in,
            w.rain_3d_in,
            w.precip_3d_in,
            w.snow_3d_in,
            w.is_rainy_day,
            w.is_heavy_rain_day,
            w.is_snow_day,
            w.is_freeze_day,
            w.is_heat_day
        FROM base b
        LEFT JOIN service_taxonomy t
          ON b.service_code = t.service_code AND b.service_desc = t.service_desc
        LEFT JOIN coord_lookup c
          ON b.lon4 = c.lon4 AND b.lat4 = c.lat4
        LEFT JOIN weather_daily w
          ON b.add_date = w.weather_date
        WHERE EXTRACT(YEAR FROM b.add_date) IN (2025, 2026)
        """
    )

    con.execute("DROP TABLE raw_requests")
    con.execute("DROP TABLE coord_lookup")

    summary = con.execute(
        """
        SELECT
            req_year,
            COUNT(*) AS total,
            COUNT(ward) AS with_ward,
            COUNT(anc) AS with_anc,
            COUNT(smd) AS with_smd,
            COUNT(details) AS with_details,
            MIN(add_date) AS min_date,
            MAX(add_date) AS max_date
        FROM requests
        GROUP BY req_year
        ORDER BY req_year
        """
    ).fetchall()

    for row in summary:
        yr, tot, w_cnt, a_cnt, s_cnt, d_cnt, min_d, max_d = row
        print(
            f"  Year {yr}: {tot:,} rows ({min_d} to {max_d}) | "
            f"Ward: {w_cnt / tot * 100:.1f}% | ANC: {a_cnt / tot * 100:.1f}% | SMD: {s_cnt / tot * 100:.1f}% | "
            f"Details: {d_cnt / tot * 100:.1f}%"
        )

    con.close()
    print(f"Warehouse built in {time.time() - t0:.1f}s at {WAREHOUSE_DB}")


if __name__ == "__main__":
    build_warehouse()
