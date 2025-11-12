# scanner.py (patched for Streamlit demo + params)
import os, re, time, requests
try:
    import streamlit as st
    EBAY_APP_ID = st.secrets.get("EBAY_APP_ID", os.getenv("EBAY_APP_ID"))
except Exception:
    EBAY_APP_ID = os.getenv("EBAY_APP_ID")

DEMO_MODE = False
if not EBAY_APP_ID or EBAY_APP_ID.strip() in ("", "test", "test-placeholder"):
    DEMO_MODE = True
    EBAY_APP_ID = "test-placeholder"
    print("⚠️ DEMO MODE: UI loads, scans return empty until a real key is set.")

EBAY_ENDPOINT = "https://svcs.ebay.com/services/search/FindingService/v1"
EBAY_HEADERS = {
    "X-EBAY-SOA-OPERATION-NAME": "findItemsByKeywords",
    "X-EBAY-SOA-SERVICE-VERSION": "1.13.0",
    "X-EBAY-SOA-SECURITY-APPNAME": EBAY_APP_ID,
    "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON"
}

MAX_PRICE_AUD = 250
KEY_TERMS = ["key issue","first appearance","1st appearance","#1","origin",
             "newsstand","bronze age","silver age","early issue","first full","first cameo"]
BOOST_TITLES = ["Amazing Spider-Man #361","ASM #300","Batman #457","Wolverine #1"]

def parse_price(item):
    selling = item.get("sellingStatus", [{}])[0]
    cur = selling.get("currentPrice", [{}])[0].get("__value__")
    try: return float(cur)
    except: return None

def looks_keyish(title):
    t = title.lower(); score = 0
    for kw in KEY_TERMS:
        if kw in t: score += 1
    for bt in BOOST_TITLES:
        if bt.lower() in t: score += 2
    if re.search(r"(#|\s)\d{1,3}\b", t): score += 1
    return score

def ebay_search(query, max_price=MAX_PRICE_AUD, pages=2):
    if DEMO_MODE: return []
    results = []
    for page in range(1, pages+1):
        params = {
            "keywords": query,
            "paginationInput.entriesPerPage": 50,
            "paginationInput.pageNumber": page,
            "itemFilter(0).name": "ListingType",
            "itemFilter(0).value(0)": "FixedPrice",
            "itemFilter(1).name": "MaxPrice",
            "itemFilter(1).value": max_price,
            "itemFilter(1).paramName": "Currency",
            "itemFilter(1).paramValue": "AUD",
            "GLOBAL-ID": "EBAY-AU",
            "siteid": "15"
        }
        r = requests.get(EBAY_ENDPOINT, headers=EBAY_HEADERS, params=params, timeout=30)
        data = r.json()
        items = (data.get("findItemsByKeywordsResponse", [{}])[0]
                    .get("searchResult", [{}])[0]
                    .get("item", []))
        for it in items:
            title = it.get("title", [""])[0]
            price = parse_price(it)
            url = it.get("viewItemURL", [""])[0]
            if price and title and url:
                results.append({"title": title, "price": price, "url": url})
        time.sleep(0.15)
    return results

def get_sold_median(title, fallback=None):
    if DEMO_MODE: return None
    return fallback  # simple v1

def rank_items(items):
    ranked = []
    for it in items:
        k = looks_keyish(it["title"])
        if k <= 0: continue
        ranked.append({**it, "fmv": None, "label": "MAYBE", "kscore": k, "score": k*10})
    ranked.sort(key=lambda x: -x["score"])
    return ranked

DEFAULT_QUERIES = ["comic key issue","first appearance comic","silver age comic","bronze age comic",
                   "marvel key comic","dc key comic","spider-man key","batman key","x-men key"]

def scan_all(max_price=MAX_PRICE_AUD, pages=2):
    if DEMO_MODE: return []
    items = []
    for q in DEFAULT_QUERIES:
        items += ebay_search(q, max_price=max_price, pages=pages)
    return rank_items(items)
