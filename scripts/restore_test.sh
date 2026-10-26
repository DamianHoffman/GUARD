#!/usr/bin/env bash
# A backup you have never restored is not a backup.
# Restores the newest backup into a throw-away database, sanity-checks row counts, measures the time.
set -euo pipefail
source "$(dirname "$0")/lib.sh"
need pg_restore; need psql; need createdb; need dropdb
exec >> >(tee -a "$LOG_DIR/restore_test.log") 2>&1

TESTDB="guard_restore_test"
src="$(latest_backup)"; [ -n "$src" ] || die "no backup found in $BACKUP_DIR"
log "restore test started with $(basename "$src")"

if [ -f "$src.sha256" ]; then
  ( cd "$BACKUP_DIR" && sha256sum -c --quiet "$(basename "$src").sha256" ) || die "checksum mismatch: backup is corrupted"
  log "checksum OK"
fi

dump="$(plain_dump_path "$src")"
cleanup() { as_admin dropdb --if-exists "$TESTDB" || true; [ "$dump" != "$src" ] && rm -f "$dump"; }
trap cleanup EXIT

start=$SECONDS
as_admin dropdb --if-exists "$TESTDB"
as_admin createdb "$TESTDB"
as_admin pg_restore --no-owner --no-privileges --exit-on-error --dbname="$TESTDB" "$dump"
elapsed=$((SECONDS-start))

fail=0
for t in core.campaigns core.advertisers core.placements core.daily_performance; do
  restored=$(as_admin psql -XAtq -d "$TESTDB"        -c "SELECT count(*) FROM $t")
  source_n=$(as_admin psql -XAtq -d "$POSTGRES_DB"   -c "SELECT count(*) FROM $t")
  # the live DB may have received new rows since the backup: restored must be >0 and <= live
  if [ "$restored" -gt 0 ] && [ "$restored" -le "$source_n" ]; then
    log "  OK   $t: restored=$restored live=$source_n"
  else
    log "  FAIL $t: restored=$restored live=$source_n"; fail=1
  fi
done
[ "$fail" -eq 0 ] || die "restore test FAILED"
log "restore test PASSED in ${elapsed}s (this is your measured RTO for this data size)"
