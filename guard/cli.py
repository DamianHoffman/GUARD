"""`guard` command line interface: one entry point for day-to-day operations."""
import argparse
import subprocess
import sys

from . import __version__
from .env import ROOT, load_env


def _script(name: str, *args: str) -> int:
    return subprocess.call([str(ROOT / "scripts" / name), *args])


def main(argv=None) -> int:
    try:
        return _main(argv)
    except KeyError as exc:
        print(f"guard: missing configuration value {exc}. Copy .env.example to .env and fill it in.", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        import psycopg2
        if isinstance(exc, psycopg2.OperationalError):
            first = str(exc).strip().splitlines()[0]
            print(f"guard: cannot connect to the database: {first}", file=sys.stderr)
            return 2
        raise


def _main(argv=None) -> int:
    load_env()
    p = argparse.ArgumentParser(
        prog="guard",
        description="GUARD: clean ad data in, trusted reports out.",
        epilog="Run 'guard <command> --help' for details. Configuration is read from .env.")
    p.add_argument("--version", action="version", version=f"guard {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    sub.add_parser("load", help="load files from data/inbox into the database", add_help=False)
    sub.add_parser("check", help="verify every ad network delivered (and loaded) a day's file", add_help=False)
    sub.add_parser("health", help="run the health check (exit 0 OK, 1 WARN, 2 CRIT)")
    sub.add_parser("backup", help="create an encrypted, checksummed backup")
    sub.add_parser("restore-test", help="restore the newest backup into a temp database and verify it")
    sub.add_parser("mask-copy", help="create a pseudonymised copy of the database for non-production use")
    sub.add_parser("demo-data", help="generate synthetic data (dimensions | backfill | daily)", add_help=False)
    c = sub.add_parser("console", help="start the read-only web console")
    c.add_argument("--host", default="127.0.0.1")
    c.add_argument("--port", type=int, default=8080)

    args, rest = p.parse_known_args(argv)

    if args.cmd == "load":
        from .load_daily import main as load_main
        return load_main(rest)
    if args.cmd == "check":
        from .check_freshness import main as check_main
        return check_main(rest)
    if args.cmd == "health":
        return _script("healthcheck.sh")
    if args.cmd == "backup":
        return _script("backup.sh")
    if args.cmd == "restore-test":
        return _script("restore_test.sh")
    if args.cmd == "mask-copy":
        return _script("make_nonprod_copy.sh", *rest)
    if args.cmd == "demo-data":
        return subprocess.call([sys.executable, str(ROOT / "generator" / "generate_data.py"), *rest])
    if args.cmd == "console":
        from .console.app import create_app
        create_app().run(host=args.host, port=args.port)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
