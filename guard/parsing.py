"""Pure parsing/validation functions (no database) so they are easy to unit test."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .config import NetworkConfig


class Reject(Exception):
    """A single row is bad. `reason` is a short machine-readable code stored in ops.etl_rejects."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class ParsedRow:
    report_date: date
    campaign_code: str
    placement_key: str
    impressions: int
    clicks: int
    cost: Decimal          # in the network's own currency


def normalize_key(text: str) -> str:
    """'  Wyborcza.pl  -  HOMEPAGE billboard ' -> 'wyborcza.pl - homepage billboard'"""
    return " ".join(text.split()).lower()


def parse_int(value, field: str) -> int:
    v = (value or "").strip().replace("\u00a0", "")
    if v == "":
        raise Reject(f"missing_{field}")
    try:
        n = int(v)
    except ValueError:
        raise Reject(f"bad_number_{field}")
    if n < 0:
        raise Reject(f"negative_{field}")
    return n


def parse_decimal(value, field: str, decimal_sep: str) -> Decimal:
    v = (value or "").strip().replace("\u00a0", "")
    if v == "":
        raise Reject(f"missing_{field}")
    if decimal_sep == ",":
        v = v.replace(",", ".")
    try:
        d = Decimal(v)
    except InvalidOperation:
        raise Reject(f"bad_number_{field}")
    if not d.is_finite():
        raise Reject(f"bad_number_{field}")
    if d < 0:
        raise Reject(f"negative_{field}")
    return d


def parse_date(value, fmt: str) -> date:
    v = (value or "").strip()
    if v == "":
        raise Reject("missing_date")
    try:
        return datetime.strptime(v, fmt).date()
    except ValueError:
        raise Reject("bad_date")


def parse_row(raw: dict, cfg: NetworkConfig, expected_date: date | None = None) -> ParsedRow:
    if None in raw or any(raw.get(h) is None for h in cfg.columns.values()):
        raise Reject("column_count_mismatch")
    c = cfg.columns
    report_date = parse_date(raw[c["date"]], cfg.date_format)
    if expected_date and report_date != expected_date:
        raise Reject("date_mismatch")
    campaign = (raw[c["campaign"]] or "").strip().upper()
    if not campaign:
        raise Reject("missing_campaign")
    placement = (raw[c["placement"]] or "").strip()
    if not placement:
        raise Reject("missing_placement")
    impressions = parse_int(raw[c["impressions"]], "impressions")
    clicks = parse_int(raw[c["clicks"]], "clicks")
    cost = parse_decimal(raw[c["cost"]], "cost", cfg.decimal)
    if clicks > impressions:
        raise Reject("clicks_gt_impressions")
    return ParsedRow(report_date, campaign, normalize_key(placement), impressions, clicks, cost)
