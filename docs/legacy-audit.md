# Legacy takeover: audit findings and remediation

**Scope:** `legacy/` (two scripts, one crontab, one manual process).
**Method:** read every script line by line, ask "what happens when this fails / when someone leaves / when the data grows?"

## Findings

| # | Finding | Risk | Severity | Fix in this project |
|---|---|---|---|---|
| 1 | Admin password `PGPASSWORD='...'` hard-coded in `weekly_report.sh` (and the script runs as the `postgres` superuser) | Anyone who can read the script owns the database; password ends up in Git history if committed | **High** | Secrets in git-ignored `.env`; separate least-privilege roles (`guard_etl`, `guard_analyst`, `guard_backup`) |
| 2 | Backup is a plain-text SQL file **on the same server and disk** as the database | Disk failure or ransomware loses data *and* backups; personal data stored unencrypted | **High** | `backup.sh`: custom format, GPG AES-256 encryption, checksum, optional copy to Azure Blob |
| 3 | Backup was **never restored** and nobody knows if it works | Unknown: could be empty or corrupt | **High** | `restore_test.sh` weekly, measures restore time (RTO), checks row counts |
| 4 | No retention ("TODO: delete old ones") and `cp` creates a second copy | Disk fills up -> database stops (the *backup* takes the DB down) | **High** | Retention in `backup.sh` and `Invoke-BackupRotation.ps1` (daily/weekly) |
| 5 | Date suffix `%d%m` (day+month, no year) | Backups overwrite each other every year | Medium | Timestamped names `guard_YYYYMMDD_HHMMSS` |
| 6 | Cron output sent to `/dev/null` | Failures are invisible. The backup could have been failing for months | **High** | Logging to `logs/`, non-zero exit codes, `healthcheck.sh` checks backup age |
| 7 | Weekly report cron has no logging at all, writes to world-readable `/tmp/report.csv` | Customer data leaks to other local users; no trace | Medium | `Export-CampaignReport.ps1` as read-only analyst role, output to a controlled directory |
| 8 | Commented-out import job whose script no longer exists | Nobody knows if imports still happen: **hidden manual dependency** | Medium | Documented process; `check_freshness.py` alerts when a file is missing |
| 9 | `SELECT *` joins without keys (`d.camp = c.id`), no constraints on the tables | Duplicates / bad rows go straight into reports | Medium | Constraints (`CHECK`, `FK`, `PK`), ETL rejects table |
| 10 | Manual Excel process with 8 steps, shared password file, one person knows it | Bus factor 1, human errors, 2+ hours every week | **High** | Automated ETL + report, runbook, process write-up |
| 11 | No change tracking: nobody knows who changed what | No accountability (RODO "rozliczalność") | Medium | `ops.audit_log` triggers, Git for all scripts |
| 12 | No documentation, no monitoring | Problems found by users, not by the team | Medium | `docs/runbook.md`, `healthcheck.sh`, Prometheus + Grafana |

## Order of work (what I would do in a real takeover)

1. **Stop the bleeding (day 1):** change the exposed password, take a verified backup *somewhere else*, check free disk space.
2. **Understand (week 1):** interview the former owner and the report's consumers, write down the real process (see `legacy/manual_process.md`).
3. **Make it safe (week 2):** least-privilege roles, encrypted + tested backups, monitoring.
4. **Make it better (weeks 3-4):** automate the manual import, add data-quality checks, document, hand over to the business.

Before/after numbers are in [`process-improvement.md`](process-improvement.md).
