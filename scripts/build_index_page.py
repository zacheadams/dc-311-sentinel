#!/usr/bin/env python3
"""
Compiles the Central Project Hub & Specific Query Explorer (index.html).
Strictly adheres to Agents.md:
- Primary monospace font (IBM Plex Mono)
- Lo-fi black & white aesthetic with light/dark theme toggle
- Zero emojis across code, markup, and UI
- Offline-first vendored Chart.js and jsPDF assets
"""

import json
import os
from datetime import datetime
from html import escape

from ui_common import COMMON_CSS, COMMON_HEAD_FONTS, COMMON_THEME_AND_SORT_JS, render_nav

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_index():
    with open(os.path.join(BASE_DIR, "data", "summary_top.json"), "r", encoding="utf-8") as f:
        summary = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "emerging_issues.json"), "r", encoding="utf-8") as f:
        emerging = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "geography_stats.json"), "r", encoding="utf-8") as f:
        geo = json.load(f)

    meta = summary["metadata"]
    queries = summary["service_queries"]
    categories = summary["categories"]
    wards = geo["wards"]

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
              <td class="num {yoy_cls}" data-val="{yoy_val if yoy_val is not None else -999}">{yoy_str}</td>
              <td class="num" data-val="{d30_val if d30_val is not None else -999}">{d30_str}</td>
              <td class="num" data-val="{q['share_2026_pct']}">{q['share_2026_pct']:.2f}%</td>
              <td class="num" data-val="{q['median_res_hours'] or 9999}">{med_str}</td>
              <td class="num" data-val="{q['sla_pct'] or 0}">{sla_str}</td>
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

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DC 311 Sentinel • District-Wide Service Request Intelligence</title>
{COMMON_HEAD_FONTS}
  <script src="assets/vendor/chartjs/chart.umd.min.js"></script>
  <script src="assets/vendor/jspdf/jspdf.umd.min.js"></script>
  <script src="assets/vendor/jspdf-autotable/jspdf.plugin.autotable.min.js"></script>
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
      margin-bottom: 18px;
      line-height: 1.6;
    }}
    .hero-nav-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 10px;
    }}
    .hero-nav-card {{
      display: block;
      text-decoration: none;
      color: var(--text-main);
      border: 1px solid var(--border);
      background: var(--bg-input);
      padding: 12px 14px;
      border-radius: 2px;
      transition: all 0.15s ease;
    }}
    .hero-nav-card:hover {{
      border-color: var(--text-main);
      background: var(--bg-surface);
    }}
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
{render_nav("index.html")}

  <main class="page-container">
    <section class="hero-banner">
      <div class="hero-kicker">Washington, DC Municipal Operations Sentinel • {meta['total_all_rows']:,} Requests Analyzed</div>
      <h1 class="hero-title">District-Wide 311 Service Request Analysis (2025 – 2026 YTD)</h1>
      <p class="hero-desc">
        Full-population analysis of <strong>{meta['total_2026_ytd']:,}</strong> DC 311 service requests filed in 2026 YTD (Jan 1 – {meta['cutoff_date']}) benchmarked against <strong>{meta['total_2025_ytd']:,}</strong> same-period 2025 requests (<strong>{meta['total_2025_full']:,}</strong> full-year 2025). Evaluates all <strong>{meta['distinct_descriptions_2026']}</strong> specific 2026 service descriptions across 8 Wards and 46 Advisory Neighborhood Commissions (ANCs).
      </p>
      <div class="hero-nav-grid">
        <a href="emerging.html" class="hero-nav-card">
          <div style="font-size:12px;font-weight:800;margin-bottom:3px;">[01] Emerging Issues & Surges</div>
          <div style="font-size:11px;color:var(--text-muted);">YTD YoY growth, recent 30-day acceleration, and localized emerging request surges.</div>
        </a>
        <a href="wards.html" class="hero-nav-card">
          <div style="font-size:12px;font-weight:800;margin-bottom:3px;">[02] Ward & ANC Concerns</div>
          <div style="font-size:11px;color:var(--text-muted);">Ward 1-8 & 46-ANC profiles, Location Quotients (LQ), and localized emerging spikes.</div>
        </a>
        <a href="map.html" class="hero-nav-card">
          <div style="font-size:12px;font-weight:800;margin-bottom:3px;">[03] Spatial Map Explorer</div>
          <div style="font-size:11px;color:var(--text-muted);">Offline Stamen Toner choropleth across Wards and ANCs for any category or specific query.</div>
        </a>
        <a href="tables.html" class="hero-nav-card">
          <div style="font-size:12px;font-weight:800;margin-bottom:3px;">[04] 129-Query Matrix & DETAILS</div>
          <div style="font-size:11px;color:var(--text-muted);">Complete sortable table of all service types, unstructured DETAILS audit, and Agency SLA scorecards.</div>
        </a>
      </div>
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

    <!-- Specific Query Interactive Trend Explorer -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Specific Service Query Trend Explorer (All {len(interactive_queries)} Queries)</h2>
          <p class="section-subtitle">Select any individual 311 service query to compare its monthly 2026 trajectory against 2025 and inspect its top corridors</p>
        </div>
      </div>
      <div class="controls-bar">
        <div class="control-group" style="flex:1;min-width:280px;">
          <label class="control-label" for="query-select">Specific 311 Query:</label>
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
        <a href="emerging.html" class="btn-action" style="text-decoration:none;">Open Full Emerging Issues Monitor</a>
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
        <a href="wards.html" class="btn-action" style="text-decoration:none;">Explore Full Ward & ANC Profiles</a>
      </div>
      <div class="grid-cards">
{chr(10).join(ward_cards_html)}
      </div>
    </section>

    <footer class="site-footer">
      <div>DC 311 Sentinel • Data Source: Open Data DC FeatureServer (Layers 18 & 21)</div>
      <div>Compiled {datetime.now().strftime('%Y-%m-%d')} • Cutoff: {meta['cutoff_date']}</div>
    </footer>
  </main>

{COMMON_THEME_AND_SORT_JS}
  <script>
    const QUERIES = {json.dumps(interactive_queries)};
    const CATEGORIES = {json.dumps(categories)};
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
        ? q.corridors.map(c => `<span class="tag-pill">${{c.corridor}} (W${{c.ward}}: ${{c.count_2026}})</span>`).join(' ')
        : '<span style="color:var(--text-muted);font-size:11px;">No concentrated corridor (>=10 requests)</span>';

      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
          <span class="badge badge-neutral">${{q.cat}}</span>
          <span style="font-size:11px;color:var(--text-muted);">Code: <code>${{q.code}}</code> • Agency: <strong>${{q.agency}}</strong></span>
        </div>
        <div style="font-size:16px;font-weight:800;margin-bottom:12px;">${{q.desc}}</div>
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
              label: '2026 YTD (Jan 1 - Nov 9)',
              data: d26,
              backgroundColor: colors.c2026
            }},
            {{
              label: '2025 Same-Period (Jan 1 - Nov 9)',
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

    out_path = os.path.join(BASE_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Compiled {out_path}")


if __name__ == "__main__":
    build_index()
