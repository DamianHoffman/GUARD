#!/usr/bin/env python3
"""
Fake data generator for the GUARD platform. All data is synthetic (Faker).

  python generator/generate_data.py dimensions                 # advertisers, campaigns, placements -> data/seed
  python generator/generate_data.py backfill --days 30         # daily network files -> data/inbox
  python generator/generate_data.py daily --date 2026-01-31    # a single day
  python generator/generate_data.py daily --date 2026-01-31 --inject schema_drift --network mediabuy

Network files are deliberately MESSY (like real ones): different delimiters, encodings,
date formats, decimal separators, currencies, duplicates, missing values, unknown ids.
"""
import argparse
import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT / "data" / "seed"
INBOX_DIR = ROOT / "data" / "inbox"

BRANDS = {1: "Wyborcza.pl", 2: "Gazeta.pl", 3: "TOK FM", 4: "Radio ZET"}
FORMATS = {
    1: ["Homepage Billboard", "Article Sidebar", "Paywall Banner", "Newsletter Sponsor"],
    2: ["Homepage Billboard", "Video Pre-roll", "Mobile Interstitial", "Sport Section Banner"],
    3: ["Podcast Pre-roll", "Podcast Mid-roll", "Live Stream Spot"],
    4: ["Morning Show Spot", "Drive Time Spot", "Website Banner"],
}
TOPICS = ["Spring Sale", "Back to School", "Black Friday", "Brand Awareness", "Summer Tour",
          "Product Launch", "Holiday Special", "Loyalty Program", "Mobile App Install", "Election Special"]

# per-network: probability that a given campaign runs on it, price (CPM) in network currency
NETWORKS = {
    "adserve":  {"p": 0.55, "cpm": (8, 22),  "cur": "PLN"},
    "mediabuy": {"p": 0.45, "cpm": (6, 18),  "cur": "PLN"},
    "euroads":  {"p": 0.35, "cpm": (2, 6),   "cur": "EUR"},
}


def placement_names():
    out, pid = [], 1
    for bid, fmts in FORMATS.items():
        for f in fmts:
            out.append((pid, bid, f"{BRANDS[bid]} - {f}", f))
            pid += 1
    return out


def write_dimensions(seed: int, n_adv: int, n_camp: int, today: date):
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(seed)
    fake = Faker("pl_PL")
    Faker.seed(seed)

    with open(SEED_DIR / "advertisers.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["advertiser_id", "company_name", "contact_person", "contact_email", "contact_phone", "nip"])
        for i in range(1, n_adv + 1):
            person = fake.name()
            company = fake.company()
            email = f"{fake.user_name()}{i}@{fake.free_email_domain()}"
            w.writerow([i, company, person, email, fake.phone_number(), "".join(str(rnd.randint(0, 9)) for _ in range(10))])

    with open(SEED_DIR / "placements.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["placement_id", "brand_id", "name", "format"])
        w.writerows(placement_names())

    with open(SEED_DIR / "campaigns.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["campaign_id", "campaign_code", "advertiser_id", "name", "start_date", "end_date", "budget_pln", "status"])
        for i in range(1, n_camp + 1):
            start = today - timedelta(days=rnd.randint(5, 75))
            end = start + timedelta(days=rnd.randint(14, 70))
            if start > today:
                status = "draft"
            elif end < today:
                status = "finished"
            else:
                status = rnd.choices(["active", "paused"], [0.9, 0.1])[0]
            w.writerow([i, f"CMP-{i:05d}", rnd.randint(1, n_adv), f"{rnd.choice(TOPICS)} {start.year}",
                        start, end, round(rnd.uniform(8_000, 250_000), 2), status])
    print(f"Dimensions written to {SEED_DIR}")


def load_campaigns():
    with open(SEED_DIR / "campaigns.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["start_date"] = date.fromisoformat(r["start_date"])
        r["end_date"] = date.fromisoformat(r["end_date"])
    return rows


def messy_placement(name: str, rnd: random.Random) -> str:
    """Same placement, different spelling: what real networks do."""
    r = rnd.random()
    if r < 0.04:
        return name.upper()
    if r < 0.08:
        return "  " + name + " "
    if r < 0.11:
        return name.replace(" - ", "  -  ")
    if r < 0.13:
        return name.lower()
    return name


def build_rows(day: date, network: str, campaigns, placements):
    cfg = NETWORKS[network]
    rnd = random.Random(f"{day.isoformat()}-{network}")
    rows = []
    for c in campaigns:
        if c["status"] == "draft" or not (c["start_date"] <= day <= c["end_date"]):
            continue
        if random.Random(f"{c['campaign_code']}-{network}").random() > cfg["p"]:
            continue
        for pl in rnd.sample(placements, rnd.randint(1, 3)):
            imps = int(rnd.uniform(1_000, 60_000))
            clicks = int(imps * rnd.uniform(0.003, 0.025))
            cost = imps / 1000 * rnd.uniform(*cfg["cpm"])
            rows.append({"campaign": c["campaign_code"], "placement": messy_placement(pl[2], rnd),
                         "imps": imps, "clicks": clicks, "cost": round(cost, 2), "date": day})
    # ---- inject data-quality problems (~4% of rows)
    n = len(rows)
    for r in rnd.sample(rows, k=min(n, max(1, int(n * 0.04)))) if n else []:
        kind = rnd.choice(["unknown_campaign", "missing_imps", "clicks_gt_imps", "negative_cost",
                           "bad_date", "wrong_day"])
        if kind == "unknown_campaign":
            r["campaign"] = "CMP-99999"
        elif kind == "missing_imps":
            r["imps"] = ""
        elif kind == "clicks_gt_imps":
            r["clicks"] = (r["imps"] or 1000) + 500
        elif kind == "negative_cost":
            r["cost"] = -abs(r["cost"])
        elif kind == "bad_date":
            r["date"] = "31-31-2026"
        elif kind == "wrong_day":
            r["date"] = day - timedelta(days=1)
    # exact duplicates (~1.5%)
    if rows:
        rows += [dict(r) for r in rnd.sample(rows, k=max(1, int(len(rows) * 0.015)))]
    rnd.shuffle(rows)
    return rows


def fmt_date(d, network):
    if isinstance(d, str):
        return d
    return {"adserve": d.strftime("%Y-%m-%d"), "mediabuy": d.strftime("%d.%m.%Y"),
            "euroads": d.strftime("%m/%d/%Y")}[network]


def write_network_file(day: date, network: str, campaigns, placements, inject=None):
    path = INBOX_DIR / f"{network}_{day.isoformat()}.csv"
    if inject == "missing_file":
        print(f"[inject] {network} {day}: file NOT written (missing file drill)")
        return None
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows(day, network, campaigns, placements)

    if network == "adserve":
        delim, enc, header = ",", "utf-8", ["date", "campaign_code", "placement", "impressions", "clicks", "cost_pln"]
    elif network == "mediabuy":
        delim, enc, header = ";", "cp1250", ["Data", "Kampania", "Miejsce reklamowe", "Wyswietlenia", "Klikniecia", "Koszt"]
    else:
        delim, enc, header = ",", "utf-8", ["day", "camp", "slot", "imps", "clk", "cost_eur"]

    if inject == "schema_drift":
        header[2] = header[2] + "_v2"   # the network silently renamed a column
    if inject == "empty_file":
        rows = []
        header = []

    with open(path, "w", newline="", encoding=enc) as f:
        w = csv.writer(f, delimiter=delim)
        if header:
            w.writerow(header)
        for r in rows:
            cost = r["cost"]
            if network == "mediabuy":
                cost = str(cost).replace(".", ",")
            w.writerow([fmt_date(r["date"], network), r["campaign"], r["placement"], r["imps"], r["clicks"], cost])
    print(f"wrote {path.name} ({len(rows)} rows){' [inject: ' + inject + ']' if inject else ''}")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dimensions"); d.add_argument("--seed", type=int, default=42)
    d.add_argument("--advertisers", type=int, default=40); d.add_argument("--campaigns", type=int, default=120)
    d.add_argument("--today", default=None, help="anchor date (default: today)")
    b = sub.add_parser("backfill"); b.add_argument("--days", type=int, default=30)
    s = sub.add_parser("daily"); s.add_argument("--date", required=True)
    for p in (s,):
        p.add_argument("--network", choices=list(NETWORKS), default=None)
        p.add_argument("--inject", choices=["missing_file", "schema_drift", "empty_file"], default=None)
    a = ap.parse_args()

    if a.cmd == "dimensions":
        today = date.fromisoformat(a.today) if a.today else date.today()
        write_dimensions(a.seed, a.advertisers, a.campaigns, today)
        return
    campaigns, placements = load_campaigns(), placement_names()
    if a.cmd == "backfill":
        yesterday = date.today() - timedelta(days=1)
        for i in range(a.days):
            day = yesterday - timedelta(days=a.days - 1 - i)
            for n in NETWORKS:
                write_network_file(day, n, campaigns, placements)
    else:
        day = date.fromisoformat(a.date)
        for n in ([a.network] if a.network else NETWORKS):
            write_network_file(day, n, campaigns, placements, a.inject)


if __name__ == "__main__":
    main()
