# Runbook

For whoever is on call (including future you at 3 a.m.). Each section: **symptom -> check -> fix -> verify -> prevent**.
All commands run from the repo root; `source .env` first (or use the helper scripts, which do it for you).

Quick overview of the system: [`architecture.md`](architecture.md). First thing to do in any incident:
`./scripts/healthcheck.sh` and `tail -50 logs/*.log`.

---

## Database down
**Symptom:** `healthcheck.sh` says "database is NOT accepting connections"; Prometheus alert `PostgresDown`.
1. Docker: `docker compose ps` and `docker compose logs --tail 100 postgres`. Native: `systemctl status postgresql`, `journalctl -u postgresql -n 100`.
2. Typical causes: disk full (see below), out of memory (`dmesg | grep -i oom`), bad config change, corrupt volume.
3. Restart: `docker compose restart postgres` (or `systemctl restart postgresql`). Watch the log until "database system is ready to accept connections".
4. Verify: `./scripts/healthcheck.sh`; run `make etl` if loads were missed (the ETL is safe to re-run).
5. If the data volume is damaged: restore from backup (section *Restore from backup*).

## Disk full
**Symptom:** `healthcheck.sh` CRIT `disk ... 9x% used`; Postgres logs `No space left on device`; backups fail.
1. Find what is big: `df -h`, `du -xh --max-depth=2 / 2>/dev/null | sort -h | tail -20`.
2. Safe things to delete first, in this order: old backups beyond retention (`ls -lh backups/`), `data/processed/*.csv` older than 90 days, old logs (`logs/`), docker leftovers (`docker system df`; `docker image prune`).
3. **Never** delete files inside the PostgreSQL data directory (`pg_wal`!) by hand.
4. If Postgres is already down, free space first, then start it.
5. Verify: `df -h` < 80%, `./scripts/healthcheck.sh`, run a manual backup.
6. Prevent: retention (`BACKUP_RETENTION_DAYS`, `Invoke-BackupRotation.ps1`), alert at 80%, copy backups off the server (Azure).

## Backup failed / backup too old
**Symptom:** `healthcheck.sh` WARN/CRIT "last successful backup Nh ago"; `logs/backup.log` contains `BACKUP FAILED`.
1. `tail -30 logs/backup.log`. Common causes: disk full; wrong `BACKUP_PASSWORD`; `gpg` missing; DB unreachable.
2. Fix the cause, then run `./scripts/backup.sh` manually.
3. Verify: new file in `backups/`, `.sha256` next to it, `./scripts/restore_test.sh` passes.
4. Tell the data owner if more than one backup was missed.

## Restore from backup
**When:** data loss, corruption, or a bad deployment. **Think first:** do you need the whole database or just a table? Restoring over live data destroys changes made since the backup.
1. Pick the file: `ls -lt backups/`. Verify: `cd backups && sha256sum -c guard_XXXX.dump.gpg.sha256`.
2. Decrypt: `gpg -d -o /tmp/restore.dump backups/guard_XXXX.dump.gpg` (passphrase from the password manager).
3. **Restore into a NEW database first** and look at it:
   `createdb guard_restored && pg_restore --no-owner --no-privileges -d guard_restored /tmp/restore.dump`
4. Only if correct: rename databases during a maintenance window (`ALTER DATABASE ... RENAME TO ...`) or copy needed tables across.
5. Re-run roles/grants: `./scripts/init_db.sh` is idempotent for roles; check with `./tests/test_security.sh`.
6. Securely remove the decrypted file: `shred -u /tmp/restore.dump`.
7. Reload files that arrived after the backup (move from `data/processed` to `data/inbox`): the ETL de-duplicates by file hash, so only truly missing ones are loaded.
The measured restore time is written to `logs/restore_test.log` on every test run; record it as your recovery-time estimate for the current data size.

## ETL job failed
**Symptom:** `check_freshness.py` prints `CRIT ... ETL FAILED`; `reporting.etl_quality` shows `failed`; file sits in `data/rejected/`.
Diagnose: `SELECT file_name, status, message FROM ops.etl_file_log WHERE status='failed' ORDER BY started_at DESC LIMIT 5;`

| Message contains | Meaning | Action |
|---|---|---|
| `schema drift: missing columns` | The ad network renamed/removed a column | Compare header with `guard/config.py`. If the change is permanent, update the config + add a test; if it is a mistake, ask the network for a corrected file. Move the file back to `data/inbox` and re-run. |
| `empty file` or `no data rows` | Network sent 0 bytes, or a header with no data | Ask the network to resend. The ETL refuses to load an empty report as "no spend". |
| `unknown network` | New file prefix | Add the network to `core.ad_networks` and `guard/config.py` (see *Onboarding a new ad network*). |
| `UnicodeDecodeError` | Encoding changed (e.g. cp1250 -> utf-8) | Check `file -i`, fix `encoding` in `guard/config.py`. |
| DB errors (`connection refused`, `permission denied`) | Database down / role changed | See *Database down*; `./tests/test_security.sh`. |

Re-run after fixing: `mv data/rejected/FILE data/inbox/ && make etl`.

## ETL finished but many rows rejected
`SELECT * FROM reporting.reject_reasons ORDER BY rows DESC;` A sudden jump in one reason points at a source problem rather than random noise (for example `unknown_campaign` spikes when sales created campaigns that are not in our database yet).
To re-load a file after fixing the cause (e.g. you added the missing campaigns): identical content is skipped by design (SHA-256), so as admin delete its log row first:
`DELETE FROM ops.etl_file_log WHERE file_name='X' AND status='partial';` (its reject rows go with it), copy the file from `data/processed` back to `data/inbox`, run `make etl`. Facts are upserted, so nothing is duplicated.

## ETL killed mid-run
**Symptom:** `healthcheck.sh` WARN "stuck in 'running' > 1h".
The file was loaded inside one transaction, so either everything for that file is in, or nothing is. Mark the log row failed and re-run:
`UPDATE ops.etl_file_log SET status='failed', finished_at=now(), message='killed mid-run' WHERE status='running' AND started_at < now() - interval '1 hour';` then move the file back from `data/inbox` (it was not moved yet) and run `make etl`.

## Expected file did not arrive
**Symptom:** `check_freshness.py`: `CRIT <network>_<date>.csv: not loaded`.
1. Is it in `data/inbox`, `data/processed`, or nowhere? `ls data/*/<network>_<date>*`.
2. If nowhere: contact the network / the business owner. Note the time in the incident log.
3. Reports for that day will be incomplete: tell the report consumers (see `docs/user-support-ticket.md` for wording).
4. When the file arrives: copy to `data/inbox`, run `make etl`.

## Too many connections
`SELECT usename, state, count(*) FROM pg_stat_activity GROUP BY 1,2 ORDER BY 3 DESC;`
Find the culprit; sessions `idle in transaction` for a long time are usually an application bug. Terminate only if needed: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle in transaction' AND state_change < now() - interval '30 min';`
Do **not** just raise `max_connections` (memory!). Consider a pooler (PgBouncer).

## Slow query / long-running query
`SELECT pid, now()-query_start AS runtime, usename, left(query,100) FROM pg_stat_activity WHERE state='active' ORDER BY runtime DESC;`
Top offenders over time: `SELECT calls, round(mean_exec_time) AS avg_ms, left(query,80) FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;` then `EXPLAIN (ANALYZE, BUFFERS)` the worst one. Cancel gently first (`pg_cancel_backend(pid)`), terminate only if that fails.

## Password / secret rotation
1. Generate new passwords (password manager), update `.env` (never commit it).
2. `./scripts/init_db.sh` re-applies `ALTER ROLE ... PASSWORD` for all application roles. For docker: also `docker compose up -d` so that exporter/Grafana pick up the new values.
3. Rotate `BACKUP_PASSPHRASE` only after re-encrypting or keeping the old one for old backups. **Losing it makes encrypted backups unreadable.**
4. Verify with `./tests/test_security.sh` and a manual `make backup`.

## Onboarding a new ad network
1. Insert into `core.ad_networks (network_id, code, name, currency)`.
2. Add a `NetworkConfig` in `guard/config.py` (delimiter, encoding, date format, decimal separator, column names).
3. Add a unit test in `tests/test_parsing.py` with a real sample row.
4. Add the network to `generator/generate_data.py` if you want test data; add it to the freshness check (automatic via `NETWORKS`).
5. Update `docs/architecture.md`.
