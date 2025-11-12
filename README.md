# Comic Deal Hunter (Mobile Web App)

Find underpriced **key comics** on eBay Australia, right from your phone.

## What it does
- Scans **eBay AU** fixed-price listings under a price cap.
- Flags likely **key issues** using keywords + heuristics.
- Pulls **sold comps** from eBay completed listings to estimate FMV.
- Scores each item: **BUY / MAYBE / PASS**.
- Web app (Streamlit) + optional **daily email** via GitHub Actions + SendGrid.

## Quick start
1. Create free accounts: **GitHub**, **Streamlit Cloud**, **eBay Developer**, **SendGrid**.
2. Put these files in a GitHub repo.
3. In the repo **Settings → Secrets → Actions**, add:
   - `EBAY_APP_ID`
   - `SENDGRID_API_KEY`
   - `TO_EMAIL`
   - `FROM_EMAIL`
4. Deploy to Streamlit: New App → point at `app.py`.
5. Open the app on your phone and tap **Scan now**.
6. The daily email runs via GitHub Actions at ~9:00 AM Australia/Sydney (adjust cron if needed).

> This is a v1 prototype using title-based heuristics. You can expand the queries/key lists or plug in CovrPrice/GoCollect later.
