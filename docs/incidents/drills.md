# Incident drills: break it on purpose, then write the postmortem

Rehearsals for the failure modes in the [runbook](../runbook.md). Run each on a throw-away VM, never on a machine you care about.
Write-ups use [`TEMPLATE.md`](TEMPLATE.md) and are saved in this folder as `001-<name>.md`, `002-<name>.md`, and so on.

| # | Drill | How to break it | What you should observe | Fix (runbook) |
|---|---|---|---|---|
| 1 | **Schema drift** | `guard demo-data daily --date $(date -I -d yesterday) --network adserve --inject schema_drift` then `make etl` | `FAILED - schema drift` in log, file in `data/rejected/`, `check_freshness.py` exits 2 | *ETL job failed* |
| 2 | **Missing file** | `... --network mediabuy --inject missing_file`, `make etl`, `python -m guard.check_freshness` | `CRIT ... not loaded` | *Expected file did not arrive* |
| 3 | **Disk full** | On a VM with a small separate disk/partition for backups: `fallocate -l <free space minus 50M> backups/filler.bin` then `./scripts/backup.sh` | Backup fails, `healthcheck.sh` WARN/CRIT on disk and backup age, `logs/backup.log` shows error | *Disk full*, *Backup failed* |
| 4 | **Kill the ETL mid-run** | Start a big load (`backfill --days 365`), `pkill -9 -f guard.load_daily` during processing | Row stuck in `running`; no half-loaded file (single transaction); `healthcheck.sh` WARN after 1 h (fake the time with an `UPDATE` to speed up) | *ETL killed mid-run* |
| 5 | **Accidental delete** | `DELETE FROM core.daily_performance WHERE report_date >= current_date - 7;` as admin (in a scratch copy first!) | Reports empty; audit log does **not** record facts (only dimension tables): discuss why, and what you would change | *Restore from backup*, or reload files from `data/processed` |
| 6 | **Lost backup passphrase** (thought experiment, don't actually do it) | n/a | Write one paragraph: what would you lose, how do you prevent it? | Password manager, escrow, test restores with the *documented* passphrase |

## Suggested first write-up
Drill 3 (disk full) touches backups, monitoring and database availability, and has an obvious set of follow-up changes
(retention, alert thresholds, off-server copy).
