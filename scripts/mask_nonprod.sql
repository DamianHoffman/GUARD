-- Pseudonymisation for NON-production copies. Deterministic (same id -> same fake value) so
-- joins and bug reports stay reproducible, but the real person cannot be identified.
BEGIN;
ALTER TABLE core.advertisers DISABLE TRIGGER USER;      -- do not write PII copies into the audit log
UPDATE core.advertisers SET
    contact_person = 'Contact ' || advertiser_id,
    contact_email  = 'advertiser' || advertiser_id || '@example.invalid',
    contact_phone  = '+48 000 000 ' || lpad((advertiser_id % 1000)::text, 3, '0'),
    nip            = lpad(advertiser_id::text, 10, '0');
ALTER TABLE core.advertisers ENABLE TRIGGER USER;
TRUNCATE ops.audit_log;                                  -- audit log holds old/new PII values
COMMIT;
