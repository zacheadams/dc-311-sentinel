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

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DC 311 Sentinel • District-Wide Service Request Intelligence</title>
{COMMON_HEAD_FONTS}
  <style>
{COMMON_CSS}
    .hero-banner {{
      border: 1px solid var(--border);
      background: var(--bg-card);
      border-radius: 2px;
      padding: 28px 24px;
      margin-bottom: 28px;
      box-shadow: var(--card-shadow);
    }}
    .hero-kicker {{
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 3px 10px;
      border: 1px solid var(--badge-border);
      background: var(--badge-bg);
      border-radius: 2px;
      margin-bottom: 12px;
    }}
    .hero-title {{
      font-size: 26px;
      font-weight: 800;
      line-height: 1.2;
      margin-bottom: 10px;
      letter-spacing: -0.02em;
    }}
    .hero-desc {{
      font-size: 13px;
      color: var(--text-muted);
      max-width: 920px;
      margin-bottom: 0;
      line-height: 1.6;
    }}
    .references-section {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 24px;
      margin-top: 10px;
      margin-bottom: 40px;
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
      .hero-banner,
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
    <section class="hero-banner">
      <div class="hero-kicker">Washington, DC Municipal Operations Sentinel • {meta['total_all_rows']:,} Requests Analyzed</div>
      <h1 class="hero-title">District-Wide 311 Service Request Analysis (2025 – 2026 YTD)</h1>
      <p class="hero-desc">
        Full-population analysis of <strong>{meta['total_2026_ytd']:,}</strong> DC 311 service requests filed in 2026 YTD (Jan 1 – {meta['cutoff_date']}) benchmarked against <strong>{meta['total_2025_ytd']:,}</strong> same-period 2025 requests (<strong>{meta['total_2025_full']:,}</strong> full-year 2025). Evaluates all <strong>{meta['distinct_descriptions_2026']}</strong> specific 2026 service descriptions across 8 Wards and 46 Advisory Neighborhood Commissions (ANCs).
      </p>
    </section>

    <!-- KPI Row -->
    <section class="kpi-row">
      <div class="kpi-box">
        <div class="kpi-num">{meta['total_2026_ytd']:,}</div>
        <div class="kpi-label">2026 YTD Requests</div>
        <div class="kpi-sub">Jan 1 – {meta['cutoff_date']} (DOY {meta['cutoff_doy']})</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num kw-surge">{meta['yoy_pct']:+.1f}%</div>
        <div class="kpi-label">Same-Period YoY Change</div>
        <div class="kpi-sub">vs. {meta['total_2025_ytd']:,} in Jan 1–Nov 9, 2025</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{meta['d30_2026']:,} <span style="font-size:15px;" class="kw-surge">({meta['d30_yoy_pct']:+.1f}%)</span></div>
        <div class="kpi-label">Last 30 Days Volume</div>
        <div class="kpi-sub">Since {meta['d30_start_date']} vs. {meta['d30_2025']:,} in 2025</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{meta['median_res_hours_2026']:.1f}h</div>
        <div class="kpi-label">Median Resolution Time</div>
        <div class="kpi-sub">vs. {meta['median_res_hours_2025']:.1f}h in 2025</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{meta['sla_pct_2026']:.1f}%</div>
        <div class="kpi-label">On-Time SLA Compliance</div>
        <div class="kpi-sub">vs. {meta['sla_pct_2025']:.1f}% in 2025 (-3.0 pts)</div>
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
