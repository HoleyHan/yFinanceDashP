import json
import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from streamlit_javascript import st_javascript
from functions import fetch_history, plot_candles_stick_bar

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Commodities",
    page_icon=":material/oil_barrel:",
    layout="wide",
    initial_sidebar_state="auto"
)

# -------------------- LOAD JSON REFS --------------------
with open(".streamlit/app_refs.json") as f:
    refs = json.load(f)

commodities_ref = refs.get("commodities", {})
default_periods = refs.get("defaults", {}).get(
    "periods", ["1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"]
)
default_intervals = refs.get("defaults", {}).get(
    "intervals", ["1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"]
)

# -------------------- TIMEZONE DETECTION --------------------
if 'timezone' not in st.session_state:
    timezone = st_javascript("""
        await (async () => Intl.DateTimeFormat().resolvedOptions().timeZone)()
        .then(tz => tz)
    """)
    st.session_state['timezone'] = ZoneInfo(timezone) if isinstance(timezone, str) else ZoneInfo("UTC")

# -------------------- SESSION STATE DEFAULTS --------------------
default_state = {
    'current_time_commodity_page': datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None),
    'selected_category': list(commodities_ref.keys())[0] if commodities_ref else None,
    'selected_ticker': None,
    'selected_period': default_periods[3],
    'selected_interval': default_intervals[-4],
    'selected_indicators': [],
    'volume_toggle': True
}
for k, v in default_state.items():
    st.session_state.setdefault(k, v)

# -------------------- PAGE CONTAINER --------------------
with st.container():
    st.header("Commodity Market Data")

    # ---- CATEGORY SELECTION ----
    categories = list(commodities_ref.keys())
    st.session_state['selected_category'] = st.selectbox(
        "Category",
        categories,
        index=categories.index(st.session_state['selected_category'])
    )

    # ---- TICKER SELECTION ----
    tickers_dict = commodities_ref[st.session_state['selected_category']]
    tickers = list(tickers_dict.keys())
    st.session_state['selected_ticker'] = st.selectbox("Commodity", tickers, index=0)
    selected_symbol = tickers_dict[st.session_state['selected_ticker']]

    # ---- PERIOD & INTERVAL ----
    st.session_state['selected_period'] = st.selectbox(
        "Period", default_periods, index=default_periods.index(st.session_state['selected_period'])
    )
    intervals = default_intervals.copy()
    if st.session_state['selected_period'] in intervals:
        idx = intervals.index(st.session_state['selected_period'])
        intervals = intervals[:idx]
    st.session_state['selected_interval'] = st.selectbox(
        "Interval", intervals, index=len(intervals)-4
    )

    # ---- VOLUME TOGGLE ----
    st.session_state['volume_toggle'] = st.checkbox("Show Volume", value=st.session_state['volume_toggle'])

    # ---- INDICATORS ----
    indicators_list = ['SMA', 'EMA', 'ATR', 'MACD', 'RSI']
    selected_indicators = st.multiselect(
        "Indicators", indicators_list, default=st.session_state['selected_indicators']
    )
    if 'SMA' in selected_indicators or 'EMA' in selected_indicators:
        time_span = st.slider("Time Span (for SMA/EMA)", min_value=10, max_value=200, value=30)
        selected_indicators = [
            f"{ind}_{time_span}" if ind in ['SMA','EMA'] else ind for ind in selected_indicators
        ]
    st.session_state['selected_indicators'] = selected_indicators

    # ---- REFRESH DATA ----
    if st.button("Refresh"):
        st.session_state['current_time_commodity_page'] = datetime.datetime.now(
            st.session_state['timezone']
        ).replace(microsecond=0)
        fetch_history.clear()

    st.write("Last update:", st.session_state['current_time_commodity_page'])

    # -------------------- HISTORICAL DATA --------------------
    @st.cache_data(show_spinner=False)
    def load_history(symbol, period, interval):
        return fetch_history(symbol, period=period, interval=interval)

    hist_df = load_history(
        selected_symbol, st.session_state['selected_period'], st.session_state['selected_interval']
    )
    if isinstance(hist_df, Exception):
        st.error(hist_df)
        st.stop()

    # ---- VOLUME CALC ----
    if not st.session_state['volume_toggle']:
        hist_df = hist_df.drop(columns=['Volume'], errors='ignore')
    else:
        hist_df['ΔVolume%'] = hist_df['Volume'].pct_change() * 100
        hist_df['ΔVolume%'] = hist_df['ΔVolume%'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else None
        )

    # ---- COMPUTE INDICATORS ----
    @st.cache_data(show_spinner=False)
    def compute_indicators(df, indicators):
        df = df.copy()
        for ind in indicators:
            if "SMA" in ind:
                window = int(ind.split("_")[1])
                df[ind] = df['Close'].rolling(window=window, min_periods=1).mean()
            elif "EMA" in ind:
                window = int(ind.split("_")[1])
                df[ind] = df['Close'].ewm(span=window, adjust=False, min_periods=1).mean()
            elif "ATR" == ind:
                prev = df['Close'].shift(1)
                tr = pd.concat([df['High']-df['Low'], (df['High']-prev).abs(), (df['Low']-prev).abs()], axis=1).max(axis=1)
                df['ATR'] = tr.rolling(14, min_periods=1).mean()
            elif "MACD" == ind:
                ema12 = df['Close'].ewm(span=12, adjust=False).mean()
                ema26 = df['Close'].ewm(span=26, adjust=False).mean()
                df['MACD'] = ema12 - ema26
                df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
                df['MACD_Hist'] = df['MACD'] - df['Signal']
            elif "RSI" == ind:
                delta = df['Close'].diff()
                gain = delta.where(delta>0,0).rolling(14,min_periods=1).mean()
                loss = -delta.where(delta<0,0).rolling(14,min_periods=1).mean()
                rs = gain/loss
                df['RSI'] = 100 - (100/(1+rs))
        return df

    hist_df = compute_indicators(hist_df, st.session_state['selected_indicators'])

    # ---- PLOT ----
    fig = plot_candles_stick_bar(hist_df, "Candlestick Chart")
    st.plotly_chart(fig, use_container_width=True)

    # ---- DATA TABLE ----
    with st.expander("Show Data Table"):
        st.dataframe(hist_df.reset_index(), hide_index=True)