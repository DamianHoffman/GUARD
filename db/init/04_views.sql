-- Business-facing views. Analysts get access to THIS schema only.
CREATE OR REPLACE VIEW reporting.campaign_summary AS
SELECT c.campaign_code,
       c.name                      AS campaign_name,
       a.company_name              AS advertiser,
       c.status,
       c.start_date, c.end_date,
       c.budget_pln,
       COALESCE(SUM(p.spend_pln),0)                         AS spend_pln,
       COALESCE(SUM(p.impressions),0)                       AS impressions,
       COALESCE(SUM(p.clicks),0)                            AS clicks,
       ROUND(100.0 * SUM(p.clicks) / NULLIF(SUM(p.impressions),0), 3)  AS ctr_pct,
       ROUND(SUM(p.spend_pln) / NULLIF(SUM(p.clicks),0), 2)            AS cpc_pln,
       ROUND(100.0 * COALESCE(SUM(p.spend_pln),0) / c.budget_pln, 1)   AS budget_used_pct,
       MAX(p.report_date)                                   AS last_data_date
FROM core.campaigns c
JOIN core.advertisers a USING (advertiser_id)
LEFT JOIN core.daily_performance p USING (campaign_id)
GROUP BY c.campaign_id, c.campaign_code, c.name, a.company_name, c.status, c.start_date, c.end_date, c.budget_pln;

CREATE OR REPLACE VIEW reporting.daily_by_brand AS
SELECT p.report_date, b.name AS brand,
       SUM(p.impressions) AS impressions, SUM(p.clicks) AS clicks, SUM(p.spend_pln) AS spend_pln
FROM core.daily_performance p
JOIN core.placements pl USING (placement_id)
JOIN core.brands b USING (brand_id)
GROUP BY p.report_date, b.name;

CREATE OR REPLACE VIEW reporting.daily_by_network AS
SELECT p.report_date, n.name AS network,
       SUM(p.impressions) AS impressions, SUM(p.clicks) AS clicks, SUM(p.spend_pln) AS spend_pln
FROM core.daily_performance p
JOIN core.ad_networks n USING (network_id)
GROUP BY p.report_date, n.name;

-- Data-quality view: what did the ETL load or reject per day and network?
CREATE OR REPLACE VIEW reporting.etl_quality AS
SELECT started_at::date AS run_date, network_code, file_name, status,
       rows_read, rows_loaded, rows_rejected, message
FROM ops.etl_file_log
WHERE status <> 'running';

CREATE OR REPLACE VIEW reporting.reject_reasons AS
SELECT l.network_code, r.reason, count(*) AS rows
FROM ops.etl_rejects r JOIN ops.etl_file_log l USING (log_id)
GROUP BY l.network_code, r.reason;

-- Masked contact list for sales people who need "who do I call", not full PII.
CREATE OR REPLACE VIEW reporting.advertiser_contacts_masked AS
SELECT advertiser_id, company_name,
       left(contact_person, 1) || '***'                               AS contact_person,
       left(contact_email, 2) || '***@' || split_part(contact_email,'@',2) AS contact_email,
       '*** *** ' || right(contact_phone, 3)                          AS contact_phone
FROM core.advertisers;

-- Pipeline run history and recent rejected lines (used by the web console)
CREATE OR REPLACE VIEW reporting.pipeline_runs AS
SELECT log_id, file_name, network_code, status, rows_read, rows_loaded, rows_rejected,
       started_at, finished_at, message
FROM ops.etl_file_log WHERE status <> 'running';

CREATE OR REPLACE VIEW reporting.recent_rejects AS
SELECT r.reject_id, l.file_name, l.network_code, r.line_no, r.reason, r.raw_line, r.created_at
FROM ops.etl_rejects r JOIN ops.etl_file_log l USING (log_id);
