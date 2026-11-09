#!/usr/bin/env python3
"""
Verification tests for DC 311 Sentinel data artifacts, HTML outputs, and
strict no-emoji compliance across the repository.
"""

import json
import os
import re
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "]+",
    flags=re.UNICODE,
)


class TestPipelineOutputs(unittest.TestCase):
    def test_json_artifacts_exist_and_complete(self):
        with open(os.path.join(BASE_DIR, "data", "summary_top.json"), encoding="utf-8") as f:
            summary = json.load(f)
        with open(os.path.join(BASE_DIR, "data", "geography_stats.json"), encoding="utf-8") as f:
            geo = json.load(f)
        with open(os.path.join(BASE_DIR, "data", "emerging_issues.json"), encoding="utf-8") as f:
            emerging = json.load(f)
        with open(os.path.join(BASE_DIR, "data", "operational_patterns.json"), encoding="utf-8") as f:
            patterns = json.load(f)

        # Verify 2025 and 2026 row counts (excluding admin test codes)
        meta = summary["metadata"]
        self.assertGreaterEqual(meta["total_2026_ytd"], 444000)
        self.assertEqual(meta["total_2025_full"], 440538)
        self.assertGreaterEqual(meta["distinct_descriptions_2026"], 125)

        # Verify all 8 Wards and 46 ANCs
        self.assertEqual(len(geo["wards"]), 8)
        self.assertEqual(len(geo["ancs"]), 46)

        # Verify weather data and DETAILS audit are populated
        self.assertIn("2025", patterns["weather_ytd_comparison"])
        self.assertIn("2026", patterns["weather_ytd_comparison"])
        self.assertGreater(patterns["details_audit"]["total_populated_2025_2026"], 700)

        # Verify no 90-day window keys exist in emerging_issues.json
        for item in emerging["items"]:
            for k in item.keys():
                self.assertNotIn("90d", k.lower())

        # Verify weekly_trajectories contains volume and completion days for 2025 and 2026
        trajs = emerging["weekly_trajectories"]
        self.assertGreater(len(trajs), 0)
        for code, t in trajs.items():
            self.assertIn("w2025", t)
            self.assertIn("w2026", t)
            self.assertIn("res_days_2025", t)
            self.assertIn("res_days_2026", t)
            self.assertEqual(len(t["w2025"]), len(t["res_days_2025"]))
            self.assertEqual(len(t["w2026"]), len(t["res_days_2026"]))
            for day_val in t["res_days_2026"]:
                if day_val is not None:
                    self.assertIsInstance(day_val, int)
                    self.assertGreaterEqual(day_val, 0)

        # Verify monthly_trajectories contains 12 months for 2025 and 2026
        mtrajs = emerging["monthly_trajectories"]
        self.assertGreater(len(mtrajs), 0)
        for code, t in mtrajs.items():
            self.assertIn("m2025", t)
            self.assertIn("m2026", t)
            self.assertIn("res_days_2025", t)
            self.assertIn("res_days_2026", t)
            self.assertEqual(len(t["m2025"]), 12)
            self.assertEqual(len(t["m2026"]), 12)
            self.assertEqual(len(t["res_days_2025"]), 12)
            self.assertEqual(len(t["res_days_2026"]), 12)

        self.assertEqual(emerging["weekly_weather"]["weeks"][0], "1/1-1/7")

    def test_html_pages_compiled_and_valid(self):
        for page in ("index.html", "trends.html", "wards.html", "map.html", "tables.html"):
            path = os.path.join(BASE_DIR, page)
            self.assertTrue(os.path.exists(path), f"Missing compiled page: {page}")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("IBM Plex Mono", content)
            self.assertIn("@page", content)
            self.assertIn("size: letter", content)

    def test_weather_and_heat_viz_removed_from_ui(self):
        trends_path = os.path.join(BASE_DIR, "trends.html")
        with open(trends_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("weather-matrix-table", content)
        self.assertNotIn("wx-overlay-select", content)
        self.assertNotIn("filter-wx", content)
        self.assertNotIn("Weather Sensitivity", content)
        self.assertNotIn("Weather-Expected", content)
        self.assertNotIn("heat days", content.lower())

    def test_trends_trajectory_dual_axis(self):
        trends_path = os.path.join(BASE_DIR, "trends.html")
        with open(trends_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("text: '311 Requests'", content)
        self.assertIn("text: 'Completion Time'", content)
        self.assertIn("text: 'Request Month'", content)
        self.assertNotIn("text: 'Request Week'", content)
        self.assertNotIn("Request Week (by Request Date)", content)
        self.assertNotIn("(Same Weeks)", content)
        self.assertNotIn("(Same weeks)", content)
        self.assertNotIn("Weekly Volume & Time to Completion", content)
        self.assertNotIn("(Dotted Line with Circles)", content)
        self.assertIn("position: 'right'", content)
        self.assertIn("drawOnChartArea: false", content)
        self.assertIn("borderDash: [3, 3]", content)
        self.assertIn("pointStyle: 'circle'", content)
        self.assertIn("height:480px", content)
        self.assertIn("traj-legend", content)
        self.assertIn("2025 Time to Completion", content)
        self.assertIn("2026 Time to Completion", content)
        self.assertIn("2025 Monthly Requests", content)
        self.assertIn("2026 Monthly Requests", content)
        self.assertIn("toggleTrajDataset", content)
        self.assertIn("renderTrajLegend", content)
        self.assertIn("'January'", content)
        self.assertIn("'February'", content)
        self.assertIn("'December'", content)
        self.assertIn("minRotation: 45", content)
        self.assertIn("maxRotation: 45", content)
        self.assertIn("autoSkip: false", content)
        self.assertNotIn("Median Completion:", content)
        self.assertNotIn('<section class="kpi-row">', content)
        self.assertNotIn("<th>Classification</th>", content)
        self.assertNotIn("<th>Z-Score</th>", content)
        self.assertNotIn("30d Accel", content)
        self.assertIn("filter-period", content)
        self.assertIn("<th>Service Request</th>", content)
        self.assertNotIn("<th>Service Query</th>", content)
        self.assertNotIn("<th>Specific Service Query</th>", content)
        self.assertIn("2026 #", content)
        self.assertIn("2025 #", content)
        self.assertIn("# % Change", content)
        self.assertNotIn("2026 YTD</th>", content)
        self.assertIn("2026 Time", content)
        self.assertIn("2025 Time", content)
        self.assertIn("Time % Change", content)
        self.assertIn("renderTrendsTable", content)
        self.assertNotIn("(${item.median_res_hours}h)", content)

        # Trends page headers and selectors
        self.assertIn("Trends by Request", content)
        self.assertNotIn("Weekly 2026 vs. 2025 Trajectory", content)
        self.assertNotIn("Weekly 311 request volume (left axis) and time to completion", content)
        self.assertIn("Trends by Geography", content)
        self.assertNotIn("Trends by Ward", content)
        self.assertNotIn("Emerging & Declining Specific Queries", content)
        self.assertNotIn("Click any column header to sort; click a service description", content)
        self.assertNotIn("filter-status", content)
        self.assertIn("Geographic Subset", content)
        self.assertIn("ward-select", content)
        self.assertIn("anc-select", content)
        self.assertIn("smd-select", content)
        self.assertIn("geo-selector-grid", content)
        self.assertNotIn("geo-selection-badge", content)
        self.assertNotIn("Ward 1 – 8 Localized Emerging Request Surges", content)

        # Bar outline and reduced saturation/brightness styling
        self.assertIn("redBarBg", content)
        self.assertIn("blueBarBg", content)
        self.assertIn("redBarBorder", content)
        self.assertIn("blueBarBorder", content)
        self.assertIn("pointBorderColor: colors.bgCard", content)

    def test_clean_service_query_titles(self):
        import sys
        sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
        from text_utils import clean_service_desc

        self.assertEqual(clean_service_desc("DMV - Vehicle Title Issues"), "Vehicle Title Issues")
        self.assertEqual(clean_service_desc("DC Dog Park Maintenance (DGS)"), "Dog Park Maintenance")
        self.assertEqual(clean_service_desc("Out of State Parking Violation (ROSA)"), "Out of State Parking Violation (ROSA)")
        self.assertEqual(clean_service_desc("DC Government Information"), "Government Information")
        self.assertEqual(clean_service_desc("FEMS - Smoke Alarm Application"), "Smoke Alarm Application")
        self.assertEqual(clean_service_desc("DGS Grounds Landscaping (DGS)"), "Grounds Landscaping")
        self.assertEqual(clean_service_desc("DOEE - Engine Idling Tips"), "Engine Idling Tips")
        self.assertEqual(clean_service_desc("DC Indoor and Outdoor Pool Maintenance  (DGS)"), "Indoor and Outdoor Pool Maintenance")
        self.assertEqual(clean_service_desc("DC Spray Parks (DGS)"), "Spray Parks")
        self.assertEqual(clean_service_desc("DFHV - Lost and Found Claims (DC Taxi)"), "Lost and Found Claims (Taxi)")

        # Verify artifacts and HTML use cleaned titles
        trends_path = os.path.join(BASE_DIR, "trends.html")
        with open(trends_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Vehicle Title Issues", content)
        self.assertIn("Dog Park Maintenance", content)
        self.assertIn("Out of State Parking Violation (ROSA)", content)
        self.assertNotIn("DMV - Vehicle Title Issues", content)
        self.assertNotIn("DC Dog Park Maintenance (DGS)", content)

    def test_admin_test_codes_excluded_from_display_and_retained_in_raw(self):
        import duckdb
        test_codes = ("zTest1", "Test01", "S0081")

        # 1. Verify completely excluded from generated JSON artifacts and HTML pages
        for fname in ("summary_top.json", "emerging_issues.json", "geography_stats.json", "operational_patterns.json"):
            fpath = os.path.join(BASE_DIR, "data", fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            for code in test_codes:
                self.assertNotIn(f'"{code}"', content, f"{code} found in {fname}")

        for page in ("trends.html", "index.html", "tables.html", "wards.html", "map.html"):
            fpath = os.path.join(BASE_DIR, page)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            for code in test_codes:
                self.assertNotIn(f"<code>{code}</code>", content, f"{code} found in {page}")
                self.assertNotIn(f"'{code}'", content, f"{code} found in {page} JS")

        # 2. Verify raw warehouse database retains the raw data
        db_path = os.path.join(BASE_DIR, "data", "warehouse.duckdb")
        con = duckdb.connect(db_path, read_only=True)
        ztest_cnt = con.execute("SELECT count(*) FROM requests WHERE service_code = 'zTest1'").fetchone()[0]
        test01_cnt = con.execute("SELECT count(*) FROM requests WHERE service_code = 'Test01'").fetchone()[0]
        s0081_cnt = con.execute("SELECT count(*) FROM requests WHERE service_code = 'S0081'").fetchone()[0]
        self.assertEqual(ztest_cnt, 82)
        self.assertEqual(test01_cnt, 153)
        self.assertEqual(s0081_cnt, 1)

    def test_other_analysis_and_centered_footer(self):
        pages = ("index.html", "trends.html", "wards.html", "map.html", "tables.html")
        for p in pages:
            with open(os.path.join(BASE_DIR, p), "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Other Analysis", content, f"Missing Other Analysis nav in {p}")
            self.assertNotIn("129-Query Matrix & NLP", content, f"Found old nav label in {p}")
            self.assertIn(">Trends</a>", content, f"Missing Trends nav link in {p}")
            self.assertNotIn(">Emerging Issues</a>", content, f"Found old Emerging Issues nav link in {p}")
            self.assertIn("<p>Last Updated November 09, 2026</p>", content, f"Missing clean centered footer in {p}")

        # Check tables.html specific structure
        with open(os.path.join(BASE_DIR, "tables.html"), "r", encoding="utf-8") as f:
            tbl_content = f.read()
        self.assertNotIn("Unstructured DETAILS Column Audit", tbl_content)
        self.assertNotIn("Complete Service Query Performance Matrix", tbl_content)
        self.assertNotIn("details-audit-table", tbl_content)
        self.assertNotIn("master-query-table", tbl_content)
        self.assertIn("Temporal Filing Rhythm", tbl_content)
        self.assertIn("Chronic Repeat Address Hotspots (2026 YTD)", tbl_content)

        # Check repeat table columns
        self.assertIn("<th>Code</th>", tbl_content)
        self.assertIn("<th>Service Request</th>", tbl_content)
        self.assertNotIn("<th>Service Query</th>", tbl_content)
        self.assertIn("<th>Category</th>", tbl_content)
        self.assertIn("Chronic Repeat Properties (&gt;=5 requests)", tbl_content)
        self.assertIn("# at Chronic Repeat Properties", tbl_content)
        self.assertNotIn("Severe Repeat Properties", tbl_content)
        self.assertNotIn("Max Requests at Single MAR ID", tbl_content)

    def test_emerging_redirect_to_trends(self):
        redir_path = os.path.join(BASE_DIR, "emerging.html")
        self.assertTrue(os.path.exists(redir_path), "Missing emerging.html redirect")
        with open(redir_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("url=trends.html", content)
        self.assertIn('href="trends.html"', content)

    def test_strict_zero_emojis_across_repo(self):
        check_exts = (".py", ".html", ".md", ".json", ".yml")
        skip_dirs = {".git", ".venv", "tiles", "vendor", "raw"}

        for root, dirs, files in os.walk(BASE_DIR):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if not fname.endswith(check_exts):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                m = EMOJI_RE.search(text)
                self.assertIsNone(m, f"Found prohibited emoji in {fpath}: {m.group(0) if m else ''}")


if __name__ == "__main__":
    unittest.main()
