# Sensitive data and RODO/GDPR (what I did and why)

> Portfolio exercise with synthetic data. Not legal advice. A real company has a DPO (IOD) and legal review.

## 1. What is personal data here?

| Column | Class | Why |
|---|---|---|
| `core.advertisers.contact_person` | **Personal data** | Names a natural person |
| `core.advertisers.contact_email` | **Personal data** | Identifies a natural person |
| `core.advertisers.contact_phone` | **Personal data** | Identifies a natural person |
| `core.advertisers.nip` | Personal data for sole traders | Tax id can identify a person running a one-person business |
| `ops.audit_log.old_data/new_data` | **Contains copies of the above** | Easy to forget! Audit tables inherit the sensitivity |
| `core.daily_performance`, campaigns, placements | Business data (confidential, not personal) | |

Columns are tagged in the database with `COMMENT ON COLUMN ... 'PII'`, so the classification lives next to the data
(`\d+ core.advertisers`).

## 2. Controls implemented (mapped to RODO principles)

| RODO principle (art. 5) | Control in this repo |
|---|---|
| Data minimisation (minimalizacja) | Analysts and Grafana use `reporting.*` views; contact data only appears **masked** (`advertiser_contacts_masked`) |
| Integrity & confidentiality (integralność i poufność) | Least-privilege roles (`tests/test_security.sh` proves who can and cannot read PII); backups encrypted with GPG AES-256; services bound to `127.0.0.1`; secrets only in git-ignored `.env`; non-root ETL container |
| Accountability (rozliczalność) | `ops.audit_log` records who changed advertisers/campaigns, using `session_user` (the real login); all scripts and docs in Git |
| Storage limitation (ograniczenie przechowywania) | Backup retention (14 days by default, `BACKUP_RETENTION_DAYS`; PowerShell GFS rotation); a documented purge process is the next step (see below) |
| Privacy by design (art. 25) | Non-production copies are **pseudonymised** by `scripts/mask_nonprod.sql` (deterministic fake values, audit log truncated) |

## 3. Non-production data
Developers and testers never receive production personal data: `./scripts/make_nonprod_copy.sh` restores the latest
backup into `guard_nonprod` and masks it. Deterministic masking (`advertiser17@example.invalid`) keeps joins and
bug reports reproducible. Remember `example.invalid` cannot receive real e-mail.

## 4. What a real organisation would add
- **Right to erasure (art. 17) vs backups:** a deletion request is executed in the live DB immediately; backups age out under the
  retention policy; if a backup is ever restored, the erasure log must be re-applied. Keep an `erasure_requests` register.
- **Breach procedure:** notify the supervisory authority (UODO) within 72 h if there is a risk to individuals. Runbook step: who decides, who calls whom.
- **Access reviews:** `powershell/Get-DbAccessAudit.ps1` produces a CSV of who can read PII; review quarterly.
- **TLS** between client and database; disk encryption on the VM; MFA on the Azure account.
- **Data Processing Agreements** for any processor (e.g. cloud backup provider); data location in the EU (Azure Poland Central / West Europe).
- **Logging hygiene:** `log_min_duration_statement` can write query text with personal data into logs. Restrict log access.

## 5. Evidence
Run `./tests/test_security.sh` (12 checks) and attach the output to your README. Example excerpt:
```
PASS  analyst cannot read core.advertisers (PII)
PASS  etl cannot read PII
PASS  audit trigger recorded 2 changes by postgres
```
