#!/usr/bin/env python3
"""
Compiles the Interactive Spatial Choropleth Explorer (map.html).
Features:
- Offline Stamen Toner local basemap tiles (tiles/light/ and tiles/blacklite/, zooms 11-17)
- Toggleable 46-ANC and 8-Ward choropleth polygons with permanent dashed Ward boundaries
- Filter by All 311 Requests, any of the 11 Category Families, or Top 45 Specific Service Queries
- Switchable metric: 2026 YTD Volume, Same-Period YoY %, 30-Day YoY %, Location Quotient (LQ), Open Backlog %
- Strictly zero emojis across code, markup, and UI
"""

import json
import os
from html import escape

from ui_common import COMMON_CSS, COMMON_HEAD_FONTS, COMMON_THEME_AND_SORT_JS, render_nav

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
    .map-workspace {{
      flex: 1;
      display: grid;
      grid-template-columns: 380px 1fr;
      height: calc(100vh - 53px);
      overflow: hidden;
    }}
    .map-sidebar {{
      background: var(--bg-surface);
      border-right: 1px solid var(--border);
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 14px;
      z-index: 500;
    }}
    #map-canvas {{
      width: 100%;
      height: 100%;
      background: var(--bg-page);
    }}
    .sidebar-block {{
      border: 1px solid var(--border);
      background: var(--bg-card);
      border-radius: 2px;
      padding: 12px;
    }}
    .sidebar-label {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
      display: block;
      margin-bottom: 5px;
    }}
    .sidebar-select {{
      width: 100%;
      margin-bottom: 10px;
    }}
    .legend-bar {{
      display: flex;
      height: 12px;
      border-radius: 2px;
      overflow: hidden;
      border: 1px solid var(--border);
      margin: 6px 0 4px 0;
    }}
    .legend-labels {{
      display: flex;
      justify-content: space-between;
      font-size: 10px;
      color: var(--text-muted);
    }}
    @media (max-width: 860px) {{
      .map-workspace {{
        grid-template-columns: 1fr;
        grid-template-rows: 46% 54%;
      }}
      .map-sidebar {{
        border-right: none;
        border-bottom: 1px solid var(--border);
      }}
    }}
  </style>
</head>
<body>
{render_nav("map.html", "Interactive Ward & 2023 ANC Spatial Choropleth Explorer")}

  <div class="map-workspace">
    <aside class="map-sidebar">
      <div class="sidebar-block">
        <label class="sidebar-label" for="geo-level-select">Geographic Layer:</label>
        <select id="geo-level-select" class="sidebar-select" onchange="updateMapChoropleth()">
          <option value="ANC">Advisory Neighborhood Commissions (46 ANCs)</option>
          <option value="WARD">Wards (8 Wards)</option>
        </select>

        <label class="sidebar-label" for="stream-select">311 Request Filter (Category or Specific Query):</label>
        <select id="stream-select" class="sidebar-select" onchange="updateMapChoropleth()">
          <option value="ALL">All 311 Service Requests (445,142 YTD)</option>
          <optgroup label="Operational Category Families (11)">
            {''.join(f'<option value="CAT:{escape(c)}">Category: {escape(c)}</option>' for c in categories)}
          </optgroup>
          <optgroup label="Top 45 Specific Service Queries">
            {''.join(f'<option value="CODE:{escape(d["service_code"])}">{escape(d["service_desc"])} [{escape(d["service_code"])}]</option>' for d in dynamic_codes)}
          </optgroup>
        </select>

        <label class="sidebar-label" for="metric-select">Choropleth Metric:</label>
        <select id="metric-select" class="sidebar-select" style="margin-bottom:4px;" onchange="updateMapChoropleth()">
          <option value="c26">2026 YTD Request Volume</option>
          <option value="lq">Location Quotient (LQ Concentration)</option>
          <option value="yoy_pct">Same-Period YoY % Change (2026 vs 2025)</option>
          <option value="d30_pct">Last 30 Days YoY % Change</option>
          <option value="open_pct">Open Backlog %</option>
        </select>

        <div id="legend-container" style="margin-top:8px;"></div>
      </div>

      <div class="sidebar-block" id="inspector-panel" style="flex:1;">
        <!-- Populated on polygon click or default -->
      </div>
    </aside>

    <div id="map-canvas"></div>
  </div>

{COMMON_THEME_AND_SORT_JS}
  <script>
    const GEO_STATS = {json.dumps(geo)};
    const WARDS_GJ = {json.dumps(wards_geojson)};
    const ANCS_GJ = {json.dumps(ancs_geojson)};

    // Single-hue color ramps (light tint -> deep dark shade)
    const RAMPS = {{
      volume: ['#dbeafe', '#93c5fd', '#3b82f6', '#1d4ed8', '#172554'],
      lq:     ['#f3e8ff', '#d8b4fe', '#a855f7', '#7e22ce', '#3b0764'],
      surge:  ['#fee2e2', '#fca5a5', '#ef4444', '#b91c1c', '#450a0a'],
      open:   ['#fef3c7', '#fcd34d', '#f59e0b', '#b45309', '#451a03']
    }};

    let map = null;
    let tileLayer = null;
    let choroLayer = null;
    let wardOutlineLayer = null;
    let selectedFeatureId = null;

    function getTileUrl() {{
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      return dark ? 'tiles/blacklite/{{z}}/{{x}}/{{y}}.png' : 'tiles/light/{{z}}/{{x}}/{{y}}.png';
    }}

    function initMap() {{
      map = L.map('map-canvas', {{
        center: [38.904, -77.015],
        zoom: 12,
        minZoom: 11,
        maxZoom: 17
      }});

      tileLayer = L.tileLayer(getTileUrl(), {{
        maxNativeZoom: 17,
        maxZoom: 17,
        attribution: 'Map tiles by Stamen Design (CC BY 4.0) • Data: Open Data DC'
      }}).addTo(map);

      /*
      // Contingency U.S. Census Bureau TIGERweb fallback configuration:
      // https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer
      */

      renderWardPermanentBoundaries();
      updateMapChoropleth();
    }}

    function renderWardPermanentBoundaries() {{
      if (wardOutlineLayer) map.removeLayer(wardOutlineLayer);
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      wardOutlineLayer = L.geoJSON(WARDS_GJ, {{
        interactive: false,
        style: {{
          color: dark ? '#c084fc' : '#7c3aed',
          weight: 2,
          dashArray: '5, 5',
          fillOpacity: 0
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
      const minV = vals[0] || 0;
      const maxV = vals[vals.length - 1] || 1;
      const q20 = vals[Math.floor(vals.length * 0.2)] || 0;
      const q40 = vals[Math.floor(vals.length * 0.4)] || 0;
      const q60 = vals[Math.floor(vals.length * 0.6)] || 0;
      const q80 = vals[Math.floor(vals.length * 0.8)] || 0;

      const ramp = getRampForMetric(metric);
      function pickColor(v) {{
        if (v <= q20) return ramp[0];
        if (v <= q40) return ramp[1];
        if (v <= q60) return ramp[2];
        if (v <= q80) return ramp[3];
        return ramp[4];
      }}

      if (choroLayer) map.removeLayer(choroLayer);
      choroLayer = L.geoJSON(gj, {{
        style: feature => {{
          const id = String(feature.properties[idProp]).trim();
          const m = extractMetricObj(profilesDict[id], streamKey);
          const v = m[metric] || 0;
          return {{
            fillColor: pickColor(v),
            fillOpacity: 0.68,
            color: '#18181b',
            weight: geoLevel === 'WARD' ? 2 : 1.1
          }};
        }},
        onEachFeature: (feature, layer) => {{
          const id = String(feature.properties[idProp]).trim();
          const p = profilesDict[id];
          const m = extractMetricObj(p, streamKey);
          const label = geoLevel === 'WARD' ? `Ward ${{id}}` : `ANC ${{id}} (Ward ${{p ? p.ward : ''}})`;
          layer.bindTooltip(
            `<strong>${{label}}</strong><br>2026 YTD: ${{m.c26.toLocaleString()}}<br>YoY: ${{m.yoy_pct >= 0 ? '+' : ''}}${{m.yoy_pct}}% • LQ: ${{m.lq}}x`,
            {{ sticky: true }}
          );
          layer.on('click', () => {{
            selectedFeatureId = id;
            renderSidebarInspector(geoLevel, id);
          }});
        }}
      }}).addTo(map);

      renderWardPermanentBoundaries();

      // Update Legend
      const fmt = v => metric === 'c26' ? Math.round(v).toLocaleString() : (metric === 'lq' ? v.toFixed(2) + 'x' : v.toFixed(1) + '%');
      document.getElementById('legend-container').innerHTML = `
        <div class="legend-bar">
          ${{ramp.map(c => `<div style="flex:1;background:${{c}};"></div>`).join('')}}
        </div>
        <div class="legend-labels">
          <span>Min: ${{fmt(minV)}}</span>
          <span>Median: ${{fmt(q40)}}</span>
          <span>Max: ${{fmt(maxV)}}</span>
        </div>
      `;

      const defaultId = selectedFeatureId && profilesDict[selectedFeatureId]
        ? selectedFeatureId
        : Object.keys(profilesDict)[0];
      renderSidebarInspector(geoLevel, defaultId);
    }}

    function renderSidebarInspector(geoLevel, id) {{
      const profilesDict = geoLevel === 'WARD' ? GEO_STATS.wards : GEO_STATS.ancs;
      const p = profilesDict[id];
      if (!p) return;

      const streamSel = document.getElementById('stream-select');
      const streamKey = streamSel.value;
      const streamLabel = streamSel.options[streamSel.selectedIndex].text;
      const m = extractMetricObj(p, streamKey);

      const title = geoLevel === 'WARD' ? `WARD ${{id}}` : `ANC ${{id}} (WARD ${{p.ward}})`;
      const topHtml = p.top_requests.slice(0, 6).map(r => `
        <div style="display:flex;justify-content:space-between;font-size:11px;padding:3px 0;border-bottom:1px dashed var(--border);">
          <span>${{r.service_desc.slice(0, 30)}}</span>
          <strong>${{r.count_2026_ytd.toLocaleString()}} (${{r.share_pct}}%)</strong>
        </div>
      `).join('');

      const lqHtml = p.signature_concerns.slice(0, 5).map(r => `
        <div style="display:flex;justify-content:space-between;font-size:11px;padding:3px 0;border-bottom:1px dashed var(--border);">
          <span>${{r.service_desc.slice(0, 30)}}</span>
          <strong class="kw-combined">${{r.lq.toFixed(2)}}x LQ (${{r.count_2026_ytd.toLocaleString()}})</strong>
        </div>
      `).join('');

      document.getElementById('inspector-panel').innerHTML = `
        <div style="border-bottom:1px solid var(--border);padding-bottom:8px;margin-bottom:10px;">
          <div style="font-size:15px;font-weight:800;">${{title}}</div>
          <div style="font-size:11px;color:var(--text-muted);">Councilmember: ${{p.councilmember}}</div>
        </div>
        <div style="background:var(--bg-input);padding:10px;border-radius:2px;margin-bottom:12px;font-size:11px;">
          <div style="font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px;">Selected Filter:</div>
          <div style="font-weight:700;margin-bottom:6px;">${{streamLabel}}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
            <div>2026 YTD: <strong>${{m.c26.toLocaleString()}}</strong></div>
            <div>2025 YTD: <strong>${{m.c25.toLocaleString()}}</strong></div>
            <div>Same-Period YoY: <strong class="${{m.yoy_pct >= 15 ? 'kw-surge' : ''}}">${{m.yoy_pct >= 0 ? '+' : ''}}${{m.yoy_pct}}%</strong></div>
            <div>30-Day YoY: <strong>${{m.d30_pct >= 0 ? '+' : ''}}${{m.d30_pct}}%</strong></div>
            <div>Location Quotient: <strong>${{m.lq}}x</strong></div>
            <div>Open Backlog: <strong>${{m.open_pct}}%</strong></div>
          </div>
        </div>
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px;">District Overall Top Requests:</div>
        <div style="margin-bottom:10px;">${{topHtml}}</div>
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px;">District Signature Concentrations (LQ):</div>
        <div>${{lqHtml}}</div>
      `;
    }}

    window.onThemeChange = function() {{
      if (tileLayer) tileLayer.setUrl(getTileUrl());
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
