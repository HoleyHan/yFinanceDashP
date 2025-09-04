import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import json

st.set_page_config(
    page_title="Macro Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- SESSION STATE ----------------
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False

# ---------------- LOAD CONFIG ----------------
with open(".streamlit/app_refs.json") as f:
    app_refs = json.load(f)
macros = app_refs.get("macros", {})

# ---------------- SIDEBAR ----------------
with st.sidebar:
    page = st.selectbox("Pages", ["Macro Dashboard", "Settings"])
    st.markdown("---")

# ---------------- TOPBAR FILTERS ----------------
st.markdown("### Filters")
col1, col2, col3, col4, col5 = st.columns([2,3,3,2,1], gap="small")

with col1:
    region = st.selectbox("Region", sorted(list(macros.get("interest_rates", {}).keys())))

with col2:
    mode = st.radio("Mode", ["Single Category", "Overlay Multi-Category"])

with col3:
    all_categories = ["Interest Rates", "Inflation", "FX Rates", "Commodities Indices", "Other Economic Data"]
    if mode == "Single Category":
        category = st.selectbox("Category", all_categories)
        categories = [category]
    else:
        categories = st.multiselect("Categories", all_categories, default=["Interest Rates"])

with col4:
    period = st.selectbox("Period", app_refs.get("default_periods", ["1d","5d","1mo","3mo","6mo","1y"]))

with col5:
    toggle_theme = st.checkbox("Dark Mode", value=st.session_state["dark_mode"])
    st.session_state["dark_mode"] = toggle_theme

# ---------------- HELPER FUNCTIONS ----------------
@st.cache_data(ttl=600)
def fetch_ticker_data(ticker, period):
    try:
        df = yf.Ticker(ticker).history(period=period)[["Close"]].rename(columns={"Close": ticker})
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        st.error(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()

def get_tickers(category, region):
    if category == "Interest Rates":
        return macros.get("interest_rates", {}).get(region, {})
    elif category == "Inflation":
        return {f"{region} CPI": macros.get("inflation", {}).get(f"{region} CPI")}
    elif category == "FX Rates":
        return macros.get("fx_rates", {})
    elif category == "Commodities Indices":
        return macros.get("commodities_indices", {})
    elif category == "Other Economic Data":
        return macros.get("other", {}).get(region, {})
    return {}

# ---------------- PAGE LOGIC ----------------
if page == "Macro Dashboard":
    st.title("Macro Dashboard")

    if mode == "Single Category":
        tickers = get_tickers(category, region)
        if not tickers:
            st.info(f"No data available for {category} ({region})")
        else:
            df_category = pd.DataFrame()
            for name, ticker in tickers.items():
                df = fetch_ticker_data(ticker, period)
                if not df.empty:
                    df = df.rename(columns={ticker: name})
                    df_category = df if df_category.empty else pd.merge(df_category, df, on="Date", how="outer")

            if not df_category.empty:
                st.subheader(f"{category} Data Table")
                st.dataframe(df_category, use_container_width=True)

                df_pct = df_category.copy()
                for col in df_pct.columns:
                    if col != "Date":
                        df_pct[col] = df_pct[col] / df_pct[col].iloc[0] * 100

                fig = go.Figure()
                colors = ["#00BFFF","#1E90FF","#32CD32","#FF4500","#FFD700","#FF8C00","#8A2BE2"]
                bg_color = "#FFFFFF" if not st.session_state['dark_mode'] else "#262A2F"
                text_color = "#000000" if not st.session_state['dark_mode'] else "#F0F0F0"

                for i, col in enumerate(df_pct.columns):
                    if col != "Date":
                        fig.add_trace(go.Scatter(
                            x=df_pct["Date"], y=df_pct[col],
                            mode='lines+markers', name=col,
                            line=dict(color=colors[i%len(colors)], width=2),
                            marker=dict(size=4),
                            hovertemplate=f"%{{y:.2f}}%<br>Date: %{{x|%Y-%m-%d}}<br>{col}"
                        ))

                fig.update_layout(
                    title=f"{category} Trends ({region}) - % Change",
                    plot_bgcolor=bg_color,
                    paper_bgcolor=bg_color,
                    font_color=text_color,
                    hovermode="x unified",
                    xaxis_title="Date",
                    yaxis_title="% Change (normalized to 100)"
                )
                st.plotly_chart(fig, use_container_width=True)

    else:  # multi-category overlay
        df_overlay = pd.DataFrame()
        overlay_names = []
        for category in categories:
            tickers = get_tickers(category, region)
            for name, ticker in tickers.items():
                df = fetch_ticker_data(ticker, period)
                if not df.empty:
                    df = df.rename(columns={ticker: name})
                    df_overlay = df if df_overlay.empty else pd.merge(df_overlay, df, on="Date", how="outer")
                    overlay_names.append(name)

        if df_overlay.empty:
            st.info("No data available for selected categories")
        else:
            st.subheader("Overlay Data Table")
            st.dataframe(df_overlay, use_container_width=True)

            df_pct = df_overlay.copy()
            for col in df_pct.columns:
                if col != "Date":
                    df_pct[col] = df_pct[col] / df_pct[col].iloc[0] * 100

            fig = go.Figure()
            colors = ["#00BFFF","#1E90FF","#32CD32","#FF4500","#FFD700","#FF8C00","#8A2BE2"]
            bg_color = "#FFFFFF" if not st.session_state['dark_mode'] else "#262A2F"
            text_color = "#000000" if not st.session_state['dark_mode'] else "#F0F0F0"

            for i, col in enumerate(df_pct.columns):
                if col != "Date":
                    fig.add_trace(go.Scatter(
                        x=df_pct["Date"], y=df_pct[col],
                        mode='lines+markers', name=col,
                        line=dict(color=colors[i%len(colors)], width=2),
                        marker=dict(size=4),
                        hovertemplate=f"%{{y:.2f}}%<br>Date: %{{x|%Y-%m-%d}}<br>{col}"
                    ))

            fig.update_layout(
                title="Multi-Category Overlay - % Change Comparison",
                plot_bgcolor=bg_color,
                paper_bgcolor=bg_color,
                font_color=text_color,
                hovermode="x unified",
                xaxis_title="Date",
                yaxis_title="% Change (normalized to 100)"
            )
            st.plotly_chart(fig, use_container_width=True)

elif page == "Settings":
    st.title("Settings")
    st.write("App preferences go here")
    st.write(f"Dark Mode: {st.session_state['dark_mode']}")