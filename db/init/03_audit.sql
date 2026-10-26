-- Generic audit trigger: who changed what, when. Uses session_user so the real
-- login is recorded even though the function is SECURITY DEFINER.
CREATE OR REPLACE FUNCTION ops.audit_trigger() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, ops AS $$
DECLARE
    pk_col text := TG_ARGV[0];
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO ops.audit_log (table_name, operation, row_pk, old_data, new_data, changed_by)
        VALUES (TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME, TG_OP, to_jsonb(NEW)->>pk_col, NULL, to_jsonb(NEW), session_user);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        IF to_jsonb(OLD) IS DISTINCT FROM to_jsonb(NEW) THEN
            INSERT INTO ops.audit_log (table_name, operation, row_pk, old_data, new_data, changed_by)
            VALUES (TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME, TG_OP, to_jsonb(NEW)->>pk_col, to_jsonb(OLD), to_jsonb(NEW), session_user);
        END IF;
        RETURN NEW;
    ELSE
        INSERT INTO ops.audit_log (table_name, operation, row_pk, old_data, new_data, changed_by)
        VALUES (TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME, TG_OP, to_jsonb(OLD)->>pk_col, to_jsonb(OLD), NULL, session_user);
        RETURN OLD;
    END IF;
END $$;

CREATE TRIGGER trg_audit_advertisers
    AFTER INSERT OR UPDATE OR DELETE ON core.advertisers
    FOR EACH ROW EXECUTE FUNCTION ops.audit_trigger('advertiser_id');

CREATE TRIGGER trg_audit_campaigns
    AFTER INSERT OR UPDATE OR DELETE ON core.campaigns
    FOR EACH ROW EXECUTE FUNCTION ops.audit_trigger('campaign_id');
