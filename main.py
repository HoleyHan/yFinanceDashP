import streamlit as st

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="yFinance Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide"
)

# -------------------- LANDING PAGE --------------------
st.title("yFinance Dashboard")

st.write("Welcome to your trading dashboard!")

st.info(
    "Use the sidebar to navigate between pages:\n"
    "- Macro Dashboard\n"
    "- Commodities\n"
    "- Forex\n"
    "- Financials\n"
    "- Data Explorer\n"
    "- stock"
)

st.write("Tip: Select a page from the sidebar to start exploring market data and visualizations.")