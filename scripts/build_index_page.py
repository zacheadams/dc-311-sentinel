#!/usr/bin/env python3
"""
Compiles the Central Project Hub (index.html).
Strictly adheres to Agents.md:
- Primary monospace font (IBM Plex Mono)
- Lo-fi black & white aesthetic with light/dark theme toggle
- Zero emojis across code, markup, and UI
"""

import json
import os

from ui_common import (
    COMMON_CSS,
    COMMON_HEAD_FONTS,
    COMMON_THEME_AND_SORT_JS,
    render_nav,
    render_footer,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_index():
    with open(os.path.join(BASE_DIR, "data", "summary_top.json"), "r", encoding="utf-8") as f:
        summary = json.load(f)

    meta = summary["metadata"]
    sla_delta = meta["sla_pct_2026"] - meta["sla_pct_2025"]
    med_pct = ((meta["median_res_hours_2026"] - meta["median_res_hours_2025"]) / meta["median_res_hours_2025"]) * 100
    yoy_cls = "kw-surge" if meta["yoy_pct"] > 0 else ("kw-decline" if meta["yoy_pct"] < 0 else "")
    d30_cls = "kw-surge" if meta["d30_yoy_pct"] > 0 else ("kw-decline" if meta["d30_yoy_pct"] < 0 else "")
    med_cls = "kw-decline" if med_pct < 0 else ("kw-surge" if med_pct > 0 else "")
    sla_cls = "kw-surge" if sla_delta < 0 else ("kw-decline" if sla_delta > 0 else "")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DC 311 Sentinel • District-Wide Service Request Intelligence</title>
{COMMON_HEAD_FONTS}
  <style>
{COMMON_CSS}
    body {{
      padding-bottom: 12px;
    }}
    .page-container {{
      max-width: 1100px;
      padding: 32px 20px 16px 20px;
    }}
    .hero {{
      text-align: center;
      padding: 40px 0 44px 0;
      border-bottom: 1px solid var(--border);
      margin-bottom: 36px;
    }}
    .hero-title {{
      font-size: 32px;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.02em;
      line-height: 1.2;
      margin-bottom: 14px;
      max-width: 820px;
      margin-left: auto;
      margin-right: auto;
    }}
    .hero-desc {{
      font-size: 13px;
      color: var(--text-muted);
      max-width: 720px;
      margin: 0 auto 28px auto;
      line-height: 1.6;
    }}
    .hero-desc a {{
      color: var(--text-main);
      text-decoration: underline;
      font-weight: 600;
    }}
    .hero-desc a:hover {{
      color: var(--accent);
    }}
    .hero-actions {{
      display: flex;
      justify-content: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .btn-hero-secondary {{
      background: var(--bg-surface);
      border: 1px solid var(--border);
      color: var(--text-main);
      text-decoration: none;
      font-size: 12px;
      font-weight: 700;
      padding: 10px 22px;
      border-radius: 2px;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .btn-hero-secondary:hover {{
      border-color: var(--text-main);
      background: var(--bg-input);
    }}
    .kpi-row {{
      padding-bottom: 36px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 36px;
    }}
    .kpi-box {{
      text-align: center;
    }}
    .references-section {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 24px;
      margin-top: 0;
      margin-bottom: 24px;
      box-shadow: var(--card-shadow);
    }}
    .references-title {{
      font-size: 15px;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.01em;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
    }}
    .site-footer {{
      margin-top: 0;
      padding-top: 20px;
      padding-bottom: 0;
    }}
    .ref-narrative {{
      font-size: 12px;
      line-height: 1.7;
      color: var(--text-muted);
      margin-bottom: 0;
      padding: 14px 16px;
      background: var(--bg-input);
      border-left: 3px solid var(--accent);
      border-radius: 2px;
    }}
    .ref-narrative a {{
      color: var(--text-main);
      text-decoration: underline;
      font-weight: 600;
    }}
    .ref-narrative a:hover {{
      color: var(--accent);
    }}
    @media print {{
      body {{
        padding-bottom: 0;
      }}
      .page-container {{
        max-width: 100%;
        padding: 0;
      }}
      .hero-actions {{
        display: none !important;
      }}
      .hero,
      .kpi-row,
      .references-section {{
        border: 1px solid #cccccc !important;
        box-shadow: none !important;
        break-inside: avoid;
      }}
    }}
  </style>
</head>
<body>
{render_nav("index.html")}

  <main class="page-container">
    <!-- Hero Section: Index -->
    <section class="hero">
      <h1 class="hero-title">Index</h1>
      <p class="hero-desc">This site provides an interactive map and charts, exploring all types of <a href="https://311.dc.gov/citizen/s/" target="_blank" rel="noopener">311 requests</a> across DC. The aim is to serve as a <a href="https://en.wikipedia.org/wiki/Sentinel_surveillance" target="_blank" rel="noopener">sentinel</a>, alerting both the District government and its residents about emergent trends in public service needs, so that they may be retrospectively identified, actively addressed, and prospectively planned for.</p>
      <div class="hero-actions">
        <a href="map.html" class="btn-hero-secondary">Map</a>
        <a href="tables.html" class="btn-hero-secondary">Trends</a>
      </div>
    </section>

    <!-- KPI Row -->
    <section class="kpi-row">
      <div class="kpi-box">
        <div class="kpi-num">{meta['total_2026_ytd']:,}<br><span style="font-size:15px;" class="{yoy_cls}">({meta['yoy_pct']:+.1f}%)</span></div>
        <div class="kpi-label">2026 YTD Requests</div>
        <div class="kpi-sub">vs. {meta['total_2025_ytd']:,} in 2025</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{meta['d30_2026']:,}<br><span style="font-size:15px;" class="{d30_cls}">({meta['d30_yoy_pct']:+.1f}%)</span></div>
        <div class="kpi-label">Last 30 Days Requests</div>
        <div class="kpi-sub">vs. {meta['d30_2025']:,} in 2025</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{meta['median_res_hours_2026']:.1f}h<br><span style="font-size:15px;" class="{med_cls}">({med_pct:+.1f}%)</span></div>
        <div class="kpi-label">Median Resolution Time</div>
        <div class="kpi-sub">vs. {meta['median_res_hours_2025']:.1f}h in 2025</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{meta['sla_pct_2026']:.1f}%<br><span style="font-size:15px;" class="{sla_cls}">({sla_delta:+.1f}%)</span></div>
        <div class="kpi-label">On-Time SLA Compliance</div>
        <div class="kpi-sub">vs. {meta['sla_pct_2025']:.1f}% in 2025</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{meta['open_backlog_2026']:,}</div>
        <div class="kpi-label">Open 2026 Backlog</div>
        <div class="kpi-sub">{meta['distinct_descriptions_2026']} active 2026 service types</div>
      </div>
    </section>

    <!-- References & Acknowledgements Section -->
    <section class="references-section">
      <h2 class="references-title">References &amp; Acknowledgements</h2>

      <div class="ref-narrative">
        <p>This project was built in a <a href="https://ghostty.org/" target="_blank" rel="noopener">Ghostty</a> terminal using <a href="https://antigravity.google/product/antigravity-cli/" target="_blank" rel="noopener">Antigravity-CLI</a> running <a href="https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/" target="_blank" rel="noopener">Gemini 4 Hydrogen</a>, and is hosted on <a href="https://github.com/" target="_blank" rel="noopener">GitHub</a>. The basemaps are <a href="https://maps.stamen.com/toner/" target="_blank" rel="noopener">Stamen Toner</a>, rendered in <a href="https://leafletjs.com/" target="_blank" rel="noopener">Leaflet.js</a>, with other graphics using <a href="https://www.chartjs.org/" target="_blank" rel="noopener">Chart.js</a>, data stored in <a href="https://duckdb.org/" target="_blank" rel="noopener">DuckDB</a>, and exports facilitated using <a href="https://github.com/parallax/jsPDF" target="_blank" rel="noopener">jsPDF</a>. The data used are publicly available thanks to <a href="https://opendata.dc.gov/" target="_blank" rel="noopener">Open Data DC</a>. This project builds on and generalizes the work of <a href="https://zach.online/missed-collections/" target="_blank" rel="noopener">Missed Collections</a>, and was spurred on by a conversation with Councilmember-elect Oye Owolewa, who asked how an elected official could tell, beyond vocal civic engagement and reports from agencies, what problems were emergent and unaddressed in the community.</p>
      </div>
    </section>

{render_footer()}
  </main>

{COMMON_THEME_AND_SORT_JS}
</body>
</html>
"""

    out_path = os.path.join(BASE_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Compiled {out_path}")


if __name__ == "__main__":
    build_index()
