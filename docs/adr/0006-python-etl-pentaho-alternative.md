# 0006: Python ETL as the reference implementation, Pentaho as documented alternative
**Status:** Accepted

**Context.** Many organisations run ETL in graphical tools such as Pentaho Data Integration; others use code. The logic (parse, validate, convert, upsert, log) is the same either way.

**Decision.** Implement and test the ETL in Python (unit-testable, reviewable in Git, runs in CI). Document how the same flow maps to Pentaho steps (`docs/pentaho-guide.md`) and provide a `kitchen.sh` wrapper so either can be scheduled by cron.

**Consequences.** Fast feedback and automated tests for the reference implementation; a clear migration path to or from PDI. The Pentaho jobs themselves are not part of the tested code base.
