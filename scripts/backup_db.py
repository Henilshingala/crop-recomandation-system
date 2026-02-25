#!/usr/bin/env python3
"""
Daily SQLite backup with 7-day retention.
Portable — uses Python's sqlite3 module, no external CLI needed.

Usage: python scripts/backup_db.py
Cron:  0 2 * * * cd /path/to/CRS && python scripts/backup_db.py
"""

import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DB_PATH = PROJECT_ROOT / "Backend" / "app" / "db.sqlite3"
BACKUP_DIR = PROJECT_ROOT / "Backups"
RETENTION_DAYS = 7


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"DB not found: {DB_PATH}")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    backup_path = BACKUP_DIR / f"db_{date_str}.sqlite3"

    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(backup_path)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()

    print(f"Backed up to {backup_path}")

    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    for f in BACKUP_DIR.glob("db_*.sqlite3"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            f.unlink()
            print(f"Removed old backup: {f}")

    print(f"Retention: kept last {RETENTION_DAYS} days")


if __name__ == "__main__":
    main()
