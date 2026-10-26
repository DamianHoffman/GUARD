#!/usr/bin/env bash
# Shared helpers: load .env, logging, connection defaults.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Load .env WITHOUT executing it and WITHOUT overriding variables that are already set in the environment
# (environment wins, like in CI, docker and the Python code).
load_env_file() {
  local file="$1" line key value
  [ -f "$file" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    case "$line" in ''|'#'*) continue ;; esac
    key="${line%%=*}"; value="${line#*=}"
    key="${key//[[:space:]]/}"
    case "$key" in ''|*[!A-Za-z0-9_]*|[0-9]*) continue ;; esac
    value="${value#\"}"; value="${value%\"}"; value="${value#\'}"; value="${value%\'}"
    if [ -z "${!key+x}" ]; then export "$key=$value"; fi
  done < "$file"
}
load_env_file "$ROOT/.env"

: "${POSTGRES_DB:=guard}" "${POSTGRES_USER:=postgres}" "${DB_HOST:=localhost}" "${DB_PORT:=5432}"
export PGHOST="$DB_HOST" PGPORT="$DB_PORT"

BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
case "$BACKUP_DIR" in /*) ;; *) BACKUP_DIR="$ROOT/${BACKUP_DIR#./}" ;; esac
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
LOG_DIR="$ROOT/logs"; mkdir -p "$LOG_DIR"

log() { printf '%s [%s] %s\n' "$(date '+%F %T')" "$(basename "${0:-script}")" "$*"; }
die() { log "ERROR: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"; }

# Run psql / other client tools as a specific role. Passwords come from .env, never from the command line.
as_admin()   { PGUSER="$POSTGRES_USER" PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD not set}" "$@"; }
as_backup()  { PGUSER=guard_backup  PGPASSWORD="${BACKUP_PASSWORD:?BACKUP_PASSWORD not set}"   "$@"; }
as_monitor() { PGUSER=guard_monitor PGPASSWORD="${MONITOR_PASSWORD:?MONITOR_PASSWORD not set}" "$@"; }
as_analyst() { PGUSER=guard_analyst PGPASSWORD="${ANALYST_PASSWORD:?ANALYST_PASSWORD not set}" "$@"; }

latest_backup() { ls -1t "$BACKUP_DIR"/guard_*.dump "$BACKUP_DIR"/guard_*.dump.gpg 2>/dev/null | head -n1 || true; }

# Decrypt (if needed) to a temp file and print its path.
plain_dump_path() {
  local f="$1"
  case "$f" in
    *.gpg) need gpg
           local tmp; tmp="$(mktemp --suffix=.dump)"
           gpg --batch --quiet --pinentry-mode loopback --passphrase-fd 3 -d -o "$tmp" --yes "$f" 3<<<"${BACKUP_PASSPHRASE:?BACKUP_PASSPHRASE needed to decrypt}" \
             || die "decryption failed"
           echo "$tmp" ;;
    *) echo "$f" ;;
  esac
}
