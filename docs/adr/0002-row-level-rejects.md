# 0002: Reject bad rows, fail bad files
**Status:** Accepted

**Context.** Ad networks send imperfect files. One faulty line should not block hundreds of good ones, but silently dropping or "fixing" data produces wrong invoices and reports.

**Decision.** Validate every row. Invalid rows go to `ops.etl_rejects` with a machine-readable reason and the raw line; valid rows load (file status `partial`). Problems that make the whole file untrustworthy (changed header, empty file, unknown network) fail the file, quarantine it in `data/rejected/` and raise an alert.

**Alternatives.** Fail the whole file on any error (blocks reporting for a single bad line); load everything and clean later (pollutes the fact table); auto-correct values (hides errors).

**Consequences.** Business users see partial but trustworthy data plus an explicit list of what is missing and why (see the support-ticket example). Reject-rate becomes a monitored data-quality signal.
