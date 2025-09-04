from functions import *
from contact import contact_form
from streamlit_javascript import st_javascript
from zoneinfo import ZoneInfo

@st.dialog("Contact Me")
def show_contact_form():
    contact_form()


st.set_page_config(
    page_title="Stock", # The page title, shown in the browser tab.
    page_icon=":material/stacked_line_chart:",
    layout="wide", # How the page content should be laid out.
    initial_sidebar_state="auto", # How the sidebar should start out.
    menu_items={ # Configure the menu that appears on the top-right side of this app.
        "Get help": "https://github.com/LMAPcoder" # The URL this menu item should point to.
    }
)

# ----LOGO----
st.html("""
  <style>
    [alt=Logo] {
      height: 3rem;
      width: auto;
      padding-left: 1rem;
    }
  </style>
""")

# ----TIME ZONE----
if 'timezone' not in st.session_state:
    timezone = st_javascript("""await (async () => {
                    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                    return userTimezone
                    })().then(returnValue => returnValue)""")
    if isinstance(timezone, int):
        st.stop()
    st.session_state['timezone'] = ZoneInfo(timezone)


# ----SESSION STATE -----
all_my_widget_keys_to_keep = {
    'current_time_price_page': datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None),
    'tickers': "MSFT",
    'dark_mode': False,
    'toggle_theme': False,
    'financial_period': "Annual"
}

for key in all_my_widget_keys_to_keep:
    if key not in st.session_state:
        st.session_state[key] = all_my_widget_keys_to_keep[key]

for key in all_my_widget_keys_to_keep:
    st.session_state[key] = st.session_state[key]

# ---- SIDEBAR ----
with st.sidebar:

    TOGGLE_THEME = st.toggle(
        label="Dark mode :material/dark_mode:",
        key="toggle_theme",
        help="Switch to dark theme"
        #value=False
    )

    if TOGGLE_THEME != st.session_state['dark_mode']:
        if TOGGLE_THEME:
            st._config.set_option(f'theme.base', "dark")
        else:
            st._config.set_option(f'theme.base', "light")
        st.session_state['dark_mode'] = TOGGLE_THEME
        st.rerun()

    PORTFOLIOS = {
        "Magnificent 7": "MSFT, GOOGL, AAPL, AMZN, META, TSLA, NVDA",
        "Top 5 Shanghai": "600519.SS, 601398.SS, 600036.SS, 601318.SS, 601857.SS",
        "Top 5 Tokyo": "7203.T, 6758.T, 8306.T, 6861.T, 7974.T",
        "Top 5 Hong Kong": "0700.HK, 9988.HK, 1299.HK, 3690.HK, 0939.HK",
        "Top 5 Euronext": "ASML.AS, MC.PA, OR.PA, RMS.PA, TTE.PA",
        "Top 5 London": "AZN.L, HSBA.L, SHEL.L, ULVR.L, DGE.L",
        "Top 5 Bombay": "RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS, ICICIBANK.NS",
        "Top 5 Toronto": "RY.TO, TD.TO, CNR.TO, ENB.TO, SHOP.TO",
        "Top 5 Frankfurt": "SAP.DE, SIE.DE, VOW3.DE, ALV.DE, DTE.DE",
        "Top 5 Australia": "BHP.AX, CBA.AX, CSL.AX, NAB.AX, WBC.AX",
        "Top 5 Singapore": "D05.SI, O39.SI, U11.SI, Z74.SI, 9CI.SI",
        "Top 5 São Paulo": "VALE3.SA, PETR4.SA, BBDC4.SA, ABEV3.SA, BBAS3.SA",
        "Top 5 Buenos Aires": "YPFD.BA, GGAL.BA, BMA.BA, BBAR.BA, PAMP.BA",
        "Oil&Gas": "CVX, XOM, SHEL, YPFD.BA, VIST, PAMP.BA",
        "Vehicles": "TSLA, F, GM, VOW3.DE, 7203.T, 1211.HK, RACE",
    }

    PORTFOLIO = st.selectbox(
        label="Portfolios",
        options=[None] + list(PORTFOLIOS.keys()),
        index=0,
        help="Choose from one of the predefined portfolios. Leave it as None to customize it"
    )

    if PORTFOLIO is not None:
        st.session_state["tickers"] = PORTFOLIOS[PORTFOLIO]

    TICKERS = st.text_input(
        label="Securities:",
        #value='MSFT',
        key='tickers'
    )

    st.write("eg.: MSFT, QQQ, SPY (max 10)")

    TICKERS = [item.strip() for item in TICKERS.split(",") if item.strip() != ""]

    TICKERS = remove_duplicates(TICKERS)

    if len(TICKERS) > 10:
        st.error("Only first 10 tickers are shown")
        TICKERS = TICKERS[:10]

    _tickers = list()
    for TICKER in TICKERS:
        info = fetch_info(TICKER)
        if isinstance(info, Exception):
            st.error(info)
            fetch_info.clear(TICKER)
        else:
            QUOTE_TYPE = info.get('quoteType', "")
            if QUOTE_TYPE not in ["EQUITY", "ETF", "INDEX"]:
                st.error(f"{TICKER} has an invalid quoteType ({QUOTE_TYPE})")
            else:
                _tickers.append(TICKER)

    TICKERS = _tickers

    period_list = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]

    PERIOD = st.selectbox(
        label="Period",
        options=period_list,
        index=3,
        placeholder="Select period...",
    )

    interval_list = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]

    if PERIOD in interval_list:
        idx = interval_list.index(PERIOD)
        interval_list = interval_list[:idx]

    INTERVAL = st.selectbox(
        label="Interval",
        options=interval_list,
        index=len(interval_list) - 4,
        placeholder="Select interval...",
    )

    if len(TICKERS) == 1:

        TOGGLE_VOL = st.toggle(
            label="Volume",
            value=True
        )

        indicator_list = ['SMA_20', 'SMA_50', 'SMA_200', 'SMA_X', 'EMA_20', 'EMA_50', 'EMA_200', 'EMA_X', 'ATR', 'MACD', 'RSI']

        INDICATORS = st.multiselect(
            label="Technical indicators:",
            options=indicator_list
        )

        if 'SMA_X' in INDICATORS or 'EMA_X' in INDICATORS:
            TIME_SPAN = st.slider(
                label="Select time span:",
                min_value=10,  # The minimum permitted value.
                max_value=200,  # The maximum permitted value.
                value=30  # The value of the slider when it first renders.
            )
            INDICATORS = [indicator.replace("X", str(TIME_SPAN)) if '_X' in indicator else indicator for indicator in INDICATORS]

    st.write("")
    button = st.button("Refresh data")

    if button:
        st.session_state['current_time_price_page'] = datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None)
        fetch_table.clear()
        fetch_info.clear()
        fetch_history.clear()
        #st.cache_data.clear()

    st.write("Last update:", st.session_state['current_time_price_page'])


    st.markdown("Made with ❤️ by Leonardo")

    col1, col2 = st.columns(2, gap="small")

    with col1:
        button = st.button("✉️ Contact Me", key="contact")
    with col2:
        st.link_button(
            label="",
            url="https://ko-fi.com/leoantiqui",
            icon=":material/coffee:"
        )

    if button:
        show_contact_form()

    # ----CREDIT----
    st.write("")
    st.write("")
    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.markdown("<p style='text-align: right;'>Powered by:</p>", unsafe_allow_html=True)
    with col2:
        st.image("static/imgs/logo_yahoo_lightpurple.svg", width=100)

# ---- MAINPAGE ----
st.title("Stock Market")

#----FIRST SECTION----

col1, col2, col3 = st.columns(3, gap="small")

with col1:

    URL = "https://finance.yahoo.com/markets/world-indices/"

    df = fetch_table(URL)

    INDICES = ["^GSPC", "^DJI", "^IXIC", "^N225", "^GDAXI", "^MERV"]

    st.subheader("Indices")
    if isinstance(df, Exception):
        st.error(df)
        fetch_table.clear(URL)
    if isinstance(df, pd.DataFrame):
        with st.container(border=True):
            i = 0
            for _ in range(3):
                cols = st.columns(2, gap="small")
                for col in cols:
                    with col:
                        row = df[df['Symbol'] == INDICES[i]].iloc[0]
                        name = row['Name']
                        symbol = row['Symbol']
                        price, change, change_pt = row['Price'].split()
                        st.metric(
                            label=f'{name} ({symbol})',
                            value=f'{price}',
                            delta=f'{change} {change_pt}'
                        )
                    i += 1

with col2:

    URL = "https://finance.yahoo.com/markets/stocks/gainers/"

    df = fetch_table(URL)

    st.subheader("Top Gainers")
    if isinstance(df, Exception):
        st.error(df)
        fetch_table.clear(URL)
    if isinstance(df, pd.DataFrame):
        with st.container(border=True):
            i = 0
            for _ in range(3):
                cols = st.columns(2, gap="small")
                for col in cols:
                    with col:
                        row = df.iloc[i]
                        name = row['Name']
                        symbol = row['Symbol']
                        price, change, change_pt = row['Price'].split()
                        st.metric(
                            label=f'{name} ({symbol})',
                            value=f'{price}',
                            delta=f'{change} {change_pt}'
                        )
                    i += 1

with col3:

    URL = "https://finance.yahoo.com/markets/stocks/losers/"

    df = fetch_table(URL)

    st.subheader("Top Losers")
    if isinstance(df, Exception):
        st.error(df)
        fetch_table.clear(URL)
    if isinstance(df, pd.DataFrame):
        with st.container(border=True):
            i = 0
            for _ in range(3):
                cols = st.columns(2, gap="small")
                for col in cols:
                    with col:
                        row = df.iloc[i]
                        name = row['Name']
                        symbol = row['Symbol']
                        price, change, change_pt = row['Price'].split()
                        st.metric(
                            label=f'{name} ({symbol})',
                            value=f'{price}',
                            delta=f'{change} {change_pt}'
                        )
                    i += 1


#----SECOND SECTION----

if len(TICKERS) == 0:
    st.header(f"Security: None")
    st.error("Error found")
    st.stop()

if len(TICKERS) == 1:

    TICKER = TICKERS[0]

    info = fetch_info(TICKER)

    NAME = info.get('shortName', "")

    st.header(f"Security: {TICKER}")
    st.write(f'{NAME}')

    # ----INFORMATION----
    with st.expander("More info"):
        col1, col2 = st.columns([0.3, 0.7], gap="small")
        with col1:
            df = info_table(info)
            PRICE = df.loc['Price', 0]
            df.drop(index="Price", inplace=True)
            df = df.reset_index()
            df = df.rename(columns={"index": "Feature", 0: "Value"})
            st.dataframe(
                data=df,
                hide_index=True
            )
        with col2:
            BUSINESS_SUMMARY = info.get('longBusinessSummary', "")
            st.write(BUSINESS_SUMMARY)

    #----METRICS----
    PREVIOUS_PRICE = info.get('previousClose', 0)
    CHANGE = PRICE - PREVIOUS_PRICE
    CHANGE_PER = (CHANGE/PREVIOUS_PRICE)*100
    HIGH = info.get('dayHigh', 0)
    LOW = info.get('dayLow', 0)
    CURRENCY = info.get('currency', "???")
    VOLUME = info.get('volume', 0)
    FIFTY_TWO_WEEK_LOW = info.get('fiftyTwoWeekLow', 0)
    FIFTY_TWO_WEEK_HIGH = info.get('fiftyTwoWeekHigh', 0)

    if CHANGE_PER == 0:
        st.metric(
            "Latest Price",
            value=f'{PRICE:.1f} {CURRENCY}'
            )
    else:
        st.metric(
            "Latest Price",
            value=f'{PRICE:.1f} {CURRENCY}',
            delta=f'{CHANGE:.1f} ({CHANGE_PER:.2f}%)'
            )


    col1, col2, col3 = st.columns(3, gap="medium")

    col1.metric(
        "High",
        value=f'{HIGH:.1f} {CURRENCY}'
        )

    col2.metric(
        "Low",
        value=f'{LOW:.1f} {CURRENCY}'
    )

    col3.metric(
        "Volume",
        value=f'{VOLUME}'
    )

    #----CANDLESTICK CHART----
    hist = fetch_history(TICKER, period=PERIOD, interval=INTERVAL)

    if isinstance(hist, Exception):
        st.error(hist)
        fetch_history.clear(TICKER, period=PERIOD, interval=INTERVAL)
        st.stop()

    df = hist.copy()

    # Price Performance

    col1, col2, col3 = st.columns(3, gap="medium")

    LEN = len(df)
    Pct_change_1P = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]

    col1.metric(
        "1 Period",
        value=f'{Pct_change_1P*100:.2f}%'
    )

    Pct_change_12P = (df['Close'].iloc[-1] - df['Close'].iloc[int(LEN/2)]) / df['Close'].iloc[int(LEN/2)]

    col2.metric(
        "1/2 Period",
        value=f'{Pct_change_12P*100:.2f}%'
    )

    Pct_change_14P = (df['Close'].iloc[-1] - df['Close'].iloc[int(LEN/4)]) / df['Close'].iloc[int(LEN/4)]

    col3.metric(
        "1/4 Period",
        value=f'{Pct_change_14P*100:.2f}%'
    )

    if not TOGGLE_VOL:
        df = df.drop(columns=['Volume'], axis=1)
    else:
        df['ΔVolume%'] = df['Volume'].pct_change(periods=1) * 100
        df['ΔVolume%'] = df['ΔVolume%'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else None)

    for INDICATOR in INDICATORS:
        if "SMA" in INDICATOR:
            window = int(INDICATOR.split("_")[1])
            df[INDICATOR] = df['Close'].rolling(window=window, min_periods=1).mean()
        if "EMA" in INDICATOR:
            window = int(INDICATOR.split("_")[1])
            df[INDICATOR] = df['Close'].ewm(span=window, adjust=False, min_periods=1).mean()

    if "ATR" in INDICATORS:

        Prev_Close = df['Close'].shift(1)
        High_Low = df['High'] - df['Low']
        High_PrevClose = abs(df['High'] - Prev_Close)
        Low_PrevClose = abs(df['Low'] - Prev_Close)

        df['TR'] = pd.concat([High_Low, High_PrevClose, Low_PrevClose], axis=1).max(axis=1)

        df['ATR'] = df['TR'].rolling(window=14, min_periods=1).mean()

        df = df.drop(columns=['TR'], axis=1)

    if "MACD" in INDICATORS:

        ema_short = df['Close'].ewm(span=12, adjust=False, min_periods=1).mean()
        ema_long = df['Close'].ewm(span=26, adjust=False, min_periods=1).mean()
        df['MACD'] = ema_short - ema_long
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False, min_periods=1).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']

    if "RSI" in INDICATORS:

        # delta = df['Close'].diff()
        delta = df['Close'].pct_change(periods=1) * 100

        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()

        # Calculate the relative strength (RS)
        rs = gain / loss

        df['RSI'] = 100 - (100 / (1 + rs))

    fig = plot_candles_stick_bar(df, title="Candlestick Chart", currency=CURRENCY)

    fig.add_hline(y=FIFTY_TWO_WEEK_LOW, line=dict(color="black", dash="dash", width=1), annotation_text='52 Week Low', row=1, col=1)
    fig.add_hline(y=FIFTY_TWO_WEEK_HIGH, line=dict(color="black", dash="dash", width=1), annotation_text='52 Week High', row=1, col=1)

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show data"):
        st.dataframe(
            data=df.reset_index(),
            hide_index=False
        )

else:

    TITLE = ", ".join(TICKERS)

    st.header(f"Securities: {TITLE}")

    dfs_hist = list()
    dfs_info = list()

    for TICKER in TICKERS:
        info = fetch_info(TICKER)

        df = info_table(info)
        df = df.rename(columns={0: TICKER})
        dfs_info.append(df)

        hist = fetch_history(TICKER, period=PERIOD, interval=INTERVAL)

        if isinstance(hist, Exception):
            st.error(hist)
            fetch_history.clear(TICKER, period=PERIOD, interval=INTERVAL)

        else:
            hist.insert(0, 'Ticker', TICKER)

            hist['Pct_change'] = ((hist['Close'] - hist['Close'].iloc[0]) / hist['Close'].iloc[0])

            dfs_hist.append(hist)

        if len(dfs_hist) == 0:
            st.error("Error found")
            st.stop()

    df = pd.concat(dfs_info, axis=1, join='inner')
    df = df.reset_index()
    df = df.rename(columns={"index": "Feature"})

    # ----INFORMATION----
    with st.expander("More info"):

        st.dataframe(
            data=df,
            hide_index=True
        )

    # ----PERFORMANCES----

    df = pd.concat(dfs_hist, ignore_index=False)

    fig = performance_table(df, TICKERS)

    st.plotly_chart(fig, use_container_width=True)

    # ----LINE CHART----

    fig = plot_line_multiple(df, "Percent Change Line Chart")

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show data"):
        st.dataframe(
            data=df.reset_index(),
            hide_index=False
        )