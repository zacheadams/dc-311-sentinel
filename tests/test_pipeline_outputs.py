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

        # Verify 2025 and 2026 row counts
        meta = summary["metadata"]
        self.assertGreaterEqual(meta["total_2026_ytd"], 445000)
        self.assertEqual(meta["total_2025_full"], 440600)
        self.assertGreaterEqual(meta["distinct_descriptions_2026"], 129)

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
        self.assertEqual(emerging["weekly_weather"]["weeks"][0], "1/1-1/7")

    def test_html_pages_compiled_and_valid(self):
        for page in ("index.html", "emerging.html", "wards.html", "map.html", "tables.html"):
            path = os.path.join(BASE_DIR, page)
            self.assertTrue(os.path.exists(path), f"Missing compiled page: {page}")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("IBM Plex Mono", content)
            self.assertIn("@page", content)
            self.assertIn("size: letter", content)

    def test_weather_and_heat_viz_removed_from_ui(self):
        emerging_path = os.path.join(BASE_DIR, "emerging.html")
        with open(emerging_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("weather-matrix-table", content)
        self.assertNotIn("wx-overlay-select", content)
        self.assertNotIn("filter-wx", content)
        self.assertNotIn("Weather Sensitivity", content)
        self.assertNotIn("Weather-Expected", content)
        self.assertNotIn("heat days", content.lower())

    def test_emerging_trajectory_dual_axis(self):
        emerging_path = os.path.join(BASE_DIR, "emerging.html")
        with open(emerging_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("text: '311 Requests'", content)
        self.assertIn("text: 'Completion Time'", content)
        self.assertIn("text: 'Request Week'", content)
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
        self.assertIn("toggleTrajDataset", content)
        self.assertIn("renderTrajLegend", content)
        self.assertIn("1/1-1/7", content)
        self.assertIn("maxRotation: 45", content)
        self.assertIn("Median Completion:", content)
        self.assertNotIn("(${item.median_res_hours}h)", content)

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
