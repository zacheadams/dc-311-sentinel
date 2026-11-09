#!/usr/bin/env python3
"""
Shared UI styles, navigation bar, and theme management for DC 311 Sentinel.
Strictly adheres to Agents.md:
- Primary monospace font (IBM Plex Mono)
- Lo-fi black & white aesthetic with light/dark theme toggle
- 2px border radius on buttons, cards, badges, inputs, and tables
- US Letter print sizing (@page { size: letter; })
- Strictly zero emojis anywhere
"""

COMMON_HEAD_FONTS = """  <!-- Self-hosted IBM Plex Mono (loaded via @font-face in CSS) -->"""

COMMON_CSS = """    @font-face {
      font-family: 'IBM Plex Mono';
      font-style: normal;
      font-weight: 400;
      font-display: swap;
      src: url('assets/fonts/IBMPlexMono-Regular.woff2') format('woff2');
    }
    @font-face {
      font-family: 'IBM Plex Mono';
      font-style: italic;
      font-weight: 400;
      font-display: swap;
      src: url('assets/fonts/IBMPlexMono-Italic.woff2') format('woff2');
    }
    @font-face {
      font-family: 'IBM Plex Mono';
      font-style: normal;
      font-weight: 500;
      font-display: swap;
      src: url('assets/fonts/IBMPlexMono-Medium.woff2') format('woff2');
    }
    @font-face {
      font-family: 'IBM Plex Mono';
      font-style: normal;
      font-weight: 600;
      font-display: swap;
      src: url('assets/fonts/IBMPlexMono-SemiBold.woff2') format('woff2');
    }
    @font-face {
      font-family: 'IBM Plex Mono';
      font-style: normal;
      font-weight: 700;
      font-display: swap;
      src: url('assets/fonts/IBMPlexMono-Bold.woff2') format('woff2');
    }
    @font-face {
      font-family: 'IBM Plex Mono';
      font-style: normal;
      font-weight: 800;
      font-display: swap;
      src: url('assets/fonts/IBMPlexMono-Bold.woff2') format('woff2');
    }

    :root {
      --font-mono: 'IBM Plex Mono', monospace;

      /* Light Theme (Default) */
      --bg-page: #f8fafc;
      --bg-surface: #ffffff;
      --bg-card: #ffffff;
      --bg-panel: rgba(255, 255, 255, 0.95);
      --bg-input: #f1f5f9;
      --border: #d4d4d8;
      --border-dark: #18181b;
      --border-focus: #09090b;
      --text-main: #09090b;
      --text-muted: #52525b;
      --text-dim: #71717a;
      --accent: #2563eb;
      --accent-hover: #1d4ed8;
      --surge-color: #dc2626;
      --decline-color: #16a34a;
      --combined-color: #2563eb;
      --warning-color: #d97706;
      --ward-boundary: #7c3aed;
      --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
      --badge-bg: rgba(37, 99, 235, 0.08);
      --badge-border: rgba(37, 99, 235, 0.25);
    }

    [data-theme="dark"] {
      /* Dark Theme */
      --bg-page: #09090b;
      --bg-surface: #121215;
      --bg-card: #121215;
      --bg-panel: rgba(18, 18, 21, 0.95);
      --bg-input: #181215;
      --bg-input: #18181b;
      --border: #27272a;
      --border-dark: #3f3f46;
      --border-focus: #f4f4f5;
      --text-main: #f4f4f5;
      --text-muted: #a1a1aa;
      --text-dim: #71717a;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --surge-color: #ef4444;
      --decline-color: #22c55e;
      --combined-color: #38bdf8;
      --warning-color: #f59e0b;
      --ward-boundary: #c084fc;
      --card-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
      --badge-bg: rgba(56, 189, 248, 0.12);
      --badge-border: rgba(56, 189, 248, 0.3);
    }

    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: inherit;
    }

    input, button, select, textarea, optgroup {
      font-family: var(--font-mono) !important;
    }

    body {
      background-color: var(--bg-page);
      color: var(--text-main);
      font-family: var(--font-mono);
      line-height: 1.5;
      padding-bottom: 64px;
      -webkit-font-smoothing: antialiased;
    }

    .kw-surge { color: var(--surge-color); font-weight: 700; }
    .kw-decline { color: var(--decline-color); font-weight: 700; }
    .kw-combined { color: var(--combined-color); font-weight: 700; }
    .kw-warn { color: var(--warning-color); font-weight: 700; }

    /* Top Navigation Bar */
    .site-nav {
      background: var(--bg-panel);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 1000;
      padding: 10px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .nav-brand {
      display: flex;
      flex-direction: column;
    }

    .nav-title {
      font-size: 14px;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.01em;
      text-decoration: none;
    }

    .nav-subtitle {
      font-size: 11px;
      color: var(--text-muted);
    }

    .nav-links {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .nav-link {
      color: var(--text-muted);
      text-decoration: none;
      font-size: 12px;
      font-weight: 600;
      padding: 5px 10px;
      border-radius: 2px;
      border: 1px solid transparent;
      transition: all 0.15s ease;
    }

    .nav-link:hover {
      color: var(--text-main);
      border-color: var(--border);
      background: var(--bg-input);
    }

    .nav-link.active {
      color: var(--text-main);
      background: var(--badge-bg);
      border-color: var(--badge-border);
      font-weight: 700;
    }

    .btn-action {
      background: var(--bg-surface);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 5px 10px;
      border-radius: 2px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      font-family: var(--font-mono);
      transition: all 0.15s ease;
    }

    .btn-action:hover {
      border-color: var(--text-main);
      background: var(--bg-input);
    }

    .page-container {
      max-width: 1220px;
      margin: 0 auto;
      padding: 28px 20px;
    }

    .section-block {
      margin-bottom: 40px;
    }

    .section-header {
      border-bottom: 1px solid var(--border);
      padding-bottom: 10px;
      margin-bottom: 18px;
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 10px;
    }

    .section-title {
      font-size: 16px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    .section-subtitle {
      font-size: 12px;
      color: var(--text-muted);
    }

    .kpi-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
      gap: 12px;
      margin-bottom: 32px;
    }

    .kpi-box {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 16px;
      box-shadow: var(--card-shadow);
    }

    .kpi-num {
      font-size: 24px;
      font-weight: 800;
      color: var(--text-main);
      line-height: 1.15;
      margin-bottom: 4px;
    }

    .kpi-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
      letter-spacing: 0.03em;
    }

    .kpi-sub {
      font-size: 11px;
      color: var(--text-dim);
      margin-top: 4px;
    }

    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 18px;
      box-shadow: var(--card-shadow);
    }

    .controls-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-bottom: 16px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 12px;
    }

    .control-group {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
    }

    .control-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
    }

    select, input[type="text"], input[type="search"] {
      background: var(--bg-input);
      color: var(--text-main);
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 6px 10px;
      font-size: 12px;
    }

    select:focus, input:focus {
      outline: none;
      border-color: var(--border-focus);
    }

    /* Tables */
    .table-wrap {
      overflow-x: auto;
      border: 1px solid var(--border);
      border-radius: 2px;
      background: var(--bg-card);
    }

    table.data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }

    table.data-table th,
    table.data-table td {
      padding: 8px 10px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }

    table.data-table th {
      background: var(--bg-input);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.02em;
      color: var(--text-main);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }

    table.data-table th:hover {
      background: var(--badge-bg);
    }

    table.data-table th[data-sort-dir="asc"]::after {
      content: " \\2191";
      opacity: 0.7;
      font-size: 10px;
    }

    table.data-table th[data-sort-dir="desc"]::after {
      content: " \\2193";
      opacity: 0.7;
      font-size: 10px;
    }

    table.data-table tr:hover td {
      background: rgba(37, 99, 235, 0.03);
    }

    .num {
      text-align: right !important;
      font-variant-numeric: tabular-nums;
    }

    .badge {
      display: inline-block;
      padding: 2px 6px;
      font-size: 10px;
      font-weight: 700;
      border-radius: 2px;
      border: 1px solid var(--border);
      text-transform: uppercase;
      white-space: nowrap;
    }

    .badge-surge {
      color: var(--surge-color);
      border-color: var(--surge-color);
      background: rgba(220, 38, 38, 0.08);
    }

    .badge-decline {
      color: var(--decline-color);
      border-color: var(--decline-color);
      background: rgba(22, 163, 74, 0.08);
    }

    .badge-weather {
      color: var(--warning-color);
      border-color: var(--warning-color);
      background: rgba(217, 119, 6, 0.08);
    }

    .badge-neutral {
      color: var(--text-muted);
      border-color: var(--border);
      background: var(--bg-input);
    }

    .tag-pill {
      display: inline-block;
      padding: 1px 6px;
      margin: 1px 3px 1px 0;
      font-size: 10px;
      border: 1px solid var(--border);
      border-radius: 2px;
      background: var(--bg-input);
      color: var(--text-main);
    }

    .site-footer {
      margin-top: 56px;
      padding-top: 20px;
      padding-bottom: 24px;
      border-top: 1px solid var(--border);
      font-size: 11px;
      color: var(--text-muted);
      text-align: center;
    }
    .site-footer p {
      margin: 0;
    }

    @page {
      size: letter;
      margin: 0.5in;
    }

    @media print {
      .site-nav, .controls-bar, .no-print {
        display: none !important;
      }
      body {
        background: #ffffff !important;
        color: #000000 !important;
        padding-bottom: 0;
      }
      .page-container {
        max-width: 100%;
        padding: 0;
      }
      .card, .kpi-box, .table-wrap {
        box-shadow: none !important;
        border-color: #000000 !important;
      }
    }"""


def render_footer():
    from datetime import datetime
    return f"""    <footer class="site-footer">
      <p>Last Updated {datetime.now().strftime('%B %d, %Y')}</p>
    </footer>"""


def render_nav(active_page, subtitle="Keeping track of a lot more than just bulk trash."):
    pages = [
        ("index.html", "Hub & Top Queries"),
        ("trends.html", "Trends"),
        ("wards.html", "Wards & ANCs"),
        ("map.html", "Spatial Map"),
        ("tables.html", "Other Analysis"),
    ]
    links_html = []
    for href, label in pages:
        cls = "nav-link active" if href == active_page else "nav-link"
        links_html.append(f'<a href="{href}" class="{cls}">{label}</a>')
    links_joined = "\n      ".join(links_html)

    return f"""  <nav class="site-nav">
    <div class="nav-brand">
      <a href="index.html" class="nav-title">DC 311 Sentinel Monitoring System</a>
      <span class="nav-subtitle">{subtitle}</span>
    </div>
    <div class="nav-links">
      {links_joined}
      <button id="theme-toggle-btn" class="btn-action" onclick="toggleTheme()">Theme: Light</button>
    </div>
  </nav>"""


COMMON_THEME_AND_SORT_JS = """  <script>
    // Theme Management
    let currentTheme = 'light';
    const savedTheme = localStorage.getItem('dc_311_sentinel_theme');
    if (savedTheme) {
      currentTheme = savedTheme;
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      currentTheme = 'dark';
    }
    document.documentElement.setAttribute('data-theme', currentTheme);
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) themeBtn.innerText = currentTheme === 'dark' ? 'Theme: Dark' : 'Theme: Light';

    function toggleTheme() {
      const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
      currentTheme = nextTheme;
      document.documentElement.setAttribute('data-theme', nextTheme);
      localStorage.setItem('dc_311_sentinel_theme', nextTheme);
      const btn = document.getElementById('theme-toggle-btn');
      if (btn) btn.innerText = nextTheme === 'dark' ? 'Theme: Dark' : 'Theme: Light';
      if (typeof window.onThemeChange === 'function') {
        window.onThemeChange(nextTheme);
      }
    }

    // Bidirectional Sortable Table Helper
    function sortTableByHeader(tableEl, th, dir) {
      if (!tableEl || !th) return;
      const headers = Array.from(tableEl.querySelectorAll('thead th'));
      const colIdx = headers.indexOf(th);
      if (colIdx === -1) return;
      const tbody = tableEl.querySelector('tbody');
      if (!tbody) return;
      const rows = Array.from(tbody.querySelectorAll('tr'));

      headers.forEach(h => h.removeAttribute('data-sort-dir'));
      th.setAttribute('data-sort-dir', dir);

      const isBottom = v => {
        if (v === null || v === undefined) return true;
        const s = String(v).trim().toUpperCase();
        return s === 'NEW' || s === 'N/A' || s === 'NULL' || s === 'UNDEFINED' || s === '-' || s === 'NONE';
      };

      rows.sort((a, b) => {
        const cellA = a.children[colIdx];
        const cellB = b.children[colIdx];
        if (!cellA || !cellB) return 0;
        const valA = cellA.getAttribute('data-val') !== null ? cellA.getAttribute('data-val') : cellA.innerText.trim();
        const valB = cellB.getAttribute('data-val') !== null ? cellB.getAttribute('data-val') : cellB.innerText.trim();

        const aBottom = isBottom(valA) || isBottom(cellA.innerText.trim());
        const bBottom = isBottom(valB) || isBottom(cellB.innerText.trim());

        if (aBottom && !bBottom) return 1;
        if (!aBottom && bBottom) return -1;
        if (aBottom && bBottom) {
          const aIsNew = String(valA).trim().toUpperCase() === 'NEW' || cellA.innerText.trim().toUpperCase() === 'NEW';
          const bIsNew = String(valB).trim().toUpperCase() === 'NEW' || cellB.innerText.trim().toUpperCase() === 'NEW';
          if (aIsNew && !bIsNew) return -1;
          if (!aIsNew && bIsNew) return 1;
          const txtA = a.children[1] ? a.children[1].innerText.trim() : '';
          const txtB = b.children[1] ? b.children[1].innerText.trim() : '';
          return txtA.localeCompare(txtB);
        }

        const numA = parseFloat(String(valA).replace(/[,%+$x]/g, ''));
        const numB = parseFloat(String(valB).replace(/[,%+$x]/g, ''));
        const bothNum = !isNaN(numA) && !isNaN(numB) && String(valA).match(/^-?[0-9.,%+$x]+$/) && String(valB).match(/^-?[0-9.,%+$x]+$/);
        let cmp = 0;
        if (bothNum) {
          cmp = numA - numB;
        } else {
          cmp = String(valA).localeCompare(String(valB), undefined, { numeric: true, sensitivity: 'base' });
        }
        return dir === 'asc' ? cmp : -cmp;
      });

      rows.forEach(r => tbody.appendChild(r));
    }

    function makeTableSortable(tableEl) {
      if (!tableEl) return;
      const headers = tableEl.querySelectorAll('thead th');
      headers.forEach((th) => {
        th.addEventListener('click', () => {
          const currentDir = th.getAttribute('data-sort-dir') || 'desc';
          const nextDir = currentDir === 'asc' ? 'desc' : 'asc';
          sortTableByHeader(tableEl, th, nextDir);
        });
      });
    }

    function exportTableToCSV(tableId, filename) {
      const table = document.getElementById(tableId);
      if (!table) return;
      const rows = Array.from(table.querySelectorAll('tr'));
      const csvLines = rows.filter(r => r.style.display !== 'none').map(row => {
        const cells = Array.from(row.querySelectorAll('th, td'));
        return cells.map(c => '"' + c.innerText.replace(/\\s+/g, ' ').trim().replace(/"/g, '""') + '"').join(',');
      });
      const blob = new Blob([csvLines.join('\\n')], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    }

    function exportTableToPDF(tableId, title, filename) {
      if (!window.jspdf || !window.jspdf.jsPDF) {
        window.print();
        return;
      }
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF({ orientation: 'landscape', unit: 'in', format: 'letter' });
      doc.setFont('courier', 'bold');
      doc.setFontSize(12);
      doc.text(title, 0.5, 0.55);
      doc.autoTable({
        html: '#' + tableId,
        startY: 0.75,
        margin: { left: 0.5, right: 0.5, top: 0.5, bottom: 0.5 },
        styles: { font: 'courier', fontSize: 7.5, cellPadding: 0.04 },
        headStyles: { fillColor: [24, 24, 27], textColor: [255, 255, 255] }
      });
      doc.save(filename);
    }

    document.addEventListener('DOMContentLoaded', () => {
      document.querySelectorAll('table.data-table').forEach(makeTableSortable);
    });
  </script>"""
