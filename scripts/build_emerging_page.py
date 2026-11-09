#!/usr/bin/env python3
"""
Compiles the Emerging Issues & Weather Sensitivity Monitor (emerging.html).
Evaluates specific 311 service queries using:
- YTD Same-Period YoY Ratio & Z-Score (Jan 1 - Nov 9, 2026 vs 2025)
- Recent 30-Day YoY Ratio & Acceleration Ratio
- Daily Rainfall, Snowfall, and Temperature Elasticity & Weather-Adjusted Residuals

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

from ui_common import COMMON_CSS, COMMON_HEAD_FONTS, COMMON_THEME_AND_SORT_JS, render_nav

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def status_badge(status):
    label = status.replace("_", " ")
    if status in ("EMERGING_ACCELERATING", "EMERGING_SURGE", "RECENT_30D_SURGE", "NEW_OR_EXPANDED"):
        return f'<span class="badge badge-surge">{escape(label)}</span>'
    if status == "WEATHER_DRIVEN_INCREASE":
        return f'<span class="badge badge-weather">{escape(label)}</span>'
    if status == "DECLINING":
        return f'<span class="badge badge-decline">{escape(label)}</span>'
    return f'<span class="badge badge-neutral">{escape(label)}</span>'


def build_emerging():
    with open(os.path.join(BASE_DIR, "data", "emerging_issues.json"), "r", encoding="utf-8") as f:
        emerging = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "operational_patterns.json"), "r", encoding="utf-8") as f:
        patterns = json.load(f)

    items = emerging["items"]
    wx_comp = patterns["weather_ytd_comparison"]
    wx26 = wx_comp.get("2026", {})
    wx25 = wx_comp.get("2025", {})

    surge_cnt = sum(1 for x in items if x["status"] in ("EMERGING_ACCELERATING", "EMERGING_SURGE", "RECENT_30D_SURGE"))
    accel_cnt = sum(1 for x in items if x["status"] == "EMERGING_ACCELERATING")
    decline_cnt = sum(1 for x in items if x["status"] == "DECLINING")

    # Build main emerging/declining table rows
    table_rows_html = []
    for x in items:
        yoy_val = x["ytd_yoy_pct"]
        yoy_str = f"{yoy_val:+.1f}%" if yoy_val is not None else "NEW"
        yoy_cls = "kw-surge" if (yoy_val or 0) >= 20 else ("kw-decline" if (yoy_val or 0) <= -15 else "")

        d30_val = x["d30_yoy_pct"]
        d30_str = f"{d30_val:+.1f}%" if d30_val is not None else "N/A"
        d30_cls = "kw-surge" if (d30_val or 0) >= 25 else ("kw-decline" if (d30_val or 0) <= -20 else "")

        wx_adj = x["weather_adj_yoy_pct"]
        wx_str = f"{wx_adj:+.1f}%" if wx_adj is not None else "N/A"

        table_rows_html.append(
            f"""            <tr data-status="{escape(x['status'])}" data-cat="{escape(x['category'])}" data-wx="{escape(x['weather_tag'])}">
              <td><code>{escape(x['service_code'])}</code></td>
              <td><a href="#chart-anchor" onclick="selectTrajectoryCode('{escape(x['service_code'])}')" style="color:var(--text-main);font-weight:700;">{escape(x['service_desc'])}</a></td>
              <td>{escape(x['category'])}</td>
              <td>{status_badge(x['status'])}</td>
              <td class="num" data-val="{x['ytd_2026']}">{x['ytd_2026']:,}</td>
              <td class="num" data-val="{x['ytd_2025']}">{x['ytd_2025']:,}</td>
              <td class="num {yoy_cls}" data-val="{yoy_val if yoy_val is not None else 9999}">{yoy_str}</td>
              <td class="num" data-val="{x['ytd_z']}">{x['ytd_z']:+.1f}</td>
              <td class="num" data-val="{x['d30_2026']}">{x['d30_2026']:,}</td>
              <td class="num {d30_cls}" data-val="{d30_val if d30_val is not None else -9999}">{d30_str}</td>
              <td class="num" data-val="{x['acceleration_ratio']}">{x['acceleration_ratio']:.2f}x</td>
              <td class="num" data-val="{wx_adj if wx_adj is not None else -9999}">{wx_str}</td>
              <td><span class="tag-pill">{escape(x['weather_tag'])}</span></td>
            </tr>"""
        )

    # Weather elasticity matrix rows
    wx_rows_html = []
    for w in patterns["weather_sensitive_queries"][:35]:
        r_rain = w["r_rain_3d"]
        r_temp = w["r_temp"]
        r_snow = w["r_snow_3d"]
        wx_res = w["weather_adj_yoy_pct"]
        wx_res_str = f"{wx_res:+.1f}%" if wx_res is not None else "N/A"
        wx_rows_html.append(
            f"""            <tr>
              <td><code>{escape(w['service_code'])}</code></td>
              <td><strong>{escape(w['service_desc'])}</strong></td>
              <td><span class="tag-pill">{escape(w['weather_tag'])}</span></td>
              <td class="num" data-val="{w['ytd_2026']}">{w['ytd_2026']:,}</td>
              <td class="num {'kw-combined' if r_rain >= 0.10 else ''}" data-val="{r_rain}">{r_rain:+.2f}</td>
              <td class="num" data-val="{w['heavy_rain_mult']}">{w['heavy_rain_mult']:.2f}x</td>
              <td class="num {'kw-surge' if r_temp >= 0.25 else ('kw-combined' if r_temp <= -0.20 else '')}" data-val="{r_temp}">{r_temp:+.2f}</td>
              <td class="num" data-val="{w['heat_mult']}">{w['heat_mult']:.2f}x</td>
              <td class="num" data-val="{r_snow}">{r_snow:+.2f}</td>
              <td class="num" data-val="{w['freeze_mult']}">{w['freeze_mult']:.2f}x</td>
              <td class="num" data-val="{w['weather_expected_2026']}">{w['weather_expected_2026']:,.0f}</td>
              <td class="num" data-val="{wx_res if wx_res is not None else -9999}">{wx_res_str}</td>
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
    wx_tags_unique = sorted({x["weather_tag"] for x in items})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DC 311 Sentinel • Emerging Issues & Weather Sensitivity</title>
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
{render_nav("emerging.html", "Emerging Issues, 30-Day Acceleration & Daily Weather Elasticity")}

  <main class="page-container">
    <!-- KPI Row -->
    <section class="kpi-row">
      <div class="kpi-box">
        <div class="kpi-num kw-surge">{surge_cnt}</div>
        <div class="kpi-label">Emerging Service Codes</div>
        <div class="kpi-sub">{accel_cnt} accelerating in last 30 days</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num kw-decline">{decline_cnt}</div>
        <div class="kpi-label">Declining Service Codes</div>
        <div class="kpi-sub">Statistically significant YoY drop (z &le; -3)</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{wx26.get('total_rain_in', 0):.2f} in</div>
        <div class="kpi-label">2026 YTD Rainfall (DC)</div>
        <div class="kpi-sub">vs. {wx25.get('total_rain_in', 0):.2f} in (2025 YTD) • {wx26.get('heavy_rain_days', 0)} heavy rain days</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{wx26.get('total_snow_in', 0):.1f} in</div>
        <div class="kpi-label">2026 YTD Snowfall</div>
        <div class="kpi-sub">vs. {wx25.get('total_snow_in', 0):.1f} in (2025 YTD) • {wx26.get('freeze_days', 0)} freeze days (&le;32F)</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num kw-warn">{wx26.get('heat_days', 0)} days</div>
        <div class="kpi-label">2026 Heat Days (&ge;85F)</div>
        <div class="kpi-sub">vs. {wx25.get('heat_days', 0)} days in 2025 YTD (+53.8% more heat days)</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{wx26.get('avg_temp_f', 0):.1f}F</div>
        <div class="kpi-label">2026 YTD Mean Temp</div>
        <div class="kpi-sub">vs. {wx25.get('avg_temp_f', 0):.1f}F in 2025 YTD (Max: {wx26.get('max_temp_f', 0):.1f}F)</div>
      </div>
    </section>

    <!-- Weekly Comparative Trajectory + Weather Overlay -->
    <section class="section-block" id="chart-anchor">
      <div class="section-header">
        <div>
          <h2 class="section-title">Weekly 2026 vs. 2025 Request Trajectory & Weather Overlay</h2>
          <p class="section-subtitle">Compare weekly request volumes against DC weekly rainfall (in), mean temperature (F), or snowfall (in)</p>
        </div>
      </div>
      <div class="controls-bar">
        <div class="control-group" style="flex:1;min-width:280px;">
          <label class="control-label" for="traj-code-select">Service Query:</label>
          <select id="traj-code-select" style="flex:1;max-width:520px;" onchange="renderTrajectoryChart()"></select>
        </div>
        <div class="control-group">
          <label class="control-label" for="wx-overlay-select">Weather Overlay (Right Axis):</label>
          <select id="wx-overlay-select" onchange="renderTrajectoryChart()">
            <option value="rain_2026">2026 Weekly Rainfall (inches)</option>
            <option value="temp_2026">2026 Weekly Mean Temperature (F)</option>
            <option value="snow_2026">2026 Weekly Snowfall (inches)</option>
            <option value="none">None (Requests Only)</option>
          </select>
        </div>
      </div>
      <div class="card">
        <div style="height:360px;">
          <canvas id="trajectoryWeatherChart"></canvas>
        </div>
        <div id="traj-summary-strip" style="margin-top:12px;padding-top:10px;border-top:1px solid var(--border);font-size:12px;display:flex;flex-wrap:wrap;gap:18px;"></div>
      </div>
    </section>

    <!-- Main Emerging & Declining Table -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Emerging, Accelerating & Declining Specific Queries ({len(items)} Evaluated)</h2>
          <p class="section-subtitle">Click any column header to sort; click a service description to plot its weekly trajectory and weather overlay above</p>
        </div>
        <div>
          <button class="btn-action" onclick="exportTableToCSV('emerging-table', 'dc_311_emerging_issues_2026.csv')">Export CSV</button>
          <button class="btn-action" onclick="exportTableToPDF('emerging-table', 'DC 311 Emerging Issues (2026 YTD)', 'dc_311_emerging_issues_2026.pdf')">Export PDF</button>
        </div>
      </div>
      <div class="controls-bar">
        <div class="control-group">
          <label class="control-label" for="filter-status">Status:</label>
          <select id="filter-status" onchange="filterEmergingTable()">
            <option value="ALL">All Statuses ({len(items)})</option>
            <option value="SURGING_ONLY">All Emerging / Surging ({surge_cnt})</option>
            <option value="EMERGING_ACCELERATING">Emerging & Accelerating ({accel_cnt})</option>
            <option value="EMERGING_SURGE">Emerging Surge</option>
            <option value="RECENT_30D_SURGE">Recent 30-Day Surge</option>
            <option value="DECLINING">Declining ({decline_cnt})</option>
            <option value="STABLE">Stable</option>
          </select>
        </div>
        <div class="control-group">
          <label class="control-label" for="filter-cat">Category:</label>
          <select id="filter-cat" onchange="filterEmergingTable()">
            <option value="ALL">All Categories</option>
            {''.join(f'<option value="{escape(c)}">{escape(c)}</option>' for c in categories_unique)}
          </select>
        </div>
        <div class="control-group">
          <label class="control-label" for="filter-wx">Weather Sensitivity:</label>
          <select id="filter-wx" onchange="filterEmergingTable()">
            <option value="ALL">All Weather Regimes</option>
            {''.join(f'<option value="{escape(w)}">{escape(w)}</option>' for w in wx_tags_unique)}
          </select>
        </div>
        <div class="control-group" style="flex:1;min-width:180px;">
          <input type="search" id="filter-search" placeholder="Search code or description..." style="width:100%;" oninput="filterEmergingTable()">
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table" id="emerging-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Specific Service Query</th>
              <th>Category</th>
              <th>Classification</th>
              <th class="num">2026 YTD</th>
              <th class="num">2025 YTD</th>
              <th class="num">YTD YoY %</th>
              <th class="num">Z-Score</th>
              <th class="num">2026 30d</th>
              <th class="num">30d YoY %</th>
              <th class="num">30d Accel</th>
              <th class="num">Weather-Adj YoY</th>
              <th>Weather Sensitivity</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(table_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Daily Rain, Snow & Temperature Sensitivity Matrix -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Daily Rainfall, Snowfall & Temperature Sensitivity Matrix</h2>
          <p class="section-subtitle">Correlations and daily request multipliers across heavy-rain days (&ge;0.5 in 3d rain), heat days (&ge;85F), and freeze days (&le;32F)</p>
        </div>
        <div>
          <button class="btn-action" onclick="exportTableToCSV('weather-matrix-table', 'dc_311_weather_sensitivity.csv')">Export CSV</button>
        </div>
      </div>
      <div class="table-wrap">
        <table class="data-table" id="weather-matrix-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Service Request Description</th>
              <th>Primary Regime</th>
              <th class="num">2026 YTD</th>
              <th class="num">r (3d Rain)</th>
              <th class="num">Heavy Rain Mult</th>
              <th class="num">r (Daily Temp)</th>
              <th class="num">Heat Day (&ge;85F) Mult</th>
              <th class="num">r (3d Snow)</th>
              <th class="num">Freeze (&le;32F) Mult</th>
              <th class="num">Weather-Expected 2026</th>
              <th class="num">Weather-Adj Residual %</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(wx_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Ward-Level Emerging Surges -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Ward 1 – 8 Localized Emerging Request Surges</h2>
          <p class="section-subtitle">Fastest-growing specific service queries within each Ward (2026 YTD vs. same-period 2025)</p>
        </div>
      </div>
      <div class="grid-cards">
{chr(10).join(ward_em_cards)}
      </div>
    </section>

    <footer class="site-footer">
      <div>DC 311 Sentinel • Emerging Issues & Weather Sensitivity Monitor</div>
      <div>Compiled {datetime.now().strftime('%Y-%m-%d')} • Cutoff: {emerging['cutoff_date']}</div>
    </footer>
  </main>

{COMMON_THEME_AND_SORT_JS}
  <script>
    const EMERGING_ITEMS = {json.dumps(items)};
    const TRAJECTORIES = {json.dumps(emerging['weekly_trajectories'])};
    const WEEKLY_WEATHER = {json.dumps(emerging['weekly_weather'])};

    let trajChart = null;

    function getChartColors() {{
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      return {{
        text: dark ? '#f4f4f5' : '#09090b',
        muted: dark ? '#a1a1aa' : '#52525b',
        grid: dark ? '#27272a' : '#e4e4e7',
        c2026: dark ? '#ef4444' : '#dc2626',
        c2025: dark ? '#71717a' : '#94a3b8',
        wx: dark ? '#38bdf8' : '#2563eb'
      }};
    }}

    function initTrajectorySelect() {{
      const sel = document.getElementById('traj-code-select');
      EMERGING_ITEMS.forEach(item => {{
        const opt = document.createElement('option');
        opt.value = item.service_code;
        const yoyStr = item.ytd_yoy_pct !== null ? `${{item.ytd_yoy_pct >= 0 ? '+' : ''}}${{item.ytd_yoy_pct}}%` : 'NEW';
        opt.textContent = `${{item.service_desc}} [${{item.service_code}}] — ${{item.ytd_2026.toLocaleString()}} (${{yoyStr}} YoY • ${{item.weather_tag}})`;
        sel.appendChild(opt);
      }});
      // Default to Dockless Vehicle Parking Complaint or first high-volume surge
      const def = EMERGING_ITEMS.find(x => x.service_code === 'DOCVEH2022') || EMERGING_ITEMS[0];
      if (def) sel.value = def.service_code;
      renderTrajectoryChart();
    }}

    function selectTrajectoryCode(code) {{
      const sel = document.getElementById('traj-code-select');
      sel.value = code;
      renderTrajectoryChart();
    }}

    function renderTrajectoryChart() {{
      const code = document.getElementById('traj-code-select').value;
      const wxMode = document.getElementById('wx-overlay-select').value;
      const item = EMERGING_ITEMS.find(x => x.service_code === code) || EMERGING_ITEMS[0];
      const series = TRAJECTORIES[item.service_code] || {{ w2025: [], w2026: [] }};

      const colors = getChartColors();
      const ctx = document.getElementById('trajectoryWeatherChart').getContext('2d');
      if (trajChart) trajChart.destroy();

      const datasets = [
        {{
          type: 'line',
          label: '2026 Weekly Requests',
          data: series.w2026,
          borderColor: colors.c2026,
          backgroundColor: colors.c2026,
          borderWidth: 2.5,
          tension: 0.2,
          pointRadius: 2.5,
          yAxisID: 'y'
        }},
        {{
          type: 'line',
          label: '2025 Weekly Requests (Same Weeks)',
          data: series.w2025,
          borderColor: colors.c2025,
          backgroundColor: colors.c2025,
          borderDash: [4, 4],
          borderWidth: 2,
          tension: 0.2,
          pointRadius: 2,
          yAxisID: 'y'
        }}
      ];

      let wxAxisDisplay = false;
      let wxTitle = '';
      if (wxMode !== 'none' && WEEKLY_WEATHER[wxMode]) {{
        wxAxisDisplay = true;
        wxTitle = wxMode === 'rain_2026' ? 'Weekly Rain (in)' : (wxMode === 'temp_2026' ? 'Weekly Mean Temp (F)' : 'Weekly Snow (in)');
        datasets.push({{
          type: wxMode === 'temp_2026' ? 'line' : 'bar',
          label: wxTitle,
          data: WEEKLY_WEATHER[wxMode],
          borderColor: colors.wx,
          backgroundColor: wxMode === 'temp_2026' ? colors.wx : 'rgba(37, 99, 235, 0.18)',
          borderWidth: 1.5,
          pointRadius: 1.5,
          yAxisID: 'y1'
        }});
      }}

      trajChart = new Chart(ctx, {{
        data: {{
          labels: WEEKLY_WEATHER.weeks,
          datasets: datasets
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ labels: {{ color: colors.text, font: {{ family: 'IBM Plex Mono', size: 11 }} }} }},
            title: {{
              display: true,
              text: `${{item.service_desc}} [${{item.service_code}}] — Weekly 2026 vs. 2025 Volume`,
              color: colors.text,
              font: {{ family: 'IBM Plex Mono', size: 12, weight: 'bold' }}
            }}
          }},
          scales: {{
            x: {{ ticks: {{ color: colors.muted, font: {{ family: 'IBM Plex Mono', size: 10 }} }}, grid: {{ color: colors.grid }} }},
            y: {{
              type: 'linear',
              position: 'left',
              beginAtZero: true,
              title: {{ display: true, text: 'Weekly 311 Requests', color: colors.text, font: {{ family: 'IBM Plex Mono', size: 11 }} }},
              ticks: {{ color: colors.muted, font: {{ family: 'IBM Plex Mono', size: 11 }} }},
              grid: {{ color: colors.grid }}
            }},
            y1: {{
              type: 'linear',
              position: 'right',
              display: wxAxisDisplay,
              title: {{ display: true, text: wxTitle, color: colors.wx, font: {{ family: 'IBM Plex Mono', size: 11 }} }},
              ticks: {{ color: colors.wx, font: {{ family: 'IBM Plex Mono', size: 11 }} }},
              grid: {{ drawOnChartArea: false }}
            }}
          }}
        }}
      }});

      const strip = document.getElementById('traj-summary-strip');
      strip.innerHTML = `
        <div><strong>2026 YTD:</strong> ${{item.ytd_2026.toLocaleString()}} (vs ${{item.ytd_2025.toLocaleString()}} in 2025, <span class="kw-surge">${{item.ytd_yoy_pct !== null ? (item.ytd_yoy_pct >= 0 ? '+' : '') + item.ytd_yoy_pct + '%' : 'NEW'}}</span>)</div>
        <div><strong>Last 30 Days:</strong> ${{item.d30_2026.toLocaleString()}} vs ${{item.d30_2025.toLocaleString()}} (${{item.d30_yoy_pct !== null ? (item.d30_yoy_pct >= 0 ? '+' : '') + item.d30_yoy_pct + '%' : 'N/A'}} • Accel: ${{item.acceleration_ratio}}x)</div>
        <div><strong>Weather-Expected 2026:</strong> ${{Math.round(item.weather_expected_2026).toLocaleString()}} (Weather-Adj Residual: <strong>${{item.weather_adj_yoy_pct !== null ? (item.weather_adj_yoy_pct >= 0 ? '+' : '') + item.weather_adj_yoy_pct + '%' : 'N/A'}}</strong>)</div>
        <div><strong>Correlations:</strong> r_rain=${{item.r_rain_3d}}, r_temp=${{item.r_temp}}, r_snow=${{item.r_snow_3d}} (${{item.weather_tag}})</div>
      `;
    }}

    function filterEmergingTable() {{
      const st = document.getElementById('filter-status').value;
      const cat = document.getElementById('filter-cat').value;
      const wx = document.getElementById('filter-wx').value;
      const q = document.getElementById('filter-search').value.trim().toLowerCase();

      const rows = document.querySelectorAll('#emerging-table tbody tr');
      rows.forEach(r => {{
        const rSt = r.getAttribute('data-status');
        const rCat = r.getAttribute('data-cat');
        const rWx = r.getAttribute('data-wx');
        const txt = r.innerText.toLowerCase();

        let matchSt = true;
        if (st === 'SURGING_ONLY') {{
          matchSt = ['EMERGING_ACCELERATING', 'EMERGING_SURGE', 'RECENT_30D_SURGE', 'NEW_OR_EXPANDED'].includes(rSt);
        }} else if (st !== 'ALL') {{
          matchSt = (rSt === st);
        }}
        const matchCat = (cat === 'ALL' || rCat === cat);
        const matchWx = (wx === 'ALL' || rWx === wx);
        const matchQ = (!q || txt.includes(q));

        r.style.display = (matchSt && matchCat && matchWx && matchQ) ? '' : 'none';
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
