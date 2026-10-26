"""Status checks shown on the console's Status page (same ideas as scripts/healthcheck.sh)."""
import os
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

from ..env import ROOT


def _backup_dir() -> Path:
    d = os.getenv("BACKUP_DIR", "./backups")
    p = Path(d)
    return p if p.is_absolute() else ROOT / d.lstrip("./")


def run_checks(q):
    """`q(sql, params=None)` returns a list of dict rows. Returns a list of {level, name, detail}."""
    checks = []

    def add(level, name, detail):
        checks.append({"level": level, "name": name, "detail": detail})

    try:
        q("SELECT 1")
        add("OK", "Database", "accepting connections")
    except Exception as exc:                      # noqa: BLE001 (show any connection problem)
        add("CRIT", "Database", f"unreachable: {exc.__class__.__name__}")
        return checks

    row = q("SELECT max(report_date) AS d FROM reporting.daily_by_brand")[0]
    if row["d"]:
        age = (date.today() - row["d"]).days
        lvl = "OK" if age <= 2 else "WARN" if age <= 4 else "CRIT"
        add(lvl, "Data freshness", f"newest report date {row['d']} ({age} day(s) old)")
    else:
        add("WARN", "Data freshness", "no data loaded yet")

    failed = q("""SELECT count(*) AS n FROM reporting.pipeline_runs
                  WHERE status='failed' AND started_at > now() - interval '24 hours'""")[0]["n"]
    add("CRIT" if failed else "OK", "Pipeline", f"{failed} failed file(s) in the last 24 h" if failed else "no failed files in the last 24 h")

    r = q("""SELECT coalesce(sum(rows_rejected),0) AS rej, coalesce(sum(rows_read),0) AS rd
             FROM reporting.pipeline_runs WHERE started_at > now() - interval '7 days'""")[0]
    if r["rd"]:
        rate = 100.0 * r["rej"] / r["rd"]
        add("OK" if rate <= 8 else "WARN" if rate <= 15 else "CRIT", "Data quality", f"{rate:.1f}% of rows rejected in the last 7 days")
    else:
        add("WARN", "Data quality", "no rows processed in the last 7 days")

    marker = _backup_dir() / ".last_success"
    if marker.is_file():
        try:
            ts = datetime.fromisoformat(marker.read_text().strip().replace("Z", "+00:00"))
            hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
            add("OK" if hours < 26 else "WARN" if hours < 48 else "CRIT", "Backup", f"last successful backup {hours:.0f} h ago")
        except ValueError:
            add("WARN", "Backup", "marker file unreadable")
    else:
        add("WARN", "Backup", "no backup marker visible from this host")

    path = _backup_dir() if _backup_dir().exists() else Path("/")
    u = shutil.disk_usage(path)
    pct = 100 * u.used / u.total
    add("OK" if pct < 80 else "WARN" if pct < 90 else "CRIT", "Disk", f"{pct:.0f}% used on the backup volume")
    return checks
