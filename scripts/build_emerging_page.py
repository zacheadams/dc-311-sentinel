#!/usr/bin/env python3
"""
Compiles the Trends & Geographic Subset Monitor (emerging.html).
Evaluates specific 311 service requests using:
- YTD Same-Period YoY Ratio & Completion Times (Jan 1 - Nov 9, 2026 vs 2025)
- Recent 30-Day YoY Ratio & Completion Times
- Geographic subset filtering across Citywide, Wards, ANCs, and SMDs
- Weekly request volume and completion time comparative trajectories

Strictly adheres to Agents.md:
- Primary monospace font (IBM Plex Mono)
- Lo-fi black & white aesthetic with light/dark theme toggle
- Zero emojis anywhere
- No 90-day window
"""

import json
import os
from datetime import datetime
from html import escape

from ui_common import COMMON_CSS, COMMON_HEAD_FONTS, COMMON_THEME_AND_SORT_JS, render_nav, render_footer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_emerging():
    with open(os.path.join(BASE_DIR, "data", "emerging_issues.json"), "r", encoding="utf-8") as f:
        emerging = json.load(f)

    items = emerging["items"]
    geo_trends = emerging.get("geo_trends", {})

    # Build initial Citywide YTD table rows for immediate SSR / first paint
    table_rows_html = []
    for x in items:
        yoy_val = x["ytd_yoy_pct"]
        yoy_str = f"{yoy_val:+.1f}%" if yoy_val is not None else "NEW"
        yoy_cls = "kw-surge" if (yoy_val or 0) >= 20 else ("kw-decline" if (yoy_val or 0) <= -15 else "")

        t26_val = x.get("ytd_res_days_2026")
        t25_val = x.get("ytd_res_days_2025")
        t26_str = f"{t26_val} {'day' if t26_val == 1 else 'days'}" if t26_val is not None else "N/A"
        t25_str = f"{t25_val} {'day' if t25_val == 1 else 'days'}" if t25_val is not None else "N/A"

        tpct_val = x.get("ytd_res_pct")
        tpct_str = f"{tpct_val:+.1f}%" if tpct_val is not None else "N/A"
        tpct_cls = "kw-surge" if (tpct_val or 0) >= 20 else ("kw-decline" if (tpct_val or 0) <= -15 else "")

        table_rows_html.append(
            f"""            <tr data-code="{escape(x['service_code'])}" data-cat="{escape(x['category'])}">
              <td><code>{escape(x['service_code'])}</code></td>
              <td><a href="#chart-anchor" onclick="selectTrajectoryCode('{escape(x['service_code'])}')" style="color:var(--text-main);font-weight:700;">{escape(x['service_desc'])}</a></td>
              <td>{escape(x['category'])}</td>
              <td class="num" data-val="{x['ytd_2026']}">{x['ytd_2026']:,}</td>
              <td class="num" data-val="{x['ytd_2025']}">{x['ytd_2025']:,}</td>
              <td class="num {yoy_cls}" data-val="{yoy_val if yoy_val is not None else 9999}">{yoy_str}</td>
              <td class="num" data-val="{t26_val if t26_val is not None else -1}">{t26_str}</td>
              <td class="num" data-val="{t25_val if t25_val is not None else -1}">{t25_str}</td>
              <td class="num {tpct_cls}" data-val="{tpct_val if tpct_val is not None else 9999}">{tpct_str}</td>
            </tr>"""
        )

    # Ward emerging cards
    ward_em_cards = []
    for w_num in range(1, 9):
        em_list = emerging["ward_emerging"].get(str(w_num), [])
        rows_li = []
        for em in em_list[:6]:
            rows_li.append(
                f"""<div style="display:flex;justify-content:space-between;gap:8px;padding:5px 0;border-bottom:1px dashed var(--border);font-size:11px;">
                  <span><strong>{escape(em['service_desc'])}</strong></span>
                  <span style="white-space:nowrap;" class="kw-surge">{em['count_2026_ytd']:,} vs {em['count_2025_ytd']:,} ({em['yoy_pct']:+.1f}%)</span>
                </div>"""
            )
        ward_em_cards.append(
            f"""        <div class="card">
          <div style="font-size:14px;font-weight:800;margin-bottom:8px;">Ward {w_num} Emerging Surges</div>
          {''.join(rows_li) if rows_li else '<div style="font-size:11px;color:var(--text-muted);">No high-volume surges above threshold</div>'}
        </div>"""
        )

    categories_unique = sorted({x["category"] for x in items})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DC 311 Sentinel • Trends</title>
{COMMON_HEAD_FONTS}
  <script src="assets/vendor/chartjs/chart.umd.min.js"></script>
  <script src="assets/vendor/jspdf/jspdf.umd.min.js"></script>
  <script src="assets/vendor/jspdf-autotable/jspdf.plugin.autotable.min.js"></script>
  <style>
{COMMON_CSS}
    .grid-cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
      gap: 12px;
    }}
  </style>
</head>
<body>
{render_nav("emerging.html", "Trends • Weekly Trajectories & Geographic Patterns")}

  <main class="page-container">
    <!-- Weekly Comparative Trajectory -->
    <section class="section-block" id="chart-anchor">
      <div class="section-header">
        <div>
          <h2 class="section-title">Trends by Request</h2>
        </div>
      </div>
      <div class="controls-bar">
        <div class="control-group" style="flex:1;min-width:280px;">
          <label class="control-label" for="traj-code-select">Service Request:</label>
          <select id="traj-code-select" style="flex:1;max-width:560px;" onchange="renderTrajectoryChart()"></select>
        </div>
      </div>
      <div class="card">
        <div id="traj-chart-title" style="text-align:center;font-weight:700;font-size:13px;color:var(--text-main);margin-bottom:8px;"></div>
        <div id="traj-legend" style="display:grid;grid-template-columns:repeat(2, minmax(180px, max-content));justify-content:center;column-gap:36px;row-gap:8px;margin:4px 0 14px 0;font-size:11px;"></div>
        <div style="height:480px;">
          <canvas id="trajectoryChart"></canvas>
        </div>
        <div id="traj-summary-strip" style="margin-top:12px;padding-top:10px;border-top:1px solid var(--border);font-size:12px;display:flex;flex-wrap:wrap;gap:18px;"></div>
      </div>
    </section>

    <!-- Main Trends by Ward Table -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Trends by Ward</h2>
        </div>
        <div>
          <button class="btn-action" onclick="exportTableToCSV('emerging-table', 'dc_311_trends.csv')">Export CSV</button>
          <button class="btn-action" onclick="exportTableToPDF('emerging-table', 'DC 311 Trends', 'dc_311_trends.pdf')">Export PDF</button>
        </div>
      </div>

      <!-- Geographic Subset Selector Card -->
      <div class="card" style="margin-bottom:12px;padding:12px 14px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <span style="font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">Geographic Subset</span>
          <span id="geo-selection-badge" class="badge badge-neutral">Citywide (All Wards)</span>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(210px, 1fr));gap:10px;align-items:center;">
          <div class="control-group" style="width:100%;">
            <label class="control-label" for="smd-search" style="min-width:44px;">Search:</label>
            <input type="search" id="smd-search" placeholder="Search SMD (e.g. 5E03), ANC, or Ward..." style="flex:1;" oninput="handleGeoSearch(this.value)">
          </div>
          <div class="control-group" style="width:100%;">
            <label class="control-label" for="ward-select" style="min-width:44px;">Ward:</label>
            <select id="ward-select" style="flex:1;" onchange="handleWardDropdown(this.value)">
              <option value="all">All Wards (Citywide)</option>
              <option value="1">Ward 1 • Brianne Nadeau</option>
              <option value="2">Ward 2 • Brooke Pinto</option>
              <option value="3">Ward 3 • Matthew Frumin</option>
              <option value="4">Ward 4 • Janeese Lewis George</option>
              <option value="5">Ward 5 • Zachary Parker</option>
              <option value="6">Ward 6 • Charles Allen</option>
              <option value="7">Ward 7 • Wendell Felder</option>
              <option value="8">Ward 8 • Trayon White, Sr.</option>
            </select>
          </div>
          <div class="control-group" style="width:100%;">
            <label class="control-label" for="anc-select" style="min-width:44px;">ANC:</label>
            <select id="anc-select" style="flex:1;" onchange="handleAncDropdown(this.value)" disabled>
              <option value="all">— Select Ward First —</option>
            </select>
          </div>
          <div class="control-group" style="width:100%;">
            <label class="control-label" for="smd-select" style="min-width:44px;">SMD:</label>
            <select id="smd-select" style="flex:1;" onchange="handleSmdDropdown(this.value)" disabled>
              <option value="all">— Select ANC First —</option>
            </select>
          </div>
        </div>
      </div>

      <div class="controls-bar">
        <div class="control-group">
          <label class="control-label" for="filter-period">Period:</label>
          <select id="filter-period" onchange="renderTrendsTable()">
            <option value="YTD" selected>Year-to-Date (YTD)</option>
            <option value="30D">Last 30 Days</option>
          </select>
        </div>
        <div class="control-group">
          <label class="control-label" for="filter-cat">Category:</label>
          <select id="filter-cat" onchange="filterTrendsTable()">
            <option value="ALL">All Categories</option>
            {''.join(f'<option value="{escape(c)}">{escape(c)}</option>' for c in categories_unique)}
          </select>
        </div>
        <div class="control-group" style="flex:1;min-width:180px;">
          <input type="search" id="filter-search" placeholder="Search code or description..." style="width:100%;" oninput="filterTrendsTable()">
        </div>
        <div>
          <button class="btn-action" onclick="resetGeoFilter()">Reset Geography</button>
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table" id="emerging-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Service Request</th>
              <th>Category</th>
              <th class="num" id="th-c26">2026 #</th>
              <th class="num" id="th-c25">2025 #</th>
              <th class="num" id="th-cpct"># % Change</th>
              <th class="num" id="th-t26">2026 Time</th>
              <th class="num" id="th-t25">2025 Time</th>
              <th class="num" id="th-tpct">Time % Change</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(table_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Ward-Level Emerging Surges -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Ward 1 – 8 Localized Emerging Request Surges</h2>
          <p class="section-subtitle">Fastest-growing specific service requests within each Ward (2026 YTD vs. same-period 2025)</p>
        </div>
      </div>
      <div class="grid-cards">
{chr(10).join(ward_em_cards)}
      </div>
    </section>

{render_footer()}
  </main>

{COMMON_THEME_AND_SORT_JS}
  <script>
    const GEO_TRENDS = {json.dumps(geo_trends)};
    const TRAJECTORIES = {json.dumps(emerging['weekly_trajectories'])};
    const WEEKLY_LABELS = {json.dumps(emerging['weekly_weather']['weeks'])};

    let trajChart = null;
    let currentGeoKey = 'CITY';
    let currentGeoLabel = 'Citywide (All Wards)';
    let _allSmdMap = null;

    function escapeHtml(str) {{
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }}

    function getChartColors() {{
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      return {{
        text: dark ? '#f4f4f5' : '#09090b',
        muted: dark ? '#a1a1aa' : '#52525b',
        grid: dark ? '#27272a' : '#e4e4e7',
        bgCard: dark ? '#121215' : '#ffffff',
        red: dark ? '#ef4444' : '#dc2626',
        blue: dark ? '#38bdf8' : '#2563eb'
      }};
    }}

    function initTrajectorySelect() {{
      const sel = document.getElementById('traj-code-select');
      sel.innerHTML = '';
      const codes = Object.keys(GEO_TRENDS.code_info || {{}}).sort((a, b) => {{
        const da = (GEO_TRENDS.code_info[a] && GEO_TRENDS.code_info[a].desc) || a;
        const db = (GEO_TRENDS.code_info[b] && GEO_TRENDS.code_info[b].desc) || b;
        return da.localeCompare(db);
      }});
      codes.forEach(code => {{
        const info = GEO_TRENDS.code_info[code];
        const opt = document.createElement('option');
        opt.value = code;
        opt.textContent = `${{info.desc}} [${{code}}]`;
        sel.appendChild(opt);
      }});
      const def = codes.find(c => c === 'DOCVEH2022') || codes[0];
      if (def) sel.value = def;
      renderTrajectoryChart();
    }}

    function selectTrajectoryCode(code) {{
      const sel = document.getElementById('traj-code-select');
      sel.value = code;
      renderTrajectoryChart();
    }}

    function toggleTrajDataset(idx) {{
      if (!trajChart) return;
      const isVisible = trajChart.isDatasetVisible(idx);
      trajChart.setDatasetVisibility(idx, !isVisible);
      trajChart.update();
      renderTrajLegend(getChartColors());
    }}

    function renderTrajLegend(colors) {{
      if (!trajChart) return;
      const legendEl = document.getElementById('traj-legend');
      if (!legendEl) return;

      const items = [
        {{ idx: 0, label: '2025 Time to Completion', type: 'line', color: colors.red }},
        {{ idx: 1, label: '2026 Time to Completion', type: 'line', color: colors.blue }},
        {{ idx: 2, label: '2025 Weekly Requests', type: 'bar', color: colors.red }},
        {{ idx: 3, label: '2026 Weekly Requests', type: 'bar', color: colors.blue }}
      ];

      legendEl.innerHTML = items.map(it => {{
        const vis = trajChart.isDatasetVisible(it.idx);
        const iconSvg = it.type === 'line'
          ? `<svg width="28" height="12" style="margin-right:8px;flex-shrink:0;"><line x1="0" y1="6" x2="28" y2="6" stroke="${{it.color}}" stroke-width="2.2" stroke-dasharray="3,3"/><circle cx="14" cy="6" r="3.5" fill="${{it.color}}"/></svg>`
          : `<svg width="28" height="12" style="margin-right:8px;flex-shrink:0;"><rect x="0" y="2" width="28" height="8" rx="2" fill="${{it.color}}" stroke="${{it.color}}" stroke-width="1"/></svg>`;
        return `
          <div onclick="toggleTrajDataset(${{it.idx}})" style="display:flex;align-items:center;cursor:pointer;opacity:${{vis ? 1 : 0.35}};text-decoration:${{vis ? 'none' : 'line-through'}};user-select:none;">
            ${{iconSvg}}
            <span style="color:var(--text-main);font-weight:600;">${{it.label}}</span>
          </div>
        `;
      }}).join('');
    }}

    function renderTrajectoryChart() {{
      const code = document.getElementById('traj-code-select').value;
      const info = (GEO_TRENDS.code_info && GEO_TRENDS.code_info[code]) || {{ desc: code, cat: 'General', agency: 'DC' }};
      const series = TRAJECTORIES[code] || {{ w2025: [], w2026: [], res_days_2025: [], res_days_2026: [] }};

      const colors = getChartColors();
      const ctx = document.getElementById('trajectoryChart').getContext('2d');
      if (trajChart) trajChart.destroy();

      document.getElementById('traj-chart-title').textContent = `${{info.desc}} [${{code}}]`;

      const datasets = [
        {{
          type: 'line',
          label: '2025 Time to Completion',
          data: series.res_days_2025 || [],
          yAxisID: 'y1',
          borderColor: colors.red,
          backgroundColor: colors.red,
          borderWidth: 2.2,
          borderDash: [3, 3],
          pointStyle: 'circle',
          pointRadius: 3.5,
          pointHoverRadius: 5.5,
          tension: 0.2,
          order: 1,
          spanGaps: false
        }},
        {{
          type: 'line',
          label: '2026 Time to Completion',
          data: series.res_days_2026 || [],
          yAxisID: 'y1',
          borderColor: colors.blue,
          backgroundColor: colors.blue,
          borderWidth: 2.5,
          borderDash: [3, 3],
          pointStyle: 'circle',
          pointRadius: 3.5,
          pointHoverRadius: 5.5,
          tension: 0.2,
          order: 1,
          spanGaps: false
        }},
        {{
          type: 'bar',
          label: '2025 Weekly Requests',
          data: series.w2025 || [],
          yAxisID: 'y',
          backgroundColor: colors.red,
          borderColor: colors.red,
          borderWidth: 1,
          borderRadius: 2,
          order: 2
        }},
        {{
          type: 'bar',
          label: '2026 Weekly Requests',
          data: series.w2026 || [],
          yAxisID: 'y',
          backgroundColor: colors.blue,
          borderColor: colors.blue,
          borderWidth: 1,
          borderRadius: 2,
          order: 2
        }}
      ];

      trajChart = new Chart(ctx, {{
        data: {{
          labels: WEEKLY_LABELS,
          datasets: datasets
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }},
            title: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: function(context) {{
                  const val = context.parsed.y;
                  if (val === null || val === undefined) return ` ${{context.dataset.label}}: N/A`;
                  if (context.dataset.yAxisID === 'y1') {{
                    return ` ${{context.dataset.label}}: ${{val}} ${{val === 1 ? 'day' : 'days'}}`;
                  }}
                  return ` ${{context.dataset.label}}: ${{val.toLocaleString()}} requests`;
                }}
              }}
            }}
          }},
          scales: {{
            x: {{
              ticks: {{
                color: colors.muted,
                font: {{ family: 'IBM Plex Mono', size: 9 }},
                minRotation: 90,
                maxRotation: 90,
                autoSkip: false
              }},
              grid: {{ color: colors.grid }},
              title: {{
                display: true,
                text: 'Request Week',
                color: colors.muted,
                font: {{ family: 'IBM Plex Mono', size: 10 }}
              }}
            }},
            y: {{
              type: 'linear',
              position: 'left',
              beginAtZero: true,
              title: {{
                display: true,
                text: '311 Requests',
                color: colors.text,
                font: {{ family: 'IBM Plex Mono', size: 11 }}
              }},
              ticks: {{
                precision: 0,
                color: colors.muted,
                font: {{ family: 'IBM Plex Mono', size: 11 }},
                callback: function(val) {{ return Number.isInteger(val) ? val.toLocaleString() : ''; }}
              }},
              grid: {{ color: colors.grid }}
            }},
            y1: {{
              type: 'linear',
              position: 'right',
              beginAtZero: true,
              title: {{
                display: true,
                text: 'Completion Time',
                color: colors.text,
                font: {{ family: 'IBM Plex Mono', size: 11 }}
              }},
              ticks: {{
                precision: 0,
                color: colors.muted,
                font: {{ family: 'IBM Plex Mono', size: 11 }},
                callback: function(val) {{ return Number.isInteger(val) ? val + 'd' : ''; }}
              }},
              grid: {{ drawOnChartArea: false }}
            }}
          }}
        }}
      }});

      renderTrajLegend(colors);

      const strip = document.getElementById('traj-summary-strip');
      strip.innerHTML = `
        <div><strong>Category:</strong> ${{info.cat}} • <strong>Agency:</strong> ${{info.agency}}</div>
      `;
    }}

    function getAllSmds() {{
      if (!_allSmdMap) {{
        _allSmdMap = {{}};
        if (GEO_TRENDS.hierarchy && GEO_TRENDS.hierarchy.ancs) {{
          Object.entries(GEO_TRENDS.hierarchy.ancs).forEach(([anc, info]) => {{
            (info.smds || []).forEach(s => {{ _allSmdMap[s] = anc; }});
          }});
        }}
      }}
      return _allSmdMap;
    }}

    function handleWardDropdown(val) {{
      const ancSel = document.getElementById('anc-select');
      const smdSel = document.getElementById('smd-select');
      const badge = document.getElementById('geo-selection-badge');

      if (val === 'all') {{
        currentGeoKey = 'CITY';
        currentGeoLabel = 'Citywide (All Wards)';
        ancSel.innerHTML = '<option value="all">— Select Ward First —</option>';
        ancSel.disabled = true;
        smdSel.innerHTML = '<option value="all">— Select ANC First —</option>';
        smdSel.disabled = true;
      }} else {{
        currentGeoKey = 'W:' + val;
        const wInfo = GEO_TRENDS.hierarchy && GEO_TRENDS.hierarchy.wards && GEO_TRENDS.hierarchy.wards[val];
        currentGeoLabel = wInfo ? wInfo.name : `Ward ${{val}}`;

        ancSel.disabled = false;
        ancSel.innerHTML = `<option value="all">All ANCs in Ward ${{val}}</option>`;
        if (wInfo && wInfo.ancs) {{
          wInfo.ancs.forEach(a => {{
            const opt = document.createElement('option');
            opt.value = a;
            opt.textContent = `ANC ${{a}}`;
            ancSel.appendChild(opt);
          }});
        }}
        smdSel.innerHTML = '<option value="all">— Select ANC First —</option>';
        smdSel.disabled = true;
      }}

      if (badge) badge.textContent = currentGeoLabel;
      renderTrendsTable();
    }}

    function handleAncDropdown(val) {{
      const wardVal = document.getElementById('ward-select').value;
      const smdSel = document.getElementById('smd-select');
      const badge = document.getElementById('geo-selection-badge');

      if (val === 'all') {{
        currentGeoKey = 'W:' + wardVal;
        const wInfo = GEO_TRENDS.hierarchy && GEO_TRENDS.hierarchy.wards && GEO_TRENDS.hierarchy.wards[wardVal];
        currentGeoLabel = wInfo ? wInfo.name : `Ward ${{wardVal}}`;
        smdSel.innerHTML = '<option value="all">— Select ANC First —</option>';
        smdSel.disabled = true;
      }} else {{
        currentGeoKey = 'A:' + val;
        currentGeoLabel = `ANC ${{val}} (Ward ${{wardVal}})`;
        smdSel.disabled = false;
        smdSel.innerHTML = `<option value="all">All SMDs in ANC ${{val}}</option>`;
        const aInfo = GEO_TRENDS.hierarchy && GEO_TRENDS.hierarchy.ancs && GEO_TRENDS.hierarchy.ancs[val];
        if (aInfo && aInfo.smds) {{
          aInfo.smds.forEach(s => {{
            const opt = document.createElement('option');
            opt.value = s;
            opt.textContent = `SMD ${{s}}`;
            smdSel.appendChild(opt);
          }});
        }}
      }}

      if (badge) badge.textContent = currentGeoLabel;
      renderTrendsTable();
    }}

    function handleSmdDropdown(val) {{
      const ancVal = document.getElementById('anc-select').value;
      const badge = document.getElementById('geo-selection-badge');

      if (val === 'all') {{
        currentGeoKey = 'A:' + ancVal;
        const aInfo = GEO_TRENDS.hierarchy && GEO_TRENDS.hierarchy.ancs && GEO_TRENDS.hierarchy.ancs[ancVal];
        currentGeoLabel = `ANC ${{ancVal}} (Ward ${{aInfo ? aInfo.ward : ''}})`;
      }} else {{
        currentGeoKey = 'S:' + val;
        currentGeoLabel = `SMD ${{val}}`;
      }}

      if (badge) badge.textContent = currentGeoLabel;
      renderTrendsTable();
    }}

    function handleGeoSearch(query) {{
      const q = (query || '').trim().toUpperCase();
      if (!q) return;

      const smdMap = getAllSmds();
      const smdClean = q.replace(/^SMD[ \t]*/i, '');
      if (smdClean in smdMap) {{
        const anc = smdMap[smdClean];
        const aInfo = GEO_TRENDS.hierarchy.ancs[anc];
        const ward = aInfo ? aInfo.ward : anc[0];
        document.getElementById('ward-select').value = ward;
        handleWardDropdown(ward);
        document.getElementById('anc-select').value = anc;
        handleAncDropdown(anc);
        document.getElementById('smd-select').value = smdClean;
        handleSmdDropdown(smdClean);
        return;
      }}

      const ancClean = q.replace(/^ANC[ \t]*/i, '');
      if (GEO_TRENDS.hierarchy && GEO_TRENDS.hierarchy.ancs && GEO_TRENDS.hierarchy.ancs[ancClean]) {{
        const ward = GEO_TRENDS.hierarchy.ancs[ancClean].ward;
        document.getElementById('ward-select').value = ward;
        handleWardDropdown(ward);
        document.getElementById('anc-select').value = ancClean;
        handleAncDropdown(ancClean);
        return;
      }}

      const wardClean = q.replace(/^WARD[ \t]*/i, '');
      if (['1','2','3','4','5','6','7','8'].includes(wardClean)) {{
        document.getElementById('ward-select').value = wardClean;
        handleWardDropdown(wardClean);
      }}
    }}

    function resetGeoFilter() {{
      document.getElementById('smd-search').value = '';
      document.getElementById('ward-select').value = 'all';
      handleWardDropdown('all');
      document.getElementById('filter-search').value = '';
      document.getElementById('filter-cat').value = 'ALL';
      filterTrendsTable();
    }}

    function renderTrendsTable() {{
      const isYTD = (document.getElementById('filter-period').value === 'YTD');
      const rawRows = (GEO_TRENDS.geo_data && GEO_TRENDS.geo_data[currentGeoKey]) || [];
      const tbody = document.querySelector('#emerging-table tbody');

      tbody.innerHTML = rawRows.map(row => {{
        const [scode, c26_ytd, c25_ytd, cpct_ytd, t26_ytd, t25_ytd, tpct_ytd, c26_30d, c25_30d, cpct_30d, t26_30d, t25_30d, tpct_30d] = row;
        const info = (GEO_TRENDS.code_info && GEO_TRENDS.code_info[scode]) || {{ desc: scode, cat: 'Other', agency: '' }};

        const c26 = isYTD ? c26_ytd : c26_30d;
        const c25 = isYTD ? c25_ytd : c25_30d;
        const cpct = isYTD ? cpct_ytd : cpct_30d;
        const t26 = isYTD ? t26_ytd : t26_30d;
        const t25 = isYTD ? t25_ytd : t25_30d;
        const tpct = isYTD ? tpct_ytd : tpct_30d;

        const cpctStr = (cpct !== null && cpct !== undefined) ? ((cpct >= 0 ? '+' : '') + cpct.toFixed(1) + '%') : (isYTD ? 'NEW' : 'N/A');
        const cpctCls = (cpct || 0) >= 20 ? 'kw-surge' : ((cpct || 0) <= -15 ? 'kw-decline' : '');

        const t26Str = (t26 !== null && t26 !== undefined) ? `${{t26}} ${{t26 === 1 ? 'day' : 'days'}}` : 'N/A';
        const t25Str = (t25 !== null && t25 !== undefined) ? `${{t25}} ${{t25 === 1 ? 'day' : 'days'}}` : 'N/A';

        const tpctStr = (tpct !== null && tpct !== undefined) ? ((tpct >= 0 ? '+' : '') + tpct.toFixed(1) + '%') : 'N/A';
        const tpctCls = (tpct || 0) >= 20 ? 'kw-surge' : ((tpct || 0) <= -15 ? 'kw-decline' : '');

        return `<tr data-code="${{escapeHtml(scode)}}" data-cat="${{escapeHtml(info.cat)}}">
          <td><code>${{escapeHtml(scode)}}</code></td>
          <td><a href="#chart-anchor" onclick="selectTrajectoryCode('${{escapeHtml(scode)}}')" style="color:var(--text-main);font-weight:700;">${{escapeHtml(info.desc)}}</a></td>
          <td>${{escapeHtml(info.cat)}}</td>
          <td class="num" data-val="${{c26 ?? 0}}">${{(c26 ?? 0).toLocaleString()}}</td>
          <td class="num" data-val="${{c25 ?? 0}}">${{(c25 ?? 0).toLocaleString()}}</td>
          <td class="num ${{cpctCls}}" data-val="${{cpct ?? (isYTD ? 9999 : -9999)}}">${{cpctStr}}</td>
          <td class="num" data-val="${{t26 ?? -1}}">${{t26Str}}</td>
          <td class="num" data-val="${{t25 ?? -1}}">${{t25Str}}</td>
          <td class="num ${{tpctCls}}" data-val="${{tpct ?? 9999}}">${{tpctStr}}</td>
        </tr>`;
      }}).join('');

      filterTrendsTable();
    }}

    function filterTrendsTable() {{
      const cat = document.getElementById('filter-cat').value;
      const q = document.getElementById('filter-search').value.trim().toLowerCase();

      const rows = document.querySelectorAll('#emerging-table tbody tr');
      rows.forEach(r => {{
        const rCat = r.getAttribute('data-cat');
        const txt = r.innerText.toLowerCase();

        const matchCat = (cat === 'ALL' || rCat === cat);
        const matchQ = (!q || txt.includes(q));

        r.style.display = (matchCat && matchQ) ? '' : 'none';
      }});
    }}

    window.onThemeChange = function() {{
      renderTrajectoryChart();
    }};

    document.addEventListener('DOMContentLoaded', () => {{
      initTrajectorySelect();
    }});
  </script>
</body>
</html>
"""

    out_path = os.path.join(BASE_DIR, "emerging.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Compiled {out_path}")


if __name__ == "__main__":
    build_emerging()
