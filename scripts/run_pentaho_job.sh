#!/usr/bin/env bash
# Cron entry point for the Pentaho (PDI) version of the same load. See docs/pentaho-guide.md.
# Requires PDI installed; set PDI_HOME (directory containing kitchen.sh).
set -euo pipefail
source "$(dirname "$0")/lib.sh"
: "${PDI_HOME:?set PDI_HOME to your data-integration directory}"
JOB="${1:-$ROOT/pentaho/daily_load.kjb}"
[ -f "$JOB" ] || die "job file not found: $JOB (build it first, see docs/pentaho-guide.md)"
log "Pentaho job start: $JOB"
"$PDI_HOME/kitchen.sh" -file="$JOB" -level=Basic \
   -param:DB_HOST="$DB_HOST" -param:DB_PORT="$DB_PORT" -param:DB_NAME="$POSTGRES_DB" \
   -param:DB_USER=guard_etl -param:DB_PASSWORD="${ETL_PASSWORD:?}" \
   -param:INBOX="$ROOT/data/inbox" >> "$LOG_DIR/pentaho.log" 2>&1
rc=$?
log "Pentaho job finished with exit code $rc (kitchen: 0 = OK, 1 = errors in job)"
exit $rc
