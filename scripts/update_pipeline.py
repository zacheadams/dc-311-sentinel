#!/usr/bin/env python3
"""
Master data refresh and static site compilation pipeline for DC 311 Sentinel.
Usage:
  .venv/bin/python scripts/update_pipeline.py                 # Incremental fetch + full rebuild
  .venv/bin/python scripts/update_pipeline.py --full          # Full 2025+2026 fetch + full rebuild
  .venv/bin/python scripts/update_pipeline.py --skip-fetch    # Rebuild warehouse, JSON, and HTML from local Parquet
  .venv/bin/python scripts/update_pipeline.py --sync-gdrive   # Also sync raw Parquet & warehouse to Google Drive

Strictly adheres to Agents.md:
- Strictly zero emojis across code, logs, and outputs
"""

import os
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")


def run_step(script_name, extra_args=None):
    cmd = [sys.executable, os.path.join(SCRIPTS_DIR, script_name)]
    if extra_args:
        cmd.extend(extra_args)
    print(f"=== Running {script_name} {' '.join(extra_args or [])} ===")
    t0 = time.time()
    subprocess.run(cmd, check=True)
    print(f"=== Completed {script_name} in {time.time() - t0:.1f}s ===\n")


def main():
    t_start = time.time()
    skip_fetch = "--skip-fetch" in sys.argv
    full_fetch = "--full" in sys.argv
    sync_gdrive = "--sync-gdrive" in sys.argv

    if not skip_fetch:
        run_step("fetch_boundaries.py")
        run_step("fetch_weather.py")
        run_step("fetch_311_data.py", ["--full"] if full_fetch else [])

    run_step("build_warehouse.py")
    run_step("analyze_311.py")
    run_step("build_index_page.py")
    run_step("build_trends_page.py")
    run_step("build_wards_page.py")
    run_step("build_map_page.py")
    run_step("build_tables_page.py")

    if sync_gdrive:
        run_step("sync_gdrive.py", ["push"])

    print(f"Pipeline finished in {time.time() - t_start:.1f}s.")


if __name__ == "__main__":
    main()
