# Pentaho Data Integration (PDI / "Kettle"): build guide

> **Status:** guide only. The tested implementation in this repo is the Python ETL (`guard/`); Pentaho jobs are designed in a GUI (Spoon),
> so this document specifies what to build. Suggested scope: rebuild **one** network (AdServe) in Pentaho, load the same data, and compare results with the Python ETL.

## 1. Install (about 30 min)
1. Install Java 17 (`sudo apt install openjdk-17-jre`).
2. Download **Pentaho Data Integration Community Edition** (Hitachi Vantara; search "Pentaho Community Edition download"), unzip to e.g. `~/data-integration`.
3. Put the PostgreSQL JDBC driver jar (from jdbc.postgresql.org) into `~/data-integration/lib/`.
4. Start the GUI: `./spoon.sh`.

## 2. Transformation `pentaho/load_adserve.ktr`
Use **parameters** (Transformation settings -> Parameters): `INBOX`, `FILE_NAME`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. Create a DB connection `guard` that uses these as `${DB_HOST}` etc. (never hard-code the password).

| Step | PDI step | Settings | Python equivalent |
|---|---|---|---|
| 1 | **CSV file input** | File `${INBOX}/${FILE_NAME}`, delimiter `,`, encoding UTF-8, header row, all fields as String | `csv.DictReader` |
| 2 | **Select values / Data Type** | Trim strings, convert `impressions`, `clicks` -> Integer; `cost_pln` -> BigNumber; `date` -> Date `yyyy-MM-dd` | `parse_int / parse_decimal / parse_date` |
| 3 | **Filter rows** | `impressions >= 0 AND clicks >= 0 AND cost_pln >= 0 AND clicks <= impressions AND NOT NULL`; "false" hop -> step 8 | the `Reject` reasons |
| 4 | **Calculator / Modified JavaScript** | Normalise placement: lower-case + collapse spaces | `normalize_key` |
| 5 | **Database lookup** | `core.campaigns` by `campaign_code` -> `campaign_id`; "don't pass the row if lookup fails" | `unknown_campaign` |
| 6 | **Database lookup** | `core.placements` by `placement_key` -> `placement_id` | `unknown_placement` |
| 7 | **Table output** (or *Insert/Update*) | Target `core.daily_performance`; with *Insert/Update* key = date + campaign + placement + network (upsert) | `ON CONFLICT DO UPDATE` |
| 8 | **Table output** (rejects) | Target `ops.etl_rejects`; add a constant `reason` field before it. Use **Error handling** on step 5/7 for DB-level errors | `ops.etl_rejects` |

Tip: use the **Preview** button after each step: it is the fastest way to learn PDI and to debug.

## 3. Job `pentaho/daily_load.kjb`
`START` -> **File exists** (`${INBOX}/adserve_${REPORT_DATE}.csv`) -> **Transformation** `load_adserve.ktr` -> **Success**.
Failure hops: file missing / transformation error -> **Write to log** + (optional) **Mail** -> **Abort job**. A non-zero exit code is what cron/monitoring will see.

## 4. Run it from cron
```bash
export PDI_HOME=~/data-integration
./scripts/run_pentaho_job.sh                 # wraps kitchen.sh, passes DB params, writes logs/pentaho.log
```
Cron line (replace the Python line in `scripts/cron/guard.cron`):
`30 5 * * * cd /opt/guard && PDI_HOME=$HOME/data-integration ./scripts/run_pentaho_job.sh >> logs/cron.log 2>&1`

`kitchen.sh` exit codes: 0 = OK, 1 = errors during execution, 2 = unexpected error, 7 = job could not be loaded, 8 = error loading steps or plugins.

## 5. Compare with the Python ETL
Load the same day with Pentaho into a scratch schema and compare row counts and totals with the Python ETL. Capture the differences in
`docs/pentaho-vs-python.md`: what is easier in Pentaho (visual flow, built-in lookups, error hops), what is harder (XML diffs in Git, testing, parameter handling), and when to choose which.
Commit the `.ktr` / `.kjb` files (XML, Git handles them) and a screenshot of the transformation.

## Key concepts
- "PDI separates **transformations** (data flow, steps run in parallel) from **jobs** (control flow, run in sequence)."
- "Parameters and environment variables keep credentials out of the files."
- "I used error-handling hops so that bad rows end up in a reject table instead of stopping the load."
- "Kitchen runs jobs, Pan runs transformations: both are command-line, so cron can schedule them."
