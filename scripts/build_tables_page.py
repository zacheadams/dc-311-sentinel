#!/usr/bin/env python3
"""
Compiles the Other Analysis Dashboard: Agency SLA Scorecards, Temporal Filing Rhythm,
and Chronic Repeat Address Hotspots (tables.html).

Strictly adheres to Agents.md:
- All table columns are sortable ascending/descending
- Rank columns omitted
- Primary monospace font (IBM Plex Mono)
- Lo-fi black & white aesthetic with light/dark theme toggle
- Strictly zero emojis across code, markup, and UI
- US Letter PDF exports
"""

import json
import os
from html import escape

from ui_common import COMMON_CSS, COMMON_HEAD_FONTS, COMMON_THEME_AND_SORT_JS, render_nav, render_footer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_tables():
    with open(os.path.join(BASE_DIR, "data", "summary_top.json"), "r", encoding="utf-8") as f:
        summary = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "operational_patterns.json"), "r", encoding="utf-8") as f:
        patterns = json.load(f)

    queries = summary["service_queries"]
    code_cat_map = {q["service_code"]: q["category"] for q in queries}
    code_desc_map = {q["service_code"]: q["service_desc"] for q in queries}

    agencies = patterns["agencies"]
    repeats = patterns["repeat_hotspots"]["by_service_code"]
    temporal = patterns["temporal"]

    # 1. Agency SLA Scorecard rows
    agency_rows_html = []
    for a in agencies:
        sla26 = f"{a['sla_pct_2026']:.1f}%" if a["sla_pct_2026"] is not None else "N/A"
        sla25 = f"{a['sla_pct_2025']:.1f}%" if a["sla_pct_2025"] is not None else "N/A"
        med_h = f"{a['median_res_hours']:.1f}h" if a["median_res_hours"] is not None else "N/A"
        p90_h = f"{a['p90_res_hours']:.1f}h" if a["p90_res_hours"] is not None else "N/A"
        agency_rows_html.append(
            f"""            <tr>
              <td><strong>{escape(a['agency'])}</strong></td>
              <td class="num" data-val="{a['count_2026_ytd']}">{a['count_2026_ytd']:,}</td>
              <td class="num" data-val="{a['count_2025_ytd']}">{a['count_2025_ytd']:,}</td>
              <td class="num {'kw-surge' if a['yoy_pct'] >= 15 else ''}" data-val="{a['yoy_pct']}">{a['yoy_pct']:+.1f}%</td>
              <td class="num" data-val="{a['share_2026_pct']}">{a['share_2026_pct']:.2f}%</td>
              <td class="num" data-val="{a['median_res_hours'] or 99999}">{med_h}</td>
              <td class="num" data-val="{a['p90_res_hours'] or 99999}">{p90_h}</td>
              <td class="num" data-val="{a['sla_pct_2026'] or 0}">{sla26}</td>
              <td class="num" data-val="{a['sla_pct_2025'] or 0}">{sla25}</td>
              <td class="num" data-val="{a['open_count']}">{a['open_count']:,}</td>
              <td class="num" data-val="{a['aged_open_30d']}">{a['aged_open_30d']:,}</td>
            </tr>"""
        )

    # 2. Chronic Repeat MAR Address Hotspots
    repeat_rows_html = []
    for r in repeats:
        cat_name = r.get("category") or code_cat_map.get(r["service_code"], "-")
        query_desc = code_desc_map.get(r["service_code"], r["service_desc"])
        repeat_rows_html.append(
            f"""            <tr>
              <td><code>{escape(r['service_code'])}</code></td>
              <td><strong>{escape(query_desc)}</strong></td>
              <td>{escape(cat_name)}</td>
              <td class="num" data-val="{r['locations_5plus']}">{r['locations_5plus']:,}</td>
              <td class="num" data-val="{r['total_chronic_tickets']}">{r['total_chronic_tickets']:,}</td>
            </tr>"""
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DC 311 Sentinel • Other Analysis</title>
{COMMON_HEAD_FONTS}
  <script src="assets/vendor/chartjs/chart.umd.min.js"></script>
  <script src="assets/vendor/jspdf/jspdf.umd.min.js"></script>
  <script src="assets/vendor/jspdf-autotable/jspdf.plugin.autotable.min.js"></script>
  <style>
{COMMON_CSS}
    .grid-2col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}
    @media (max-width: 860px) {{
      .grid-2col {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
{render_nav("tables.html", "Other Analysis • Agency SLA Scorecards, Temporal Filing Rhythm & Repeat Hotspots")}

  <main class="page-container">
    <!-- Section 1: Agency SLA & Backlog Scorecard -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Agency SLA Compliance & Backlog Scorecard (2026 YTD vs. 2025 YTD)</h2>
          <p class="section-subtitle">Evaluating median and 90th-percentile resolution hours, SLA compliance rate, and aged open backlog (&gt;30 days)</p>
        </div>
        <div>
          <button class="btn-action" onclick="exportTableToCSV('agency-table', 'dc_311_agency_sla_2026.csv')">Export CSV</button>
          <button class="btn-action" onclick="exportTableToPDF('agency-table', 'DC 311 Agency SLA Scorecard (2026 YTD)', 'dc_311_agency_sla_2026.pdf')">Export PDF</button>
        </div>
      </div>
      <div class="table-wrap">
        <table class="data-table" id="agency-table">
          <thead>
            <tr>
              <th>Agency</th>
              <th class="num">2026 YTD</th>
              <th class="num">2025 YTD</th>
              <th class="num">YoY %</th>
              <th class="num">Share %</th>
              <th class="num">Median Res</th>
              <th class="num">p90 Res</th>
              <th class="num">2026 SLA Met %</th>
              <th class="num">2025 SLA Met %</th>
              <th class="num">Open Backlog</th>
              <th class="num">Aged Open (&gt;30d)</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(agency_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Section 2: Temporal Filing Rhythm -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Temporal Filing Rhythm</h2>
          <p class="section-subtitle">Day-of-week and hour-of-day submission distributions across 2026 YTD service requests</p>
        </div>
      </div>
      <div class="grid-2col">
        <div class="card">
          <div style="height:250px;">
            <canvas id="dowChart"></canvas>
          </div>
        </div>
        <div class="card">
          <div style="height:250px;">
            <canvas id="hourChart"></canvas>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 3: Chronic Repeat Address Hotspots (2026 YTD) -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Chronic Repeat Address Hotspots (2026 YTD)</h2>
          <p class="section-subtitle">Master Address Repository (MAR) locations with 5 or more requests for the same service query</p>
        </div>
        <div>
          <button class="btn-action" onclick="exportTableToCSV('repeat-table', 'dc_311_repeat_hotspots_2026.csv')">Export CSV</button>
          <button class="btn-action" onclick="exportTableToPDF('repeat-table', 'DC 311 Chronic Repeat Hotspots (2026 YTD)', 'dc_311_repeat_hotspots_2026.pdf')">Export PDF</button>
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table" id="repeat-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Service Query</th>
              <th>Category</th>
              <th class="num">Chronic Repeat Properties (&gt;=5 requests)</th>
              <th class="num"># at Chronic Repeat Properties</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(repeat_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

{render_footer()}
  </main>

{COMMON_THEME_AND_SORT_JS}
  <script>
    const TEMPORAL = {json.dumps(temporal)};
    let dowChart = null;
    let hourChart = null;

    function getChartColors() {{
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      return {{
        text: dark ? '#f4f4f5' : '#09090b',
        muted: dark ? '#a1a1aa' : '#52525b',
        grid: dark ? '#27272a' : '#e4e4e7',
        bar: dark ? '#38bdf8' : '#2563eb'
      }};
    }}

    function renderTemporalCharts() {{
      const colors = getChartColors();
      if (dowChart) dowChart.destroy();
      if (hourChart) hourChart.destroy();

      dowChart = new Chart(document.getElementById('dowChart').getContext('2d'), {{
        type: 'bar',
        data: {{
          labels: TEMPORAL.dow_labels,
          datasets: [{{
            label: '2026 YTD Requests by Day of Week',
            data: TEMPORAL.dow_counts_2026,
            backgroundColor: colors.bar
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: colors.text, font: {{ family: 'IBM Plex Mono', size: 11 }} }} }} }},
          scales: {{
            x: {{ ticks: {{ color: colors.text, font: {{ family: 'IBM Plex Mono', size: 11 }} }}, grid: {{ display: false }} }},
            y: {{ beginAtZero: true, ticks: {{ color: colors.muted, font: {{ family: 'IBM Plex Mono', size: 11 }} }}, grid: {{ color: colors.grid }} }}
          }}
        }}
      }});

      hourChart = new Chart(document.getElementById('hourChart').getContext('2d'), {{
        type: 'bar',
        data: {{
          labels: Array.from({{ length: 24 }}, (_, i) => `${{String(i).padStart(2, '0')}}:00`),
          datasets: [{{
            label: '2026 YTD Requests by Hour of Day (ET)',
            data: TEMPORAL.hour_counts_2026,
            backgroundColor: colors.bar
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: colors.text, font: {{ family: 'IBM Plex Mono', size: 11 }} }} }} }},
          scales: {{
            x: {{ ticks: {{ color: colors.text, font: {{ family: 'IBM Plex Mono', size: 10 }} }}, grid: {{ display: false }} }},
            y: {{ beginAtZero: true, ticks: {{ color: colors.muted, font: {{ family: 'IBM Plex Mono', size: 11 }} }}, grid: {{ color: colors.grid }} }}
          }}
        }}
      }});
    }}

    window.onThemeChange = function() {{
      renderTemporalCharts();
    }};

    document.addEventListener('DOMContentLoaded', renderTemporalCharts);
  </script>
</body>
</html>
"""

    out_path = os.path.join(BASE_DIR, "tables.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Compiled {out_path}")


if __name__ == "__main__":
    build_tables()
