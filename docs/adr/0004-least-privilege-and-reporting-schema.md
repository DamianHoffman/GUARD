# 0004: Least-privilege roles; `reporting` schema as the only business interface
**Status:** Accepted

**Context.** The database contains personal data (advertiser contacts). Different actors need very different access, and RODO requires data minimisation and accountability.

**Decision.** Four login roles with distinct duties (`guard_etl` writes facts, `guard_analyst` reads views, `guard_backup` reads everything, `guard_monitor` reads statistics and the ETL log). Business users and the web console only see the `reporting` schema, where contacts appear masked. A trigger records changes to dimension tables in `ops.audit_log` using `session_user`. `tests/test_security.sh` proves who can and cannot do what.

**Consequences.** A bug or compromise in the ETL or console cannot read or leak personal data. Schema changes to `core` need view maintenance. The audit log itself contains personal data and is restricted and masked in non-production copies.
