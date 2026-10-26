from datetime import date
from decimal import Decimal

import pytest

from guard.config import NETWORKS
from guard.parsing import Reject, normalize_key, parse_row

ADSERVE, MEDIABUY, EUROADS = NETWORKS["adserve"], NETWORKS["mediabuy"], NETWORKS["euroads"]
D = date(2026, 1, 31)


def adserve_row(**kw):
    row = {"date": "2026-01-31", "campaign_code": "CMP-00001", "placement": "Wyborcza.pl - Homepage Billboard",
           "impressions": "1000", "clicks": "10", "cost_pln": "12.50"}
    row.update(kw)
    return row


def test_valid_adserve_row():
    p = parse_row(adserve_row(), ADSERVE, D)
    assert (p.campaign_code, p.impressions, p.clicks, p.cost) == ("CMP-00001", 1000, 10, Decimal("12.50"))


def test_mediabuy_polish_formats():
    raw = {"Data": "31.01.2026", "Kampania": "cmp-00001", "Miejsce reklamowe": "TOK FM - Podcast Pre-roll",
           "Wyswietlenia": "5000", "Klikniecia": "50", "Koszt": "36,40"}
    p = parse_row(raw, MEDIABUY, D)
    assert p.cost == Decimal("36.40") and p.campaign_code == "CMP-00001"


def test_euroads_us_date():
    raw = {"day": "01/31/2026", "camp": "CMP-00002", "slot": "Radio ZET - Drive Time Spot",
           "imps": "100", "clk": "1", "cost": "1.10"}
    raw["cost_eur"] = raw.pop("cost")
    assert parse_row(raw, EUROADS, D).report_date == D


@pytest.mark.parametrize("override,reason", [
    ({"impressions": ""}, "missing_impressions"),
    ({"impressions": "abc"}, "bad_number_impressions"),
    ({"clicks": "-3"}, "negative_clicks"),
    ({"cost_pln": "-1"}, "negative_cost"),
    ({"cost_pln": "NaN"}, "bad_number_cost"),
    ({"date": "31-31-2026"}, "bad_date"),
    ({"date": "2026-01-30"}, "date_mismatch"),
    ({"clicks": "2000"}, "clicks_gt_impressions"),
    ({"campaign_code": "  "}, "missing_campaign"),
])
def test_rejects(override, reason):
    with pytest.raises(Reject) as e:
        parse_row(adserve_row(**override), ADSERVE, D)
    assert e.value.reason == reason


def test_column_count_mismatch():
    bad = adserve_row()
    bad[None] = ["extra"]
    with pytest.raises(Reject) as e:
        parse_row(bad, ADSERVE, D)
    assert e.value.reason == "column_count_mismatch"


def test_normalize_key():
    assert normalize_key("  Wyborcza.pl  -  HOMEPAGE Billboard ") == "wyborcza.pl - homepage billboard"
