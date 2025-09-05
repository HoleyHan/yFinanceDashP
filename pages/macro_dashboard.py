import streamlit as st
import pandas as pd
import yfinance as yf
import altair as alt
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="Macro Dashboard", page_icon=":bar_chart:", layout="wide")

# ---------------- SESSION STATE ----------------
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = True  # force dark theme

# ---------------- LOAD CONFIG ----------------
with open(".streamlit/app_refs.json") as f:
    app_refs = json.load(f)

macros = app_refs.get("macros", {})

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("Macro Dashboard Settings")
    page = st.radio("Pages", ["Macro Dashboard", "Settings"])

# ---------------- TOPBAR FILTERS ----------------
st.markdown("### Filters")
col1, col2, col3, col4 = st.columns([3, 2, 3, 2], gap="small")  # Category first

# --- Category ---
category_options = ["Interest Rates", "Inflation", "FX Rates", "Commodities", "Economic Indicators", "Indices", "Debt"]
with col1:
    category = st.selectbox("Category", category_options, index=category_options.index("Interest Rates"))

# --- Region (dynamic based on category) ---
def get_regions(category):
    if category == "Interest Rates":
        return sorted(macros.get("interest_rates", {}).keys())
    elif category == "Debt":
        return sorted(macros.get("debt", {}).keys())
    elif category == "Economic Indicators":
        return sorted(macros.get("economic_indicators", {}).keys())
    elif category == "Indices":
        return sorted(macros.get("indices", {}).keys())
    else:
        return ["Global"]  # FX, Commodities, Inflation are global

with col2:
    region_list = get_regions(category)
    region = st.selectbox("Region", region_list, index=region_list.index("US") if "US" in region_list else 0)

# --- Subcategory / Instruments ---
def get_instruments(category, region):
    if category == "Interest Rates":
        return macros.get("interest_rates", {}).get(region, {})
    elif category == "Debt":
        return macros.get("debt", {}).get(region, {})
    elif category == "Inflation":
        key = f"{region} CPI"
        return {key: macros["inflation"][key]} if key in macros.get("inflation", {}) else {}
    elif category == "FX Rates":
        return macros.get("fx_rates", {})
    elif category == "Commodities":
        return macros.get("commodities", {})
    elif category == "Economic Indicators":
        return macros.get("economic_indicators", {}).get(region, {})
    elif category == "Indices":
        return macros.get("indices", {}).get(region, {})
    return {}

# Flatten selected instruments safely
def flatten_selection(selected, instruments_dict):
    result = {}
    if isinstance(selected, dict):
        for sub_cat, names in selected.items():
            tickers_map = instruments_dict.get(sub_cat, {})
            for name in names:
                val = tickers_map.get(name)
                if isinstance(val, dict):
                    for k, v in val.items():
                        result[k] = v
                elif isinstance(val, str):
                    result[name] = val
    else:
        for name in selected:
            val = instruments_dict.get(name)
            if isinstance(val, dict):
                for k, v in val.items():
                    result[k] = v
            elif isinstance(val, str):
                result[name] = val
    return result

instruments_dict = get_instruments(category, region)
selected_instruments = {}

with col3:
    if instruments_dict:
        # Determine if instruments_dict is nested
        if any(isinstance(v, dict) for v in instruments_dict.values()):
            sub_category = st.selectbox(f"Select {category} Sub-Category", sorted(instruments_dict.keys()))
            sub_instruments = instruments_dict[sub_category]
            if len(sub_instruments) > 1:
                selected = st.multiselect(
                    f"Select {category} Instruments",
                    sorted(sub_instruments.keys()),
                    default=list(sub_instruments.keys())[:1]
                )
            else:
                selected = list(sub_instruments.keys())
                st.write(f"Selected Instrument: {selected[0]}")
            selected_instruments[sub_category] = selected
        else:
            if len(instruments_dict) > 1:
                selected = st.multiselect(
                    f"Select {category} Instruments",
                    sorted(instruments_dict.keys()),
                    default=list(instruments_dict.keys())[:1]
                )
            else:
                selected = list(instruments_dict.keys())
                st.write(f"Selected Instrument: {selected[0]}")
            selected_instruments = selected

# --- Period ---
with col4:
    periods = [p for p in app_refs.get("default_periods", []) if p != "1d"]
    period = st.selectbox("Period", periods, index=periods.index("1mo") if "1mo" in periods else 0)

# ---------------- FETCH DATA ----------------
@st.cache_data(ttl=600)
def fetch_ticker_data(ticker, period):
    try:
        df = yf.Ticker(ticker).history(period=period)[["Close"]].rename(columns={"Close": ticker})
        df.reset_index(inplace=True)
        if len(df) < 2:
            today = datetime.today()
            df = yf.Ticker(ticker).history(
                start=today - timedelta(days=365), 
                end=today
            )[["Close"]].rename(columns={"Close": ticker})
            df.reset_index(inplace=True)
        return df
    except Exception as e:
        st.error(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()

# ---------------- BUILD DATAFRAME ----------------
if selected_instruments:
    df_plot = pd.DataFrame()
    all_tickers = flatten_selection(selected_instruments, instruments_dict)

    for name, ticker in all_tickers.items():
        if isinstance(ticker, dict):
            st.warning(f"Skipping {name}: invalid ticker format")
            continue
        df = fetch_ticker_data(str(ticker), period)
        if not df.empty:
            df.rename(columns={ticker: name}, inplace=True)
            df_plot = df if df_plot.empty else pd.merge(df_plot, df, on="Date", how="outer")

    if not df_plot.empty:
        # ---------------- DATA TABLE ----------------
        numeric_cols = [c for c in df_plot.columns if c != "Date"]
        st.subheader(f"{category} Data Table")
        st.dataframe(
            df_plot.style.format({col: "{:.2f}" for col in numeric_cols}).set_properties(**{'text-align': 'center'}),
            use_container_width=True,
            height=min(600, 100 + 40*len(df_plot))
        )

        # ---------------- NORMALIZE ----------------
        df_pct = df_plot.copy()
        for col in numeric_cols:
            df_pct[col] = df_pct[col] / df_pct[col].iloc[0] * 100

        # ---------------- MELT FOR CHART ----------------
        df_melted = df_pct.melt(id_vars=['Date'], var_name='Instrument', value_name='Percent')

        # Map subcategory for coloring
        subcategory_map = {}
        if isinstance(selected_instruments, dict):
            for sub_cat, names in selected_instruments.items():
                for name in names:
                    subcategory_map[name] = sub_cat
        else:
            for name in selected_instruments:
                subcategory_map[name] = category
        df_melted['Subcategory'] = df_melted['Instrument'].map(subcategory_map)

        # ---------------- ALT AIR CHART ----------------
        alt.data_transformers.disable_max_rows()
        chart = alt.Chart(df_melted).mark_line(point=True).encode(
            x='Date:T',
            y=alt.Y('Percent:Q', title='% Change (normalized to 100)'),
            color=alt.Color('Instrument:N', legend=alt.Legend(title='Instrument')),
            tooltip=['Instrument:N', alt.Tooltip('Percent:Q', format=".2f"), 'Date:T']
        ).interactive()

        st.altair_chart(chart, use_container_width=True)

else:
    st.info(f"No data available for {category} ({region})")

# ---------------- SETTINGS ----------------
if page == "Settings":
    st.title("Settings")
    st.write("App preferences go here")