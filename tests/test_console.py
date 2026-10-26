"""Console smoke tests. Need a loaded database; skipped automatically when none is reachable."""
import os

import pytest

pytest.importorskip("flask")
from guard.console.app import create_app, q  # noqa: E402
from guard.env import load_env  # noqa: E402

load_env()


def _db_ready():
    try:
        return bool(os.getenv("ANALYST_PASSWORD")) and q("SELECT count(*) AS n FROM reporting.pipeline_runs")[0]["n"] >= 0
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _db_ready(), reason="database not available")


@pytest.fixture()
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


@pytest.mark.parametrize("path,text", [("/", "Overview"), ("/runs", "Pipeline runs"), ("/rejects", "Rejected rows"),
                                       ("/campaigns", "Campaigns"), ("/status", "System status")])
def test_pages_render(client, path, text):
    r = client.get(path)
    assert r.status_code == 200 and text in r.get_data(as_text=True)


def test_healthz(client):
    assert client.get("/healthz").get_json()["status"] == "ok"


def test_filters_do_not_break(client):
    assert client.get("/runs?status=failed").status_code == 200
    assert client.get("/rejects?reason=bad_date").status_code == 200
    assert client.get("/campaigns?status=active").status_code == 200


def test_sql_injection_in_filter_is_harmless(client):
    assert client.get("/runs?status=x';DROP TABLE core.campaigns;--").status_code == 200


def test_basic_auth_when_configured(monkeypatch):
    monkeypatch.setenv("CONSOLE_AUTH_USER", "ops")
    monkeypatch.setenv("CONSOLE_AUTH_PASSWORD", "secret")
    c = create_app().test_client()
    assert c.get("/").status_code == 401
    assert c.get("/healthz").status_code == 200
    import base64
    ok = {"Authorization": "Basic " + base64.b64encode(b"ops:secret").decode()}
    assert c.get("/", headers=ok).status_code == 200
