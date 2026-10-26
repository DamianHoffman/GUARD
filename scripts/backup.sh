#!/usr/bin/env bash
# Logical backup of the whole database: custom format, optional GPG (AES256) encryption,
# checksum, retention cleanup, optional upload to Azure Blob Storage.
set -euo pipefail
source "$(dirname "$0")/lib.sh"
need pg_dump; need sha256sum
mkdir -p "$BACKUP_DIR"
exec >> >(tee -a "$LOG_DIR/backup.log") 2>&1

trap 'log "BACKUP FAILED (line $LINENO)"' ERR
ts="$(date +%Y%m%d_%H%M%S)"
out="$BACKUP_DIR/guard_${ts}.dump"
start=$SECONDS

log "backup started -> $out"
as_backup pg_dump --format=custom --compress=6 --dbname="$POSTGRES_DB" --file="$out"

if [ -n "${BACKUP_PASSPHRASE:-}" ]; then
  need gpg
  gpg --batch --yes --quiet --pinentry-mode loopback --symmetric --cipher-algo AES256 \
      --passphrase-fd 3 -o "$out.gpg" "$out" 3<<<"$BACKUP_PASSPHRASE"
  rm -f "$out"          # never leave the unencrypted dump on disk
  out="$out.gpg"
else
  log "WARNING: BACKUP_PASSPHRASE not set, backup is NOT encrypted"
fi

( cd "$BACKUP_DIR" && sha256sum "$(basename "$out")" > "$(basename "$out").sha256" )
size=$(du -h "$out" | cut -f1)
date -u +%FT%TZ > "$BACKUP_DIR/.last_success"
log "backup OK: $(basename "$out") ($size) in $((SECONDS-start))s"

if [ -n "${AZURE_STORAGE_ACCOUNT:-}" ]; then
  "$ROOT/scripts/azure_upload_backup.sh" "$out" || log "WARNING: Azure upload failed (local backup is fine)"
fi

# retention: delete local backups older than N days
find "$BACKUP_DIR" -maxdepth 1 -name 'guard_*' -type f -mtime +"$BACKUP_RETENTION_DAYS" -print -delete \
  | sed 's/^/retention: removed /' || true
