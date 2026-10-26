"""End-to-end ETL tests against a throw-away database (created and dropped by the tests themselves).

Needs a reachable PostgreSQL and admin credentials in the environment / .env (POSTGRES_PASSWORD etc.);
skipped automatically otherwise. The tests in this module build on each other and run in file order.
"""
import os
import subprocess
from datetime import date
from pathlib import Path

import psycopg2
import pytest

from guard import check_freshness, load_daily
from guard.env import ROOT, load_env

load_env()
TESTDB = "guard_itest"
NEEDED = ("POSTGRES_PASSWORD", "ETL_PASSWORD", "ANALYST_PASSWORD", "BACKUP_PASSWORD", "MONITOR_PASSWORD")


def _connect(dbname):
    return psycopg2.connect(host=os.getenv("DB_HOST", "localhost"), port=os.getenv("DB_PORT", "5432"), dbname=dbname,
                            user=os.getenv("POSTGRES_USER", "postgres"), password=os.environ["POSTGRES_PASSWORD"],
                            connect_timeout=5)


def _available():
    if not all(os.getenv(k) for k in NEEDED):
        return False
    try:
        _connect("postgres").close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _available(), reason="PostgreSQL with admin credentials not available")


@pytest.fixture(scope="module")
def db():
    admin = _connect("postgres")
    admin.autocommit = True
    with admin.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {TESTDB}")
        cur.execute(f"CREATE DATABASE {TESTDB}")
    subprocess.run([str(ROOT / "scripts" / "init_db.sh")], env={**os.environ, "POSTGRES_DB": TESTDB},
                   check=True, capture_output=True)
    conn = _connect(TESTDB)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("INSERT INTO core.advertisers VALUES (1,'Test Co','Jan Test','jan@example.invalid','+48 000 000 001','0000000001')")
        cur.execute("""INSERT INTO core.placements (placement_id, brand_id, name, format) VALUES
                       (1,1,'Wyborcza.pl - Homepage Billboard','Homepage Billboard'),
                       (2,4,'Radio ZET - Drive Time Spot','Drive Time Spot')""")
        cur.execute("""INSERT INTO core.campaigns VALUES
                       (1,'CMP-00001',1,'Spring Sale','2026-01-01','2026-12-31',10000,'active')""")
    mp = pytest.MonkeyPatch()
    mp.setenv("POSTGRES_DB", TESTDB)
    yield conn
    mp.undo()
    conn.close()
    with admin.cursor() as cur:
        cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()", (TESTDB,))
        cur.execute(f"DROP DATABASE IF EXISTS {TESTDB}")
    admin.close()


def q(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def run_load(tmp_path: Path, files: dict):
    inbox, done, bad = tmp_path / "inbox", tmp_path / "processed", tmp_path / "rejected"
    inbox.mkdir(exist_ok=True)
    for name, content in files.items():
        (inbox / name).write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    rc = load_daily.main(["--inbox", str(inbox), "--processed", str(done), "--rejected", str(bad)])
    return rc, done, bad


ADSERVE_HEADER = "date,campaign_code,placement,impressions,clicks,cost_pln\n"
ADSERVE_15 = ADSERVE_HEADER + "\n".join([
    "2026-01-15,CMP-00001,Wyborcza.pl - Homepage Billboard,1000,10,12.50",
    "2026-01-15,CMP-00001,  RADIO zet  -  drive time spot ,2000,20,25.00",   # messy spelling, same placement
    "2026-01-15,CMP-00001,Wyborcza.pl - Homepage Billboard,1000,10,12.50",   # duplicate
    "2026-01-15,CMP-00001,Radio ZET - Drive Time Spot,100,500,1.00",         # clicks > impressions
    "2026-01-15,CMP-99999,Wyborcza.pl - Homepage Billboard,1000,10,12.50",   # unknown campaign
]) + "\n"


def test_valid_rows_loaded_and_bad_rows_rejected_with_reasons(db, tmp_path):
    rc, done, _ = run_load(tmp_path, {"adserve_2026-01-15.csv": ADSERVE_15})
    assert rc == 0
    assert (done / "adserve_2026-01-15.csv").exists()
    assert q(db, "SELECT count(*) FROM core.daily_performance")[0][0] == 2
    log = q(db, "SELECT status, rows_read, rows_loaded, rows_rejected FROM ops.etl_file_log WHERE file_name='adserve_2026-01-15.csv'")
    assert log == [("partial", 5, 2, 3)]
    reasons = {r[0] for r in q(db, "SELECT reason FROM ops.etl_rejects")}
    assert reasons == {"duplicate_row", "clicks_gt_impressions", "unknown_campaign"}


def test_identical_file_is_skipped_and_nothing_is_duplicated(db, tmp_path):
    rc, _, _ = run_load(tmp_path, {"adserve_2026-01-15.csv": ADSERVE_15})
    assert rc == 0
    assert q(db, "SELECT count(*) FROM core.daily_performance")[0][0] == 2
    assert q(db, "SELECT count(*) FROM ops.etl_file_log WHERE status='skipped'")[0][0] == 1


def test_corrected_file_updates_existing_rows(db, tmp_path):
    corrected = ADSERVE_15.replace("1000,10,12.50\n2026-01-15,CMP-00001,  RADIO", "1500,10,12.50\n2026-01-15,CMP-00001,  RADIO", 1)
    rc, _, _ = run_load(tmp_path, {"adserve_2026-01-15.csv": corrected})
    assert rc == 0
    assert q(db, "SELECT count(*) FROM core.daily_performance")[0][0] == 2          # upsert, not insert
    assert q(db, "SELECT impressions FROM core.daily_performance WHERE placement_id=1")[0][0] == 1500


def test_eur_file_is_converted_to_pln(db, tmp_path):
    euroads = "day,camp,slot,imps,clk,cost_eur\n01/15/2026,CMP-00001,Wyborcza.pl - Homepage Billboard,1000,10,10.00\n"
    rc, _, _ = run_load(tmp_path, {"euroads_2026-01-15.csv": euroads})
    assert rc == 0
    spend = q(db, "SELECT spend_pln FROM core.daily_performance WHERE network_id=3")[0][0]
    assert float(spend) == 42.80                                                      # 10.00 EUR x 4.28


def test_windows1250_semicolon_decimal_comma_file(db, tmp_path):
    mediabuy = ("Data;Kampania;Miejsce reklamowe;Wyswietlenia;Klikniecia;Koszt\n"
                "15.01.2026;CMP-00001;Wyborcza.pl - Homepage Billboard;3000;30;36,40\n").encode("cp1250")
    rc, _, _ = run_load(tmp_path, {"mediabuy_2026-01-15.csv": mediabuy})
    assert rc == 0
    spend = q(db, "SELECT spend_pln FROM core.daily_performance WHERE network_id=2")[0][0]
    assert float(spend) == 36.40


def test_schema_drift_empty_and_unknown_network_fail_loudly(db, tmp_path):
    drift = ADSERVE_15.replace("placement,", "placement_v2,", 1)
    rc, _, bad = run_load(tmp_path, {
        "adserve_2026-01-16.csv": drift,
        "euroads_2026-01-16.csv": b"",
        "newnet_2026-01-16.csv": "a,b\n1,2\n",
        "mediabuy_2026-01-16.csv": "Data;Kampania;Miejsce reklamowe;Wyswietlenia;Klikniecia;Koszt\n".encode("cp1250"),
    })
    assert rc == 1                                                                    # non-zero exit for cron / alerting
    assert {p.name for p in bad.iterdir()} == {"adserve_2026-01-16.csv", "euroads_2026-01-16.csv",
                                               "newnet_2026-01-16.csv", "mediabuy_2026-01-16.csv"}
    msgs = dict(q(db, "SELECT file_name, message FROM ops.etl_file_log WHERE status='failed'"))
    assert "schema drift" in msgs["adserve_2026-01-16.csv"]
    assert "empty file" in msgs["euroads_2026-01-16.csv"]
    assert "unknown network" in msgs["newnet_2026-01-16.csv"]
    assert "no data rows" in msgs["mediabuy_2026-01-16.csv"]                          # header only is NOT "no spend"
    assert q(db, "SELECT count(*) FROM core.daily_performance WHERE report_date='2026-01-16'")[0][0] == 0


def test_freshness_check_reports_ok_missing_and_failed(db, capsys):
    assert check_freshness.main(["--date", "2026-01-15"]) == 0                        # all three networks delivered
    assert check_freshness.main(["--date", "2026-01-17"]) == 2                        # nothing delivered
    assert check_freshness.main(["--date", "2026-01-16"]) == 2                        # delivered but failed
    out = capsys.readouterr().out
    assert "not loaded" in out and "ETL FAILED" in out


def test_etl_role_cannot_read_personal_data(db):
    conn = psycopg2.connect(host=os.getenv("DB_HOST", "localhost"), port=os.getenv("DB_PORT", "5432"), dbname=TESTDB,
                            user="guard_etl", password=os.environ["ETL_PASSWORD"])
    with pytest.raises(psycopg2.errors.InsufficientPrivilege):
        with conn.cursor() as cur:
            cur.execute("SELECT contact_email FROM core.advertisers")
    conn.close()
