# app.py
import os, pandas as pd, streamlit as st
from scanner import scan_all

st.set_page_config(page_title="Comic Deal Hunter", layout="centered")

st.title("🕵️ Comic Deal Hunter")
st.caption("eBay AU • fixed price • under $250 • key-ish searches • BUY/MAYBE/PASS")

with st.sidebar:
    st.markdown("### Filters")
    price_cap = st.slider("Max price (AUD)", 50, 400, 250, 10)
    pages = st.slider("Pages per query", 1, 5, 2, 1)
    st.markdown("---")
    st.caption("Tip: On your phone, add this page to Home Screen.")

if st.button("🔎 Scan now"):
    with st.spinner("Scanning eBay AU…"):
        results = scan_all(max_price=price_cap, pages=pages)
    if not results:
        st.info("No promising items found right now.")
    else:
        df = pd.DataFrame([{
            "Verdict": r["label"],
            "Score": r["score"],
            "Title": r["title"],
            "Price (AUD)": r["price"],
            "FMV (sold median)": r["fmv"],
            "Link": r["url"]
        } for r in results])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.success(f"Found {len(results)} candidates. BUYs shown first.")
else:
    st.info("Tap ‘Scan now’ to fetch fresh deals.")