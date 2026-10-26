#!/usr/bin/env bash
# Nagios-style health check. Exit 0 = OK, 1 = WARN, 2 = CRIT. Run from cron every few minutes.
set -uo pipefail
source "$(dirname "$0")/lib.sh"
worst=0
report() { # level message
  case "$1" in OK) ;; WARN) [ $worst -lt 1 ] && worst=1 ;; CRIT) worst=2 ;; esac
  printf '%-5s %s\n' "$1" "$2"
}
Q() { as_monitor psql -XAtq -d "$POSTGRES_DB" -c "$1" 2>/dev/null; }

# 1. is the database up?
if as_monitor pg_isready -q -d "$POSTGRES_DB"; then report OK "database accepts connections"
else report CRIT "database is NOT accepting connections"; exit 2; fi

# 1b. can we actually log in and query? (pg_isready does not check credentials)
if [ "$(Q 'SELECT 1')" != "1" ]; then
  report CRIT "cannot run queries as guard_monitor (wrong password or missing permissions?)"; exit 2
fi

# 2. disk space (backup volume + root)
for path in "$BACKUP_DIR" /; do
  [ -d "$path" ] || continue
  used=$(df --output=pcent "$path" | tail -1 | tr -dc '0-9')
  if   [ "$used" -ge 90 ]; then report CRIT "disk $path ${used}% used"
  elif [ "$used" -ge 80 ]; then report WARN "disk $path ${used}% used"
  else report OK "disk $path ${used}% used"; fi
done

# 3. connections vs max_connections
read -r conns maxc < <(Q "SELECT count(*), current_setting('max_connections')::int FROM pg_stat_activity" | tr '|' ' ')
pct=$(( 100 * conns / maxc ))
if   [ "$pct" -ge 90 ]; then report CRIT "connections ${conns}/${maxc} (${pct}%)"
elif [ "$pct" -ge 75 ]; then report WARN "connections ${conns}/${maxc} (${pct}%)"
else report OK "connections ${conns}/${maxc} (${pct}%)"; fi

# 4. long-running queries (> 5 min) and idle-in-transaction sessions
long=$(Q "SELECT count(*) FROM pg_stat_activity WHERE state='active' AND now()-query_start > interval '5 minutes' AND pid<>pg_backend_pid()")
[ "${long:-0}" -gt 0 ] && report WARN "$long query(ies) running > 5 min" || report OK "no long-running queries"
idle=$(Q "SELECT count(*) FROM pg_stat_activity WHERE state='idle in transaction' AND now()-state_change > interval '10 minutes'")
[ "${idle:-0}" -gt 0 ] && report WARN "$idle session(s) idle in transaction > 10 min" || report OK "no stuck transactions"

# 5. database size
report OK "database size: $(Q "SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB'))")"

# 6. last backup age
if [ -f "$BACKUP_DIR/.last_success" ]; then
  age_h=$(( ( $(date +%s) - $(date -d "$(cat "$BACKUP_DIR/.last_success")" +%s) ) / 3600 ))
  if   [ "$age_h" -ge 48 ]; then report CRIT "last successful backup ${age_h}h ago"
  elif [ "$age_h" -ge 26 ]; then report WARN "last successful backup ${age_h}h ago"
  else report OK "last successful backup ${age_h}h ago"; fi
else report CRIT "no successful backup recorded"; fi

# 7. ETL: any failed file in the last 24h?
failed=$(Q "SELECT count(*) FROM ops.etl_file_log WHERE status='failed' AND started_at > now() - interval '24 hours'")
[ "${failed:-0}" -gt 0 ] && report CRIT "$failed ETL file(s) FAILED in last 24h (see ops.etl_file_log)" || report OK "no failed ETL files in last 24h"

# 8. ETL runs stuck in 'running' for > 1h (process was killed / server rebooted mid-load)
stuck=$(Q "SELECT count(*) FROM ops.etl_file_log WHERE status='running' AND started_at < now() - interval '1 hour'")
[ "${stuck:-0}" -gt 0 ] && report WARN "$stuck ETL run(s) stuck in 'running' > 1h (see runbook: ETL killed mid-run)" || report OK "no stuck ETL runs"

exit $worst
