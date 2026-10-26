# Architecture decision records

Short records of the significant decisions, the alternatives considered and the consequences.

| # | Decision | Status |
|---|---|---|
| [0001](0001-postgresql.md) | PostgreSQL as the system of record | Accepted |
| [0002](0002-row-level-rejects.md) | Reject bad rows, fail bad files | Accepted |
| [0003](0003-idempotent-loads.md) | Idempotent loads: content hash + upsert | Accepted |
| [0004](0004-least-privilege-and-reporting-schema.md) | Least-privilege roles; `reporting` schema as the only business interface | Accepted |
| [0005](0005-logical-encrypted-backups.md) | Encrypted logical backups now, WAL/PITR later | Accepted |
| [0006](0006-python-etl-pentaho-alternative.md) | Python ETL as the reference implementation, Pentaho as documented alternative | Accepted |
