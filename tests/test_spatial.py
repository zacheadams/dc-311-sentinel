#!/usr/bin/env python3
"""
Unit tests for spatial point-in-polygon assignment and ANC sorting utilities.
Strictly zero emojis.
"""

import json
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

from build_warehouse import load_polygon_index, lookup_polygon
from spatial_utils import anc_sort_key, is_point_in_poly


class TestSpatialUtils(unittest.TestCase):
    def test_point_in_simple_polygon_and_hole(self):
        outer = [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]
        hole = [[3.0, 3.0], [7.0, 3.0], [7.0, 7.0], [3.0, 7.0], [3.0, 3.0]]
        self.assertTrue(is_point_in_poly(1.5, 1.5, [outer, hole]))
        self.assertFalse(is_point_in_poly(5.0, 5.0, [outer, hole]))
        self.assertFalse(is_point_in_poly(12.0, 5.0, [outer, hole]))

    def test_dc_ward_and_anc_landmarks(self):
        ward_path = os.path.join(BASE_DIR, "data", "dc_wards.geojson")
        anc_path = os.path.join(BASE_DIR, "data", "dc_ancs.geojson")
        ward_items, ward_grid = load_polygon_index(ward_path, "WARD")
        anc_items, anc_grid = load_polygon_index(anc_path, "ANC_ID")

        # US Capitol / Capitol Hill -> Ward 6
        w_cap = lookup_polygon(-76.995, 38.889, ward_grid, ward_items)
        a_cap = lookup_polygon(-76.995, 38.889, anc_grid, anc_items)
        self.assertEqual(w_cap, "6")
        self.assertTrue(a_cap.startswith("6"))

        # Columbia Heights -> Ward 1
        w_ch = lookup_polygon(-77.032, 38.928, ward_grid, ward_items)
        self.assertEqual(w_ch, "1")

        # Tenleytown -> Ward 3
        w_tt = lookup_polygon(-77.079, 38.948, ward_grid, ward_items)
        self.assertEqual(w_tt, "3")

        # Congress Heights -> Ward 8
        w_c8 = lookup_polygon(-76.995, 38.843, ward_grid, ward_items)
        self.assertEqual(w_c8, "8")

    def test_anc_sort_order(self):
        raw = ["8F", "1B", "3/4G", "3F", "4A", "1A", "2C"]
        ordered = sorted(raw, key=anc_sort_key)
        self.assertEqual(ordered, ["1A", "1B", "2C", "3F", "3/4G", "4A", "8F"])


if __name__ == "__main__":
    unittest.main()
