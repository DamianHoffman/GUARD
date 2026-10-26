INSERT INTO core.brands (brand_id, name) VALUES
  (1,'Wyborcza.pl'), (2,'Gazeta.pl'), (3,'TOK FM'), (4,'Radio ZET');

INSERT INTO core.ad_networks (network_id, code, name, currency) VALUES
  (1,'adserve',  'AdServe PL',        'PLN'),
  (2,'mediabuy', 'MediaBuy Polska',   'PLN'),
  (3,'euroads',  'EuroAds Network',   'EUR');

INSERT INTO core.fx_rates (currency, valid_from, rate_to_pln) VALUES
  ('EUR', '2025-01-01', 4.2500),
  ('EUR', '2026-01-01', 4.2800);
