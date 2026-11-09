#!/usr/bin/env python3
"""
Unit tests for emerging issue statistical detection and weather baseline regression.
Strictly zero emojis.
"""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

from analyze_311 import fit_weather_baseline_and_predict, log_rate_ratio_and_z, pearson_r


class TestEmergingAnalytics(unittest.TestCase):
    def test_log_rate_ratio_and_z(self):
        # Identical counts over identical windows -> RR=1.0, pct=0.0, z=0.0
        rr, pct, z = log_rate_ratio_and_z(500, 300, 500, 300)
        self.assertAlmostEqual(rr, 1.0, places=3)
        self.assertAlmostEqual(pct, 0.0, places=1)
        self.assertAlmostEqual(z, 0.0, places=2)

        # Doubling with high volume -> RR ~ 2.0, pct ~ +100%, z > 10
        rr2, pct2, z2 = log_rate_ratio_and_z(1000, 300, 500, 300)
        self.assertGreater(rr2, 1.98)
        self.assertGreater(pct2, 99.0)
        self.assertGreater(z2, 10.0)

    def test_pearson_correlation(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        ys = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
        self.assertAlmostEqual(pearson_r(xs, ys), 1.0, places=3)
        ys_inv = [12.0, 10.0, 8.0, 6.0, 4.0, 2.0]
        self.assertAlmostEqual(pearson_r(xs, ys_inv), -1.0, places=3)

    def test_weather_baseline_prediction(self):
        # Construct synthetic 2025 daily data where requests depend strongly on rain_3d_in
        daily_2025 = []
        for i in range(100):
            rain = 1.0 if i % 5 == 0 else 0.0
            daily_2025.append({
                "rain_3d_in": rain,
                "snow_3d_in": 0.0,
                "temp_mean_f": 60.0,
                "is_wknd": (i % 7 in (5, 6)),
                "cnt": int(10 + 20 * rain),
            })
        # If 2026 has the exact same weather distribution, predicted volume should be close to 2025
        pred_same = fit_weather_baseline_and_predict(daily_2025, daily_2025)
        actual_2025 = sum(d["cnt"] for d in daily_2025)
        self.assertAlmostEqual(pred_same, actual_2025, delta=actual_2025 * 0.05)


if __name__ == "__main__":
    unittest.main()
