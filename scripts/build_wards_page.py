#!/usr/bin/env python3
"""Deprecated: wards.html has been deprecated in favor of map.html."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REDIRECT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=map.html">
  <link rel="canonical" href="map.html">
  <title>DC 311 Sentinel • Redirecting to Map</title>
</head>
<body>
  <p>The Wards &amp; ANCs section has been deprecated. Redirecting to <a href="map.html">Map</a>...</p>
</body>
</html>
"""


def build_wards():
    out_path = os.path.join(BASE_DIR, "wards.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(REDIRECT_HTML)
    print(f"Wrote deprecated redirect {out_path} -> map.html")


if __name__ == "__main__":
    build_wards()
