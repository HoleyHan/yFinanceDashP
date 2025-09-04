from functions import *
from contact import contact_form
from streamlit_javascript import st_javascript
from zoneinfo import ZoneInfo

@st.dialog("Contact Me")
def show_contact_form():
    contact_form()

st.set_page_config(
    page_title="Financials", # The page title, shown in the browser tab.
    page_icon=":material/finance:",
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
    'current_time_financials_page': datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None),
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

    TICKERS = st.text_input(
        label="Securities:",
        key='tickers'
    )

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
            if QUOTE_TYPE not in ["EQUITY"]:
                st.error(f"{TICKER} has an invalid quoteType ({QUOTE_TYPE})")
            else:
                _tickers.append(TICKER)

    TICKERS = _tickers

    TIME_PERIOD = st.radio(
        label="Time Period:",
        options=["Annual", "Quarterly"],
        key="financial_period"
    )

    st.write("")
    button = st.button("Refresh data")

    if button:
        st.session_state['current_time_financials_page'] = datetime.datetime.now(st.session_state['timezone']).replace(microsecond=0, tzinfo=None)
        fetch_info.clear()
        fetch_balance.clear()
        fetch_income.clear()
        fetch_cash.clear()
        #st.cache_data.clear()

    st.write("Last update:", st.session_state['current_time_financials_page'])

    st.markdown("Made with ❤️ by Leonardo")

    button = st.button("✉️ Contact Me", key="contact")

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

st.title("Financials")

if len(TICKERS) == 0:
    st.header(f"Security: None")
    st.error("Error found")
    st.stop()

if len(TICKERS) == 1:

    TICKER = TICKERS[0]

    info = fetch_info(TICKER)

    NAME = info.get('shortName', "")
    st.write(f'{NAME}')

    bs = fetch_balance(TICKER, tp=TIME_PERIOD) #balance sheet
    ist = fetch_income(TICKER, tp=TIME_PERIOD) #income statement
    cf = fetch_cash(TICKER, tp=TIME_PERIOD) #cash flow

    CURRENCY = info.get('financialCurrency', "???")

    #----CAPITAL STRUCTURE-----

    st.header("Capital Structure")

    if isinstance(bs, Exception):
        st.error(bs)
        fetch_balance.clear(TICKER, tp=TIME_PERIOD)
        st.stop()

    fig = plot_capital(bs, ticker=TICKER, currency=CURRENCY)

    st.plotly_chart(
        fig,
        use_container_width=True,
        # theme=None
    )

    # ----BALANCE SHEET----

    st.header("Balance Sheet")

    st.write("The balance sheet refers to a financial statement that reports "
             "a company's assets, liabilities, and shareholder equity at a specific point in time.")


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
        st.dataframe(
            data=bs,
            hide_index=False
        )


    # ----INCOME STATEMENT----

    st.header("Income Statement")

    st.write("The income statement refers to a financial statement that tracks the "
             "company's revenue, expenses, gains, and losses during a set period.")

    if isinstance(ist, Exception):
        st.error(ist)
        fetch_income.clear(TICKER, tp=TIME_PERIOD)
        st.stop()

    fig = plot_income(ist, ticker=TICKER, currency=CURRENCY)

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ratios"):
        tab1, tab2, tab3 = st.tabs(
            ["Net Margin", "Earnings per Share", "Price-to-Earnings Ratio"]
        )

        with tab1:

            st.write("Net profit margin measures how much net income or profit a company generates"
                     " as a percentage of its revenue.")

            try:
                fig = plot_margins(ist, ticker=TICKER)
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    #theme=None
                )
            except:
                st.error("The data available is not enough to plot this ratio")

        with tab2:

            st.write("Basic earnings per share (EPS) is a rough measurement of the amount of a "
                     "company's profit that can be allocated to one share of its common stock.")

            try:
                fig = plot_eps(TICKER)
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    #theme=None
                )
            except:
                st.error("The data available is not enough to plot this ratio")

        with tab3:

            st.write("The price-to-earnings (P/E) ratio measures a company's share price"
                     " relative to its earnings per share (EPS)")

            try:
                fig = plot_pe_ratio(TICKER)
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    # theme=None
                )
            except:
                st.error("The data available is not enough to plot this ratio")

    with st.expander("Show data"):
        st.dataframe(
            data=ist,
            hide_index=False
        )

    # ----CASH FLOW----

    st.header("Cash Flow")

    st.write("The cash flow statement provides aggregate data regarding all cash inflows and"
             " all cash outflows during a given period")

    if isinstance(cf, Exception):
        st.error(cf)
        fetch_cash.clear(TICKER, tp=TIME_PERIOD)
        st.stop()

    fig = plot_cash(cf, ticker=TICKER, currency=CURRENCY)

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show data"):
        st.dataframe(
            data=cf,
            hide_index=False
        )

else:

    # ----CAPITAL STRUCTURE-----

    st.header("Capital Structure")

    fig = plot_capital_multiple(TICKERS, tp=TIME_PERIOD)

    st.plotly_chart(
        fig,
        use_container_width=True,
        # theme=None
    )


    # ----BALANCE SHEET----

    st.header("Balance Sheet")

    fig = plot_balance_multiple(TICKERS, tp=TIME_PERIOD)

    st.plotly_chart(fig, use_container_width=True)

    # ----INCOME STATEMENT----

    st.header("Income Statement")

    fig = plot_income_multiple(TICKERS, tp=TIME_PERIOD)

    st.plotly_chart(fig, use_container_width=True)

    # ----CASH FLOW----

    st.header("Cash Flow")

    fig = plot_cash_multiple(TICKERS, tp=TIME_PERIOD)

    st.plotly_chart(fig, use_container_width=True)
