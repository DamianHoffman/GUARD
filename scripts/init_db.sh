#!/usr/bin/env bash
# Apply db/init/* to an existing PostgreSQL server (CI, native install, or docker if you skipped auto-init).
# In docker-compose the same files run automatically on first start.
set -euo pipefail
source "$(dirname "$0")/lib.sh"
need psql
export PGUSER="$POSTGRES_USER" PGPASSWORD="${POSTGRES_PASSWORD:?}" PGDATABASE="$POSTGRES_DB"
export ETL_PASSWORD ANALYST_PASSWORD BACKUP_PASSWORD MONITOR_PASSWORD
for f in "$ROOT"/db/init/*; do
  log "applying $(basename "$f")"
  case "$f" in
    *.sql) psql -v ON_ERROR_STOP=1 -q -f "$f" ;;
    *.sh)  bash "$f" ;;
  esac
done
log "database initialised"
