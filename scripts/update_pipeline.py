#!/usr/bin/env python3
"""
Master data refresh and static site compilation pipeline for DC 311 Sentinel.
Usage:
  .venv/bin/python scripts/update_pipeline.py                         # Incremental fetch + full rebuild
  .venv/bin/python scripts/update_pipeline.py --full                  # Full 2025+2026 fetch + full rebuild
  .venv/bin/python scripts/update_pipeline.py --skip-fetch            # Rebuild warehouse, JSON, and HTML from local Parquet
  .venv/bin/python scripts/update_pipeline.py --sync-gdrive           # Also sync raw Parquet & warehouse to Google Drive
  .venv/bin/python scripts/update_pipeline.py --with-missed-collections  # Also rebuild sibling dc-missed-collections from warehouse

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
    with_missed_collections = "--with-missed-collections" in sys.argv

    if not skip_fetch:
        run_step("fetch_boundaries.py")
        run_step("fetch_weather.py")
        run_step("fetch_311_data.py", ["--full"] if full_fetch else [])

    run_step("build_warehouse.py")
    run_step("analyze_311.py")
    run_step("build_index_page.py")
    run_step("build_trends_page.py")
    run_step("build_map_page.py")
    run_step("build_tables_page.py")

    if with_missed_collections:
        missed_dir = os.path.join(os.path.dirname(BASE_DIR), "dc-missed-collections")
        missed_script = os.path.join(missed_dir, "scripts", "update_pipeline.py")
        if not os.path.exists(missed_script):
            raise FileNotFoundError(f"Missing sibling dc-missed-collections pipeline at {missed_script}")
        print("=== Running sibling dc-missed-collections/scripts/update_pipeline.py ===")
        t0 = time.time()
        env = dict(os.environ)
        env["SENTINEL_DIR"] = BASE_DIR
        subprocess.run([sys.executable, missed_script], cwd=missed_dir, env=env, check=True)
        print(f"=== Completed dc-missed-collections pipeline in {time.time() - t0:.1f}s ===\n")

    if sync_gdrive:
        run_step("sync_gdrive.py", ["push"])

    print(f"Pipeline finished in {time.time() - t_start:.1f}s.")


if __name__ == "__main__":
    main()
