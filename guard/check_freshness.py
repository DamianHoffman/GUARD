#!/usr/bin/env python3
"""
Did every ad network deliver (and did we load) the file for a given day?
Also warns when a file is suspiciously small compared with the last 7 loaded files.
Exit codes: 0 ok, 1 warning, 2 critical (missing / failed file). Meant for cron + alerting.
"""
import argparse
import sys
from datetime import date, timedelta

from . import db
from .config import NETWORKS


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=(date.today() - timedelta(days=1)).isoformat(),
                    help="report date to check (default: yesterday)")
    args = ap.parse_args(argv)
    worst = 0
    # monitor role can read the ETL log; no need for ETL credentials here
    conn = db.connect("MONITOR_USER", "MONITOR_PASSWORD", "guard_monitor")
    with conn, conn.cursor() as cur:
        for network in NETWORKS:
            name = f"{network}_{args.date}.csv"
            cur.execute("""SELECT status, rows_loaded, rows_rejected, message FROM ops.etl_file_log
                           WHERE file_name=%s AND status IN ('success','partial','failed')
                           ORDER BY started_at DESC LIMIT 1""", (name,))
            row = cur.fetchone()
            if row is None:
                print(f"CRIT  {name}: not loaded (file missing or ETL did not run)")
                worst = 2
                continue
            status, loaded, rejected, msg = row
            if status == "failed":
                print(f"CRIT  {name}: ETL FAILED - {msg}")
                worst = 2
                continue
            cur.execute("""SELECT avg(rows_loaded) FROM (
                             SELECT rows_loaded FROM ops.etl_file_log
                             WHERE network_code=%s AND status IN ('success','partial') AND file_name<>%s
                             ORDER BY started_at DESC LIMIT 7) t""", (network, name))
            avg = cur.fetchone()[0]
            if avg and loaded < 0.5 * float(avg):
                print(f"WARN  {name}: only {loaded} rows loaded (7-file average {float(avg):.0f})")
                worst = max(worst, 1)
            else:
                print(f"OK    {name}: {status}, loaded={loaded}, rejected={rejected}")
    return worst


if __name__ == "__main__":
    sys.exit(main())
