# email_report.py
"""
Daily email digest using SendGrid.
Env needed:
  EBAY_APP_ID
  SENDGRID_API_KEY
  TO_EMAIL
  FROM_EMAIL (verified sender in SendGrid)
"""
import os, json, requests, pandas as pd
from datetime import datetime
from scanner import scan_all

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
TO_EMAIL = os.getenv("TO_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL", "deals@example.com")

def build_html(rows):
    if not rows:
        return "<p>No promising items today.</p>"
    df = pd.DataFrame([{
        "Verdict": r["label"], "Score": r["score"], "Title": r["title"],
        "Price (AUD)": r["price"], "FMV": r["fmv"], "Link": r["url"]
    } for r in rows[:60]])
    html = ["<h2>Comic Deal Hunter — Daily Report</h2><ol>"]
    for _, x in df.iterrows():
        html.append(f"<li><b>[{x['Verdict']}]</b> {x['Title']} — ${int(x['Price (AUD)'])} "
                    f"(FMV: {x['FMV']}) • Score {int(x['Score'])} — "
                    f"<a href='{x['Link']}'>Open</a></li>")
    html.append("</ol>")
    return "\n".join(html)

def send_email(subject, html):
    url = "https://api.sendgrid.com/v3/mail/send"
    payload = {
      "personalizations": [{"to": [{"email": TO_EMAIL}]}],
      "from": {"email": FROM_EMAIL, "name": "Comic Deal Hunter"},
      "subject": subject,
      "content": [{"type": "text/html", "value": html}]
    }
    r = requests.post(url, headers={"Authorization": f"Bearer {SENDGRID_API_KEY}",
                                    "Content-Type": "application/json"},
                      data=json.dumps(payload), timeout=30)
    r.raise_for_status()

if __name__ == "__main__":
    results = scan_all()
    subject = f"Comic Deal Hunter — {datetime.now().strftime('%Y-%m-%d')}"
    html = build_html(results)
    send_email(subject, html)
    print("Email sent.")