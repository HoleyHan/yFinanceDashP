# Page_forex.py
import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from streamlit_javascript import st_javascript
from functions import *

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Forex",
    page_icon=":material/currency_exchange:",
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

# -------------------- TIMEZONE DETECTION --------------------
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
    'current_time_forex_page': datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None),
    'base_currency': 'EUR',
    'quote_currency': 'USD',
    'period': '3mo',
    'interval': '1d',
    'indicators': []
}

for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# -------------------- PAGE CONTROLS --------------------
with st.container():
    currencies = ['USD', 'EUR', 'JPY', 'GBP', 'CNY', 'ARS', 'BRL', 'CLP', 'BTC', 'ETH']
    
    base_currency = st.selectbox("Base currency", currencies, index=currencies.index(st.session_state['base_currency']))
    st.session_state['base_currency'] = base_currency

    quote_currency = st.selectbox("Quote currency", [c for c in currencies if c != base_currency], index=0)
    st.session_state['quote_currency'] = quote_currency

    period_options = ["1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"]
    period = st.selectbox("Period", period_options, index=period_options.index(st.session_state['period']))
    st.session_state['period'] = period

    intervals = ["1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"]
    if period in intervals:
        intervals = intervals[:intervals.index(period)]
    interval = st.selectbox("Interval", intervals, index=len(intervals)-4)
    st.session_state['interval'] = interval

    indicator_list = ['SMA_20','SMA_50','SMA_200','EMA_20','EMA_50','EMA_200','ATR','MACD','RSI']
    indicators = st.multiselect("Indicators", indicator_list, default=st.session_state['indicators'])
    st.session_state['indicators'] = indicators

    if any(x.endswith('_X') for x in indicators):
        time_span = st.slider("Time Span", min_value=10, max_value=200, value=30)
        indicators = [ind.replace('_X', str(time_span)) if '_X' in ind else ind for ind in indicators]
        st.session_state['indicators'] = indicators

    if st.button("Refresh data"):
        st.session_state['current_time_forex_page'] = datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0)
        fetch_history.clear()
        fetch_info.clear()
        fetch_table.clear()

    st.write("Last update:", st.session_state['current_time_forex_page'])

# -------------------- MAIN PAGE --------------------
st.title(f"Forex: {base_currency}/{quote_currency}")

ticker = f"{base_currency}{quote_currency}=X" if base_currency not in ["BTC","ETH"] else f"{base_currency}-{quote_currency}"

info = fetch_info(ticker)
if isinstance(info, Exception):
    st.error(info)
    fetch_info.clear(ticker)
    st.stop()

exchange_rate = info.get('previousClose', 0)
bid_price = info.get('dayLow', 0)
ask_price = info.get('dayHigh', 0)

col1, col2, col3 = st.columns(3)
col1.metric("Exchange Rate", f"{exchange_rate:.4f}")
col2.metric("Bid Price", f"{bid_price:.4f}")
col3.metric("Ask Price", f"{ask_price:.4f}")

hist_df = fetch_history(ticker, period=period, interval=interval)
if isinstance(hist_df, Exception):
    st.error(hist_df)
    fetch_history.clear(ticker, period=period, interval=interval)
    st.stop()

hist_df = hist_df.drop(columns=['Volume'], errors='ignore')

for ind in indicators:
    if "SMA" in ind:
        window = int(ind.split("_")[1])
        hist_df[ind] = hist_df['Close'].rolling(window=window, min_periods=1).mean()
    if "EMA" in ind:
        window = int(ind.split("_")[1])
        hist_df[ind] = hist_df['Close'].ewm(span=window, adjust=False, min_periods=1).mean()
    if "ATR" == ind:
        prev_close = hist_df['Close'].shift(1)
        tr = pd.concat([hist_df['High']-hist_df['Low'], (hist_df['High']-prev_close).abs(), (hist_df['Low']-prev_close).abs()], axis=1).max(axis=1)
        hist_df['ATR'] = tr.rolling(14, min_periods=1).mean()
    if "MACD" == ind:
        ema12 = hist_df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = hist_df['Close'].ewm(span=26, adjust=False).mean()
        hist_df['MACD'] = ema12 - ema26
        hist_df['Signal'] = hist_df['MACD'].ewm(span=9, adjust=False).mean()
        hist_df['MACD_Hist'] = hist_df['MACD'] - hist_df['Signal']
    if "RSI" == ind:
        delta = hist_df['Close'].pct_change()*100
        gain = delta.where(delta>0,0).rolling(14,min_periods=1).mean()
        loss = -delta.where(delta<0,0).rolling(14,min_periods=1).mean()
        rs = gain/loss
        hist_df['RSI'] = 100 - (100/(1+rs))

fig = plot_candles_stick_bar(hist_df, f"{base_currency}/{quote_currency} Candlestick Chart")
st.plotly_chart(fig, use_container_width=True)

with st.expander("Show data"):
    st.dataframe(hist_df.reset_index(), hide_index=False)