# Process improvement: weekly campaign report

Based on the legacy process in `legacy/manual_process.md` in the repository.

## Before (manual)

| | |
|---|---|
| Steps | 8, most of them in Excel by hand |
| People who can do it | 1 |
| Time per week | Not yet measured (see method below) |
| Error handling | "If numbers look weird, ask Jan" |
| Data quality | Whatever the person notices |
| Audit trail | None |

> **Method for the baseline:** take one week of generated files (`guard demo-data backfill --days 7`), perform steps 3-6
> of the manual routine in Excel with a stopwatch, and record the minutes and the mistakes made. This figure is still to be added.

## After (automated)

| | |
|---|---|
| Steps | 0 manual: files land in `data/inbox`, cron runs `run_etl.sh`, PowerShell exports the report |
| People who can operate it | Anyone with the runbook |
| Load time (measured*) | **90 files / 6,303 rows in about 0.7 s** |
| Error handling | Bad rows go to `ops.etl_rejects` with a reason; bad *files* (schema drift, empty) fail loudly and are quarantined in `data/rejected`; a missing file triggers `check_freshness.py` |
| Data quality | **294 of 6,303 rows (4.7%) rejected and explained**, e.g. duplicates (88), clicks greater than impressions (42), unknown campaign (41), negative cost (39), bad date (31), missing impressions (29), wrong day (24) |
| Re-runs | Safe: identical file is skipped (SHA-256), corrected file replaces earlier rows (upsert) |
| Audit trail | `ops.etl_file_log`, `ops.audit_log`, Git history |

\*Measured in my development sandbox on synthetic data with PostgreSQL 16 on a single small machine. Absolute times depend on hardware.

## What the business gets

- The weekly report no longer depends on one person.
- Rejected rows are visible (`reporting.reject_reasons`), so the sales team can ask the ad network for corrected files instead of silently trusting bad numbers.
- Report can be produced any day, not just on Mondays.

## What I would measure in a real environment

Hours saved per month, number of report corrections after publication, time-to-detect a missing file (before: days, after: < 1 h).
