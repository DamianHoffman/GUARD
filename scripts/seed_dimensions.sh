#!/usr/bin/env bash
# Load advertisers, placements, campaigns from data/seed/*.csv (created by generator/generate_data.py dimensions)
set -euo pipefail
source "$(dirname "$0")/lib.sh"
need psql
[ -f "$ROOT/data/seed/campaigns.csv" ] || die "no seed data. Run: python generator/generate_data.py dimensions"
as_admin psql -v ON_ERROR_STOP=1 -q -d "$POSTGRES_DB" <<SQL
BEGIN;
TRUNCATE core.daily_performance, core.campaigns, core.placements, core.advertisers RESTART IDENTITY CASCADE;
\copy core.advertisers FROM '$ROOT/data/seed/advertisers.csv' CSV HEADER
\copy core.placements (placement_id, brand_id, name, format) FROM '$ROOT/data/seed/placements.csv' CSV HEADER
\copy core.campaigns FROM '$ROOT/data/seed/campaigns.csv' CSV HEADER
COMMIT;
SELECT 'advertisers' AS tbl, count(*) FROM core.advertisers
UNION ALL SELECT 'placements', count(*) FROM core.placements
UNION ALL SELECT 'campaigns', count(*) FROM core.campaigns;
SQL
