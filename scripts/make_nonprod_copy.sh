#!/usr/bin/env bash
# Create a masked copy of production for developers/testers (no real personal data leaves prod).
set -euo pipefail
source "$(dirname "$0")/lib.sh"
need pg_restore; need psql
NONPROD="${1:-guard_nonprod}"
src="$(latest_backup)"; [ -n "$src" ] || die "no backup found"
dump="$(plain_dump_path "$src")"
trap '[ "$dump" != "$src" ] && rm -f "$dump"' EXIT
as_admin dropdb --if-exists "$NONPROD"; as_admin createdb "$NONPROD"
as_admin pg_restore --no-owner --no-privileges --exit-on-error --dbname="$NONPROD" "$dump"
as_admin psql -v ON_ERROR_STOP=1 -q -d "$NONPROD" -f "$ROOT/scripts/mask_nonprod.sql"
log "masked copy ready: database '$NONPROD'"
as_admin psql -XAt -d "$NONPROD" -c "SELECT advertiser_id, contact_person, contact_email, contact_phone FROM core.advertisers ORDER BY 1 LIMIT 3"
