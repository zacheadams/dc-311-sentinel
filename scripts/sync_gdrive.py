#!/usr/bin/env python3
"""
Automated Google Drive synchronization for DC 311 Sentinel using rclone.
Syncs raw Parquet datasets and DuckDB spatial warehouse to/from personal Google Drive.

Usage:
  python scripts/sync_gdrive.py push    # Upload local data/raw and warehouse to Google Drive
  python scripts/sync_gdrive.py pull    # Download data/raw and warehouse from Google Drive
  python scripts/sync_gdrive.py status  # List remote files and sizes on Google Drive

Strictly adheres to Agents.md:
- Strictly zero emojis across code, logs, and outputs
"""

import argparse
import os
import shutil
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
WAREHOUSE_PATH = os.path.join(DATA_DIR, "warehouse.duckdb")
GDRIVE_REMOTE = "gdrive:dc-311-sentinel"


def check_rclone():
    rclone_bin = shutil.which("rclone")
    if not rclone_bin:
        sys.exit("Error: 'rclone' executable not found in PATH. Install rclone first.")
    # Check if gdrive remote is configured
    res = subprocess.run([rclone_bin, "listremotes"], capture_output=True, text=True)
    if "gdrive:" not in res.stdout:
        sys.exit("Error: 'gdrive:' remote is not configured in rclone. Run 'rclone config' first.")
    return rclone_bin


def push_to_gdrive(rclone_bin):
    print(f"Syncing raw Parquet datasets to {GDRIVE_REMOTE}/raw/ ...")
    if os.path.exists(RAW_DIR):
        subprocess.run(
            [rclone_bin, "sync", RAW_DIR, f"{GDRIVE_REMOTE}/raw", "--stats=5s", "--stats-one-line"],
            check=True,
        )
        print("Raw datasets synchronized successfully.")
    else:
        print(f"Warning: Local raw directory '{RAW_DIR}' not found. Skipping raw sync.")

    if os.path.exists(WAREHOUSE_PATH):
        print(f"Uploading warehouse database to {GDRIVE_REMOTE}/ ...")
        subprocess.run(
            [rclone_bin, "copy", WAREHOUSE_PATH, GDRIVE_REMOTE, "--stats=5s", "--stats-one-line"],
            check=True,
        )
        print("Warehouse database uploaded successfully.")
    else:
        print(f"Notice: '{WAREHOUSE_PATH}' does not exist locally. Skipping warehouse upload.")


def pull_from_gdrive(rclone_bin):
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"Downloading raw Parquet datasets from {GDRIVE_REMOTE}/raw/ to {RAW_DIR} ...")
    subprocess.run(
        [rclone_bin, "sync", f"{GDRIVE_REMOTE}/raw", RAW_DIR, "--stats=5s", "--stats-one-line"],
        check=True,
    )
    print("Raw datasets downloaded successfully.")

    print(f"Downloading warehouse database from {GDRIVE_REMOTE}/ to {DATA_DIR} ...")
    subprocess.run(
        [rclone_bin, "copy", f"{GDRIVE_REMOTE}/warehouse.duckdb", DATA_DIR, "--stats=5s", "--stats-one-line"],
        check=True,
    )
    print("Warehouse database downloaded successfully.")


def status_gdrive(rclone_bin):
    print(f"=== Remote Files in {GDRIVE_REMOTE} ===")
    subprocess.run([rclone_bin, "lsf", "-R", "--format", "ps", GDRIVE_REMOTE], check=True)
    print("\n=== Remote Storage Usage ===")
    subprocess.run([rclone_bin, "size", GDRIVE_REMOTE], check=True)


def main():
    parser = argparse.ArgumentParser(description="Sync DC 311 Sentinel datasets with Google Drive via rclone.")
    parser.add_argument(
        "action",
        choices=["push", "pull", "status"],
        help="Action to perform: 'push' (upload), 'pull' (download), or 'status' (list remote files)",
    )
    args = parser.parse_args()

    rclone_bin = check_rclone()

    if args.action == "push":
        push_to_gdrive(rclone_bin)
    elif args.action == "pull":
        pull_from_gdrive(rclone_bin)
    elif args.action == "status":
        status_gdrive(rclone_bin)


if __name__ == "__main__":
    main()
