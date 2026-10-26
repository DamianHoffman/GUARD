#!/usr/bin/env bash
# Upload an (encrypted) backup to Azure Blob Storage. See docs/azure.md for one-time setup.
# Auth: `az login` (interactive) or a managed identity on an Azure VM. No storage keys in files.
set -euo pipefail
source "$(dirname "$0")/lib.sh"
need az
f="${1:?usage: azure_upload_backup.sh <file>}"
: "${AZURE_STORAGE_ACCOUNT:?}" ; container="${AZURE_STORAGE_CONTAINER:-guard-backups}"
az storage blob upload --auth-mode login --account-name "$AZURE_STORAGE_ACCOUNT" \
   --container-name "$container" --name "$(basename "$f")" --file "$f" --only-show-errors
[ -f "$f.sha256" ] && az storage blob upload --auth-mode login --account-name "$AZURE_STORAGE_ACCOUNT" \
   --container-name "$container" --name "$(basename "$f").sha256" --file "$f.sha256" --only-show-errors
log "uploaded $(basename "$f") to $AZURE_STORAGE_ACCOUNT/$container"
