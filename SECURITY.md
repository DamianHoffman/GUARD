# Security policy

GUARD is a portfolio project that runs on **synthetic data**. Still, security issues are taken seriously.

**Reporting:** open a private security advisory on GitHub (Security tab > Report a vulnerability) rather than a public issue.

**Scope notes**
- `legacy/` is intentionally insecure example material (it contains a fake password) and is out of scope.
- The web console is read-only and binds to `127.0.0.1` by default. For any other exposure put it behind a reverse proxy with TLS and set `CONSOLE_AUTH_USER` / `CONSOLE_AUTH_PASSWORD`.
- Default passwords in `.env.example` are placeholders that must be changed.
