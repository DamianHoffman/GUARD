-- =====================================================================
-- GUARD data platform: schema
--   core      business data (dimensions + daily ad performance facts)
--   ops       operational data (ETL log, rejected rows, audit log)
--   reporting views for business users (no direct access to personal data)
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS ops;
CREATE SCHEMA IF NOT EXISTS reporting;

CREATE TABLE core.brands (
    brand_id smallint PRIMARY KEY,
    name     text NOT NULL UNIQUE
);

CREATE TABLE core.ad_networks (
    network_id smallint PRIMARY KEY,
    code       text NOT NULL UNIQUE,      -- matches the file prefix, e.g. adserve_2026-01-31.csv
    name       text NOT NULL,
    currency   char(3) NOT NULL DEFAULT 'PLN'
);

CREATE TABLE core.fx_rates (
    currency    char(3) NOT NULL,
    valid_from  date    NOT NULL,
    rate_to_pln numeric(10,4) NOT NULL CHECK (rate_to_pln > 0),
    PRIMARY KEY (currency, valid_from)
);

CREATE TABLE core.advertisers (
    advertiser_id  int  PRIMARY KEY,
    company_name   text NOT NULL,
    contact_person text,      -- PERSONAL DATA
    contact_email  text,      -- PERSONAL DATA
    contact_phone  text,      -- PERSONAL DATA
    nip            text       -- company tax id (may identify a sole trader -> treat as personal)
);
COMMENT ON COLUMN core.advertisers.contact_person IS 'PII: personal data (RODO/GDPR)';
COMMENT ON COLUMN core.advertisers.contact_email  IS 'PII: personal data (RODO/GDPR)';
COMMENT ON COLUMN core.advertisers.contact_phone  IS 'PII: personal data (RODO/GDPR)';
COMMENT ON COLUMN core.advertisers.nip            IS 'PII-adjacent: may identify a sole trader';

CREATE TABLE core.campaigns (
    campaign_id   int  PRIMARY KEY,
    campaign_code text NOT NULL UNIQUE,                       -- what the ad networks send us
    advertiser_id int  NOT NULL REFERENCES core.advertisers,
    name          text NOT NULL,
    start_date    date NOT NULL,
    end_date      date NOT NULL,
    budget_pln    numeric(12,2) NOT NULL CHECK (budget_pln > 0),
    status        text NOT NULL CHECK (status IN ('draft','active','paused','finished')),
    CHECK (end_date >= start_date)
);

CREATE TABLE core.placements (
    placement_id  int PRIMARY KEY,
    brand_id      smallint NOT NULL REFERENCES core.brands,
    name          text NOT NULL,
    format        text NOT NULL,
    -- normalised name used to match messy names coming from ad networks
    placement_key text GENERATED ALWAYS AS (lower(btrim(regexp_replace(name, '\s+', ' ', 'g')))) STORED,
    UNIQUE (placement_key)
);

CREATE TABLE core.daily_performance (
    report_date  date NOT NULL,
    campaign_id  int  NOT NULL REFERENCES core.campaigns,
    placement_id int  NOT NULL REFERENCES core.placements,
    network_id   smallint NOT NULL REFERENCES core.ad_networks,
    impressions  bigint NOT NULL CHECK (impressions >= 0),
    clicks       bigint NOT NULL CHECK (clicks >= 0),
    spend_pln    numeric(12,2) NOT NULL CHECK (spend_pln >= 0),
    source_file  text NOT NULL,
    loaded_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (report_date, campaign_id, placement_id, network_id),
    CHECK (clicks <= impressions)
);
CREATE INDEX ix_daily_perf_campaign ON core.daily_performance (campaign_id, report_date);

-- ---------------- ops ----------------
CREATE TABLE ops.etl_file_log (
    log_id        bigserial PRIMARY KEY,
    file_name     text NOT NULL,
    file_sha256   text,
    network_code  text,
    status        text NOT NULL CHECK (status IN ('running','success','partial','failed','skipped')),
    rows_read     int  NOT NULL DEFAULT 0,
    rows_loaded   int  NOT NULL DEFAULT 0,
    rows_rejected int  NOT NULL DEFAULT 0,
    started_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz,
    message       text
);
-- the same file content must never be loaded twice (idempotent ETL)
CREATE UNIQUE INDEX ux_etl_file_sha ON ops.etl_file_log (file_sha256) WHERE status IN ('success','partial');
CREATE INDEX ix_etl_file_name ON ops.etl_file_log (file_name, started_at DESC);

CREATE TABLE ops.etl_rejects (
    reject_id  bigserial PRIMARY KEY,
    log_id     bigint NOT NULL REFERENCES ops.etl_file_log ON DELETE CASCADE,
    line_no    int,
    reason     text NOT NULL,
    raw_line   text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ops.audit_log (
    audit_id   bigserial PRIMARY KEY,
    table_name text NOT NULL,
    operation  text NOT NULL,
    row_pk     text,
    old_data   jsonb,
    new_data   jsonb,
    changed_by text NOT NULL,
    changed_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE ops.audit_log IS 'Contains personal data copies (old/new values). Restrict access, mask in non-prod.';
