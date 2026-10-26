# Roadmap

Planned improvements, roughly in order of value. Nothing here is promised; it documents where the design would go next.

| Item | Why |
|---|---|
| WAL archiving and point-in-time recovery (`pg_basebackup` + archived WAL) | Reduces data-loss window (RPO) from 24 h to minutes |
| Alertmanager with e-mail/Teams delivery | Alerts are currently visible in Prometheus only |
| Secrets in Azure Key Vault instead of `.env` | Central rotation and audit of secrets |
| Table partitioning of `core.daily_performance` by month; `COPY`-based bulk loads | Scale from thousands to hundreds of millions of rows |
| Infrastructure as code (Ansible for the VM, Terraform for Azure resources) | Reproducible environments |
| Console authentication via OIDC (Entra ID) instead of basic auth | Proper SSO and per-user audit |
| Rejected-row workflow: export a corrected-file request per network | Closes the loop with ad-network contacts |
| Pentaho PDI implementation of one network, with comparison write-up | Alternative tooling |
