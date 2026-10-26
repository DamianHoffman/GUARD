# Contributing

## Development setup
```bash
git clone https://github.com/<your-username>/guard.git && cd guard
make setup && $EDITOR .env        # python venv, editable install, config
make up                            # or use a native PostgreSQL, see README
make demo && make test && make security
```

## Ground rules
- Every change keeps `make test`, `make security` and `shellcheck scripts/*.sh tests/*.sh db/init/*.sh` green; CI runs the same.
- Database changes go into `db/init/*.sql` and must be idempotent where reasonable. Update the security tests if permissions change.
- A new ad network needs: a `NetworkConfig` in `guard/config.py`, a row in `core.ad_networks`, a parsing unit test with a real sample line.
- Operational behaviour changes need a runbook entry (`docs/runbook.md`); design changes need an ADR (`docs/adr/`).
- Never commit secrets, backups or real personal data. `.env` is git-ignored; use `.env.example` for new variables.

## Commit messages
Short imperative summary (`Add freshness check for missing files`), body explains *why* when it is not obvious.
