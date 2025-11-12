# scanner.py
"""
Comic Deal Hunter — eBay AU scanner + scoring.
- Searches eBay AU fixed-price listings for key-ish comics under MAX_PRICE_AUD
- Pulls rough FMV from eBay sold/complete results
- Ranks: BUY / MAYBE / PASS

Env needed:
  EBAY_APP_ID  -> your eBay Developer "App ID (Client ID)"
"""

import os, re, time
import requests

EBAY_APP_ID = os.getenv("EBAY_APP_ID")
if not EBAY_APP_ID:
    raise RuntimeError("Missing EBAY_APP_ID environment variable. Set it in Streamlit/Actions secrets.")

EBAY_ENDPOINT = "https://svcs.ebay.com/services/search/FindingService/v1"
EBAY_HEADERS = {
    "X-EBAY-SOA-OPERATION-NAME": "findItemsByKeywords",
    "X-EBAY-SOA-SERVICE-VERSION": "1.13.0",
    "X-EBAY-SOA-SECURITY-APPNAME": EBAY_APP_ID,
    "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON"
}

# Sold comps (completed listings)
EBAY_COMPLETED_OP = "findCompletedItems"
EBAY_COMPLETED_ENDPOINT = EBAY_ENDPOINT

MAX_PRICE_AUD = 250  # v1 focus

KEY_TERMS = [
    "key issue", "first appearance", "1st appearance", "#1", "origin",
    "newsstand", "bronze age", "silver age", "early issue", "first full", "first cameo"
]

BOOST_TITLES = [
    "Amazing Spider-Man #361", "ASM #361", "ASM 361",
    "Amazing Spider-Man #300", "ASM #300",
    "Batman #457", "OMAC #1", "Swamp Thing #1",
    "Marvel Comics Presents #72", "Wolverine #1",
    "Incredible Hulk #181", "Hulk #181", "New Mutants #98", "X-Men #266"
]

DEFAULT_QUERIES = [
    "comic key issue", "first appearance comic", "silver age comic", "bronze age comic",
    "marvel key comic", "dc key comic", "spider-man key", "batman key", "x-men key"
]

def parse_price(item):
    selling = item.get("sellingStatus", [{}])[0]
    cur = selling.get("currentPrice", [{}])[0].get("__value__")
    try:
        return float(cur)
    except:
        return None

def looks_keyish(title):
    t = title.lower()
    score = 0
    for kw in KEY_TERMS:
        if kw in t: score += 1
    for bt in BOOST_TITLES:
        if bt.lower() in t: score += 2
    # basic issue number signal
    if re.search(r"(#|\s)\d{1,3}\b", t): score += 1
    return score

def ebay_search(query, max_price=MAX_PRICE_AUD, pages=2):
    results = []
    for page in range(1, pages+1):
        params = {
            "keywords": query,
            "paginationInput.entriesPerPage": 50,
            "paginationInput.pageNumber": page,
            "buyerPostalCode": "2000",  # Sydney
            "itemFilter(0).name": "ListingType",
            "itemFilter(0).value(0)": "FixedPrice",
            "itemFilter(1).name": "MaxPrice",
            "itemFilter(1).value": max_price,
            "itemFilter(1).paramName": "Currency",
            "itemFilter(1).paramValue": "AUD",
            "GLOBAL-ID": "EBAY-AU",
            "siteid": "15",
        }
        r = requests.get(EBAY_ENDPOINT, headers=EBAY_HEADERS, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        items = (data.get("findItemsByKeywordsResponse", [{}])[0]
                    .get("searchResult", [{}])[0]
                    .get("item", []))
        for it in items:
            title = it.get("title", [""])[0]
            price = parse_price(it)
            url = it.get("viewItemURL", [""])[0]
            gallery = it.get("galleryURL", [""])[0]
            if price is None or not title or not url:
                continue
            results.append({
                "title": title, "price": price, "url": url, "img": gallery
            })
        time.sleep(0.15)
    return results

def get_sold_median(title, fallback=None):
    headers = {
        "X-EBAY-SOA-OPERATION-NAME": EBAY_COMPLETED_OP,
        "X-EBAY-SOA-SERVICE-VERSION": "1.13.0",
        "X-EBAY-SOA-SECURITY-APPNAME": EBAY_APP_ID,
        "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
    }
    params = {
        "keywords": title,
        "GLOBAL-ID": "EBAY-AU",
        "siteid": "15",
        "paginationInput.entriesPerPage": 50,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value(0)": "true",
    }
    try:
        r = requests.get(EBAY_COMPLETED_ENDPOINT, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        items = (data.get("findCompletedItemsResponse", [{}])[0]
                   .get("searchResult", [{}])[0]
                   .get("item", []))
        sold_prices = []
        for it in items:
            selling = it.get("sellingStatus", [{}])[0]
            if selling.get("sellingState", [""])[0] != "EndedWithSales":
                continue
            price = float(selling["currentPrice"][0]["__value__"])
            sold_prices.append(price)
        if not sold_prices:
            return fallback
        sold_prices.sort()
        return sold_prices[len(sold_prices)//2]
    except Exception:
        return fallback

def rank_items(items):
    ranked = []
    for it in items:
        kscore = looks_keyish(it["title"])
        if kscore <= 0:
            continue
        fmv = get_sold_median(it["title"], fallback=None)
        if fmv is None:
            if kscore >= 2 and it["price"] <= 60:
                label, score = "MAYBE", 55
            else:
                label, score = "PASS", 40
        else:
            ratio = it["price"] / fmv if fmv and fmv > 0 else 9.9
            if ratio <= 0.7:
                label, score = "BUY", 90 - int(ratio*10)
            elif ratio <= 0.9:
                label, score = "MAYBE", 70 - int((ratio-0.7)*50)
            else:
                label, score = "PASS", 40 - int((ratio-0.9)*80)
        ranked.append({**it, "fmv": fmv, "label": label, "kscore": kscore, "score": score})
        time.sleep(0.1)
    ranked.sort(key=lambda x: ({"BUY":0,"MAYBE":1,"PASS":2}[x["label"]], -x["score"]))
    return ranked

def scan_all(queries=DEFAULT_QUERIES, max_price=MAX_PRICE_AUD, pages=2):
    items = []
    for q in queries:
        items += ebay_search(q, max_price=max_price, pages=pages)
    return rank_items(items)

if __name__ == "__main__":
    results = scan_all()
    print(f"Found {len(results)} candidates")
    for r in results[:20]:
        print(f"[{r['label']}] {r['title']} — ${r['price']:.0f} (FMV: {r['fmv']})  score={r['score']}")
        print(" ", r['url'])
