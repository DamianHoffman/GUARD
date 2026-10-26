# Weekly campaign report: Jan's notes (every Monday)

1. Log in to the 3 ad network portals (passwords in the shared Excel "hasla.xlsx" on the file server).
2. Download last week's CSV from each portal (3 networks x 7 days if the portal has no weekly export).
3. Open each file in Excel. MediaBuy opens with broken Polish characters: re-import as "Windows-1250".
4. MediaBuy uses commas for decimals, EuroAds uses dollars-style dates and EUR. Fix by hand / formulas.
5. Copy-paste everything into `master_2025_v7_FINAL (2).xlsx`.
6. VLOOKUP the campaign names, remove duplicates (Data > Remove duplicates), delete rows that look wrong.
7. Run `weekly_report.sh` on the server to get campaign list, paste next to the data.
8. Build pivot table, e-mail the Excel to sales. If numbers look weird, ask Jan.
