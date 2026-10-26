# 0003: Idempotent loads: content hash + upsert
**Status:** Accepted

**Context.** Jobs get re-run after crashes, files get re-delivered, corrected files replace earlier ones.

**Decision.** Fingerprint each file (SHA-256) and skip content that was already loaded; load each file in a single transaction; write facts with `INSERT ... ON CONFLICT DO UPDATE` on the natural key `(report_date, campaign, placement, network)`.

**Consequences.** Re-running is always safe; a corrected file updates earlier rows instead of duplicating them; after a crash a file is either fully loaded or not at all. Trade-off: re-loading identical content on purpose requires deleting its log row (documented in the runbook).
