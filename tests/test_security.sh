#!/usr/bin/env bash
# Verifies least-privilege roles, masking views and the audit trigger against a live database.
set -uo pipefail
source "$(dirname "$0")/../scripts/lib.sh"
pass=0; failn=0
expect_ok()   { if "${@:2}" >/dev/null 2>&1; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1 (expected success)"; failn=$((failn+1)); fi; }
expect_deny() { if "${@:2}" >/dev/null 2>&1; then echo "FAIL  $1 (expected permission denied)"; failn=$((failn+1)); else echo "PASS  $1"; pass=$((pass+1)); fi; }
P() { psql -XAtq -v ON_ERROR_STOP=1 -d "$POSTGRES_DB" -c "$1"; }

expect_ok   "analyst can read reporting.campaign_summary"  as_analyst P "SELECT count(*) FROM reporting.campaign_summary"
expect_deny "analyst cannot read core.advertisers (PII)"   as_analyst P "SELECT contact_email FROM core.advertisers"
expect_deny "analyst cannot read ops.audit_log"            as_analyst P "SELECT * FROM ops.audit_log"
expect_deny "analyst cannot write facts"                   as_analyst P "DELETE FROM core.daily_performance"
expect_ok   "analyst sees masked contacts only"            as_analyst P "SELECT contact_email FROM reporting.advertiser_contacts_masked LIMIT 1"
expect_deny "etl cannot read PII"                          bash -c 'source scripts/lib.sh; PGUSER=guard_etl PGPASSWORD=$ETL_PASSWORD psql -XAtq -d $POSTGRES_DB -c "SELECT contact_email FROM core.advertisers"'
expect_deny "etl cannot drop tables"                       bash -c 'source scripts/lib.sh; PGUSER=guard_etl PGPASSWORD=$ETL_PASSWORD psql -XAtq -d $POSTGRES_DB -c "DROP TABLE core.campaigns"'
expect_ok   "backup role can read everything"              as_backup P "SELECT count(*) FROM core.advertisers"
expect_deny "backup role cannot write"                     as_backup P "UPDATE core.campaigns SET budget_pln = 1"
expect_ok   "monitor role can see ETL log"                 as_monitor P "SELECT count(*) FROM ops.etl_file_log"
expect_deny "monitor role cannot read PII"                 as_monitor P "SELECT contact_email FROM core.advertisers"

# audit trigger: change as admin, make sure it is recorded with the real login, then revert
before=$(as_admin P "SELECT count(*) FROM ops.audit_log")
as_admin P "UPDATE core.campaigns SET budget_pln = budget_pln + 1 WHERE campaign_id = 1" >/dev/null
as_admin P "UPDATE core.campaigns SET budget_pln = budget_pln - 1 WHERE campaign_id = 1" >/dev/null
after=$(as_admin P "SELECT count(*) FROM ops.audit_log")
who=$(as_admin P "SELECT changed_by FROM ops.audit_log ORDER BY audit_id DESC LIMIT 1")
if [ "$((after-before))" -eq 2 ] && [ "$who" = "$POSTGRES_USER" ]; then echo "PASS  audit trigger recorded 2 changes by $who"; pass=$((pass+1)); else echo "FAIL  audit trigger ($before -> $after, by '$who')"; failn=$((failn+1)); fi

echo "---- $pass passed, $failn failed"; [ "$failn" -eq 0 ]
