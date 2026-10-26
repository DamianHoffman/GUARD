"""Per-network file formats. Adding a new ad network = adding one entry here (and one row in core.ad_networks)."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class NetworkConfig:
    code: str
    delimiter: str
    encoding: str
    date_format: str
    decimal: str
    currency: str
    columns: dict = field(default_factory=dict)   # logical name -> header used by this network


NETWORKS = {
    "adserve": NetworkConfig(
        "adserve", ",", "utf-8-sig", "%Y-%m-%d", ".", "PLN",
        {"date": "date", "campaign": "campaign_code", "placement": "placement",
         "impressions": "impressions", "clicks": "clicks", "cost": "cost_pln"}),
    "mediabuy": NetworkConfig(
        "mediabuy", ";", "cp1250", "%d.%m.%Y", ",", "PLN",
        {"date": "Data", "campaign": "Kampania", "placement": "Miejsce reklamowe",
         "impressions": "Wyswietlenia", "clicks": "Klikniecia", "cost": "Koszt"}),
    "euroads": NetworkConfig(
        "euroads", ",", "utf-8-sig", "%m/%d/%Y", ".", "EUR",
        {"date": "day", "campaign": "camp", "placement": "slot",
         "impressions": "imps", "clicks": "clk", "cost": "cost_eur"}),
}
