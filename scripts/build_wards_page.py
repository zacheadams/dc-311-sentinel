#!/usr/bin/env python3
"""
Compiles the Ward & ANC Areas of Concern Explorer (wards.html).
Strictly adheres to Agents.md:
- Geographic column hierarchy: Ward -> Councilmember -> ANC
- Primary monospace font (IBM Plex Mono)
- Lo-fi black & white aesthetic with light/dark theme toggle
- Zero emojis anywhere
"""

import json
import os
from datetime import datetime
from html import escape

from ui_common import COMMON_CSS, COMMON_HEAD_FONTS, COMMON_THEME_AND_SORT_JS, render_nav, render_footer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_wards():
    with open(os.path.join(BASE_DIR, "data", "geography_stats.json"), "r", encoding="utf-8") as f:
        geo = json.load(f)
    with open(os.path.join(BASE_DIR, "data", "operational_patterns.json"), "r", encoding="utf-8") as f:
        patterns = json.load(f)

    wards = geo["wards"]
    ancs = geo["ancs"]
    repeat_by_ward = patterns["repeat_hotspots"]["by_ward"]

    # Ward table rows (Ward -> Councilmember -> metrics)
    ward_rows_html = []
    for w_num in range(1, 9):
        w = wards[str(w_num)]
        rep = repeat_by_ward.get(str(w_num), {})
        top1 = w["top_requests"][0]["service_desc"] if w["top_requests"] else "N/A"
        sig1 = w["signature_concerns"][0] if w["signature_concerns"] else None
        sig1_str = f"{sig1['service_desc']} ({sig1['lq']}x)" if sig1 else "N/A"

        ward_rows_html.append(
            f"""            <tr>
              <td><a href="#inspector-anchor" onclick="selectDistrict('WARD', '{w_num}')" style="color:var(--text-main);font-weight:800;">Ward {w_num}</a></td>
              <td>{escape(w['councilmember'])}</td>
              <td class="num" data-val="{w['count_2026_ytd']}">{w['count_2026_ytd']:,}</td>
              <td class="num" data-val="{w['count_2025_ytd']}">{w['count_2025_ytd']:,}</td>
              <td class="num {'kw-surge' if w['yoy_pct'] >= 15 else ''}" data-val="{w['yoy_pct']}">{w['yoy_pct']:+.1f}%</td>
              <td class="num" data-val="{w['d30_yoy_pct']}">{w['d30_yoy_pct']:+.1f}%</td>
              <td class="num" data-val="{w['share_city_pct']}">{w['share_city_pct']:.1f}%</td>
              <td class="num" data-val="{w['median_res_hours'] or 9999}">{w['median_res_hours'] or 0:.1f}h</td>
              <td class="num" data-val="{w['sla_pct'] or 0}">{w['sla_pct'] or 0:.1f}%</td>
              <td class="num" data-val="{w['open_count']}">{w['open_count']:,}</td>
              <td class="num" data-val="{rep.get('chronic_properties', 0)}">{rep.get('chronic_properties', 0):,}</td>
              <td>{escape(top1)}</td>
              <td>{escape(sig1_str)}</td>
            </tr>"""
        )

    # ANC table rows (Ward -> Councilmember -> ANC -> metrics)
    anc_rows_html = []
    for anc_id, a in ancs.items():
        top1 = a["top_requests"][0]["service_desc"] if a["top_requests"] else "N/A"
        sig1 = a["signature_concerns"][0] if a["signature_concerns"] else None
        sig1_str = f"{sig1['service_desc']} ({sig1['lq']}x)" if sig1 else "N/A"
        anc_rows_html.append(
            f"""            <tr data-ward="{escape(str(a['ward']))}">
              <td>Ward {escape(str(a['ward']))}</td>
              <td>{escape(a['councilmember'])}</td>
              <td><a href="#inspector-anchor" onclick="selectDistrict('ANC', '{escape(anc_id)}')" style="color:var(--text-main);font-weight:800;">ANC {escape(anc_id)}</a></td>
              <td class="num" data-val="{a['count_2026_ytd']}">{a['count_2026_ytd']:,}</td>
              <td class="num" data-val="{a['count_2025_ytd']}">{a['count_2025_ytd']:,}</td>
              <td class="num {'kw-surge' if a['yoy_pct'] >= 15 else ''}" data-val="{a['yoy_pct']}">{a['yoy_pct']:+.1f}%</td>
              <td class="num" data-val="{a['d30_yoy_pct']}">{a['d30_yoy_pct']:+.1f}%</td>
              <td class="num" data-val="{a['median_res_hours'] or 9999}">{a['median_res_hours'] or 0:.1f}h</td>
              <td class="num" data-val="{a['sla_pct'] or 0}">{a['sla_pct'] or 0:.1f}%</td>
              <td class="num" data-val="{a['open_count']}">{a['open_count']:,}</td>
              <td>{escape(top1)}</td>
              <td>{escape(sig1_str)}</td>
            </tr>"""
        )

    # Ward 1-8 Signature Profile Cards
    ward_profile_cards = []
    for w_num in range(1, 9):
        w = wards[str(w_num)]
        top_items = "".join(
            f'<div style="display:flex;justify-content:space-between;font-size:11px;padding:3px 0;border-bottom:1px dashed var(--border);">'
            f'<span>{escape(t["service_desc"][:34])}</span><strong>{t["count_2026_ytd"]:,} ({t["share_pct"]:.1f}%)</strong></div>'
            for t in w["top_requests"][:5]
        )
        sig_items = "".join(
            f'<div style="display:flex;justify-content:space-between;font-size:11px;padding:3px 0;border-bottom:1px dashed var(--border);">'
            f'<span>{escape(s["service_desc"][:34])}</span><strong class="kw-combined">{s["lq"]:.2f}x LQ ({s["count_2026_ytd"]:,})</strong></div>'
            for s in w["signature_concerns"][:5]
        )
        ward_profile_cards.append(
            f"""        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--border);padding-bottom:8px;margin-bottom:10px;">
            <div>
              <span style="font-size:16px;font-weight:800;">WARD {w_num}</span>
              <span style="font-size:11px;color:var(--text-muted);margin-left:6px;">{escape(w['councilmember'])}</span>
            </div>
            <div style="font-size:13px;font-weight:800;">{w['count_2026_ytd']:,} <span class="{'kw-surge' if w['yoy_pct'] >= 15 else ''}">({w['yoy_pct']:+.1f}%)</span></div>
          </div>
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px;">Top Volume Requests (2026 YTD):</div>
          <div style="margin-bottom:10px;">{top_items}</div>
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px;">Highest Concentration Signatures (Location Quotient):</div>
          <div>{sig_items}</div>
        </div>"""
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DC 311 Sentinel • Ward & ANC Areas of Concern</title>
{COMMON_HEAD_FONTS}
  <script src="assets/vendor/chartjs/chart.umd.min.js"></script>
  <script src="assets/vendor/jspdf/jspdf.umd.min.js"></script>
  <script src="assets/vendor/jspdf-autotable/jspdf.plugin.autotable.min.js"></script>
  <style>
{COMMON_CSS}
    .grid-3col {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 14px;
    }}
    .grid-2col {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
      gap: 14px;
    }}
  </style>
</head>
<body>
{render_nav("wards.html", "Ward 1-8 & 46-ANC Volume, Location Quotients (LQ) & SLA Profiles")}

  <main class="page-container">
    <!-- Ward Volume & YoY Bar Chart -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Ward 1 – 8 Volume & Year-over-Year Comparison (2026 YTD vs. 2025 YTD)</h2>
          <p class="section-subtitle">100.0% of 2025 and 2026 service requests mapped to Ward and 2023 ANC boundaries</p>
        </div>
      </div>
      <div class="card">
        <div style="height:310px;">
          <canvas id="wardComparisonChart"></canvas>
        </div>
      </div>
    </section>

    <!-- Interactive Ward / ANC Deep-Dive Inspector -->
    <section class="section-block" id="inspector-anchor">
      <div class="section-header">
        <div>
          <h2 class="section-title">Interactive Ward & ANC Deep-Dive Inspector</h2>
          <p class="section-subtitle">Select any Ward (1–8) or Advisory Neighborhood Commission (46 ANCs) to inspect top requests, Location Quotient concentrations, and emerging surges</p>
        </div>
      </div>
      <div class="controls-bar">
        <div class="control-group">
          <label class="control-label" for="dist-type-select">Jurisdiction Level:</label>
          <select id="dist-type-select" onchange="populateDistrictSelect()">
            <option value="WARD">Ward (8 Wards)</option>
            <option value="ANC">Advisory Neighborhood Commission (46 ANCs)</option>
          </select>
        </div>
        <div class="control-group" style="flex:1;min-width:260px;">
          <label class="control-label" for="dist-id-select">Select District:</label>
          <select id="dist-id-select" style="flex:1;max-width:440px;" onchange="renderDistrictInspector()"></select>
        </div>
      </div>

      <div id="district-kpi-strip" class="kpi-row" style="margin-bottom:16px;"></div>

      <div class="grid-3col">
        <div class="card">
          <div style="font-size:13px;font-weight:800;text-transform:uppercase;margin-bottom:8px;border-bottom:1px solid var(--border);padding-bottom:6px;">Top Requests by Volume</div>
          <div id="inspector-top-list"></div>
        </div>
        <div class="card">
          <div style="font-size:13px;font-weight:800;text-transform:uppercase;margin-bottom:8px;border-bottom:1px solid var(--border);padding-bottom:6px;">Signature Concerns (Highest LQ)</div>
          <div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">Location Quotient (LQ) = Local Share / Citywide Share. LQ &ge; 1.5x indicates disproportionate concentration.</div>
          <div id="inspector-lq-list"></div>
        </div>
        <div class="card">
          <div style="font-size:13px;font-weight:800;text-transform:uppercase;margin-bottom:8px;border-bottom:1px solid var(--border);padding-bottom:6px;">Localized Emerging Surges</div>
          <div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">Fastest-growing specific requests in this district (2026 YTD vs. same-period 2025).</div>
          <div id="inspector-emerging-list"></div>
        </div>
      </div>
    </section>

    <!-- Ward 1-8 Summary Matrix -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Ward 1 – 8 Performance & Concern Matrix</h2>
          <p class="section-subtitle">Click any Ward name to load it in the Deep-Dive Inspector above; click column headers to sort</p>
        </div>
        <div>
          <button class="btn-action" onclick="exportTableToCSV('ward-matrix-table', 'dc_311_wards_2026.csv')">Export CSV</button>
          <button class="btn-action" onclick="exportTableToPDF('ward-matrix-table', 'DC 311 Ward Performance Matrix (2026 YTD)', 'dc_311_wards_2026.pdf')">Export PDF</button>
        </div>
      </div>
      <div class="table-wrap">
        <table class="data-table" id="ward-matrix-table">
          <thead>
            <tr>
              <th>Ward</th>
              <th>Councilmember</th>
              <th class="num">2026 YTD</th>
              <th class="num">2025 YTD</th>
              <th class="num">YoY %</th>
              <th class="num">30d YoY %</th>
              <th class="num">City Share</th>
              <th class="num">Median Res</th>
              <th class="num">SLA Met %</th>
              <th class="num">Open Backlog</th>
              <th class="num">Repeat Props (5+)</th>
              <th>#1 Volume Request</th>
              <th>Top Signature (LQ)</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(ward_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Ward 1-8 Profile Cards -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Ward 1 – 8 Top Volume vs. Disproportionate Signature Profiles</h2>
          <p class="section-subtitle">Side-by-side comparison of raw ticket volume leaders vs. Location Quotient (LQ) concentration anomalies</p>
        </div>
      </div>
      <div class="grid-2col">
{chr(10).join(ward_profile_cards)}
      </div>
    </section>

    <!-- Complete 46-ANC Matrix -->
    <section class="section-block">
      <div class="section-header">
        <div>
          <h2 class="section-title">Advisory Neighborhood Commission (46 ANCs) Performance Matrix</h2>
          <p class="section-subtitle">Strict geographic column hierarchy: Ward &rarr; Councilmember &rarr; ANC</p>
        </div>
        <div>
          <button class="btn-action" onclick="exportTableToCSV('anc-matrix-table', 'dc_311_ancs_2026.csv')">Export CSV</button>
          <button class="btn-action" onclick="exportTableToPDF('anc-matrix-table', 'DC 311 ANC Performance Matrix (2026 YTD)', 'dc_311_ancs_2026.pdf')">Export PDF</button>
        </div>
      </div>
      <div class="controls-bar">
        <div class="control-group">
          <label class="control-label" for="anc-ward-filter">Filter by Ward:</label>
          <select id="anc-ward-filter" onchange="filterAncTable()">
            <option value="ALL">All 8 Wards (46 ANCs)</option>
            {''.join(f'<option value="{w}">Ward {w} ({escape(wards[str(w)]["councilmember"])})</option>' for w in range(1, 9))}
          </select>
        </div>
      </div>
      <div class="table-wrap">
        <table class="data-table" id="anc-matrix-table">
          <thead>
            <tr>
              <th>Ward</th>
              <th>Councilmember</th>
              <th>ANC</th>
              <th class="num">2026 YTD</th>
              <th class="num">2025 YTD</th>
              <th class="num">YoY %</th>
              <th class="num">30d YoY %</th>
              <th class="num">Median Res</th>
              <th class="num">SLA Met %</th>
              <th class="num">Open Backlog</th>
              <th>#1 Volume Request</th>
              <th>Top Signature (LQ)</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(anc_rows_html)}
          </tbody>
        </table>
      </div>
    </section>

{render_footer()}
  </main>

{COMMON_THEME_AND_SORT_JS}
  <script>
    const WARDS = {json.dumps(wards)};
    const ANCS = {json.dumps(ancs)};

    let wardChart = null;

    function getChartColors() {{
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      return {{
        text: dark ? '#f4f4f5' : '#09090b',
        muted: dark ? '#a1a1aa' : '#52525b',
        grid: dark ? '#27272a' : '#e4e4e7',
        c2026: dark ? '#38bdf8' : '#2563eb',
        c2025: dark ? '#71717a' : '#94a3b8'
      }};
    }}

    function renderWardComparisonChart() {{
      const colors = getChartColors();
      const ctx = document.getElementById('wardComparisonChart').getContext('2d');
      if (wardChart) wardChart.destroy();
      const wardKeys = ['1', '2', '3', '4', '5', '6', '7', '8'];
      wardChart = new Chart(ctx, {{
        type: 'bar',
        data: {{
          labels: wardKeys.map(k => `Ward ${{k}} (${{WARDS[k].councilmember.split(' ').pop()}})`),
          datasets: [
            {{
              label: '2026 YTD Requests',
              data: wardKeys.map(k => WARDS[k].count_2026_ytd),
              backgroundColor: colors.c2026
            }},
            {{
              label: '2025 Same-Period Requests',
              data: wardKeys.map(k => WARDS[k].count_2025_ytd),
              backgroundColor: colors.c2025
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ labels: {{ color: colors.text, font: {{ family: 'IBM Plex Mono', size: 11 }} }} }}
          }},
          scales: {{
            x: {{ ticks: {{ color: colors.text, font: {{ family: 'IBM Plex Mono', size: 11 }} }}, grid: {{ display: false }} }},
            y: {{ beginAtZero: true, ticks: {{ color: colors.muted, font: {{ family: 'IBM Plex Mono', size: 11 }} }}, grid: {{ color: colors.grid }} }}
          }}
        }}
      }});
    }}

    function populateDistrictSelect() {{
      const type = document.getElementById('dist-type-select').value;
      const sel = document.getElementById('dist-id-select');
      sel.innerHTML = '';
      if (type === 'WARD') {{
        for (let w = 1; w <= 8; w++) {{
          const info = WARDS[String(w)];
          const opt = document.createElement('option');
          opt.value = String(w);
          opt.textContent = `Ward ${{w}} — ${{info.councilmember}} (${{info.count_2026_ytd.toLocaleString()}} requests, ${{info.yoy_pct >= 0 ? '+' : ''}}${{info.yoy_pct}}% YoY)`;
          sel.appendChild(opt);
        }}
      }} else {{
        Object.keys(ANCS).forEach(ancId => {{
          const info = ANCS[ancId];
          const opt = document.createElement('option');
          opt.value = ancId;
          opt.textContent = `ANC ${{ancId}} (Ward ${{info.ward}} • ${{info.councilmember}}) — ${{info.count_2026_ytd.toLocaleString()}} requests (${{info.yoy_pct >= 0 ? '+' : ''}}${{info.yoy_pct}}% YoY)`;
          sel.appendChild(opt);
        }});
      }}
      renderDistrictInspector();
    }}

    function selectDistrict(type, id) {{
      document.getElementById('dist-type-select').value = type;
      populateDistrictSelect();
      document.getElementById('dist-id-select').value = id;
      renderDistrictInspector();
    }}

    function renderDistrictInspector() {{
      const type = document.getElementById('dist-type-select').value;
      const id = document.getElementById('dist-id-select').value;
      const d = type === 'WARD' ? WARDS[id] : ANCS[id];
      if (!d) return;

      const label = type === 'WARD' ? `Ward ${{id}}` : `ANC ${{id}} (Ward ${{d.ward}})`;
      document.getElementById('district-kpi-strip').innerHTML = `
        <div class="kpi-box">
          <div class="kpi-num">${{d.count_2026_ytd.toLocaleString()}}</div>
          <div class="kpi-label">${{label}} 2026 YTD</div>
          <div class="kpi-sub">Councilmember: ${{d.councilmember}}</div>
        </div>
        <div class="kpi-box">
          <div class="kpi-num ${{d.yoy_pct >= 15 ? 'kw-surge' : ''}}">${{d.yoy_pct >= 0 ? '+' : ''}}${{d.yoy_pct}}%</div>
          <div class="kpi-label">Same-Period YoY</div>
          <div class="kpi-sub">vs. ${{d.count_2025_ytd.toLocaleString()}} in 2025 YTD</div>
        </div>
        <div class="kpi-box">
          <div class="kpi-num">${{d.count_2026_30d.toLocaleString()}} (${{d.d30_yoy_pct >= 0 ? '+' : ''}}${{d.d30_yoy_pct}}%)</div>
          <div class="kpi-label">Last 30 Days Volume</div>
          <div class="kpi-sub">vs. ${{d.count_2025_30d.toLocaleString()}} in 2025</div>
        </div>
        <div class="kpi-box">
          <div class="kpi-num">${{d.median_res_hours !== null ? d.median_res_hours + 'h' : 'N/A'}}</div>
          <div class="kpi-label">Median Resolution</div>
          <div class="kpi-sub">SLA Met: ${{d.sla_pct !== null ? d.sla_pct + '%' : 'N/A'}}</div>
        </div>
        <div class="kpi-box">
          <div class="kpi-num">${{d.open_count.toLocaleString()}} (${{d.open_pct}}%)</div>
          <div class="kpi-label">Open Backlog</div>
          <div class="kpi-sub">${{d.unique_addresses.toLocaleString()}} unique MAR addresses</div>
        </div>
      `;

      document.getElementById('inspector-top-list').innerHTML = d.top_requests.map(r => `
        <div style="display:flex;justify-content:space-between;gap:8px;padding:6px 0;border-bottom:1px dashed var(--border);font-size:12px;">
          <span><strong>${{r.service_desc}}</strong> <code style="font-size:10px;color:var(--text-muted);">[${{r.service_code}}]</code></span>
          <span style="white-space:nowrap;"><strong>${{r.count_2026_ytd.toLocaleString()}}</strong> (${{r.share_pct}}%)</span>
        </div>
      `).join('');

      document.getElementById('inspector-lq-list').innerHTML = d.signature_concerns.map(r => `
        <div style="display:flex;justify-content:space-between;gap:8px;padding:6px 0;border-bottom:1px dashed var(--border);font-size:12px;">
          <span><strong>${{r.service_desc}}</strong> <code style="font-size:10px;color:var(--text-muted);">[${{r.service_code}}]</code></span>
          <span style="white-space:nowrap;"><strong class="kw-combined">${{r.lq.toFixed(2)}}x LQ</strong> (${{r.count_2026_ytd.toLocaleString()}})</span>
        </div>
      `).join('');

      document.getElementById('inspector-emerging-list').innerHTML = (d.emerging_requests && d.emerging_requests.length)
        ? d.emerging_requests.map(r => `
          <div style="display:flex;justify-content:space-between;gap:8px;padding:6px 0;border-bottom:1px dashed var(--border);font-size:12px;">
            <span><strong>${{r.service_desc}}</strong></span>
            <span style="white-space:nowrap;" class="kw-surge"><strong>+${{r.yoy_pct}}%</strong> (${{r.count_2026_ytd.toLocaleString()}} vs ${{r.count_2025_ytd.toLocaleString()}})</span>
          </div>
        `).join('')
        : '<div style="font-size:12px;color:var(--text-muted);">No high-volume surges above statistical threshold</div>';
    }}

    function filterAncTable() {{
      const w = document.getElementById('anc-ward-filter').value;
      const rows = document.querySelectorAll('#anc-matrix-table tbody tr');
      rows.forEach(r => {{
        r.style.display = (w === 'ALL' || r.getAttribute('data-ward') === w) ? '' : 'none';
      }});
    }}

    window.onThemeChange = function() {{
      renderWardComparisonChart();
    }};

    document.addEventListener('DOMContentLoaded', () => {{
      renderWardComparisonChart();
      populateDistrictSelect();
    }});
  </script>
</body>
</html>
"""

    out_path = os.path.join(BASE_DIR, "wards.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Compiled {out_path}")


if __name__ == "__main__":
    build_wards()
