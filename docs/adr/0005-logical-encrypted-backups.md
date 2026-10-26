# 0005: Encrypted logical backups now, WAL/PITR later
**Status:** Accepted

**Context.** Backups contain personal data and must be restorable. Data volume is small; the recovery objective is "yesterday evening is acceptable" for this workload.

**Decision.** Nightly `pg_dump` (custom format), encrypted with GPG AES-256, checksummed, retention-managed, optionally copied to Azure Blob Storage. A weekly automated restore test proves the backup and measures recovery time.

**Alternatives.** Physical base backups with WAL archiving (point-in-time recovery, more moving parts); storage snapshots only (not portable, not verified).

**Consequences.** Simple and portable, restore time is measured, RPO is up to 24 h. The roadmap lists WAL archiving for a lower RPO. The encryption passphrase becomes a critical secret (loss makes backups unreadable); the runbook covers storage and rotation.
