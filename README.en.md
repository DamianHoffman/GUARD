<p align="center">
  <a href="docs/media/guard-demo.mp4"><img src="docs/media/guard-demo.gif" alt="GUARD in action: a 46-second film" width="100%"></a>
</p>
<p align="center"><sub>▶ Click for the full-quality film (MP4, 46 s)</sub></p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/brand/guard-logo-white.svg">
    <img src="docs/assets/brand/guard-logo-black.svg" alt="GUARD" width="320">
  </picture>
</p>
<p align="center"><b>Clean ad data in. Trusted reports out.</b> · <a href="README.md">Polski</a></p>

---

## What is it?

Ad networks send daily files with campaign results, each in a different format and with mistakes.
GUARD **validates the files, loads the good rows into PostgreSQL, explains every rejected row, protects personal data,
backs everything up (and proves the backups restore) and monitors itself.** Business users get a read-only console.

> A **portfolio project** on synthetic data: it models the day-to-day work of a junior DevOps engineer
> (databases, Linux, automation, backups, data protection, supporting business users).

<p align="center"><img src="docs/images/problem-solution.png" alt="Without GUARD vs with GUARD" width="100%"></p>
<p align="center"><img src="docs/images/how-it-works.png" alt="Four steps: files, validation, database, reports" width="100%"></p>
<p align="center"><img src="docs/images/console-overview-card.png" alt="Read-only web console" width="100%"></p>

## Quick start

```bash
git clone https://github.com/<your-username>/guard.git && cd guard
make setup && $EDITOR .env    # install the `guard` command, set passwords (change them all)
make up                       # PostgreSQL, console, Grafana, Prometheus (Docker)
make demo                     # synthetic data: 30 days of messy files, loaded
make check                    # lint + 31 tests + 12 permission/security checks
```

Console: <http://localhost:8080>

## Highlights

- **Idempotent ETL** for three file formats (UTF-8 / Windows-1250, PLN / EUR, three date styles); every rejected row is kept with a reason.
- **Least-privilege roles**, masked reporting views, audit trigger, pseudonymised copies for developers (RODO / GDPR aware).
- **Encrypted backups** (GPG AES-256) with a weekly automated restore test.
- **Monitoring**: health check, Prometheus alert rules, Grafana, status page. **Runbook** for every alarm.
- **Case studies**: [legacy takeover audit](docs/legacy-audit.md), [before/after](docs/process-improvement.md), [support ticket](docs/user-support-ticket.md).

## What is verified (and what is not)

Verified by running it: database, roles, audit, ETL (8 end-to-end tests), backup/restore, health check, masking, console, PowerShell scripts (PowerShell 7.4 on Linux).
Validated with tools but not run: Docker Compose, Dockerfile, Prometheus rules, GitHub Actions workflows. Documented only: Azure, Pentaho.
Details in the [Polish README](README.md#co-jest-sprawdzone-a-co-nie) and in [`docs/`](docs/) (technical docs are in English).

[MIT license](LICENSE) · [Roadmap](ROADMAP.md) · [Changelog](CHANGELOG.md)
