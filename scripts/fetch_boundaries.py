#!/usr/bin/env python3
"""
Fetch and verify DC Administrative Boundary GeoJSON files (Wards and 2023 ANCs).
Strictly adheres to:
- Strictly zero emojis across code, logs, and outputs
"""

import json
import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANC_PATH = os.path.join(BASE_DIR, "data", "dc_ancs.geojson")
WARD_PATH = os.path.join(BASE_DIR, "data", "dc_wards.geojson")

ANC_URL = (
    "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/"
    "Administrative_Other_Boundaries_WebMercator/MapServer/54/query"
    "?where=1%3D1&outFields=ANC_ID,NAME,WEB_URL&outSR=4326&f=geojson"
)


def round_coords(coords, precision=5):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], precision), round(coords[1], precision)]
    return [round_coords(c, precision) for c in coords]


def fetch_anc_boundaries(force=False):
    if os.path.exists(ANC_PATH) and not force:
        with open(ANC_PATH, "r", encoding="utf-8") as f:
            gj = json.load(f)
        print(f"Verified existing ANC GeoJSON: {len(gj.get('features', []))} ANCs")
        return len(gj.get("features", []))

    print("Downloading 2023 ANC boundary polygons from Open Data DC...")
    req = urllib.request.Request(
        ANC_URL, headers={"User-Agent": "DC-311-Sentinel-Pipeline/1.0"}
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        gj = json.load(resp)

    features = gj.get("features", [])
    for feat in features:
        geom = feat.get("geometry")
        if geom and "coordinates" in geom:
            geom["coordinates"] = round_coords(geom["coordinates"], 5)

    os.makedirs(os.path.dirname(ANC_PATH), exist_ok=True)
    with open(ANC_PATH, "w", encoding="utf-8") as f:
        json.dump(gj, f, separators=(",", ":"))

    print(f"Saved {len(features)} ANC polygons to {ANC_PATH}")
    return len(features)


if __name__ == "__main__":
    fetch_anc_boundaries()
    if os.path.exists(WARD_PATH):
        with open(WARD_PATH, "r", encoding="utf-8") as f:
            w = json.load(f)
        print(f"Verified Ward GeoJSON: {len(w.get('features', []))} Wards")
