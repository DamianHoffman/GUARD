#!/usr/bin/env python3
"""
Daily ETL: load ad-network CSV files from data/inbox into core.daily_performance.

For every file:
  1. fingerprint (sha256) -> skip if this exact content was already loaded (idempotent)
  2. validate header (schema drift => whole file fails, goes to data/rejected)
  3. validate each row; bad rows go to ops.etl_rejects with a reason, good rows are loaded
  4. convert currency (EUR -> PLN), upsert facts, write a summary row to ops.etl_file_log
  5. move the file to data/processed (or data/rejected)

Exit code: 0 = all good (partial loads are OK, see reject table), 1 = at least one file failed.
"""
import argparse
import csv
import hashlib
import logging
import shutil
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from psycopg2.extras import execute_values

from . import db
from .config import NETWORKS
from .parsing import Reject, parse_row

log = logging.getLogger("guard.etl")
ROOT = Path(__file__).resolve().parent.parent
CENT = Decimal("0.01")


class FileError(Exception):
    """The whole file is unusable (schema drift, empty, unknown network)."""


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_date(path: Path) -> date | None:
    try:
        return date.fromisoformat(path.stem.split("_", 1)[1])
    except (IndexError, ValueError):
        return None


def raw_text(raw: dict, delimiter: str) -> str:
    parts = []
    for k, v in raw.items():
        if isinstance(v, list):
            parts.extend(v)
        else:
            parts.append("" if v is None else str(v))
    return delimiter.join(parts)[:500]


def start_log(conn, path: Path, sha: str, network: str) -> int:
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO ops.etl_file_log (file_name, file_sha256, network_code, status)
                       VALUES (%s,%s,%s,'running') RETURNING log_id""", (path.name, sha, network))
        log_id = cur.fetchone()[0]
    conn.commit()
    return log_id


def finish_log(conn, log_id, status, read=0, loaded=0, rejected=0, message=None):
    with conn.cursor() as cur:
        cur.execute("""UPDATE ops.etl_file_log
                       SET status=%s, rows_read=%s, rows_loaded=%s, rows_rejected=%s,
                           finished_at=now(), message=%s WHERE log_id=%s""",
                    (status, read, loaded, rejected, message, log_id))
    conn.commit()


def process_file(conn, path: Path) -> str:
    network = path.name.split("_", 1)[0]
    sha = sha256_of(path)

    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM ops.etl_file_log WHERE file_sha256=%s AND status IN ('success','partial')", (sha,))
        if cur.fetchone():
            cur.execute("""INSERT INTO ops.etl_file_log (file_name, file_sha256, network_code, status, finished_at, message)
                           VALUES (%s,%s,%s,'skipped',now(),'identical file already loaded')""", (path.name, sha, network))
            conn.commit()
            log.info("%s: skipped (already loaded)", path.name)
            return "skipped"

    log_id = start_log(conn, path, sha, network)
    rows_read = 0
    try:
        cfg = NETWORKS.get(network)
        if cfg is None:
            raise FileError(f"unknown network '{network}' (add it to guard/config.py)")
        if path.stat().st_size == 0:
            raise FileError("empty file (0 bytes)")

        with conn.cursor() as cur:
            cur.execute("SELECT campaign_code, campaign_id FROM core.campaigns")
            campaigns = dict(cur.fetchall())
            cur.execute("SELECT placement_key, placement_id FROM core.placements")
            placements = dict(cur.fetchall())
            cur.execute("SELECT network_id FROM core.ad_networks WHERE code=%s", (network,))
            net = cur.fetchone()
            if not net:
                raise FileError(f"network '{network}' missing in core.ad_networks")
            network_id = net[0]
            fx_cache: dict = {}

            def fx(day: date) -> Decimal:
                if cfg.currency == "PLN":
                    return Decimal(1)
                key = (cfg.currency, day)
                if key not in fx_cache:
                    cur.execute("""SELECT rate_to_pln FROM core.fx_rates
                                   WHERE currency=%s AND valid_from<=%s ORDER BY valid_from DESC LIMIT 1""",
                                (cfg.currency, day))
                    r = cur.fetchone()
                    fx_cache[key] = r[0] if r else None
                if fx_cache[key] is None:
                    raise Reject("no_fx_rate")
                return fx_cache[key]

            good: dict = {}
            rejects: list = []
            expected = file_date(path)

            with open(path, newline="", encoding=cfg.encoding) as f:
                reader = csv.DictReader(f, delimiter=cfg.delimiter)
                if reader.fieldnames is None:
                    raise FileError("empty file (no header)")
                reader.fieldnames = [h.strip() for h in reader.fieldnames]
                missing = sorted(set(cfg.columns.values()) - set(reader.fieldnames))
                if missing:
                    raise FileError(f"schema drift: missing columns {missing}, got {reader.fieldnames}")

                for raw in reader:
                    rows_read += 1
                    try:
                        p = parse_row(raw, cfg, expected)
                        if p.campaign_code not in campaigns:
                            raise Reject("unknown_campaign")
                        if p.placement_key not in placements:
                            raise Reject("unknown_placement")
                        key = (p.report_date, campaigns[p.campaign_code], placements[p.placement_key], network_id)
                        if key in good:
                            raise Reject("duplicate_row")
                        spend = (p.cost * fx(p.report_date)).quantize(CENT, ROUND_HALF_UP)
                        good[key] = (*key, p.impressions, p.clicks, spend, path.name)
                    except Reject as r:
                        rejects.append((log_id, reader.line_num, r.reason, raw_text(raw, cfg.delimiter)))

            if rows_read == 0:
                raise FileError("no data rows (header only): refusing to load an empty report as 'no spend'")

            if good:
                execute_values(cur, """
                    INSERT INTO core.daily_performance
                        (report_date, campaign_id, placement_id, network_id, impressions, clicks, spend_pln, source_file)
                    VALUES %s
                    ON CONFLICT (report_date, campaign_id, placement_id, network_id) DO UPDATE
                       SET impressions=EXCLUDED.impressions, clicks=EXCLUDED.clicks,
                           spend_pln=EXCLUDED.spend_pln, source_file=EXCLUDED.source_file, loaded_at=now()
                """, list(good.values()))
            if rejects:
                execute_values(cur, "INSERT INTO ops.etl_rejects (log_id, line_no, reason, raw_line) VALUES %s", rejects)
        conn.commit()

        status = "success" if not rejects else "partial"
        finish_log(conn, log_id, status, rows_read, len(good), len(rejects),
                   None if not rejects else f"{len(rejects)} rows rejected, see ops.etl_rejects")
        log.info("%s: %s (read=%d loaded=%d rejected=%d)", path.name, status, rows_read, len(good), len(rejects))
        return status

    except Exception as exc:                       # FileError, DB errors, decoding errors, ...
        conn.rollback()
        finish_log(conn, log_id, "failed", rows_read, 0, 0, f"{type(exc).__name__}: {exc}"[:1000])
        log.error("%s: FAILED - %s", path.name, exc)
        return "failed"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inbox", default=str(ROOT / "data" / "inbox"))
    ap.add_argument("--processed", default=str(ROOT / "data" / "processed"))
    ap.add_argument("--rejected", default=str(ROOT / "data" / "rejected"))
    ap.add_argument("--file", help="process just this file")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    inbox = Path(args.inbox)
    files = [Path(args.file)] if args.file else sorted(inbox.glob("*.csv"))
    if not files:
        log.warning("no files in %s", inbox)
        return 0

    Path(args.processed).mkdir(parents=True, exist_ok=True)
    Path(args.rejected).mkdir(parents=True, exist_ok=True)
    conn = db.connect()
    counts = {"success": 0, "partial": 0, "skipped": 0, "failed": 0}
    try:
        for p in files:
            status = process_file(conn, p)
            counts[status] += 1
            dest = Path(args.rejected if status == "failed" else args.processed) / p.name
            shutil.move(str(p), dest)
    finally:
        conn.close()
    log.info("done: %s", counts)
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
