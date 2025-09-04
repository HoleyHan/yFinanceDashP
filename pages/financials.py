# Page_financials.py
import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from streamlit_javascript import st_javascript
from functions import *

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Financials",
    page_icon=":material/finance:",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"Get help": "https://github.com/LMAPcoder"}
)

# -------------------- LOGO STYLE --------------------
st.html("""
  <style>
    [alt=Logo] {
      height: 3rem;
      width: auto;
      padding-left: 1rem;
    }
  </style>
""")

# -------------------- TIMEZONE DETECTION (LAZY LOAD) --------------------
if 'timezone' not in st.session_state:
    timezone = st_javascript("""
        await (async () => Intl.DateTimeFormat().resolvedOptions().timeZone)()
        .then(tz => tz)
    """)
    if not isinstance(timezone, str):
        st.session_state['timezone'] = ZoneInfo("UTC")
    else:
        st.session_state['timezone'] = ZoneInfo(timezone)

# -------------------- SESSION STATE DEFAULTS --------------------
defaults = {
    'current_time_financials_page': datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None),
    'ticker': 'MSFT',
    'financial_period': 'Annual'
}

for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# -------------------- PAGE CONTAINER --------------------
with st.container():
    # --- Ticker input ---
    TICKER = st.text_input("Security (single symbol)", value=st.session_state['ticker'])
    st.session_state['ticker'] = TICKER.strip().upper()

    # --- Time period selection ---
    TIME_PERIOD = st.radio("Time Period", ["Annual", "Quarterly"], index=["Annual", "Quarterly"].index(st.session_state['financial_period']))
    st.session_state['financial_period'] = TIME_PERIOD

    # --- Refresh button ---
    if st.button("Refresh data"):
        st.session_state['current_time_financials_page'] = datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0)
        fetch_info.clear(st.session_state['ticker'])
        fetch_balance.clear(st.session_state['ticker'], tp=TIME_PERIOD)
        fetch_income.clear(st.session_state['ticker'], tp=TIME_PERIOD)
        fetch_cash.clear(st.session_state['ticker'], tp=TIME_PERIOD)

    st.write("Last update:", st.session_state['current_time_financials_page'])

# -------------------- MAIN PAGE --------------------
st.title(f"Financials: {st.session_state['ticker']}")

TICKER = st.session_state['ticker']

# --- Fetch Info ---
info = fetch_info(TICKER)
if isinstance(info, Exception):
    st.error(info)
    st.stop()

NAME = info.get('shortName', "")
st.write(NAME)

CURRENCY = info.get('financialCurrency', "???")

# --- FETCH FINANCIAL STATEMENTS ---
bs = fetch_balance(TICKER, tp=TIME_PERIOD)
ist = fetch_income(TICKER, tp=TIME_PERIOD)
cf = fetch_cash(TICKER, tp=TIME_PERIOD)

# --- CAPITAL STRUCTURE ---
st.header("Capital Structure")
if isinstance(bs, Exception):
    st.error(bs)
    st.stop()

fig = plot_capital(bs, ticker=TICKER, currency=CURRENCY)
st.plotly_chart(fig, use_container_width=True)

# --- BALANCE SHEET ---
st.header("Balance Sheet")
fig = plot_balance(bs[bs.columns[::-1]], ticker=TICKER, currency=CURRENCY)
st.plotly_chart(fig, use_container_width=True)

with st.expander("Show components"):
    tab1, tab2, tab3 = st.tabs(["Assets", "Liabilities", "Equity"])
    with tab1:
        fig = plot_assets(bs, ticker=TICKER, currency=CURRENCY)
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        fig = plot_liabilities(bs, ticker=TICKER, currency=CURRENCY)
        st.plotly_chart(fig, use_container_width=True)
    with tab3:
        fig = plot_equity(bs, ticker=TICKER, currency=CURRENCY)
        st.plotly_chart(fig, use_container_width=True)

with st.expander("Show data"):
    st.dataframe(bs, hide_index=False)

# --- INCOME STATEMENT ---
st.header("Income Statement")
if isinstance(ist, Exception):
    st.error(ist)
    st.stop()

fig = plot_income(ist, ticker=TICKER, currency=CURRENCY)
st.plotly_chart(fig, use_container_width=True)

with st.expander("Ratios"):
    tab1, tab2, tab3 = st.tabs(["Net Margin", "EPS", "P/E Ratio"])
    with tab1:
        try:
            fig = plot_margins(ist, ticker=TICKER)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.error("Not enough data to plot this ratio")
    with tab2:
        try:
            fig = plot_eps(TICKER)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.error("Not enough data to plot EPS")
    with tab3:
        try:
            fig = plot_pe_ratio(TICKER)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.error("Not enough data to plot P/E ratio")

with st.expander("Show data"):
    st.dataframe(ist, hide_index=False)

# --- CASH FLOW ---
st.header("Cash Flow")
if isinstance(cf, Exception):
    st.error(cf)
    st.stop()

fig = plot_cash(cf, ticker=TICKER, currency=CURRENCY)
st.plotly_chart(fig, use_container_width=True)

with st.expander("Show data"):
    st.dataframe(cf, hide_index=False)