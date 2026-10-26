# Service levels and recovery targets

Design targets for operating GUARD as if it were a business-critical service. They tell the on-call person what "good" means
and drive the alert thresholds. Targets are measured with the tools in this repository.

| Objective | Target | How it is measured |
|---|---|---|
| **Data freshness** | Every network's file for day D is loaded by 08:00 on D+1 | `guard check` (cron 06:15) |
| **Load success** | No unexplained failed files; partial loads explained in `ops.etl_rejects` | `reporting.pipeline_runs`, `guard health` |
| **Data quality** | Rejected rows below 8% per week (warn), 15% (critical) | Console "System status", `reporting.reject_reasons` |
| **Backup success** | One verified backup every night; no gap above 26 h | `guard health` (backup age), `logs/backup.log` |
| **Recovery point (RPO)** | Up to 24 h of data (re-loadable from `data/processed` for facts) | Backup schedule |
| **Recovery time (RTO)** | Restore of the full database within 30 min at production volume | Weekly `guard restore-test`; the measured time is logged. Demo data restores in about 1 s, which is **not** representative: re-measure at realistic volume. |
| **Monitoring coverage** | DB up, disk, connections, long queries, stuck loads, backup age, failed files | `scripts/healthcheck.sh`, Prometheus rules |

Alert thresholds: disk 80% warn / 90% critical; connections 75% / 90%; backup age 26 h / 48 h; open transaction 10 min.
Response procedures for every alert are in the [runbook](runbook.md).
