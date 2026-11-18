#!/usr/bin/env python3
"""
Compiles the Unlisted Scorecard & Figures Dashboard (other.html):
- Specific Service Request Trend Explorer
- Most Requested 311 Services (Top 20 chart + Top 25 table)
- Operational Category Family Rollup
- Headline Emerging Service Requests & Ward 1-8 Executive Snapshot
- Agency SLA Compliance & Backlog Scorecard
- Chronic Repeat Address Hotspots

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

from ui_common import (
    COMMON_CSS,
    COMMON_HEAD_FONTS,
    COMMON_THEME_AND_SORT_JS,
    render_nav,
    render_footer,
    safe_json_for_script,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_tables():
    with open(os.path.join(BASE_DIR, "data", "summary_top.json"), "r", encoding="utf-8") as f:
        summary = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "emerging_issues.json"), "r", encoding="utf-8") as f:
        emerging = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "geography_stats.json"), "r", encoding="utf-8") as f:
        geo = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "operational_patterns.json"), "r", encoding="utf-8") as f:
        patterns = json.load(f)

    meta = summary["metadata"]
    cutoff_dt = datetime.strptime(meta["cutoff_date"], "%Y-%m-%d")
    cutoff_short = f"{cutoff_dt.strftime('%b')} {cutoff_dt.day}"
    queries = summary["service_queries"]
    categories = summary["categories"]
    wards = geo["wards"]

    code_cat_map = {q["service_code"]: q["category"] for q in queries}
    code_desc_map = {q["service_code"]: q["service_desc"] for q in queries}

    # Build top 25 specific queries table rows
    top25_rows_html = []
    for q in queries[:25]:
        yoy_val = q["yoy_pct"]
        yoy_str = f"{yoy_val:+.1f}%" if yoy_val is not None else "N/A"
        yoy_cls = "kw-surge" if (yoy_val or 0) >= 15 else ("kw-decline" if (yoy_val or 0) <= -10 else "")
        d30_val = q["d30_yoy_pct"]
        d30_str = f"{d30_val:+.1f}%" if d30_val is not None else "N/A"
        sla_str = f"{q['sla_pct']:.1f}%" if q["sla_pct"] is not None else "N/A"
        med_str = f"{q['median_res_hours']:.1f}h" if q["median_res_hours"] is not None else "N/A"
        alias_note = f' <span class="tag-pill" title="Includes legacy description: {escape(", ".join(q["legacy_aliases"]))}">+alias</span>' if q.get("legacy_aliases") else ""

        top25_rows_html.append(
            f"""            <tr>
              <td><code>{escape(q['service_code'])}</code></td>
              <td><strong>{escape(q['service_desc'])}</strong>{alias_note}</td>
              <td>{escape(q['category'])}</td>
              <td>{escape(q['agency'])}</td>
              <td class="num" data-val="{q['count_2026_ytd']}">{q['count_2026_ytd']:,}</td>
              <td class="num" data-val="{q['count_2025_ytd']}">{q['count_2025_ytd']:,}</td>
              <td class="num {yoy_cls}" data-val="{yoy_val if yoy_val is not None else 'N/A'}">{yoy_str}</td>
              <td class="num" data-val="{d30_val if d30_val is not None else 'N/A'}">{d30_str}</td>
              <td class="num" data-val="{q['share_2026_pct']}">{q['share_2026_pct']:.2f}%</td>
              <td class="num" data-val="{q['median_res_hours'] if q['median_res_hours'] is not None else 'N/A'}">{med_str}</td>
              <td class="num" data-val="{q['sla_pct'] if q['sla_pct'] is not None else 'N/A'}">{sla_str}</td>
            </tr>"""
        )

    # Category summary rows
    cat_rows_html = []
    for c in categories:
        yoy_val = c["yoy_pct"]
        yoy_cls = "kw-surge" if (yoy_val or 0) >= 15 else ("kw-decline" if (yoy_val or 0) <= -10 else "")
        cat_rows_html.append(
            f"""            <tr>
              <td><strong>{escape(c['category'])}</strong></td>
              <td class="num" data-val="{c['query_count']}">{c['query_count']}</td>
              <td class="num" data-val="{c['count_2026_ytd']}">{c['count_2026_ytd']:,}</td>
              <td class="num" data-val="{c['count_2025_ytd']}">{c['count_2025_ytd']:,}</td>
              <td class="num {yoy_cls}" data-val="{yoy_val}">{yoy_val:+.1f}%</td>
              <td class="num" data-val="{c['d30_yoy_pct']}">{c['d30_yoy_pct']:+.1f}%</td>
              <td class="num" data-val="{c['share_2026_pct']}">{c['share_2026_pct']:.2f}%</td>
              <td class="num" data-val="{c['median_res_hours'] or 9999}">{c['median_res_hours'] or 0:.1f}h</td>
              <td class="num" data-val="{c['sla_pct'] or 0}">{c['sla_pct'] or 0:.1f}%</td>
            </tr>"""
        )

    # Top emerging high-volume highlights (ytd_2026 >= 350)
    top_emerging_cards = []
    high_vol_emerging = [
        e for e in emerging["items"]
        if e["ytd_2026"] >= 350 and e["status"] in ("EMERGING_ACCELERATING", "EMERGING_SURGE")
    ][:8]
    for e in high_vol_emerging:
        d30_str = f"{e['d30_yoy_pct']:+.1f}%" if e["d30_yoy_pct"] is not None else "N/A"
        top_emerging_cards.append(
            f"""        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span class="badge badge-surge">{escape(e['status'].replace('_', ' '))}</span>
            <span style="font-size:11px;color:var(--text-muted);"><code>{escape(e['service_code'])}</code> • {escape(e['agency'])}</span>
          </div>
          <div style="font-size:14px;font-weight:800;margin-bottom:8px;">{escape(e['service_desc'])}</div>
          <div style="font-size:12px;display:grid;grid-template-columns:1fr 1fr;gap:6px;">
            <div>2026 YTD: <strong>{e['ytd_2026']:,}</strong></div>
            <div>2025 YTD: <strong>{e['ytd_2025']:,}</strong></div>
            <div>Same-Period YoY: <span class="kw-surge">{e['ytd_yoy_pct']:+.1f}%</span></div>
            <div>30-Day YoY: <strong>{d30_str}</strong></div>
          </div>
        </div>"""
        )

    # Ward snapshot row
    ward_cards_html = []
    for w_num in range(1, 9):
        w = wards[str(w_num)]
        top_req = w["top_requests"][0]["service_desc"] if w["top_requests"] else "N/A"
        sig_req = w["signature_concerns"][0] if w["signature_concerns"] else None
        sig_str = f"{sig_req['service_desc']} ({sig_req['lq']}x LQ)" if sig_req else "N/A"
        ward_cards_html.append(
            f"""        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">
            <span style="font-size:15px;font-weight:800;">Ward {w_num}</span>
            <span style="font-size:11px;color:var(--text-muted);">{escape(w['councilmember'])}</span>
          </div>
          <div style="font-size:20px;font-weight:800;margin-bottom:4px;">{w['count_2026_ytd']:,} <span style="font-size:12px;font-weight:600;" class="{'kw-surge' if w['yoy_pct'] >= 15 else ''}">({w['yoy_pct']:+.1f}% YoY)</span></div>
          <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">#1 Volume: <strong style="color:var(--text-main);">{escape(top_req)}</strong></div>
          <div style="font-size:11px;color:var(--text-muted);">Top Concentration: <strong style="color:var(--text-main);">{escape(sig_str)}</strong></div>
        </div>"""
        )

    # Embed compact JSON for interactive query selector & charts
    interactive_queries = [
        {
            "code": q["service_code"],
            "desc": q["service_desc"],
            "cat": q["category"],
            "agency": q["agency"],
            "c26": q["count_2026_ytd"],
            "c25": q["count_2025_ytd"],
            "c25_full": q["count_2025_full"],
            "yoy": q["yoy_pct"],
            "d30_yoy": q["d30_yoy_pct"],
            "med_hrs": q["median_res_hours"],
            "sla": q["sla_pct"],
            "open": q["open_count"],
            "m25": q["monthly_2025"],
            "m26": q["monthly_2026"],
            "corridors": q["top_corridors_2026"],
        }
        for q in queries
        if q["count_2026_ytd"] > 0 or q["count_2025_full"] > 0
    ]

    agencies = patterns["agencies"]
    repeats = patterns["repeat_hotspots"]["by_service_code"]

    # Agency SLA Scorecard rows
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
              <td class="num" data-val="{a['median_res_hours'] if a['median_res_hours'] is not None else 'N/A'}">{med_h}</td>
              <td class="num" data-val="{a['p90_res_hours'] if a['p90_res_hours'] is not None else 'N/A'}">{p90_h}</td>
              <td class="num" data-val="{a['sla_pct_2026'] if a['sla_pct_2026'] is not None else 'N/A'}">{sla26}</td>
              <td class="num" data-val="{a['sla_pct_2025'] if a['sla_pct_2025'] is not None else 'N/A'}">{sla25}</td>
              <td class="num" data-val="{a['open_count']}">{a['open_count']:,}</td>
              <td class="num" data-val="{a['aged_open_30d']}">{a['aged_open_30d']:,}</td>
            </tr>"""
        )

    # Chronic Repeat MAR Address Hotspots
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
  <meta name="robots" content="noindex, nofollow">
  <title>DC 311 Sentinel • Scorecards & Repeat Hotspots</title>
{COMMON_HEAD_FONTS}
  <script src="assets/vendor/chartjs/chart.umd.min.js"></script>
  <script src="assets/vendor/jspdf/jspdf.umd.min.js"></script>
  <script src="assets/vendor/jspdf-autotable/jspdf.plugin.autotable.min.js"></script>
  <style>
{COMMON_CSS}
    .grid-2col {{
      display: grid;
      grid-template-columns: 1.3fr 1fr;
      gap: 16px;
    }}
    .grid-cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(255px, 1fr));
      gap: 12px;
    }}
    @media (max-width: 900px) {{
      .grid-2col {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
{render_nav("")}

  <main class="page-container">
    <!-- Specific Query Interactive Trend Explorer -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Specific Service Request Trend Explorer (All {len(interactive_queries)} Requests)</h2>
          <p class="section-subtitle">Select any individual 311 service request to compare its monthly 2026 trajectory against 2025 and inspect its top corridors</p>
        </div>
      </div>
      <div class="controls-bar">
        <div class="control-group" style="flex:1;min-width:280px;">
          <label class="control-label" for="query-select">Specific 311 Request:</label>
          <select id="query-select" style="flex:1;max-width:560px;" onchange="updateQueryExplorer()"></select>
        </div>
        <div class="control-group">
          <label class="control-label" for="cat-filter">Filter Category:</label>
          <select id="cat-filter" onchange="populateQueryDropdown()">
            <option value="ALL">All Categories ({len(interactive_queries)})</option>
          </select>
        </div>
      </div>
      <div class="grid-2col">
        <div class="card">
          <div style="height:290px;">
            <canvas id="queryTrendChart"></canvas>
          </div>
        </div>
        <div class="card" id="query-detail-card">
          <!-- Populated dynamically by updateQueryExplorer() -->
        </div>
      </div>
    </section>

    <!-- Top 20 Specific Service Queries Bar Chart -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Most Requested 311 Services in 2026 YTD vs. Same-Period 2025</h2>
          <p class="section-subtitle">Toggle between the Top 20 Specific Service Queries and the 11 Operational Category Rollups</p>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn-action" id="btn-view-specific" onclick="setTopChartMode('specific')">View: Top 20 Specific Queries</button>
          <button class="btn-action" id="btn-view-category" onclick="setTopChartMode('category')">View: 11 Category Families</button>
        </div>
      </div>
      <div class="card" style="margin-bottom:18px;">
        <div style="height:440px;">
          <canvas id="topRequestsChart"></canvas>
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table" id="top25-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Service Request Description</th>
              <th>Category Family</th>
              <th>Agency</th>
              <th class="num">2026 YTD</th>
              <th class="num">2025 YTD</th>
              <th class="num">YoY %</th>
              <th class="num">30-Day YoY %</th>
              <th class="num">2026 Share</th>
              <th class="num">Median Res</th>
              <th class="num">SLA Met %</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(top25_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Operational Category Rollup Table -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Operational Category Family Rollup (2026 YTD vs. 2025 YTD)</h2>
          <p class="section-subtitle">Aggregated across all {meta['distinct_service_codes_all']} canonical service codes</p>
        </div>
        <div>
          <button class="btn-action" onclick="exportTableToCSV('category-table', 'dc_311_categories_2026.csv')">Export CSV</button>
          <button class="btn-action" onclick="exportTableToPDF('category-table', 'DC 311 Category Rollup (2026 YTD)', 'dc_311_categories_2026.pdf')">Export PDF</button>
        </div>
      </div>
      <div class="table-wrap">
        <table class="data-table" id="category-table">
          <thead>
            <tr>
              <th>Category Family</th>
              <th class="num">Specific Codes</th>
              <th class="num">2026 YTD</th>
              <th class="num">2025 YTD</th>
              <th class="num">Same-Period YoY %</th>
              <th class="num">30-Day YoY %</th>
              <th class="num">Share of 311</th>
              <th class="num">Median Resolution</th>
              <th class="num">SLA Met %</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(cat_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Headline Emerging Surges -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Headline Emerging Service Requests (High-Volume Surges)</h2>
          <p class="section-subtitle">Specific requests with statistically significant YTD growth and recent 30-day acceleration</p>
        </div>
        <a href="tables.html" class="btn-action" style="text-decoration:none;">Open Full Trends Monitor</a>
      </div>
      <div class="grid-cards">
{chr(10).join(top_emerging_cards)}
      </div>
    </section>

    <!-- Ward 1-8 Snapshot -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Ward 1 – 8 Executive Snapshot</h2>
          <p class="section-subtitle">2026 YTD volume, same-period YoY growth, top request by volume, and highest Location Quotient concentration</p>
        </div>
        <a href="map.html" class="btn-action" style="text-decoration:none;">Explore Spatial Map</a>
      </div>
      <div class="grid-cards">
{chr(10).join(ward_cards_html)}
      </div>
    </section>

    <!-- Agency SLA & Backlog Scorecard -->
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

    <!-- Chronic Repeat Address Hotspots (2026 YTD) -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Chronic Repeat Address Hotspots (2026 YTD)</h2>
          <p class="section-subtitle">Master Address Repository (MAR) locations with 5 or more requests for the same service request</p>
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
              <th>Service Request</th>
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
    const QUERIES = {safe_json_for_script(interactive_queries)};
    const CATEGORIES = {safe_json_for_script(categories)};
    const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    let queryChart = null;
    let topChart = null;
    let currentTopMode = 'specific';

    function getChartColors() {{
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      return {{
        text: dark ? '#f4f4f5' : '#09090b',
        muted: dark ? '#a1a1aa' : '#52525b',
        grid: dark ? '#27272a' : '#e4e4e7',
        c2026: dark ? '#38bdf8' : '#2563eb',
        c2025: dark ? '#71717a' : '#94a3b8',
      }};
    }}

    function initCategoryFilter() {{
      const catSel = document.getElementById('cat-filter');
      CATEGORIES.forEach(c => {{
        const opt = document.createElement('option');
        opt.value = c.category;
        opt.textContent = `${{c.category}} (${{c.query_count}})`;
        catSel.appendChild(opt);
      }});
      populateQueryDropdown();
    }}

    function populateQueryDropdown() {{
      const catVal = document.getElementById('cat-filter').value;
      const qSel = document.getElementById('query-select');
      const prevCode = qSel.value;
      qSel.innerHTML = '';
      const filtered = catVal === 'ALL' ? QUERIES : QUERIES.filter(q => q.cat === catVal);
      filtered.forEach(q => {{
        const opt = document.createElement('option');
        opt.value = q.code;
        const yoyTxt = q.yoy !== null ? `${{q.yoy >= 0 ? '+' : ''}}${{q.yoy.toFixed(1)}}%` : 'N/A';
        opt.textContent = `${{q.desc}} [${{q.code}}] — ${{q.c26.toLocaleString()}} in 2026 (${{yoyTxt}} YoY)`;
        qSel.appendChild(opt);
      }});
      if (filtered.some(q => q.code === prevCode)) {{
        qSel.value = prevCode;
      }}
      updateQueryExplorer();
    }}

    function updateQueryExplorer() {{
      const code = document.getElementById('query-select').value;
      const q = QUERIES.find(x => x.code === code) || QUERIES[0];
      if (!q) return;

      const card = document.getElementById('query-detail-card');
      const yoyTxt = q.yoy !== null ? `${{q.yoy >= 0 ? '+' : ''}}${{q.yoy.toFixed(1)}}%` : 'N/A';
      const d30Txt = q.d30_yoy !== null ? `${{q.d30_yoy >= 0 ? '+' : ''}}${{q.d30_yoy.toFixed(1)}}%` : 'N/A';
      const corridorsHtml = (q.corridors && q.corridors.length)
        ? q.corridors.map(c => `<span class="tag-pill">${{escapeHtml(c.corridor)}} (W${{escapeHtml(c.ward)}}: ${{c.count_2026}})</span>`).join(' ')
        : '<span style="color:var(--text-muted);font-size:11px;">No concentrated corridor (>=10 requests)</span>';

      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
          <span class="badge badge-neutral">${{escapeHtml(q.cat)}}</span>
          <span style="font-size:11px;color:var(--text-muted);">Code: <code>${{escapeHtml(q.code)}}</code> • Agency: <strong>${{escapeHtml(q.agency)}}</strong></span>
        </div>
        <div style="font-size:16px;font-weight:800;margin-bottom:12px;">${{escapeHtml(q.desc)}}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12px;margin-bottom:14px;">
          <div style="padding:8px;background:var(--bg-input);border-radius:2px;">
            <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">2026 YTD Volume</div>
            <div style="font-size:18px;font-weight:800;">${{q.c26.toLocaleString()}}</div>
          </div>
          <div style="padding:8px;background:var(--bg-input);border-radius:2px;">
            <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">2025 Same-Period</div>
            <div style="font-size:18px;font-weight:800;">${{q.c25.toLocaleString()}} <span style="font-size:11px;color:var(--text-muted);">(${{q.c25_full.toLocaleString()}} full yr)</span></div>
          </div>
          <div style="padding:8px;background:var(--bg-input);border-radius:2px;">
            <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Same-Period YoY</div>
            <div style="font-size:16px;font-weight:800;" class="${{(q.yoy || 0) >= 15 ? 'kw-surge' : ((q.yoy || 0) <= -10 ? 'kw-decline' : '')}}">${{yoyTxt}}</div>
          </div>
          <div style="padding:8px;background:var(--bg-input);border-radius:2px;">
            <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Last 30 Days YoY</div>
            <div style="font-size:16px;font-weight:800;">${{d30Txt}}</div>
          </div>
          <div style="padding:8px;background:var(--bg-input);border-radius:2px;">
            <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Median Resolution</div>
            <div style="font-size:15px;font-weight:700;">${{q.med_hrs !== null ? q.med_hrs + ' hrs' : 'N/A'}}</div>
          </div>
          <div style="padding:8px;background:var(--bg-input);border-radius:2px;">
            <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">On-Time SLA / Open</div>
            <div style="font-size:15px;font-weight:700;">${{q.sla !== null ? q.sla + '%' : 'N/A'}} • ${{q.open.toLocaleString()}} open</div>
          </div>
        </div>
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px;">Top 2026 Street Corridors:</div>
        <div>${{corridorsHtml}}</div>
      `;

      const colors = getChartColors();
      const ctx = document.getElementById('queryTrendChart').getContext('2d');
      if (queryChart) queryChart.destroy();
      queryChart = new Chart(ctx, {{
        type: 'line',
        data: {{
          labels: MONTHS,
          datasets: [
            {{
              label: '2026 Monthly Requests (Jan-Nov)',
              data: q.m26.slice(0, 11).concat([null]),
              borderColor: colors.c2026,
              backgroundColor: colors.c2026,
              borderWidth: 2.5,
              tension: 0.2,
              pointRadius: 3
            }},
            {{
              label: '2025 Monthly Requests (Jan-Dec)',
              data: q.m25,
              borderColor: colors.c2025,
              backgroundColor: colors.c2025,
              borderDash: [4, 4],
              borderWidth: 2,
              tension: 0.2,
              pointRadius: 2.5
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ labels: {{ color: colors.text, font: {{ family: 'IBM Plex Mono', size: 11 }} }} }},
            title: {{
              display: true,
              text: `${{q.desc}} [${{q.code}}] — Monthly Volume (2025 vs 2026)`,
              color: colors.text,
              font: {{ family: 'IBM Plex Mono', size: 12, weight: 'bold' }}
            }}
          }},
          scales: {{
            x: {{ ticks: {{ color: colors.muted, font: {{ family: 'IBM Plex Mono', size: 11 }} }}, grid: {{ color: colors.grid }} }},
            y: {{ beginAtZero: true, ticks: {{ color: colors.muted, font: {{ family: 'IBM Plex Mono', size: 11 }} }}, grid: {{ color: colors.grid }} }}
          }}
        }}
      }});
    }}

    function setTopChartMode(mode) {{
      currentTopMode = mode;
      const colors = getChartColors();
      const ctx = document.getElementById('topRequestsChart').getContext('2d');
      if (topChart) topChart.destroy();

      let labels = [];
      let d26 = [];
      let d25 = [];

      if (mode === 'specific') {{
        const top20 = QUERIES.slice(0, 20);
        labels = top20.map(q => q.desc.length > 34 ? q.desc.slice(0, 32) + '..' : q.desc);
        d26 = top20.map(q => q.c26);
        d25 = top20.map(q => q.c25);
      }} else {{
        labels = CATEGORIES.map(c => c.category);
        d26 = CATEGORIES.map(c => c.count_2026_ytd);
        d25 = CATEGORIES.map(c => c.count_2025_ytd);
      }}

      topChart = new Chart(ctx, {{
        type: 'bar',
        data: {{
          labels: labels,
          datasets: [
            {{
              label: '2026 YTD (Jan 1 - {cutoff_short})',
              data: d26,
              backgroundColor: colors.c2026
            }},
            {{
              label: '2025 Same-Period (Jan 1 - {cutoff_short})',
              data: d25,
              backgroundColor: colors.c2025
            }}
          ]
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ labels: {{ color: colors.text, font: {{ family: 'IBM Plex Mono', size: 11 }} }} }}
          }},
          scales: {{
            x: {{ ticks: {{ color: colors.muted, font: {{ family: 'IBM Plex Mono', size: 11 }} }}, grid: {{ color: colors.grid }} }},
            y: {{ ticks: {{ color: colors.text, font: {{ family: 'IBM Plex Mono', size: 11 }} }}, grid: {{ display: false }} }}
          }}
        }}
      }});
    }}

    window.onThemeChange = function() {{
      updateQueryExplorer();
      setTopChartMode(currentTopMode);
    }};

    document.addEventListener('DOMContentLoaded', () => {{
      initCategoryFilter();
      setTopChartMode('specific');
    }});
  </script>
</body>
</html>
"""

    out_path = os.path.join(BASE_DIR, "other.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Compiled {out_path}")


if __name__ == "__main__":
    build_tables()
