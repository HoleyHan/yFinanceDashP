import datetime
import pandas as pd
from zoneinfo import ZoneInfo
import streamlit as st
from streamlit_javascript import st_javascript
from functions import fetch_table, fetch_info, fetch_history, info_table, plot_candles_stick_bar, plot_line_multiple, remove_duplicates
from contact import contact_form

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Stock Dashboard",
    page_icon=":material/stacked_line_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": "https://github.com/LMAPcoder"}
)

# ---- TIMEZONE ----
if "timezone" not in st.session_state:
    tz = st_javascript("""
        await (async () => Intl.DateTimeFormat().resolvedOptions().timeZone)().then(r => r)
    """)
    if isinstance(tz, int):
        st.stop()
    st.session_state["timezone"] = ZoneInfo(tz)

# ---- SESSION STATE ----
default_state = {
    "current_time_price_page": datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None),
    "tickers": "MSFT",
    "dark_mode": False,
    "toggle_theme": False,
    "financial_period": "Annual",
    "indicators": [],
    "period": "3mo",
    "interval": "1d"
}

for key, val in default_state.items():
    st.session_state.setdefault(key, val)

# ---- SIDEBAR ----
with st.sidebar:
    page = st.selectbox("Pages", ["Market Overview", "Portfolio", "Securities Analysis", "Settings"])
    st.markdown("---")

# ---- TOPBAR CONTROLS ----
st.markdown("### Controls")
col1, col2, col3, col4 = st.columns([2,2,2,1], gap="small")

with col1:
    ticker_input = st.text_input("Ticker", value=st.session_state["tickers"])

with col2:
    periods = ["1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"]
    PERIOD = st.selectbox("Period", periods, index=periods.index(st.session_state["period"]))

with col3:
    intervals = ["1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"]
    INTERVAL = st.selectbox("Interval", intervals, index=intervals.index(st.session_state["interval"]))

with col4:
    dark_toggle = st.checkbox("Dark Mode", value=st.session_state["dark_mode"])
    st.session_state["dark_mode"] = dark_toggle

# ---- INDICATORS & ACTIONS ----
col1, col2, col3 = st.columns([3,1,1], gap="small")
with col1:
    INDICATORS = []
    if ticker_input.strip():
        indicator_list = ['SMA_20','SMA_50','SMA_200','SMA_X','EMA_20','EMA_50','EMA_200','EMA_X','ATR','MACD','RSI']
        INDICATORS = st.multiselect("Indicators", indicator_list)
        if any("_X" in i for i in INDICATORS):
            TIME_SPAN = st.slider("Custom time span", 10, 200, 30)
            INDICATORS = [i.replace("_X", str(TIME_SPAN)) if "_X" in i else i for i in INDICATORS]

with col2:
    refresh_btn = st.button("Refresh Data")

with col3:
    contact_btn = st.button("✉️ Contact Me")
    if contact_btn:
        contact_form()

# ---- UPDATE SESSION STATE ----
st.session_state.update({
    "tickers": ticker_input.strip(),
    "period": PERIOD,
    "interval": INTERVAL,
    "indicators": INDICATORS
})

if refresh_btn:
    fetch_table.clear()
    fetch_info.clear()
    fetch_history.clear()
    st.session_state["current_time_price_page"] = datetime.datetime.now(st.session_state["timezone"]).replace(microsecond=0, tzinfo=None)
    st.experimental_rerun()

# ---- PAGE CONTENT ----
if page == "Market Overview":
    st.title("Market Overview")
    df_indices = fetch_table("https://finance.yahoo.com/markets/world-indices/")
    df_gainers = fetch_table("https://finance.yahoo.com/markets/stocks/gainers/")
    df_losers = fetch_table("https://finance.yahoo.com/markets/stocks/losers/")

    for df, title in zip([df_indices, df_gainers, df_losers], ["Indices", "Gainers", "Losers"]):
        if isinstance(df, pd.DataFrame):
            st.subheader(title)
            st.dataframe(df)

elif page == "Portfolio":
    st.title("Portfolio Overview")
    tickers_list = remove_duplicates([ticker_input])
    if tickers_list:
        all_dfs = []
        for t in tickers_list:
            hist = fetch_history(t, PERIOD, INTERVAL)
            if isinstance(hist, pd.DataFrame):
                hist.insert(0, 'Ticker', t)
                all_dfs.append(hist)
        if all_dfs:
            df_combined = pd.concat(all_dfs, ignore_index=True)
            st.plotly_chart(plot_line_multiple(df_combined, title="Portfolio Performance"), use_container_width=True)

elif page == "Securities Analysis":
    st.title("Securities Analysis")
    if ticker_input.strip():
        TICKER = ticker_input.strip()
        info = fetch_info(TICKER)
        if isinstance(info, dict):
            st.subheader(f"{TICKER} Info")
            st.dataframe(info_table(info))

        hist = fetch_history(TICKER, PERIOD, INTERVAL)
        if isinstance(hist, pd.DataFrame):
            df = hist.copy()
            for ind in INDICATORS:
                if "SMA" in ind:
                    window = int(ind.split("_")[1])
                    df[ind] = df['Close'].rolling(window).mean()
                if "EMA" in ind:
                    window = int(ind.split("_")[1])
                    df[ind] = df['Close'].ewm(span=window, adjust=False).mean()
            st.plotly_chart(plot_candles_stick_bar(df, title=f"{TICKER} Candlestick", currency=info.get("currency","USD")), use_container_width=True)
    else:
        st.warning("Securities Analysis only works for a single ticker.")

elif page == "Settings":
    st.title("Settings")
    st.write("Adjust app preferences here")
    st.write(f"Last update: {st.session_state['current_time_price_page']}")