"""GUARD console: a small, read-only web UI over the `reporting` schema.

Connects as the least-privileged analyst role, so even a bug here cannot read personal data or change anything.
"""
import hmac
import os
from datetime import datetime

import psycopg2
from flask import Flask, Response, jsonify, render_template, request
from psycopg2.extras import RealDictCursor

from .. import __version__
from ..env import load_env
from . import charts
from .health import run_checks


def _conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"), port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "guard"), user=os.getenv("CONSOLE_DB_USER", "guard_analyst"),
        password=os.environ["ANALYST_PASSWORD"], application_name="guard-console", connect_timeout=5)


def q(sql, params=None):
    with _conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def create_app() -> Flask:
    load_env()
    app = Flask(__name__)

    # --- optional HTTP basic auth (set both variables). Without it, bind to localhost only.
    user, pwd = os.getenv("CONSOLE_AUTH_USER"), os.getenv("CONSOLE_AUTH_PASSWORD")

    @app.before_request
    def _auth():
        if not (user and pwd) or request.path == "/healthz":
            return None
        a = request.authorization
        if a and hmac.compare_digest(a.username or "", user) and hmac.compare_digest(a.password or "", pwd):
            return None
        return Response("Authentication required", 401, {"WWW-Authenticate": 'Basic realm="GUARD"'})

    @app.template_filter("num")
    def _num(v):
        return f"{float(v or 0):,.0f}".replace(",", " ")

    @app.template_filter("money")
    def _money(v):
        return f"{float(v or 0):,.0f}".replace(",", " ") + " PLN"

    @app.template_filter("pct")
    def _pct(v, d=1):
        return "-" if v is None else f"{float(v):.{d}f}%"

    @app.template_filter("dt")
    def _dt(v):
        return v.strftime("%Y-%m-%d %H:%M") if isinstance(v, datetime) else (v or "")

    @app.context_processor
    def _ctx():
        return {"version": __version__, "path": request.path}

    @app.get("/")
    def overview():
        k = q("""SELECT count(*) FILTER (WHERE status IN ('success','partial')) AS files,
                        coalesce(sum(rows_read)     FILTER (WHERE status IN ('success','partial')),0) AS rows_read,
                        coalesce(sum(rows_loaded)   FILTER (WHERE status IN ('success','partial')),0) AS rows_loaded,
                        coalesce(sum(rows_rejected) FILTER (WHERE status IN ('success','partial')),0) AS rows_rejected,
                        count(*) FILTER (WHERE status='failed') AS failed
                 FROM reporting.pipeline_runs""")[0]
        k["reject_pct"] = 100.0 * k["rows_rejected"] / k["rows_read"] if k["rows_read"] else None
        days = list(reversed(q("""SELECT report_date, sum(spend_pln) AS spend FROM reporting.daily_by_brand
                                  GROUP BY 1 ORDER BY 1 DESC LIMIT 30""")))
        reasons = q("SELECT reason, sum(rows) AS rows FROM reporting.reject_reasons GROUP BY 1 ORDER BY 2 DESC")
        networks = q("SELECT network, sum(spend_pln) AS spend FROM reporting.daily_by_network GROUP BY 1 ORDER BY 2 DESC")
        top = q("""SELECT campaign_code, advertiser, spend_pln, budget_pln, budget_used_pct
                   FROM reporting.campaign_summary WHERE spend_pln > 0 ORDER BY spend_pln DESC LIMIT 5""")
        return render_template(
            "overview.html", k=k, top=top,
            spend_chart=charts.bar_chart([d["report_date"].strftime("%d %b") for d in days], [d["spend"] for d in days]),
            reasons_chart=charts.hbar([(r["reason"], r["rows"]) for r in reasons], color=None),
            network_chart=charts.hbar([(n["network"], n["spend"]) for n in networks]))

    @app.get("/runs")
    def runs():
        status = request.args.get("status") or None
        rows = q("""SELECT * FROM reporting.pipeline_runs WHERE (%(s)s::text IS NULL OR status = %(s)s)
                    ORDER BY log_id DESC LIMIT 100""", {"s": status})
        return render_template("runs.html", rows=rows, status=status)

    @app.get("/rejects")
    def rejects():
        reason = request.args.get("reason") or None
        summary = q("SELECT reason, sum(rows) AS rows FROM reporting.reject_reasons GROUP BY 1 ORDER BY 2 DESC")
        rows = q("""SELECT file_name, line_no, reason, raw_line FROM reporting.recent_rejects
                    WHERE (%(r)s::text IS NULL OR reason = %(r)s) ORDER BY reject_id DESC LIMIT 100""", {"r": reason})
        return render_template("rejects.html", rows=rows, summary=summary, reason=reason)

    @app.get("/campaigns")
    def campaigns():
        status = request.args.get("status") or None
        rows = q("""SELECT * FROM reporting.campaign_summary WHERE (%(s)s::text IS NULL OR status = %(s)s)
                    ORDER BY spend_pln DESC, campaign_code""", {"s": status})
        return render_template("campaigns.html", rows=rows, status=status)

    @app.get("/status")
    def status():
        checks = run_checks(q)
        worst = "CRIT" if any(c["level"] == "CRIT" for c in checks) else "WARN" if any(c["level"] == "WARN" for c in checks) else "OK"
        return render_template("status.html", checks=checks, worst=worst)

    @app.get("/healthz")
    def healthz():
        try:
            q("SELECT 1")
            return jsonify(status="ok", version=__version__)
        except Exception:                          # noqa: BLE001
            return jsonify(status="database unreachable", version=__version__), 503

    return app
