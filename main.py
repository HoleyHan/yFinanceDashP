import json
from pathlib import Path
import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(show_spinner=False)
def load_refs():
    path = Path(".streamlit/app_refs.json")
    with open(path) as f:
        return json.load(f)

@st.cache_data
def fetch_history(symbol, period="1mo", interval="1d"):
    return yf.Ticker(symbol).history(period=period, interval=interval)

# -------------------- LOAD APP REFS --------------------
with open(".streamlit/app_refs.json") as f:
    refs = json.load(f)

# Optional: show welcome or dashboard landing page
st.set_page_config(
    page_title="yFinance Dash",
    page_icon=":chart_with_upwards_trend:",
    layout="wide"
)

st.title("yFinance Dashboard")
st.markdown("Welcome! Use the sidebar to navigate between pages.")

# Show categories and key links dynamically if needed
if "commodities" in refs:
    st.subheader("Commodity Categories")
    for category, items in refs["commodities"].items():
        st.markdown(f"**{category}**: {', '.join(items.keys())}")

# -------------------- NAVIGATION --------------------
# Streamlit >=1.18 supports multi-page apps via /pages folder
# Users navigate to pages like Page_commodity.py automatically
# Optionally, you can add quick links:
st.sidebar.markdown("## Quick Navigation")
st.sidebar.markdown("- [Commodities](./pages/Page_commodity.py)")
st.sidebar.markdown("- [Data Exporer](./pages/Page_data_explorer.py)")
st.sidebar.markdown("- [Financials](./pages/Page_financials.py)")
st.sidebar.markdown("- [Forex](./pages/Page_forex.py)")
st.sidebar.markdown("- [Price](./pages/Page_price.py)")
