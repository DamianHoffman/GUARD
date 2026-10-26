# LEGACY SYSTEM: the "before" picture (DO NOT RUN, DO NOT COPY)

This folder simulates what you inherit when you "take over" an undocumented system. It is
intentionally bad. Every flaw is listed and fixed in [`docs/legacy-audit.md`](../docs/legacy-audit.md).

**The story:** until last month a colleague (Jan, now on another team) prepared the weekly advertising
report by hand. He left behind two scripts, a crontab and a few lines of notes. Nobody else knows how it works.

| File | What it is |
|---|---|
| `backup_old.sh` | Jan's "backup", run by cron at 03:00 |
| `weekly_report.sh` | Pulls numbers for the weekly Excel report |
| `crontab.txt` | The crontab found on the server |
| `manual_process.md` | The weekly manual routine (from Jan's notes) |
