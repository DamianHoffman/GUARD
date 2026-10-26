# Azure: off-site encrypted backups

> **Status:** documented but not verified end to end. Check each command against the current Azure CLI before relying on it.
> **Cost safety first:** create a budget alert *before* creating anything (step 0).

## 0. Budget alert (portal)
Cost Management + Billing -> Budgets -> Add: e.g. 5 PLN/month, alerts at 50% and 100%, e-mail you. Also use the free account's credit view.

## 1. Resources (Azure CLI, `az login` first)
```bash
RG=rg-guard-demo; LOC=polandcentral; SA=guardbackup$RANDOM   # storage account names: 3-24 lowercase letters/digits, globally unique
az group create -n $RG -l $LOC
az storage account create -n $SA -g $RG -l $LOC --sku Standard_LRS --kind StorageV2 \
    --min-tls-version TLS1_2 --allow-blob-public-access false
az storage container create --account-name $SA --name guard-backups --auth-mode login
# give YOURSELF data-plane permission (RBAC instead of storage keys)
SCOPE=$(az storage account show -n $SA -g $RG --query id -o tsv)
az role assignment create --assignee "$(az ad signed-in-user show --query id -o tsv)" \
    --role "Storage Blob Data Contributor" --scope "$SCOPE"
```
Put `AZURE_STORAGE_ACCOUNT=$SA` in `.env`. `scripts/backup.sh` then uploads each (already encrypted) backup via `scripts/azure_upload_backup.sh`.
Why RBAC + `--auth-mode login` and not an account key: keys give full access to everything and are secrets you would have to store.

## 2. Lifecycle policy: cheaper and automatic retention
`policy.json`:
```json
{"rules":[{"name":"age-out-backups","enabled":true,"type":"Lifecycle",
 "definition":{"filters":{"blobTypes":["blockBlob"],"prefixMatch":["guard-backups/guard_"]},
 "actions":{"baseBlob":{"tierToCool":{"daysAfterModificationGreaterThan":30},
                        "delete":{"daysAfterModificationGreaterThan":180}}}}}]}
```
```bash
az storage account management-policy create --account-name $SA -g $RG --policy @policy.json
```

## 3. Restore drill from Azure
```bash
az storage blob download --auth-mode login --account-name $SA -c guard-backups -n guard_XXXX.dump.gpg -f /tmp/x.gpg
```
Then follow `runbook.md#restore-from-backup`. Time it and write the number in your README.

## 4. Stretch goals (only if you have time)
- Azure Database for PostgreSQL Flexible Server (Burstable B1ms) instead of the local DB. **It costs money while running; stop or delete it after the demo.**
- Run the same Ubuntu VM in Azure (B1s) with the cron jobs; use a *managed identity* for blob access so no login is needed on the VM.
- Azure Monitor alert on storage account failures.

## 5. AZ-900 mapping
Resource groups/regions (1), storage redundancy LRS vs GRS (2), RBAC vs keys (3), Cost Management budgets (4), shared responsibility model (5): each of these concepts is exercised by the steps above.
