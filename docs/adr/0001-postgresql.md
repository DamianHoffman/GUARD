# 0001: PostgreSQL as the system of record
**Status:** Accepted

**Context.** The workload is relational (campaigns, advertisers, daily facts) with strong integrity needs and moderate volume.
Typical enterprise estates mix PostgreSQL, SQL Server and others.

**Decision.** Use PostgreSQL 16.

**Alternatives.** SQL Server on Linux (licensing, heavier for a portfolio setup); MySQL/MariaDB (weaker constraint and role features for this design); a document store (the data is inherently relational).

**Consequences.** Rich constraints (`CHECK`, `FK`, generated columns), schemas and roles, `pg_dump`/WAL tooling and good observability (`pg_stat_*`). The concepts (schemas, roles, backups, indexes, execution plans) map directly to other relational systems.
