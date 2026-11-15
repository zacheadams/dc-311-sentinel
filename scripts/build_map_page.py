#!/usr/bin/env python3
"""
Compiles the Interactive Spatial Choropleth Explorer (map.html).
Features:
- Full-viewport Leaflet map with floating glassmorphic Control, Inspector, and Legend panels
- Offline Stamen Toner local basemap tiles (tiles/light/ and tiles/blacklite/, zooms 11-17)
- Toggleable 46-ANC and 8-Ward choropleth polygons with permanent dashed Ward boundaries
- Interactive hover highlights, sticky cursor-following tooltips, animated fitBounds focus, and contextual dimming
- Filter by All 311 Requests, any of the 11 Category Families, or Top 45 Specific Service Queries
- Switchable metric: 2026 YTD Volume, Same-Period YoY %, 30-Day YoY %, Location Quotient (LQ), Open Backlog %
- Geographic Subset search & Ward/ANC drilldown with Reset to Default
- Mobile responsive bottom drawers (Control drawer + two-snap Peek/Expanded Inspector drawer) with swipe-to-dismiss
- Strictly zero emojis across code, markup, and UI
"""

import json
import os
from html import escape

from ui_common import COMMON_CSS, COMMON_HEAD_FONTS, COMMON_THEME_AND_SORT_JS, render_nav, render_footer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_map():
    with open(os.path.join(BASE_DIR, "data", "geography_stats.json"), "r", encoding="utf-8") as f:
        geo = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "summary_top.json"), "r", encoding="utf-8") as f:
        summary = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "dc_wards.geojson"), "r", encoding="utf-8") as f:
        wards_geojson = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "dc_ancs.geojson"), "r", encoding="utf-8") as f:
        ancs_geojson = json.load(f)

    categories = [c["category"] for c in summary["categories"]]
    dynamic_codes = geo["map_dynamic_codes"]
    meta = summary.get("metadata", {})
    total_ytd = meta.get("total_2026_ytd", 0)
    city_summary = {
        "count_2026_ytd": meta.get("total_2026_ytd", 0),
        "count_2025_ytd": meta.get("total_2025_ytd", 0),
        "yoy_pct": meta.get("yoy_pct", 0.0),
        "d30_yoy_pct": meta.get("d30_yoy_pct", 0.0),
        "open_count": meta.get("open_backlog_2026", 0),
        "open_pct": round((meta.get("open_backlog_2026", 0) / total_ytd * 100.0), 1) if total_ytd else 0.0,
        "top_requests": [
            {
                "service_desc": sq.get("service_desc", ""),
                "count_2026_ytd": sq.get("count_2026_ytd", 0),
                "share_pct": round((sq.get("count_2026_ytd", 0) / total_ytd * 100.0), 1) if total_ytd else 0.0,
            }
            for sq in summary.get("service_queries", [])[:6]
        ],
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DC 311 Sentinel • Interactive Ward & ANC Map Explorer</title>
{COMMON_HEAD_FONTS}
  <link rel="stylesheet" href="assets/vendor/leaflet/leaflet.css">
  <script src="assets/vendor/leaflet/leaflet.js"></script>
  <style>
{COMMON_CSS}
    body {{
      padding-bottom: 0;
      overflow: hidden;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    .leaflet-container, .leaflet-popup, .leaflet-control, .leaflet-tooltip {{
      font-family: var(--font-mono) !important;
    }}

    /* Full-Viewport Map Workspace */
    .map-workspace {{
      position: relative;
      flex: 1;
      width: 100vw;
      height: calc(100vh - 53px);
      overflow: hidden;
    }}

    #map-canvas {{
      width: 100%;
      height: 100%;
      background: var(--bg-page);
    }}

    /* Floating Left Control Panel */
    .control-panel {{
      position: absolute;
      top: 14px;
      left: 14px;
      width: 325px;
      max-height: calc(100vh - 140px);
      overflow-y: auto;
      background: var(--bg-panel);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 14px;
      z-index: 500;
      box-shadow: var(--card-shadow);
      transition: background 0.2s, border-color 0.2s;
    }}

    .control-panel .site-footer {{
      margin-top: 10px;
      padding-top: 8px;
      padding-bottom: 0;
      font-size: 10px;
    }}

    .control-divider {{
      border-top: 1px solid var(--border);
      margin: 10px 0;
    }}

    .sidebar-label {{
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-main);
      display: block;
      margin-bottom: 5px;
    }}

    .sidebar-select {{
      width: 100%;
      background: var(--bg-surface);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 5px 8px;
      border-radius: 2px;
      font-size: 11px;
      margin-bottom: 8px;
    }}

    .sidebar-select:focus {{
      outline: none;
      border-color: var(--border-focus);
    }}

    .sidebar-select:disabled {{
      opacity: 0.45;
      cursor: not-allowed;
    }}

    .search-box {{
      margin-bottom: 8px;
    }}

    .search-box input {{
      width: 100%;
      background: var(--bg-surface);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 6px 8px;
      border-radius: 2px;
      font-size: 11px;
    }}

    .search-box input:focus {{
      outline: none;
      border-color: var(--border-focus);
    }}

    .hierarchy-container {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .hierarchy-row {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .hierarchy-label {{
      width: 40px;
      font-size: 10px;
      font-weight: 700;
      color: var(--text-dim);
      text-transform: uppercase;
      flex-shrink: 0;
    }}

    .hierarchy-row .sidebar-select {{
      flex: 1;
      margin-bottom: 0;
    }}

    /* Floating Right Inspector Panel */
    .inspector-panel {{
      position: absolute;
      top: 14px;
      right: 14px;
      width: 335px;
      max-height: calc(100vh - 96px);
      overflow-y: auto;
      background: var(--bg-panel);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 14px;
      z-index: 500;
      box-shadow: var(--card-shadow);
      transition: background 0.2s, border-color 0.2s;
    }}

    .inspector-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 8px;
      padding-bottom: 6px;
      border-bottom: 1px solid var(--border);
    }}

    .inspector-title {{
      font-size: 15px;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.01em;
    }}

    .inspector-sub {{
      font-size: 10px;
      color: var(--text-dim);
      margin-top: 2px;
    }}

    .inspector-filter-pill {{
      font-size: 10px;
      font-weight: 700;
      color: var(--text-muted);
      background: var(--bg-input);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 4px 8px;
      margin-bottom: 8px;
    }}

    .inspector-stat-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      margin-bottom: 10px;
    }}

    .stat-tile {{
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 6px 8px;
    }}

    .stat-tile-lbl {{
      font-size: 9px;
      color: var(--text-dim);
      text-transform: uppercase;
      font-weight: 700;
    }}

    .stat-tile-val {{
      font-size: 15px;
      font-weight: 800;
      color: var(--text-main);
    }}

    .inspector-details {{
      font-size: 11px;
      color: var(--text-muted);
      line-height: 1.45;
    }}

    .inspector-section-title {{
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
      margin: 10px 0 4px 0;
      letter-spacing: 0.03em;
    }}

    .inspector-list-row {{
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-size: 11px;
      padding: 3px 0;
      border-bottom: 1px dashed var(--border);
    }}

    /* Floating Bottom-Left Legend Panel */
    .legend-panel {{
      position: absolute;
      bottom: 20px;
      left: 14px;
      background: var(--bg-panel);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 8px 12px;
      z-index: 500;
      font-size: 10px;
      box-shadow: var(--card-shadow);
      transition: opacity 0.2s ease, background 0.2s, border-color 0.2s;
      min-width: 190px;
      max-width: 280px;
    }}

    .legend-title {{
      font-weight: 700;
      color: var(--text-main);
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      line-height: 1.3;
      margin-bottom: 6px;
    }}

    .legend-scale {{
      display: flex;
      align-items: center;
      gap: 2px;
      width: 100%;
    }}

    .scale-box {{
      flex: 1;
      min-width: 24px;
      height: 10px;
      border-radius: 2px;
      border: 1px solid rgba(0, 0, 0, 0.15);
    }}

    .scale-labels {{
      display: flex;
      justify-content: space-between;
      color: var(--text-dim);
      font-size: 9px;
      margin-top: 4px;
      gap: 8px;
    }}

    /* Leaflet Tooltips & Attribution */
    .leaflet-tooltip-map {{
      background: var(--bg-panel) !important;
      border: 1px solid var(--border-dark) !important;
      color: var(--text-main) !important;
      border-radius: 2px !important;
      padding: 6px 10px !important;
      font-family: var(--font-mono) !important;
      box-shadow: var(--card-shadow) !important;
    }}

    .leaflet-control-attribution {{
      background: var(--bg-panel) !important;
      backdrop-filter: blur(8px);
      color: var(--text-dim) !important;
      border: 1px solid var(--border) !important;
      border-radius: 2px !important;
      padding: 3px 8px !important;
      font-size: 10px !important;
      font-family: var(--font-mono) !important;
      margin: 0 10px 10px 0 !important;
      box-shadow: var(--card-shadow) !important;
    }}

    .leaflet-control-attribution a {{
      color: var(--accent) !important;
      text-decoration: none !important;
    }}

    .leaflet-control-attribution a:hover {{
      text-decoration: underline !important;
    }}

    /* Mobile controls hidden on desktop */
    .mobile-fab {{ display: none; }}
    .drawer-backdrop {{ display: none; }}
    .sheet-handle {{ display: none; }}
    .mobile-control-header {{ display: none; }}
    .mobile-inspector-toggle {{ display: none; }}

    @media (max-width: 768px) {{
      .site-nav {{
        padding: 8px 12px;
        flex-wrap: wrap;
        gap: 6px;
      }}
      .nav-subtitle {{
        display: none;
      }}
      .nav-links {{
        width: 100%;
        overflow-x: auto;
        padding-bottom: 2px;
        gap: 6px;
        -webkit-overflow-scrolling: touch;
      }}
      .nav-link, .btn-action {{
        font-size: 11px;
        padding: 5px 8px;
        white-space: nowrap;
        flex-shrink: 0;
      }}
      .map-workspace {{
        height: calc(100vh - 84px);
      }}

      /* Control Panel -> Bottom Drawer */
      .control-panel {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        top: auto;
        width: 100%;
        max-height: 82vh;
        border-radius: 2px 2px 0 0;
        border-left: none;
        border-right: none;
        border-bottom: none;
        padding: 0 14px env(safe-area-inset-bottom, 20px) 14px;
        z-index: 700;
        transform: translateY(100%);
        transition: transform 0.32s cubic-bezier(0.32, 0.72, 0, 1);
        overflow-y: auto;
        -webkit-overflow-scrolling: touch;
        will-change: transform;
      }}
      .control-panel.is-open {{
        transform: translateY(0);
      }}
      .mobile-control-header {{
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-bottom: 8px;
        cursor: grab;
        user-select: none;
        -webkit-user-select: none;
        touch-action: none;
      }}
      .mobile-control-title {{
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--text-main);
      }}

      /* Inspector Panel -> Two-Snap Bottom Drawer */
      .inspector-panel {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        top: auto;
        width: 100%;
        border-radius: 2px 2px 0 0;
        border-left: none;
        border-right: none;
        border-bottom: none;
        padding: 0 14px env(safe-area-inset-bottom, 20px) 14px;
        z-index: 650;
        transform: translateY(100%);
        transition: transform 0.32s cubic-bezier(0.32, 0.72, 0, 1);
        overflow: hidden;
        will-change: transform;
        max-height: 65vh;
        box-shadow: 0 -6px 24px rgba(0, 0, 0, 0.25);
      }}
      .inspector-panel.is-peek {{
        transform: translateY(0);
        max-height: 145px;
        overflow: hidden;
      }}
      .inspector-panel.is-expanded {{
        transform: translateY(0);
        max-height: 65vh;
        overflow-y: auto;
        -webkit-overflow-scrolling: touch;
      }}
      .inspector-header {{
        align-items: center;
        cursor: pointer;
        padding-bottom: 4px;
      }}
      .mobile-inspector-toggle {{
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 44px;
        min-height: 44px;
        font-size: 13px;
        font-weight: 800;
        color: var(--accent);
      }}
      .sheet-handle {{
        display: block;
        width: 36px;
        height: 4px;
        border-radius: 2px;
        background: var(--border-dark);
        margin: 10px auto 8px auto;
        flex-shrink: 0;
        cursor: grab;
        touch-action: none;
      }}

      .mobile-fab {{
        display: flex;
        position: fixed;
        bottom: 20px;
        left: 16px;
        z-index: 800;
        background: var(--bg-panel);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 2px;
        padding: 10px 16px;
        font-size: 12px;
        font-weight: 700;
        color: var(--text-main);
        cursor: pointer;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.22);
        align-items: center;
        gap: 6px;
        min-height: 44px;
        min-width: 44px;
        transition: background 0.15s, transform 0.15s;
      }}
      .mobile-fab:active {{
        transform: scale(0.96);
        background: var(--bg-input);
      }}

      .drawer-backdrop {{
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.38);
        z-index: 600;
      }}
      .drawer-backdrop.is-visible {{
        display: block;
      }}

      .legend-panel {{
        position: fixed;
        bottom: 80px;
        left: 16px;
        right: auto;
        padding: 6px 10px;
        max-width: calc(100vw - 80px);
        z-index: 500;
      }}
      body.drawer-active .legend-panel,
      body.drawer-active .mobile-fab,
      body.drawer-active .leaflet-bottom.leaflet-right {{
        opacity: 0;
        pointer-events: none;
      }}

      .leaflet-bottom.leaflet-right {{
        display: block;
        position: fixed !important;
        bottom: 20px;
        right: 12px;
        left: auto;
        top: auto;
        z-index: 400;
        pointer-events: none;
        transition: opacity 0.2s ease;
      }}
      .leaflet-bottom.leaflet-right .leaflet-control {{
        margin: 0 0 6px 0 !important;
        pointer-events: auto;
      }}
      .leaflet-control-attribution {{
        max-width: min(240px, calc(100vw - 120px)) !important;
        text-align: right;
        font-size: 9px !important;
        margin: 0 !important;
      }}

      .sidebar-select, #geo-search {{
        min-height: 44px;
        font-size: 13px;
      }}
    }}
  </style>
</head>
<body>
{render_nav("map.html")}

  <div class="map-workspace" id="map-interactive">
    <div id="map-canvas"></div>

    <!-- Mobile FAB: opens Layers & Filters drawer -->
    <button class="mobile-fab" id="mobile-fab-filters" onclick="toggleDrawer('control')" aria-label="Open map layers">
      [=] Layers
    </button>

    <!-- Backdrop: tap to dismiss any open drawer -->
    <div class="drawer-backdrop" id="drawer-backdrop" onclick="closeAllDrawers()" aria-hidden="true"></div>

    <!-- Floating Left Control Panel -->
    <aside class="control-panel" id="control-panel">
      <div class="mobile-control-header" id="ctrl-sheet-handle">
        <div class="sheet-handle"></div>
        <div class="mobile-control-title">Filters &amp; Layers</div>
      </div>

      <label class="sidebar-label" for="geo-level-select">Geographic Layer</label>
      <select id="geo-level-select" class="sidebar-select" onchange="handleGeoLevelChange()">
        <option value="WARD" selected>Wards (8 Wards)</option>
        <option value="ANC">Advisory Neighborhood Commissions (46 ANCs)</option>
      </select>

      <label class="sidebar-label" for="stream-select">311 Request Filter</label>
      <select id="stream-select" class="sidebar-select" onchange="updateMapChoropleth()">
        <option value="ALL">All 311 Service Requests ({total_ytd:,} YTD)</option>
        <optgroup label="Operational Category Families (11)">
          {''.join(f'<option value="CAT:{escape(c)}">Category: {escape(c)}</option>' for c in categories)}
        </optgroup>
        <optgroup label="Top 45 Specific Service Requests">
          {''.join(f'<option value="CODE:{escape(d["service_code"])}">{escape(d["service_desc"])} [{escape(d["service_code"])}]</option>' for d in dynamic_codes)}
        </optgroup>
      </select>

      <label class="sidebar-label" for="metric-select">Choropleth Metric</label>
      <select id="metric-select" class="sidebar-select" style="margin-bottom:0;" onchange="updateMapChoropleth()">
        <option value="c26">2026 YTD Request Volume</option>
        <option value="lq">Location Quotient (LQ Concentration)</option>
        <option value="yoy_pct">Same-Period YoY % Change (2026 vs 2025)</option>
        <option value="d30_pct">Last 30 Days YoY % Change</option>
        <option value="open_pct">Open Backlog %</option>
      </select>

      <div class="control-divider"></div>

      <label class="sidebar-label" for="geo-search">Geographic Subset</label>
      <div class="search-box">
        <input type="text" id="geo-search" placeholder="Search ANC (e.g. 1A), Ward, or Councilmember..." oninput="handleGeoSearch(this.value)">
      </div>

      <div class="hierarchy-container">
        <div class="hierarchy-row">
          <span class="hierarchy-label">Ward</span>
          <select class="sidebar-select" id="ward-filter-select" onchange="handleWardDropdown(this.value)">
            <option value="all">All Wards (Citywide)</option>
          </select>
        </div>
        <div class="hierarchy-row" id="anc-filter-row" style="display:none;">
          <span class="hierarchy-label">ANC</span>
          <select class="sidebar-select" id="anc-filter-select" onchange="handleAncDropdown(this.value)" disabled>
            <option value="all">-- Select Ward First --</option>
          </select>
        </div>
      </div>

      <div class="control-divider"></div>

      <button id="btn-reset-default" class="btn-action" style="width:100%;text-align:center;padding:7px 10px;font-weight:700;border-radius:2px;" onclick="resetToDefault()">Reset to Default</button>
{render_footer()}
    </aside>

    <!-- Floating Right Inspector Panel -->
    <aside class="inspector-panel" id="inspector-panel">
      <div class="sheet-handle" id="insp-sheet-handle"></div>
      <div class="inspector-header" id="insp-header" onclick="handleInspectorHeaderTap()">
        <div>
          <div class="inspector-title" id="insp-title">District of Columbia</div>
          <div class="inspector-sub" id="insp-sub">Citywide 311 Summary</div>
        </div>
        <div class="mobile-inspector-toggle" id="insp-toggle-icon">^</div>
      </div>
      <div id="insp-body">
        <!-- Populated dynamically -->
      </div>
    </aside>

    <!-- Floating Bottom-Left Legend Panel -->
    <div class="legend-panel" id="legend-panel">
      <div class="legend-title" id="legend-title">2026 YTD Request Volume</div>
      <div class="legend-scale" id="legend-scale"></div>
      <div class="scale-labels" id="legend-labels"></div>
    </div>
  </div>

{COMMON_THEME_AND_SORT_JS}
  <script>
    const GEO_STATS = {json.dumps(geo)};
    const CITY_SUMMARY = {json.dumps(city_summary)};
    const WARDS_GJ = {json.dumps(wards_geojson)};
    const ANCS_GJ = {json.dumps(ancs_geojson)};

    // Green (low/good) -> Yellow (neutral/mid) -> Red (high/bad) spectrum
    const GOOD_TO_BAD_RAMP = ['#16a34a', '#84cc16', '#facc15', '#f97316', '#dc2626'];
    const RAMPS = {{
      volume: GOOD_TO_BAD_RAMP,
      lq:     GOOD_TO_BAD_RAMP,
      surge:  GOOD_TO_BAD_RAMP,
      open:   GOOD_TO_BAD_RAMP
    }};

    const METRIC_ACCENTS = {{
      c26: '#2563eb',
      lq: '#7c3aed',
      yoy_pct: '#dc2626',
      d30_pct: '#dc2626',
      open_pct: '#d97706'
    }};

    const METRIC_LABELS = {{
      c26: '2026 YTD Volume',
      lq: 'Location Quotient (LQ)',
      yoy_pct: 'Same-Period YoY %',
      d30_pct: 'Last 30 Days YoY %',
      open_pct: 'Open Backlog %'
    }};

    let map = null;
    let tileLayer = null;
    let choroLayer = null;
    let wardOutlineLayer = null;
    let activeHoverLayer = null;

    let selectedWardNum = null;
    let selectedFeatureId = null;
    let currentQuantiles = {{ minV: 0, maxV: 1, q20: 0, q40: 0, q60: 0, q80: 0 }};

    const choroTooltip = L.tooltip({{
      sticky: true,
      direction: 'top',
      className: 'leaflet-tooltip-map',
      offset: [0, -10]
    }});

    function getTileUrl() {{
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      return dark ? 'tiles/blacklite/{{z}}/{{x}}/{{y}}.png' : 'tiles/light/{{z}}/{{x}}/{{y}}.png';
    }}

    function initMap() {{
      map = L.map('map-canvas', {{
        center: [38.904, -77.015],
        zoom: 12,
        zoomControl: false,
        minZoom: 11,
        maxZoom: 17,
        scrollWheelZoom: true
      }});

      L.control.zoom({{ position: 'bottomright' }}).addTo(map);

      map.createPane('tonerBasePane');
      map.getPane('tonerBasePane').style.zIndex = 200;

      map.createPane('choroPane');
      map.getPane('choroPane').style.zIndex = 350;

      map.createPane('wardPane');
      map.getPane('wardPane').style.zIndex = 390;

      tileLayer = L.tileLayer(getTileUrl(), {{
        pane: 'tonerBasePane',
        maxNativeZoom: 17,
        maxZoom: 17,
        attribution: 'Map tiles by Stamen Design (CC BY 4.0) &bull; Data: Open Data DC'
      }}).addTo(map);

      /*
      // Contingency U.S. Census Bureau TIGERweb fallback configuration:
      // https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer
      */

      populateWardDropdown();
      initMobileHandling();
      renderWardPermanentBoundaries();
      updateMapChoropleth();
    }}

    function populateWardDropdown() {{
      const wSel = document.getElementById('ward-filter-select');
      if (!wSel) return;
      const wards = Object.keys(GEO_STATS.wards).sort((a, b) => Number(a) - Number(b));
      wSel.innerHTML = '<option value="all">All Wards (Citywide)</option>' +
        wards.map(w => {{
          const p = GEO_STATS.wards[w];
          return `<option value="${{w}}">Ward ${{w}} - ${{p.councilmember}}</option>`;
        }}).join('');
    }}

    function populateAncDropdown(wardVal) {{
      const aSel = document.getElementById('anc-filter-select');
      if (!aSel) return;
      if (!wardVal || wardVal === 'all') {{
        aSel.innerHTML = '<option value="all">-- Select Ward First --</option>';
        aSel.disabled = true;
        return;
      }}
      const ancs = Object.keys(GEO_STATS.ancs)
        .filter(id => String(GEO_STATS.ancs[id].ward) === String(wardVal))
        .sort();
      aSel.innerHTML = `<option value="all">All ANCs in Ward ${{wardVal}} (${{ancs.length}})</option>` +
        ancs.map(id => `<option value="${{id}}">ANC ${{id}}</option>`).join('');
      aSel.disabled = false;
    }}

    function renderWardPermanentBoundaries() {{
      if (wardOutlineLayer) map.removeLayer(wardOutlineLayer);
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      wardOutlineLayer = L.geoJSON(WARDS_GJ, {{
        pane: 'wardPane',
        interactive: false,
        style: feature => {{
          const wid = String(feature.properties.WARD).trim();
          const isSelectedWard = selectedWardNum && String(selectedWardNum) === wid;
          return {{
            color: dark ? '#c084fc' : '#7c3aed',
            weight: isSelectedWard ? 3.5 : 2.0,
            dashArray: '5, 5',
            fillOpacity: 0
          }};
        }}
      }}).addTo(map);
    }}

    function extractMetricObj(profile, streamKey) {{
      if (!profile) return {{ c26: 0, c25: 0, yoy_pct: 0, d30_pct: 0, lq: 1.0, open_pct: 0 }};
      if (streamKey === 'ALL') {{
        return {{
          c26: profile.count_2026_ytd,
          c25: profile.count_2025_ytd,
          yoy_pct: profile.yoy_pct,
          d30_pct: profile.d30_yoy_pct,
          lq: 1.0,
          open_pct: profile.open_pct
        }};
      }}
      if (streamKey.startsWith('CAT:')) {{
        const catName = streamKey.slice(4);
        return profile.categories[catName] || {{ c26: 0, c25: 0, yoy_pct: 0, d30_pct: 0, lq: 0, open_pct: 0 }};
      }}
      if (streamKey.startsWith('CODE:')) {{
        const code = streamKey.slice(5);
        return profile.top_codes[code] || {{ c26: 0, c25: 0, yoy_pct: 0, d30_pct: 0, lq: 0, open_pct: 0 }};
      }}
      return {{ c26: 0, c25: 0, yoy_pct: 0, d30_pct: 0, lq: 1.0, open_pct: 0 }};
    }}

    function getRampForMetric(metric) {{
      if (metric === 'lq') return RAMPS.lq;
      if (metric === 'yoy_pct' || metric === 'd30_pct') return RAMPS.surge;
      if (metric === 'open_pct') return RAMPS.open;
      return RAMPS.volume;
    }}

    function getMetricScale(metric, q) {{
      if (metric === 'c26' || metric === 'open_pct') {{
        const scaleMax = q.maxV > 0 ? q.maxV : (metric === 'c26' ? 10 : 1);
        return {{ scaleMin: 0, scaleMid: scaleMax / 2, scaleMax }};
      }}
      if (metric === 'yoy_pct' || metric === 'd30_pct') {{
        const halfSpan = Math.max(Math.abs(q.minV), Math.abs(q.maxV), 1);
        return {{ scaleMin: -halfSpan, scaleMid: 0, scaleMax: halfSpan }};
      }}
      if (metric === 'lq') {{
        const isFlatOne = q.minV === 1 && q.maxV === 1;
        const halfSpan = isFlatOne ? 1 : Math.max(1 - q.minV, q.maxV - 1, 0.1);
        return {{
          scaleMin: Math.max(0, 1 - halfSpan),
          scaleMid: 1,
          scaleMax: Math.max(q.maxV, 1 + halfSpan)
        }};
      }}
      return {{ scaleMin: q.minV, scaleMid: q.q40, scaleMax: q.maxV }};
    }}

    function pickColor(v, ramp, metric, q) {{
      const {{ scaleMin, scaleMid, scaleMax }} = getMetricScale(metric, q);
      let t;
      if (v <= scaleMid) {{
        const denom = scaleMid - scaleMin;
        t = denom > 0 ? 0.5 * (v - scaleMin) / denom : 0.5;
      }} else {{
        const denom = scaleMax - scaleMid;
        t = denom > 0 ? 0.5 + 0.5 * (v - scaleMid) / denom : 0.5;
      }}
      t = Math.min(1, Math.max(0, t));
      const idx = Math.min(ramp.length - 1, Math.max(0, Math.floor(t * ramp.length)));
      return ramp[idx];
    }}

    function formatMetricValue(v, metric) {{
      if (metric === 'c26') return Math.round(v).toLocaleString();
      if (metric === 'lq') return v.toFixed(2) + 'x';
      const prefix = (metric === 'yoy_pct' || metric === 'd30_pct') && v > 0 ? '+' : '';
      return prefix + v.toFixed(1) + '%';
    }}

    function getFeatureStyle(feature) {{
      const geoLevel = document.getElementById('geo-level-select').value;
      const streamKey = document.getElementById('stream-select').value;
      const metric = document.getElementById('metric-select').value;
      const profilesDict = geoLevel === 'WARD' ? GEO_STATS.wards : GEO_STATS.ancs;
      const idProp = geoLevel === 'WARD' ? 'WARD' : 'ANC_ID';

      const id = String(feature.properties[idProp]).trim();
      const p = profilesDict[id];
      const m = extractMetricObj(p, streamKey);
      const v = m[metric] || 0;
      const ramp = getRampForMetric(metric);
      const fillColor = pickColor(v, ramp, metric, currentQuantiles);
      const accent = METRIC_ACCENTS[metric] || '#2563eb';
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      const baseBorder = dark ? '#3f3f46' : '#18181b';

      if (selectedFeatureId) {{
        if (id === selectedFeatureId) {{
          return {{
            fillColor,
            fillOpacity: 0.92,
            color: accent,
            weight: 3.8,
            opacity: 1
          }};
        }}
        if (geoLevel === 'ANC' && selectedWardNum && p && String(p.ward) === String(selectedWardNum)) {{
          return {{
            fillColor,
            fillOpacity: 0.42,
            color: accent,
            weight: 1.0,
            opacity: 0.65
          }};
        }}
        return {{
          fillColor,
          fillOpacity: 0.14,
          color: baseBorder,
          weight: 0.6,
          opacity: 0.25
        }};
      }}

      if (selectedWardNum && geoLevel === 'ANC' && p) {{
        if (String(p.ward) === String(selectedWardNum)) {{
          return {{
            fillColor,
            fillOpacity: 0.80,
            color: accent,
            weight: 1.5,
            opacity: 0.95
          }};
        }}
        return {{
          fillColor,
          fillOpacity: 0.14,
          color: baseBorder,
          weight: 0.6,
          opacity: 0.25
        }};
      }}

      return {{
        fillColor,
        fillOpacity: 0.68,
        color: baseBorder,
        weight: geoLevel === 'WARD' ? 2.0 : 1.1,
        opacity: 0.85
      }};
    }}

    function handleGeoLevelChange() {{
      selectedFeatureId = null;
      selectedWardNum = null;
      document.getElementById('ward-filter-select').value = 'all';
      populateAncDropdown('all');
      document.getElementById('anc-filter-row').style.display =
        document.getElementById('geo-level-select').value === 'ANC' ? 'flex' : 'none';
      updateMapChoropleth();
      map.setView([38.904, -77.015], 12, {{ animate: true }});
    }}

    function updateMapChoropleth() {{
      const geoLevel = document.getElementById('geo-level-select').value;
      const streamKey = document.getElementById('stream-select').value;
      const metric = document.getElementById('metric-select').value;

      const profilesDict = geoLevel === 'WARD' ? GEO_STATS.wards : GEO_STATS.ancs;
      const gj = geoLevel === 'WARD' ? WARDS_GJ : ANCS_GJ;
      const idProp = geoLevel === 'WARD' ? 'WARD' : 'ANC_ID';

      const vals = [];
      gj.features.forEach(f => {{
        const id = String(f.properties[idProp]).trim();
        const m = extractMetricObj(profilesDict[id], streamKey);
        vals.push(m[metric] || 0);
      }});
      vals.sort((a, b) => a - b);
      currentQuantiles = {{
        minV: vals[0] || 0,
        maxV: vals[vals.length - 1] || 1,
        q20: vals[Math.floor(vals.length * 0.2)] || 0,
        q40: vals[Math.floor(vals.length * 0.4)] || 0,
        q60: vals[Math.floor(vals.length * 0.6)] || 0,
        q80: vals[Math.floor(vals.length * 0.8)] || 0
      }};

      activeHoverLayer = null;
      if (choroLayer) map.removeLayer(choroLayer);

      choroLayer = L.geoJSON(gj, {{
        pane: 'choroPane',
        style: getFeatureStyle,
        onEachFeature: (feature, layer) => {{
          const id = String(feature.properties[idProp]).trim();
          const p = profilesDict[id];
          const m = extractMetricObj(p, streamKey);
          const label = geoLevel === 'WARD' ? `Ward ${{id}}` : `ANC ${{id}} (Ward ${{p ? p.ward : ''}})`;
          const accent = METRIC_ACCENTS[metric] || '#2563eb';

          layer.on({{
            mouseover: function(e) {{
              if (activeHoverLayer && activeHoverLayer !== layer) {{
                const prevId = String(activeHoverLayer.feature.properties[idProp]).trim();
                if (!selectedFeatureId || selectedFeatureId !== prevId) {{
                  choroLayer.resetStyle(activeHoverLayer);
                }}
              }}
              activeHoverLayer = layer;
              layer.setStyle({{ weight: 3.8, color: accent, fillOpacity: 0.90, opacity: 1 }});
              if (layer.bringToFront) layer.bringToFront();

              const metricVal = formatMetricValue(m[metric] || 0, metric);
              choroTooltip.setContent(`
                <div style="font-weight:800;font-size:12px;color:var(--text-main);">${{label}}</div>
                <div style="font-size:10px;color:var(--text-dim);">${{p ? p.councilmember : ''}}</div>
                <div style="margin-top:4px;font-size:12px;font-weight:700;color:${{accent}};">
                  ${{METRIC_LABELS[metric]}}: ${{metricVal}}
                </div>
                <div style="font-size:10px;color:var(--text-muted);margin-top:2px;">
                  2026 YTD: ${{m.c26.toLocaleString()}} &bull; YoY: ${{m.yoy_pct >= 0 ? '+' : ''}}${{m.yoy_pct}}% &bull; LQ: ${{m.lq.toFixed(2)}}x
                </div>
              `);
              choroTooltip.setLatLng(e.latlng);
              if (!map.hasLayer(choroTooltip)) choroTooltip.openOn(map);
            }},
            mousemove: function(e) {{
              choroTooltip.setLatLng(e.latlng);
            }},
            mouseout: function() {{
              if (!selectedFeatureId || selectedFeatureId !== id) {{
                choroLayer.resetStyle(layer);
              }}
              if (activeHoverLayer === layer) activeHoverLayer = null;
              choroTooltip.close();
            }},
            click: function() {{
              if (selectedFeatureId === id) {{
                resetToDefault();
                return;
              }}
              selectFeatureById(geoLevel, id);
            }}
          }});
        }}
      }}).addTo(map);

      renderWardPermanentBoundaries();
      updateLegend(metric, streamKey);

      if (selectedFeatureId && profilesDict[selectedFeatureId]) {{
        renderSidebarInspector(geoLevel, selectedFeatureId);
      }} else if (selectedWardNum && geoLevel === 'ANC') {{
        renderWardSummaryInspector(selectedWardNum);
      }} else {{
        renderCitywideInspector();
      }}
    }}

    function updateLegend(metric, streamKey) {{
      const legendPanel = document.getElementById('legend-panel');
      if (!legendPanel) return;
      const ramp = getRampForMetric(metric);
      const streamSel = document.getElementById('stream-select');
      const streamShort = streamKey === 'ALL'
        ? 'All 311 Requests'
        : streamSel.options[streamSel.selectedIndex].text.replace(/^Category:\\s*/, '');

      document.getElementById('legend-title').innerText = `${{METRIC_LABELS[metric]}} - ${{streamShort}}`;
      document.getElementById('legend-scale').innerHTML =
        ramp.map(c => `<div class="scale-box" style="background:${{c}};"></div>`).join('');

      const {{ scaleMin, scaleMid, scaleMax }} = getMetricScale(metric, currentQuantiles);
      document.getElementById('legend-labels').innerHTML = `
        <span>${{formatMetricValue(scaleMin, metric)}}</span>
        <span>${{formatMetricValue(scaleMid, metric)}}</span>
        <span>${{formatMetricValue(scaleMax, metric)}}</span>
      `;
    }}

    function selectFeatureById(geoLevel, id) {{
      if (!choroLayer) return;
      const profilesDict = geoLevel === 'WARD' ? GEO_STATS.wards : GEO_STATS.ancs;
      const idProp = geoLevel === 'WARD' ? 'WARD' : 'ANC_ID';
      const p = profilesDict[id];
      if (!p) return;

      selectedFeatureId = id;
      selectedWardNum = String(p.ward || id);

      const wSel = document.getElementById('ward-filter-select');
      if (wSel) wSel.value = selectedWardNum;
      if (geoLevel === 'ANC') {{
        populateAncDropdown(selectedWardNum);
        const aSel = document.getElementById('anc-filter-select');
        if (aSel) aSel.value = id;
      }}

      choroLayer.setStyle(getFeatureStyle);
      renderWardPermanentBoundaries();

      let targetLayer = null;
      choroLayer.eachLayer(l => {{
        if (String(l.feature.properties[idProp]).trim() === id) targetLayer = l;
      }});
      if (targetLayer) {{
        if (targetLayer.bringToFront) targetLayer.bringToFront();
        map.fitBounds(targetLayer.getBounds(), {{
          maxZoom: geoLevel === 'WARD' ? 14 : 15,
          padding: [60, 60],
          animate: true,
          duration: 0.55
        }});
      }}

      renderSidebarInspector(geoLevel, id);
      ensureMobileInspectorOpen();
    }}

    function handleWardDropdown(val) {{
      if (val === 'all') {{
        resetToDefault();
        return;
      }}
      const geoLevel = document.getElementById('geo-level-select').value;
      selectedWardNum = String(val);
      if (geoLevel === 'WARD') {{
        selectFeatureById('WARD', selectedWardNum);
        return;
      }}
      selectedFeatureId = null;
      populateAncDropdown(selectedWardNum);
      choroLayer.setStyle(getFeatureStyle);
      renderWardPermanentBoundaries();

      const wardFeat = WARDS_GJ.features.find(f => String(f.properties.WARD).trim() === selectedWardNum);
      if (wardFeat) {{
        const b = L.geoJSON(wardFeat).getBounds();
        map.fitBounds(b, {{ padding: [45, 45], maxZoom: 14, animate: true, duration: 0.55 }});
      }}
      renderWardSummaryInspector(selectedWardNum);
      ensureMobileInspectorOpen();
    }}

    function handleAncDropdown(val) {{
      if (val === 'all') {{
        const wVal = document.getElementById('ward-filter-select').value;
        handleWardDropdown(wVal);
        return;
      }}
      selectFeatureById('ANC', val);
    }}

    function handleGeoSearch(query) {{
      const q = (query || '').trim().toUpperCase();
      if (!q) return;

      // Exact or prefix ANC match (e.g. "1A", "ANC 1A")
      const ancClean = q.replace(/^ANC\\s+/, '');
      const ancMatch = Object.keys(GEO_STATS.ancs).find(id => id.toUpperCase() === ancClean);
      if (ancMatch) {{
        if (document.getElementById('geo-level-select').value !== 'ANC') {{
          document.getElementById('geo-level-select').value = 'ANC';
          document.getElementById('anc-filter-row').style.display = 'flex';
          updateMapChoropleth();
        }}
        selectFeatureById('ANC', ancMatch);
        return;
      }}

      // Ward match (e.g. "5" or "WARD 5")
      const wardClean = q.replace(/^WARD\\s+/, '');
      if (GEO_STATS.wards[wardClean]) {{
        document.getElementById('ward-filter-select').value = wardClean;
        handleWardDropdown(wardClean);
        return;
      }}

      // Councilmember substring match
      const cmWard = Object.keys(GEO_STATS.wards).find(w =>
        GEO_STATS.wards[w].councilmember.toUpperCase().includes(q)
      );
      if (cmWard) {{
        document.getElementById('ward-filter-select').value = cmWard;
        handleWardDropdown(cmWard);
      }}
    }}

    function resetToDefault() {{
      selectedFeatureId = null;
      selectedWardNum = null;
      document.getElementById('geo-level-select').value = 'WARD';
      document.getElementById('anc-filter-row').style.display = 'none';
      document.getElementById('geo-search').value = '';
      document.getElementById('ward-filter-select').value = 'all';
      populateAncDropdown('all');
      updateMapChoropleth();
      map.setView([38.904, -77.015], 12, {{ animate: true }});
      renderCitywideInspector();
      collapseMobileControlPanel();
    }}

    function renderCitywideInspector() {{
      document.getElementById('insp-title').innerText = 'District of Columbia';
      document.getElementById('insp-sub').innerText = 'Citywide 311 Summary (All 8 Wards • 46 ANCs)';

      const topHtml = (CITY_SUMMARY.top_requests || []).map(r => `
        <div class="inspector-list-row">
          <span>${{r.service_desc.slice(0, 30)}}</span>
          <strong>${{r.count_2026_ytd.toLocaleString()}} (${{r.share_pct}}%)</strong>
        </div>
      `).join('');

      document.getElementById('insp-body').innerHTML = `
        <div class="inspector-stat-grid">
          <div class="stat-tile">
            <div class="stat-tile-lbl">2026 YTD</div>
            <div class="stat-tile-val">${{CITY_SUMMARY.count_2026_ytd.toLocaleString()}}</div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-lbl">2025 YTD</div>
            <div class="stat-tile-val">${{CITY_SUMMARY.count_2025_ytd.toLocaleString()}}</div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-lbl">Same-Period YoY</div>
            <div class="stat-tile-val ${{CITY_SUMMARY.yoy_pct >= 15 ? 'kw-surge' : ''}}">${{CITY_SUMMARY.yoy_pct >= 0 ? '+' : ''}}${{CITY_SUMMARY.yoy_pct}}%</div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-lbl">30-Day YoY</div>
            <div class="stat-tile-val">${{CITY_SUMMARY.d30_yoy_pct >= 0 ? '+' : ''}}${{CITY_SUMMARY.d30_yoy_pct}}%</div>
          </div>
          <div class="stat-tile" style="grid-column:span 2;">
            <div class="stat-tile-lbl">Open Backlog</div>
            <div class="stat-tile-val">${{CITY_SUMMARY.open_count.toLocaleString()}} (${{CITY_SUMMARY.open_pct}}%)</div>
          </div>
        </div>
        <div class="inspector-details">
          Click any Ward or ANC polygon on the map—or use the Geographic Subset controls—to inspect localized volume, YoY acceleration, and signature concentrations.
        </div>
        <div class="inspector-section-title">Citywide Top Service Requests</div>
        <div>${{topHtml}}</div>
      `;
    }}

    function renderWardSummaryInspector(wardId) {{
      renderSidebarInspector('WARD', String(wardId));
    }}

    function renderSidebarInspector(geoLevel, id) {{
      const profilesDict = geoLevel === 'WARD' ? GEO_STATS.wards : GEO_STATS.ancs;
      const p = profilesDict[id];
      if (!p) return;

      const streamSel = document.getElementById('stream-select');
      const streamKey = streamSel.value;
      const streamLabel = streamSel.options[streamSel.selectedIndex].text;
      const m = extractMetricObj(p, streamKey);

      document.getElementById('insp-title').innerText =
        geoLevel === 'WARD' ? `Ward ${{id}}` : `ANC ${{id}} (Ward ${{p.ward}})`;
      document.getElementById('insp-sub').innerText = `Councilmember: ${{p.councilmember}}`;

      const topHtml = (p.top_requests || []).slice(0, 6).map(r => `
        <div class="inspector-list-row">
          <span>${{r.service_desc.slice(0, 30)}}</span>
          <strong>${{r.count_2026_ytd.toLocaleString()}} (${{r.share_pct}}%)</strong>
        </div>
      `).join('');

      const lqHtml = (p.signature_concerns || []).slice(0, 5).map(r => `
        <div class="inspector-list-row">
          <span>${{r.service_desc.slice(0, 30)}}</span>
          <strong class="kw-combined">${{r.lq.toFixed(2)}}x LQ (${{r.count_2026_ytd.toLocaleString()}})</strong>
        </div>
      `).join('');

      document.getElementById('insp-body').innerHTML = `
        <div class="inspector-filter-pill">Filter: ${{streamLabel}}</div>
        <div class="inspector-stat-grid">
          <div class="stat-tile">
            <div class="stat-tile-lbl">2026 YTD</div>
            <div class="stat-tile-val">${{m.c26.toLocaleString()}}</div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-lbl">2025 YTD</div>
            <div class="stat-tile-val">${{m.c25.toLocaleString()}}</div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-lbl">Same-Period YoY</div>
            <div class="stat-tile-val ${{m.yoy_pct >= 15 ? 'kw-surge' : ''}}">${{m.yoy_pct >= 0 ? '+' : ''}}${{m.yoy_pct}}%</div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-lbl">30-Day YoY</div>
            <div class="stat-tile-val">${{m.d30_pct >= 0 ? '+' : ''}}${{m.d30_pct}}%</div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-lbl">Location Quotient</div>
            <div class="stat-tile-val">${{m.lq.toFixed(2)}}x</div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-lbl">Open Backlog</div>
            <div class="stat-tile-val">${{m.open_pct}}%</div>
          </div>
        </div>
        <div class="inspector-section-title">District Overall Top Requests</div>
        <div>${{topHtml}}</div>
        <div class="inspector-section-title">District Signature Concentrations (LQ)</div>
        <div>${{lqHtml}}</div>
      `;
    }}

    // ── Mobile Drawer & Gesture Handling ───────────────────────────────────
    let _openDrawer = null;       // null | 'control' | 'inspector'
    let _inspectorSnap = null;    // null | 'peek' | 'expanded'

    function _setDrawerActive(active) {{
      document.body.classList.toggle('drawer-active', active);
    }}

    function _setBackdrop(visible) {{
      const el = document.getElementById('drawer-backdrop');
      if (el) el.classList.toggle('is-visible', visible);
    }}

    function _openControlDrawer() {{
      if (_openDrawer === 'inspector') _closeInspectorDrawer();
      const cp = document.getElementById('control-panel');
      const fab = document.getElementById('mobile-fab-filters');
      if (cp) cp.classList.add('is-open');
      if (fab) fab.textContent = '[X] Close';
      _setBackdrop(true);
      _setDrawerActive(true);
      _openDrawer = 'control';
    }}

    function _closeControlDrawer() {{
      const cp = document.getElementById('control-panel');
      const fab = document.getElementById('mobile-fab-filters');
      if (cp) cp.classList.remove('is-open');
      if (fab) fab.textContent = '[=] Layers';
      if (_openDrawer === 'control') {{
        _openDrawer = null;
        _setBackdrop(false);
        _setDrawerActive(false);
      }}
    }}

    function _openInspectorPeek() {{
      if (_openDrawer === 'control') _closeControlDrawer();
      const insp = document.getElementById('inspector-panel');
      if (!insp) return;
      insp.classList.remove('is-expanded');
      insp.classList.add('is-peek');
      _inspectorSnap = 'peek';
      const icon = document.getElementById('insp-toggle-icon');
      if (icon) icon.textContent = '^';
      _setBackdrop(true);
      _setDrawerActive(true);
      _openDrawer = 'inspector';
    }}

    function _expandInspector() {{
      const insp = document.getElementById('inspector-panel');
      if (!insp) return;
      insp.classList.remove('is-peek');
      insp.classList.add('is-expanded');
      _inspectorSnap = 'expanded';
      const icon = document.getElementById('insp-toggle-icon');
      if (icon) icon.textContent = 'v';
    }}

    function _closeInspectorDrawer() {{
      const insp = document.getElementById('inspector-panel');
      if (!insp) return;
      insp.classList.remove('is-peek', 'is-expanded');
      _inspectorSnap = null;
      const icon = document.getElementById('insp-toggle-icon');
      if (icon) icon.textContent = '^';
      if (_openDrawer === 'inspector') {{
        _openDrawer = null;
        _setBackdrop(false);
        _setDrawerActive(false);
      }}
    }}

    function handleInspectorHeaderTap() {{
      if (window.innerWidth > 768) return;
      if (_inspectorSnap === 'peek') {{
        _expandInspector();
      }} else if (_inspectorSnap === 'expanded') {{
        _closeInspectorDrawer();
      }}
    }}

    function toggleDrawer(type) {{
      if (window.innerWidth > 768) return;
      if (type === 'control') {{
        if (_openDrawer === 'control') _closeControlDrawer();
        else _openControlDrawer();
      }}
    }}

    function closeAllDrawers() {{
      if (window.innerWidth > 768) return;
      _closeControlDrawer();
      _closeInspectorDrawer();
      _setBackdrop(false);
      _setDrawerActive(false);
      _openDrawer = null;
    }}

    function ensureMobileInspectorOpen() {{
      if (window.innerWidth <= 768 && _openDrawer !== 'control') {{
        _openInspectorPeek();
      }}
    }}

    function collapseMobileControlPanel() {{
      if (window.innerWidth <= 768) _closeControlDrawer();
    }}

    function initDrawerSwipeToDismiss(panelId, getType) {{
      const el = document.getElementById(panelId);
      if (!el) return;
      let startY = 0, dragY = 0, dragging = false;

      el.addEventListener('pointerdown', function(e) {{
        if (window.innerWidth > 768) return;
        const handle = el.querySelector('.sheet-handle');
        const header = el.querySelector('.mobile-control-header') || el.querySelector('.inspector-header');
        const isHandle = (handle && handle.contains(e.target)) || (header && header.contains(e.target));
        if (!isHandle) return;
        startY = e.clientY;
        dragY = 0;
        dragging = true;
        el.style.transition = 'none';
        el.setPointerCapture(e.pointerId);
      }});

      el.addEventListener('pointermove', function(e) {{
        if (!dragging) return;
        dragY = e.clientY - startY;
        if (dragY > 0) el.style.transform = 'translateY(' + dragY + 'px)';
      }});

      function onEnd() {{
        if (!dragging) return;
        dragging = false;
        el.style.transition = '';
        el.style.transform = '';
        const type = getType();
        if (dragY > 90) {{
          if (type === 'control') _closeControlDrawer();
          else if (type === 'inspector') _closeInspectorDrawer();
        }}
        dragY = 0;
      }}

      el.addEventListener('pointerup', onEnd);
      el.addEventListener('pointercancel', onEnd);
    }}

    function initMobileHandling() {{
      const cp = document.getElementById('control-panel');
      const insp = document.getElementById('inspector-panel');
      const leg = document.getElementById('legend-panel');

      [cp, insp, leg].forEach(el => {{
        if (el) {{
          L.DomEvent.disableClickPropagation(el);
          L.DomEvent.disableScrollPropagation(el);
        }}
      }});

      initDrawerSwipeToDismiss('control-panel', () => 'control');
      initDrawerSwipeToDismiss('inspector-panel', () => 'inspector');

      let wasMobile = window.innerWidth <= 768;
      window.addEventListener('resize', () => {{
        const isMobile = window.innerWidth <= 768;
        if (isMobile !== wasMobile) {{
          wasMobile = isMobile;
          if (cp) {{ cp.classList.remove('is-open'); cp.style.transform = ''; cp.style.maxHeight = ''; }}
          if (insp) {{ insp.classList.remove('is-peek', 'is-expanded'); insp.style.transform = ''; }}
          _openDrawer = null;
          _inspectorSnap = null;
          _setBackdrop(false);
          _setDrawerActive(false);
          const fab = document.getElementById('mobile-fab-filters');
          if (fab) fab.textContent = '[=] Layers';
        }}
      }});

      if (window.visualViewport) {{
        window.visualViewport.addEventListener('resize', () => {{
          if (window.innerWidth <= 768 && _openDrawer === 'control' && cp) {{
            cp.style.maxHeight = Math.max(160, Math.floor(window.visualViewport.height - 20)) + 'px';
          }}
        }});
      }}
    }}

    window.onThemeChange = function() {{
      if (tileLayer) tileLayer.setUrl(getTileUrl());
      if (choroLayer) choroLayer.setStyle(getFeatureStyle);
      renderWardPermanentBoundaries();
    }};

    document.addEventListener('DOMContentLoaded', initMap);
  </script>
</body>
</html>
"""

    out_path = os.path.join(BASE_DIR, "map.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Compiled {out_path}")


if __name__ == "__main__":
    build_map()
