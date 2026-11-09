#!/usr/bin/env python3
"""
Compiles the Master 129-Query Matrix, Unstructured DETAILS Audit, Agency SLA
Scorecard, and Repeat Hotspot Explorer (tables.html).

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
from datetime import datetime
from html import escape

from ui_common import COMMON_CSS, COMMON_HEAD_FONTS, COMMON_THEME_AND_SORT_JS, render_nav

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_tables():
    with open(os.path.join(BASE_DIR, "data", "summary_top.json"), "r", encoding="utf-8") as f:
        summary = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "operational_patterns.json"), "r", encoding="utf-8") as f:
        patterns = json.load(f)

    queries = summary["service_queries"]
    details_audit = patterns["details_audit"]
    agencies = patterns["agencies"]
    repeats = patterns["repeat_hotspots"]["by_service_code"]
    temporal = patterns["temporal"]

    # 1. Master all-queries table rows
    master_rows_html = []
    for q in queries:
        yoy_val = q["yoy_pct"]
        yoy_str = f"{yoy_val:+.1f}%" if yoy_val is not None else "N/A"
        yoy_cls = "kw-surge" if (yoy_val or 0) >= 20 else ("kw-decline" if (yoy_val or 0) <= -15 else "")

        d30_val = q["d30_yoy_pct"]
        d30_str = f"{d30_val:+.1f}%" if d30_val is not None else "N/A"
        med_str = f"{q['median_res_hours']:.1f}h" if q["median_res_hours"] is not None else "N/A"
        p90_str = f"{q['p90_res_hours']:.1f}h" if q["p90_res_hours"] is not None else "N/A"
        sla_str = f"{q['sla_pct']:.1f}%" if q["sla_pct"] is not None else "N/A"

        top_corr = q["top_corridors_2026"][0] if q.get("top_corridors_2026") else None
        corr_str = f"{top_corr['corridor']} ({top_corr['count_2026']})" if top_corr else "-"
        aliases_str = f" (formerly: {', '.join(q['legacy_aliases'])})" if q.get("legacy_aliases") else ""

        master_rows_html.append(
            f"""            <tr data-cat="{escape(q['category'])}" data-agency="{escape(q['agency'])}">
              <td><code>{escape(q['service_code'])}</code></td>
              <td><strong>{escape(q['service_desc'])}</strong><span style="font-size:10px;color:var(--text-muted);">{escape(aliases_str)}</span></td>
              <td>{escape(q['category'])}</td>
              <td>{escape(q['agency'])}</td>
              <td class="num" data-val="{q['count_2026_ytd']}">{q['count_2026_ytd']:,}</td>
              <td class="num" data-val="{q['count_2025_ytd']}">{q['count_2025_ytd']:,}</td>
              <td class="num" data-val="{q['count_2025_full']}">{q['count_2025_full']:,}</td>
              <td class="num {yoy_cls}" data-val="{yoy_val if yoy_val is not None else -9999}">{yoy_str}</td>
              <td class="num" data-val="{d30_val if d30_val is not None else -9999}">{d30_str}</td>
              <td class="num" data-val="{q['share_2026_pct']}">{q['share_2026_pct']:.2f}%</td>
              <td class="num" data-val="{q['median_res_hours'] or 99999}">{med_str}</td>
              <td class="num" data-val="{q['p90_res_hours'] or 99999}">{p90_str}</td>
              <td class="num" data-val="{q['sla_pct'] or 0}">{sla_str}</td>
              <td class="num" data-val="{q['open_count']}">{q['open_count']:,}</td>
              <td style="font-size:11px;">{escape(corr_str)}</td>
            </tr>"""
        )

    # 2. Unstructured DETAILS audit table rows
    details_rows_html = []
    for d in details_audit["by_service_code"]:
        phrases_html = " ".join(f'<span class="tag-pill">{escape(p)}</span>' for p in d["top_phrases"][:4])
        details_rows_html.append(
            f"""            <tr>
              <td><code>{escape(d['service_code'])}</code></td>
              <td><strong>{escape(d['service_desc'])}</strong></td>
              <td>{escape(d['agency'])}</td>
              <td class="num" data-val="{d['total_details']}">{d['total_details']:,}</td>
              <td class="num" data-val="{d['details_2025']}">{d['details_2025']:,}</td>
              <td class="num" data-val="{d['details_2026']}">{d['details_2026']:,}</td>
              <td class="num" data-val="{d['closed_pct']}">{d['closed_pct']:.1f}%</td>
              <td style="font-size:11px;max-width:420px;">"{escape(d['dominant_note'][:180])}{'...' if len(d['dominant_note']) > 180 else ''}"</td>
              <td>{phrases_html}</td>
            </tr>"""
        )

    # 3. Agency SLA Scorecard rows
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

    # 4. Chronic Repeat MAR Address Hotspots
    repeat_rows_html = []
    for r in repeats:
        repeat_rows_html.append(
            f"""            <tr>
              <td><code>{escape(r['service_code'])}</code></td>
              <td><strong>{escape(r['service_desc'])}</strong></td>
              <td class="num" data-val="{r['locations_5plus']}">{r['locations_5plus']:,}</td>
              <td class="num" data-val="{r['locations_10plus']}">{r['locations_10plus']:,}</td>
              <td class="num" data-val="{r['total_chronic_tickets']}">{r['total_chronic_tickets']:,}</td>
              <td class="num" data-val="{r['max_single_location']}">{r['max_single_location']:,}</td>
            </tr>"""
        )

    categories_unique = sorted({q["category"] for q in queries})
    agencies_unique = sorted({q["agency"] for q in queries})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DC 311 Sentinel • Master Query Matrix, DETAILS Audit & Agency Scorecards</title>
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
{render_nav("tables.html", "Complete Service Query Matrix, Unstructured DETAILS Audit & Agency Scorecards")}

  <main class="page-container">
    <!-- Section 1: Complete Service Query Matrix -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Complete Service Query Performance Matrix ({len(queries)} Canonical Codes / {len(summary['raw_descriptions'])} Descriptions)</h2>
          <p class="section-subtitle">Bidirectional sorting on all columns; includes legacy description continuity mapping and top 2026 street corridors</p>
        </div>
        <div>
          <button class="btn-action" onclick="exportTableToCSV('master-query-table', 'dc_311_all_queries_2026.csv')">Export CSV</button>
          <button class="btn-action" onclick="exportTableToPDF('master-query-table', 'DC 311 Complete Service Query Matrix (2026 YTD)', 'dc_311_all_queries_2026.pdf')">Export PDF</button>
        </div>
      </div>

      <div class="controls-bar">
        <div class="control-group">
          <label class="control-label" for="m-cat-filter">Category:</label>
          <select id="m-cat-filter" onchange="filterMasterTable()">
            <option value="ALL">All Categories</option>
            {''.join(f'<option value="{escape(c)}">{escape(c)}</option>' for c in categories_unique)}
          </select>
        </div>
        <div class="control-group">
          <label class="control-label" for="m-agency-filter">Agency:</label>
          <select id="m-agency-filter" onchange="filterMasterTable()">
            <option value="ALL">All Agencies</option>
            {''.join(f'<option value="{escape(a)}">{escape(a)}</option>' for a in agencies_unique)}
          </select>
        </div>
        <div class="control-group" style="flex:1;min-width:200px;">
          <input type="search" id="m-search" placeholder="Search code, description, alias, or corridor..." style="width:100%;" oninput="filterMasterTable()">
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table" id="master-query-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Service Request Description</th>
              <th>Category</th>
              <th>Agency</th>
              <th class="num">2026 YTD</th>
              <th class="num">2025 YTD</th>
              <th class="num">2025 Full</th>
              <th class="num">YoY %</th>
              <th class="num">30d YoY %</th>
              <th class="num">Share %</th>
              <th class="num">Median Res</th>
              <th class="num">p90 Res</th>
              <th class="num">SLA Met %</th>
              <th class="num">Open</th>
              <th>Top 2026 Corridor</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(master_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Section 2: Unstructured DETAILS Column Audit & Text Insights -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Unstructured DETAILS Column Audit & Administrative Closure Insights</h2>
          <p class="section-subtitle">Full inspection of all {details_audit['total_populated_2025_2026']:,} populated DETAILS narratives across 885,742 service requests</p>
        </div>
      </div>

      <div class="card" style="margin-bottom:16px;">
        <div style="font-size:13px;font-weight:800;margin-bottom:6px;">Key Unstructured Text Finding: DGS Automated Mass-Closure Boilerplate</div>
        <p style="font-size:12px;color:var(--text-muted);line-height:1.6;">
          Across the entire 885,742-row 2025–2026 dataset in Open Data DC's public FeatureServer, <strong>{details_audit['total_populated_2025_2026']:,}</strong> records contain non-empty <code>DETAILS</code> text ({details_audit['populated_2025']:,} in 2025 and {details_audit['populated_2026']:,} in 2026). Text mining reveals that <strong>{details_audit['dgs_mass_closure_boilerplate_count']:,} ({details_audit['dgs_mass_closure_share_pct']}%)</strong> of all populated <code>DETAILS</code> entries are identical Department of General Services (DGS) administrative closure templates across 7 recreation and grounds maintenance service codes:
          <em>"Thank you for establishing a request for city services. At this time, we have closed this request for any further action. If this issue is still present, please submit a new 311 request so that it can be investigated and addressed."</em>
          Similarly, in 2026, populated <code>DETAILS</code> on <code>SnowIceRP24</code> capture post-storm administrative batch closures following the January 2026 snow event.
        </p>
      </div>

      <div class="table-wrap">
        <table class="data-table" id="details-audit-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Service Request Description</th>
              <th>Agency</th>
              <th class="num">Total Populated</th>
              <th class="num">2025</th>
              <th class="num">2026</th>
              <th class="num">Closed %</th>
              <th>Dominant Unstructured DETAILS Narrative</th>
              <th>Top Extracted Phrases</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(details_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Section 3: Agency SLA & Backlog Scorecard -->
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

    <!-- Section 4: Temporal Filing Profiles & Chronic Repeat Properties -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Temporal Filing Rhythm & Chronic Repeat Address Hotspots (2026 YTD)</h2>
          <p class="section-subtitle">Day-of-week and hour-of-day submission distributions alongside MAR address repeat concentrations</p>
        </div>
      </div>
      <div class="grid-2col" style="margin-bottom:18px;">
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

      <div class="table-wrap">
        <table class="data-table" id="repeat-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Service Request Description</th>
              <th class="num">Chronic Properties (&ge;5 Requests)</th>
              <th class="num">Severe Repeat Properties (&ge;10 Requests)</th>
              <th class="num">Total Tickets at Chronic Properties</th>
              <th class="num">Max Requests at Single MAR ID</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(repeat_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <footer class="site-footer">
      <div>DC 311 Sentinel • Complete Data Matrices & Operational Patterns</div>
      <div>Compiled {datetime.now().strftime('%Y-%m-%d')}</div>
    </footer>
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

    function filterMasterTable() {{
      const cat = document.getElementById('m-cat-filter').value;
      const ag = document.getElementById('m-agency-filter').value;
      const q = document.getElementById('m-search').value.trim().toLowerCase();

      const rows = document.querySelectorAll('#master-query-table tbody tr');
      rows.forEach(r => {{
        const rCat = r.getAttribute('data-cat');
        const rAg = r.getAttribute('data-agency');
        const txt = r.innerText.toLowerCase();
        const ok = (cat === 'ALL' || rCat === cat) && (ag === 'ALL' || rAg === ag) && (!q || txt.includes(q));
        r.style.display = ok ? '' : 'none';
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
