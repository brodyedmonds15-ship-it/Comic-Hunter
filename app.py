# app.py (patched to work with params)
import pandas as pd, streamlit as st
from scanner import scan_all

st.set_page_config(page_title="Comic Deal Hunter", layout="centered")
st.title("🕵️ Comic Deal Hunter")
st.caption("eBay AU • fixed price • under $250 • key-ish searches • BUY/MAYBE/PASS")

with st.sidebar:
    price_cap = st.slider("Max price (AUD)", 50, 400, 250, 10)
    pages = st.slider("Pages per search term", 1, 5, 2, 1)
    st.caption("Tip: Add this to your phone's Home Screen.")

if st.button("🔎 Scan now"):
    with st.spinner("Scanning…"):
        try:
            results = scan_all(max_price=price_cap, pages=pages)
        except TypeError:
            # fallback if an older scanner is present
            results = scan_all()
    if not results:
        st.info("No promising items found right now (or running in demo mode without a real eBay key).")
    else:
        df = pd.DataFrame([{
            "Verdict": r.get("label",""),
            "Score": r.get("score",""),
            "Title": r.get("title",""),
            "Price (AUD)": r.get("price",""),
            "FMV": r.get("fmv",""),
            "Link": r.get("url","")
        } for r in results])
        st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Tap ‘Scan now’ to fetch fresh deals.")
