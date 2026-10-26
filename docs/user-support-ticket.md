# User support example: "the numbers don't match"

> Worked example based on **real queries against the demo data** (generated 2026-10-18). Dates and random rows depend on
> when the data is generated, so values will differ in a fresh run; the method stays the same.
> It demonstrates the support workflow: reproduce, trace, quantify, explain in plain language, follow up.

---

## Ticket #1042
**From:** Anna K., Sales (advertising)  **Priority:** Normal  **Received:** Mon 09:12

> Hi, the weekly report for campaign **CMP-00036** shows fewer placements on **30 September** than the EuroAds
> portal. EuroAds shows 3 placements for that day, your report only 1. Which one is right? I'm sending the numbers to the client today.

## Investigation (what I did, in order)

1. **Reproduce.** Queried what the report shows for that campaign, day and network:
   ```sql
   SELECT n.code, pl.name, impressions, clicks, spend_pln
   FROM core.daily_performance p JOIN core.ad_networks n USING (network_id)
        JOIN core.placements pl USING (placement_id) JOIN core.campaigns c USING (campaign_id)
   WHERE c.campaign_code='CMP-00036' AND report_date='2026-09-30' AND n.code='euroads';
   ```
   -> 1 row (Gazeta.pl - Mobile Interstitial). Anna is right that we show fewer rows than the portal.
2. **Was the file loaded?** `SELECT * FROM ops.etl_file_log WHERE file_name='euroads_2026-09-30.csv';`
   -> status `partial`: 52 rows read, 49 loaded, **3 rejected**. So the file arrived and loaded, but not completely.
3. **Which rows were rejected?**
   ```sql
   SELECT r.reason, r.raw_line FROM ops.etl_rejects r JOIN ops.etl_file_log l USING (log_id)
   WHERE l.file_name='euroads_2026-09-30.csv' AND r.raw_line LIKE '%CMP-00036%';
   ```
   | reason | raw line |
   |---|---|
   | `bad_date` | `31-31-2026,CMP-00036,Radio ZET - Website Banner,32286,247,123.37` |
   | `clicks_gt_impressions` | `09/30/2026,CMP-00036,Gazeta.pl - Homepage Billboard,47012,47512,173.21` |
4. **Root cause:** two of the three EuroAds rows for this campaign were **invalid in the file EuroAds sent us**: one has an
   impossible date (`31-31-2026`), one reports more clicks (47,512) than impressions (47,012), which cannot be true.
   Our system correctly refused to load them instead of guessing. The portal probably shows them because it displays raw data without validation.
5. **Impact check:** missing from our report: 2 placements, 79,298 impressions and 296.58 EUR of spend (EuroAds bills in EUR; at the 4.28 rate in `core.fx_rates` that is about 1,269 PLN) on that one day. Campaign total spend is about 70,700 PLN, so this is roughly 1.8% of it.

## Reply to the user (plain language, no jargon)

> Hi Anna,
>
> Thanks for checking before sending to the client: that was the right call.
>
> **Short answer:** the EuroAds portal is showing 2 lines that we deliberately did not load, because the data EuroAds sent us for those lines is faulty.
> - *Radio ZET - Website Banner:* the file has an invalid date ("31-31-2026"), so we can't tell which day it belongs to.
> - *Gazeta.pl - Homepage Billboard:* the file reports 47,512 clicks but only 47,012 impressions. There can't be more clicks than impressions.
>
> Together that is about 79,000 impressions and roughly 1,270 PLN (297 EUR) for 30 September, so our total for this campaign is lower than the portal for that day.
>
> **What I suggest:** please don't send the 30 Sep figure for this campaign as final yet. I am asking EuroAds for a corrected file for 30 Sep.
> When it arrives I load it and the report updates automatically; I'll tell you the same day.
> If the client can't wait, you can send the figures with a note "30 Sep EuroAds, 2 lines pending correction (~1.8% of campaign spend)".
>
> I also added a monthly overview of rejected lines per network to my to-do list, so you see this kind of problem earlier.
>
> Best regards,
> Platform operations

## Follow-up actions
- [ ] Corrected file received -> `make etl` -> verify the 2 placements appear -> confirm to Anna and close the ticket.
- [ ] Add the network contact and a template e-mail ("please resend, here are the 2 faulty lines") to the runbook.
- [ ] Prevention: if rejected rows for one network exceed 5% of a file, alert (small improvement to `check_freshness.py`).

## Why this ticket is in the portfolio
It shows: reproducing the problem from the user's words, using logs/tables to find the cause, distinguishing
"our bug" from "source data problem", quantifying impact, communicating without jargon, and following up with prevention.
