#!/usr/bin/env bash
# Creates least-privilege roles. Runs automatically in docker (docker-entrypoint-initdb.d)
# and manually via scripts/init_db.sh. Passwords come from environment variables.
set -euo pipefail

PSQL=(psql -v ON_ERROR_STOP=1 -U "${PGUSER:-$POSTGRES_USER}" -d "${PGDATABASE:-$POSTGRES_DB}"
      -v etl_pw="${ETL_PASSWORD:?}" -v analyst_pw="${ANALYST_PASSWORD:?}"
      -v backup_pw="${BACKUP_PASSWORD:?}" -v monitor_pw="${MONITOR_PASSWORD:?}")

"${PSQL[@]}" <<'SQL'
-- idempotent role creation, then (re)set password
SELECT 'CREATE ROLE guard_etl     LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname='guard_etl')     \gexec
SELECT 'CREATE ROLE guard_analyst LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname='guard_analyst') \gexec
SELECT 'CREATE ROLE guard_backup  LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname='guard_backup')  \gexec
SELECT 'CREATE ROLE guard_monitor LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname='guard_monitor') \gexec
ALTER ROLE guard_etl     PASSWORD :'etl_pw';
ALTER ROLE guard_analyst PASSWORD :'analyst_pw';
ALTER ROLE guard_backup  PASSWORD :'backup_pw';
ALTER ROLE guard_monitor PASSWORD :'monitor_pw';

-- nobody gets anything by default
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA core, ops, reporting FROM PUBLIC;
SELECT format('GRANT CONNECT ON DATABASE %I TO guard_etl, guard_analyst, guard_backup, guard_monitor', current_database()) \gexec

-- ETL: read dimensions, write facts + its own log. Cannot touch PII or audit log.
GRANT USAGE ON SCHEMA core, ops TO guard_etl;
GRANT SELECT ON core.campaigns, core.placements, core.ad_networks, core.fx_rates TO guard_etl;
GRANT SELECT, INSERT, UPDATE ON core.daily_performance TO guard_etl;
GRANT SELECT, INSERT, UPDATE ON ops.etl_file_log TO guard_etl;
GRANT SELECT, INSERT ON ops.etl_rejects TO guard_etl;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA ops TO guard_etl;

-- Analyst: reporting views only. No access to core.advertisers (personal data).
GRANT USAGE ON SCHEMA reporting TO guard_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA reporting TO guard_analyst;

-- Backup: read everything (pg_dump), write nothing.
GRANT pg_read_all_data TO guard_backup;

-- Monitoring: pg_monitor (stats views) + read ETL log for health checks.
GRANT pg_monitor TO guard_monitor;
GRANT USAGE ON SCHEMA ops TO guard_monitor;
GRANT SELECT ON ops.etl_file_log TO guard_monitor;
SQL
echo "Roles configured."
