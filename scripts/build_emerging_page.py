#!/usr/bin/env python3
"""
Compiles the Emerging Issues & 30-Day Surge Monitor (emerging.html).
Evaluates specific 311 service queries using:
- YTD Same-Period YoY Ratio & Z-Score (Jan 1 - Nov 9, 2026 vs 2025)
- Recent 30-Day YoY Ratio & Acceleration Ratio
- Ward-level emerging query concentrations

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
    if status == "DECLINING":
        return f'<span class="badge badge-decline">{escape(label)}</span>'
    return f'<span class="badge badge-neutral">{escape(label)}</span>'


def build_emerging():
    with open(os.path.join(BASE_DIR, "data", "emerging_issues.json"), "r", encoding="utf-8") as f:
        emerging = json.load(f)

    items = emerging["items"]

    surge_cnt = sum(1 for x in items if x["status"] in ("EMERGING_ACCELERATING", "EMERGING_SURGE", "RECENT_30D_SURGE"))
    accel_cnt = sum(1 for x in items if x["status"] == "EMERGING_ACCELERATING")
    recent30_cnt = sum(1 for x in items if x["status"] == "RECENT_30D_SURGE")
    new_cnt = sum(1 for x in items if x["status"] == "NEW_OR_EXPANDED")
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

        table_rows_html.append(
            f"""            <tr data-status="{escape(x['status'])}" data-cat="{escape(x['category'])}">
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

    client_items = [
        {
            "service_code": x["service_code"],
            "service_desc": x["service_desc"],
            "category": x["category"],
            "agency": x["agency"],
            "status": x["status"],
            "ytd_2026": x["ytd_2026"],
            "ytd_2025": x["ytd_2025"],
            "ytd_yoy_pct": x["ytd_yoy_pct"],
            "ytd_z": x["ytd_z"],
            "d30_2026": x["d30_2026"],
            "d30_2025": x["d30_2025"],
            "d30_yoy_pct": x["d30_yoy_pct"],
            "acceleration_ratio": x["acceleration_ratio"],
            "median_res_hours": x.get("median_res_hours"),
        }
        for x in items
    ]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DC 311 Sentinel • Emerging Issues & 30-Day Surges</title>
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
{render_nav("emerging.html", "Emerging Issues & 30-Day Surge Acceleration")}

  <main class="page-container">
    <!-- KPI Row -->
    <section class="kpi-row">
      <div class="kpi-box">
        <div class="kpi-num">{len(items)}</div>
        <div class="kpi-label">Specific Queries Evaluated</div>
        <div class="kpi-sub">Jan 1 – Nov 9, 2026 vs. same-period 2025</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num kw-surge">{surge_cnt}</div>
        <div class="kpi-label">Emerging Service Surges</div>
        <div class="kpi-sub">Statistically significant YoY increase (z &ge; 3)</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num kw-surge">{accel_cnt}</div>
        <div class="kpi-label">30-Day Accelerating Surges</div>
        <div class="kpi-sub">Recent 30-day velocity outpaces YTD baseline</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num kw-surge">{recent30_cnt}</div>
        <div class="kpi-label">Recent 30-Day Spikes</div>
        <div class="kpi-sub">30-day YoY &ge; +30% (z &ge; 2.8)</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num">{new_cnt}</div>
        <div class="kpi-label">New or Expanded Services</div>
        <div class="kpi-sub">Launched or expanded in 2026</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-num kw-decline">{decline_cnt}</div>
        <div class="kpi-label">Declining Service Codes</div>
        <div class="kpi-sub">Statistically significant YoY drop (z &le; -3)</div>
      </div>
    </section>

    <!-- Weekly Comparative Trajectory -->
    <section class="section-block" id="chart-anchor">
      <div class="section-header">
        <div>
          <h2 class="section-title">Weekly 2026 vs. 2025 Trajectory</h2>
          <p class="section-subtitle">Weekly 311 request volume (left axis) and time to completion (right axis) for 2026 YTD vs. 2025</p>
        </div>
      </div>
      <div class="controls-bar">
        <div class="control-group" style="flex:1;min-width:280px;">
          <label class="control-label" for="traj-code-select">Service Query:</label>
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

    <!-- Main Emerging & Declining Table -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Emerging, Accelerating & Declining Specific Queries ({len(items)} Evaluated)</h2>
          <p class="section-subtitle">Click any column header to sort; click a service description to plot its weekly trajectory above</p>
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
            <option value="NEW_OR_EXPANDED">New or Expanded ({new_cnt})</option>
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
          <p class="section-subtitle">Fastest-growing specific service queries within each Ward (2026 YTD vs. same-period 2025)</p>
        </div>
      </div>
      <div class="grid-cards">
{chr(10).join(ward_em_cards)}
      </div>
    </section>

    <footer class="site-footer">
      <div>DC 311 Sentinel • Emerging Issues & 30-Day Surge Monitor</div>
      <div>Compiled {datetime.now().strftime('%Y-%m-%d')} • Cutoff: {emerging['cutoff_date']}</div>
    </footer>
  </main>

{COMMON_THEME_AND_SORT_JS}
  <script>
    const EMERGING_ITEMS = {json.dumps(client_items)};
    const TRAJECTORIES = {json.dumps(emerging['weekly_trajectories'])};
    const WEEKLY_LABELS = {json.dumps(emerging['weekly_weather']['weeks'])};

    let trajChart = null;

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
      EMERGING_ITEMS.forEach(item => {{
        const opt = document.createElement('option');
        opt.value = item.service_code;
        const yoyStr = item.ytd_yoy_pct !== null ? `${{item.ytd_yoy_pct >= 0 ? '+' : ''}}${{item.ytd_yoy_pct}}%` : 'NEW';
        opt.textContent = `${{item.service_desc}} [${{item.service_code}}] — ${{item.ytd_2026.toLocaleString()}} (${{yoyStr}} YoY)`;
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
      const item = EMERGING_ITEMS.find(x => x.service_code === code) || EMERGING_ITEMS[0];
      const series = TRAJECTORIES[item.service_code] || {{ w2025: [], w2026: [], res_days_2025: [], res_days_2026: [] }};

      const colors = getChartColors();
      const ctx = document.getElementById('trajectoryChart').getContext('2d');
      if (trajChart) trajChart.destroy();

      document.getElementById('traj-chart-title').textContent = `${{item.service_desc}} [${{item.service_code}}]`;

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
          data: series.w2025,
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
          data: series.w2026,
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
            legend: {{
              display: false
            }},
            title: {{
              display: false
            }},
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
              ticks: {{ color: colors.muted, font: {{ family: 'IBM Plex Mono', size: 10 }} }},
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
              grid: {{
                drawOnChartArea: false
              }}
            }}
          }}
        }}
      }});

      renderTrajLegend(colors);

      const strip = document.getElementById('traj-summary-strip');
      const zStr = item.ytd_z !== null ? (item.ytd_z >= 0 ? '+' : '') + item.ytd_z.toFixed(1) : 'N/A';
      const medDays = (item.median_res_hours !== null && item.median_res_hours !== undefined)
        ? Math.ceil(item.median_res_hours / 24)
        : null;
      const compStr = medDays !== null ? `${{medDays}} ${{medDays === 1 ? 'day' : 'days'}} (${{item.median_res_hours}}h)` : 'N/A';
      strip.innerHTML = `
        <div><strong>2026 YTD:</strong> ${{item.ytd_2026.toLocaleString()}} (vs ${{item.ytd_2025.toLocaleString()}} in 2025, <span class="kw-surge">${{item.ytd_yoy_pct !== null ? (item.ytd_yoy_pct >= 0 ? '+' : '') + item.ytd_yoy_pct + '%' : 'NEW'}}</span>)</div>
        <div><strong>Z-Score:</strong> ${{zStr}}</div>
        <div><strong>Last 30 Days:</strong> ${{item.d30_2026.toLocaleString()}} vs ${{item.d30_2025.toLocaleString()}} (${{item.d30_yoy_pct !== null ? (item.d30_yoy_pct >= 0 ? '+' : '') + item.d30_yoy_pct + '%' : 'N/A'}} • Accel: ${{item.acceleration_ratio}}x)</div>
        <div><strong>Median Completion:</strong> ${{compStr}}</div>
        <div><strong>Category:</strong> ${{item.category}} • <strong>Agency:</strong> ${{item.agency}}</div>
      `;
    }}

    function filterEmergingTable() {{
      const st = document.getElementById('filter-status').value;
      const cat = document.getElementById('filter-cat').value;
      const q = document.getElementById('filter-search').value.trim().toLowerCase();

      const rows = document.querySelectorAll('#emerging-table tbody tr');
      rows.forEach(r => {{
        const rSt = r.getAttribute('data-status');
        const rCat = r.getAttribute('data-cat');
        const txt = r.innerText.toLowerCase();

        let matchSt = true;
        if (st === 'SURGING_ONLY') {{
          matchSt = ['EMERGING_ACCELERATING', 'EMERGING_SURGE', 'RECENT_30D_SURGE', 'NEW_OR_EXPANDED'].includes(rSt);
        }} else if (st !== 'ALL') {{
          matchSt = (rSt === st);
        }}
        const matchCat = (cat === 'ALL' || rCat === cat);
        const matchQ = (!q || txt.includes(q));

        r.style.display = (matchSt && matchCat && matchQ) ? '' : 'none';
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
