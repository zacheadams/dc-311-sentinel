#!/usr/bin/env python3
"""Compatibility wrapper for build_trends_page.py."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_trends_page import build_trends

if __name__ == "__main__":
    build_trends()
