import streamlit as st

st.set_page_config(
    page_title="yFinance Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide"
)

st.title("yFinance Dashboard")
st.markdown("Welcome! Use the sidebar to navigate between pages.")

# Sidebar for navigation only
st.sidebar.title("Pages")
st.sidebar.markdown("- [Macro Dashboard](./pages/macro_dashboard.py)")
st.sidebar.markdown("- [Commodities](./pages/commodities.py)")
st.sidebar.markdown("- [Data Explorer](./pages/data_explorer.py)")
st.sidebar.markdown("- [Financials](./pages/financials.py)")
st.sidebar.markdown("- [Forex](./pages/forex.py)")
st.sidebar.markdown("- [Price](./pages/price.py)")