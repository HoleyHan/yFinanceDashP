import datetime
import pandas as pd
from zoneinfo import ZoneInfo
import streamlit as st
from streamlit_javascript import st_javascript
from functions import fetch_table, fetch_info, fetch_history, info_table, plot_candles_stick_bar, performance_table, plot_line_multiple, remove_duplicates
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
    timezone = st_javascript("""
        await (async () => {
            const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            return tz
        })().then(r => r)
    """)
    if isinstance(timezone, int):
        st.stop()
    st.session_state["timezone"] = ZoneInfo(timezone)


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
    if key not in st.session_state:
        st.session_state[key] = val


# ---- SIDEBAR: PAGE NAVIGATION ONLY ----
with st.sidebar:
    page = st.selectbox(
        "Pages",
        options=["Market Overview", "Portfolio", "Securities Analysis", "Settings"],
        index=0
    )
    st.markdown("---")


# ---- TOPBAR CONTROLS ----
st.markdown("### Controls")
col1, col2, col3, col4 = st.columns([2, 2, 2, 1], gap="small")

with col1:
    tickers_input = st.text_input(
        "Tickers (comma-separated)",
        value=st.session_state["tickers"]
    )

with col2:
    period_list = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    PERIOD = st.selectbox("Period", period_list, index=period_list.index(st.session_state["period"]))

with col3:
    interval_list = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    INTERVAL = st.selectbox("Interval", interval_list, index=interval_list.index(st.session_state["interval"]))

with col4:
    toggle_theme = st.checkbox("Dark Mode", value=st.session_state["dark_mode"])
    if toggle_theme != st.session_state["dark_mode"]:
        st.session_state["dark_mode"] = toggle_theme
        st._config.set_option("theme.base", "dark" if toggle_theme else "light")


# ---- SECOND ROW: INDICATORS + ACTIONS ----
col1, col2, col3 = st.columns([3, 1, 1], gap="small")
with col1:
    INDICATORS = []
    if len(tickers_input.split(",")) == 1:
        indicator_list = ['SMA_20', 'SMA_50', 'SMA_200', 'SMA_X', 'EMA_20', 'EMA_50', 'EMA_200', 'EMA_X', 'ATR', 'MACD', 'RSI']
        INDICATORS = st.multiselect("Indicators:", indicator_list)
        if any("_X" in i for i in INDICATORS):
            TIME_SPAN = st.slider("Custom time span:", 10, 200, 30)
            INDICATORS = [i.replace("_X", str(TIME_SPAN)) if "_X" in i else i for i in INDICATORS]

with col2:
    refresh_button = st.button("Refresh Data")

with col3:
    contact_button = st.button("✉️ Contact Me")
    if contact_button:
        show_contact_form()


# ---- UPDATE SESSION STATE ----
st.session_state.update({
    "tickers": tickers_input,
    "period": PERIOD,
    "interval": INTERVAL,
    "indicators": INDICATORS
})

if refresh_button:
    fetch_table.clear()
    fetch_info.clear()
    fetch_history.clear()
    st.session_state["current_time_price_page"] = datetime.datetime.now(st.session_state["timezone"]).replace(microsecond=0, tzinfo=None)
    st.experimental_rerun()


# ---- PAGE DYNAMIC CONTENT ----
if page == "Market Overview":
    st.title("Market Overview")
    df_indices = fetch_table("https://finance.yahoo.com/markets/world-indices/")
    if isinstance(df_indices, pd.DataFrame):
        st.dataframe(df_indices)

    df_gainers = fetch_table("https://finance.yahoo.com/markets/stocks/gainers/")
    if isinstance(df_gainers, pd.DataFrame):
        st.dataframe(df_gainers)

    df_losers = fetch_table("https://finance.yahoo.com/markets/stocks/losers/")
    if isinstance(df_losers, pd.DataFrame):
        st.dataframe(df_losers)


elif page == "Portfolio":
    st.title("Portfolio Overview")
    tickers_list = remove_duplicates([t.strip() for t in tickers_input.split(",") if t.strip()])
    if tickers_list:
        all_dfs = []
        for TICKER in tickers_list:
            hist = fetch_history(TICKER, PERIOD, INTERVAL)
            if isinstance(hist, pd.DataFrame):
                hist.insert(0, 'Ticker', TICKER)
                all_dfs.append(hist)
        if all_dfs:
            df_combined = pd.concat(all_dfs, ignore_index=True)
            fig = plot_line_multiple(df_combined, title="Portfolio Performance")
            st.plotly_chart(fig, use_container_width=True)

elif page == "Securities Analysis":
    st.title("Securities Analysis")
    tickers_list = remove_duplicates([t.strip() for t in tickers_input.split(",") if t.strip()])
    if len(tickers_list) == 1:
        TICKER = tickers_list[0]
        info = fetch_info(TICKER)
        if isinstance(info, dict):
            st.subheader(f"{TICKER} Info")
            st.dataframe(info_table(info))

        hist = fetch_history(TICKER, PERIOD, INTERVAL)
        if isinstance(hist, pd.DataFrame):
            # Compute indicators dynamically
            df = hist.copy()
            for ind in INDICATORS:
                if "SMA" in ind:
                    window = int(ind.split("_")[1])
                    df[ind] = df['Close'].rolling(window).mean()
                if "EMA" in ind:
                    window = int(ind.split("_")[1])
                    df[ind] = df['Close'].ewm(span=window, adjust=False).mean()
            fig = plot_candles_stick_bar(df, title=f"{TICKER} Candlestick", currency=info.get("currency", "USD"))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Securities Analysis only works for a single ticker.")


elif page == "Settings":
    st.title("Settings")
    st.write("Adjust app-wide preferences here")
    st.write(f"Last update: {st.session_state['current_time_price_page']}")