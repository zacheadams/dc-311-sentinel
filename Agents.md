# Repository Standards & Agent Instructions

This document codifies development standards, operational conventions, and architectural guidelines for automated agents and developers contributing to `dc-311-sentinel`.

---

## 1. Strict No-Emoji Standard

- **No Emojis Anywhere**: Absolutely no emojis may be used anywhere in the codebase or application.
  - No emojis in HTML markup, navigation bars, buttons, page titles, section headings, or tooltips.
  - No emojis in Chart.js legends, axis titles, or tooltips.
  - No emojis in Python script strings, log outputs, or error messages.
  - No emojis in documentation (`README.md`, `Agents.md`, markdown artifacts), commit messages, or PR descriptions.
- **Iconography**: Use clean, semantic text labels, standard typography, or inline SVG icons when visual indicators are needed.

---

## 2. Typography & Lo-Fi Monochrome Design

- **Primary Monospace Font**:
  - The primary typeface for all applications (`index.html`, `emerging.html`, `wards.html`, `map.html`, `tables.html`) must be `IBM Plex Mono`.
  - Body text, navigation elements, KPI cards, buttons, dropdowns, inputs, data tables, and chart labels must use monospace typography.
- **Lo-Fi Black & White Aesthetic**:
  - A clean, technical, lo-fi aesthetic with 1px borders and high contrast.
  - Browser-default light/dark mode detected via `prefers-color-scheme` with manual toggle button in navigation (`Theme: Light` / `Theme: Dark`) persisted in `localStorage`.
- **Button & Control Border Radius**:
  - Buttons, inputs, badges, cards, table containers, and interactive toggles must use slightly beveled 2px border radius (`border-radius: 2px;`) to avoid excessively rounded aesthetics while maintaining crisp technical styling.
- **Geographic Column Hierarchy in Tables**:
  - Across all data tables and exports, columns representing geographic jurisdictions must strictly follow: **Ward goes before ANC** (e.g. `Ward` -> `Councilmember` -> `ANC`).

---

## 3. Map Cartography & Single-Hue Choropleths

- **Local Basemap Tiles (`tiles/light/` & `tiles/blacklite/`)**:
  - Basemap tiles are Stamen Toner, stored locally in `tiles/light/{z}/{x}/{y}.png` and `tiles/blacklite/{z}/{x}/{y}.png` for Zooms 11 through 17.
- **Single-Hue Relative Intensity Color Ramps**:
  - Choropleth fills use single-hue intensity gradients (light tint to deep dark shade) for volume, Location Quotient, and YoY surge intensity.
- **Permanent Ward Boundaries**:
  - Ward boundaries remain visible on the map with crisp contrast and dashed outlines (`#7c3aed` / `#c084fc`).

---

## 4. Vendored Third-Party Dependencies

- **Local Storage (`assets/vendor/`)**: All client-side JavaScript and CSS libraries are stored locally in `assets/vendor/`:
  - `Leaflet` (v1.9.4): Mapping engine (`assets/vendor/leaflet/`)
  - `Chart.js` (v4.4.1): Charting library (`assets/vendor/chartjs/`)
  - `jsPDF` (v2.5.1): Client-side PDF generation (`assets/vendor/jspdf/`)
  - `html2canvas` (v1.4.1): Canvas capture for static exports (`assets/vendor/html2canvas/`)
  - `jsPDF-AutoTable` (v3.8.2): Table formatting for PDF exports (`assets/vendor/jspdf-autotable/`)

---

## 5. Paper Standards & Clean UI

- **US Letter Under the Hood**: All exportable reports, printable views, and generated PDFs conform strictly to US Letter (`8.5 in x 11.0 in`, `letter` format in jsPDF, `@page { size: letter; }` in print CSS).
- **Bidirectional Sortable Tables**: All data tables support ascending and descending sorting on every column, with rank numbers omitted so sorting remains clean.

---

## 6. Data Warehouse & Analytical Architecture

- **Columnar Parquet + DuckDB**: Raw 2025 and 2026 311 service requests (including `DETAILS`) and daily weather records are stored as compressed Parquet in `data/raw/` (gitignored) and queried via `duckdb` + `pyarrow`.
- **Specific Service Query Granularity**: All individual `SERVICECODE` / `SERVICECODEDESCRIPTION` trends are tracked alongside category family rollups.
- **Seasonality & Acceleration Controls**: Emerging issue detection evaluates YTD same-period YoY and recent 30-day YoY acceleration (excluding any 90-day window).
