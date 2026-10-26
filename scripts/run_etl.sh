#!/usr/bin/env bash
# Cron entry point for the daily load (Python implementation).
set -euo pipefail
source "$(dirname "$0")/lib.sh"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python"; [ -x "$PY" ] || PY=python3
export POSTGRES_DB DB_HOST DB_PORT ETL_PASSWORD
log "ETL start"
"$PY" -m guard.load_daily "$@" 2>&1 | tee -a "$LOG_DIR/etl.log"
rc=${PIPESTATUS[0]}
log "ETL finished with exit code $rc"
exit "$rc"
