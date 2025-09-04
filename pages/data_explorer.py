import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="My Data Explorer",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": "https://github.com/LMAPcoder"}
)

st.title("My Data Explorer")

# ---- SESSION STATE CACHE ----
if "df_cache" not in st.session_state:
    st.session_state["df_cache"] = {}  # key = source_key, value = DataFrame

# ---- SIDEBAR: User Controls ONLY ----
st.sidebar.header("Data Source & Filters")

data_source = st.sidebar.radio(
    "Select data source:",
    ["Internal CSV", "Database"]
)

# Internal CSV selection
file_choice = None
if data_source == "Internal CSV":
    csv_folder = Path("data")
    csv_files = list(csv_folder.glob("*.csv"))
    if csv_files:
        file_choice = st.sidebar.selectbox(
            "Select a CSV file",
            [f.name for f in csv_files]
        )

# Database selection
db_path = None
table_name = None
if data_source == "Database":
    db_path = st.sidebar.text_input("SQLite DB path", value="data/local.db")
    table_name = st.sidebar.text_input("Table name", value="my_table")

# Optional chart type
chart_type = st.sidebar.radio("Chart type", ["Line", "Bar", "Scatter", "Candlestick"])

# Optional filter
filter_col = None
filter_val = None

# ----------------- PAGE LOGIC -----------------
df = None
source_key = None

# ---- LOAD DATA FUNCTION ----
def load_internal_csv(file_name):
    return pd.read_csv(csv_folder / file_name)

def load_db_table(db_path, table_name):
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    finally:
        conn.close()

# ---- LAZY LOAD DATA ----
if data_source == "Internal CSV" and file_choice:
    source_key = f"internal::{file_choice}"
    if source_key in st.session_state["df_cache"]:
        df = st.session_state["df_cache"][source_key]
    else:
        df = load_internal_csv(file_choice)
        st.session_state["df_cache"][source_key] = df

elif data_source == "Database" and db_path and table_name and Path(db_path).exists():
    source_key = f"db::{db_path}::{table_name}"
    if source_key in st.session_state["df_cache"]:
        df = st.session_state["df_cache"][source_key]
    else:
        df = load_db_table(db_path, table_name)
        st.session_state["df_cache"][source_key] = df

# ---- PROCESS DATA ----
if df is not None:

    # Date as index if exists
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)

    # Convert Volume
    if "Volume" in df.columns:
        df["Volume"] = df["Volume"].astype(str).str.replace(',', '').astype(float)

    # Compute % Change
    if "% Change" not in df.columns or df["% Change"].isnull().all():
        if "Close" in df.columns:
            df["% Change"] = df["Close"].pct_change() * 100

    # Compute % Change vs Average
    if "% Change vs Average" not in df.columns or df["% Change vs Average"].isnull().all():
        if "Close" in df.columns:
            df["% Change vs Average"] = (df["Close"] - df["Close"].rolling(20).mean()) / df["Close"].rolling(20).mean() * 100

    numeric_cols = df.select_dtypes(include=["float", "int"]).columns.tolist()
    all_cols = df.columns.tolist()

    # ---- FILTERS ----
    st.sidebar.subheader("Optional Filters")
    filter_col = st.sidebar.selectbox("Filter column", [None] + all_cols)
    if filter_col:
        unique_vals = df[filter_col].unique().tolist()
        filter_val = st.sidebar.selectbox(f"Select {filter_col}", unique_vals)
    if filter_col and filter_val is not None:
        df = df[df[filter_col] == filter_val]

    # ---- DATA TABLE ----
    st.subheader("Data Table")
    st.dataframe(df, use_container_width=True)

    # ---- PLOTS ----
    st.subheader("Visualizations")

    if chart_type in ["Line", "Bar", "Scatter"]:
        if numeric_cols:
            y_col = st.selectbox("Y axis", numeric_cols, index=0)
            x_col = df.index if "Date" in df.columns else st.selectbox("X axis", numeric_cols, index=0)
            if chart_type == "Line":
                fig = px.line(df, x=x_col, y=y_col)
            elif chart_type == "Bar":
                fig = px.bar(df, x=x_col, y=y_col)
            else:
                fig = px.scatter(df, x=x_col, y=y_col)
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Candlestick":
        required_cols = ["Open", "High", "Low", "Close"]
        if all(col in df.columns for col in required_cols):
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"]
            )])
            st.plotly_chart(fig, use_container_width=True)

    # ---- SUMMARY METRICS ----
    if numeric_cols:
        st.subheader("Summary Metrics")
        metrics_cols = st.columns(len(numeric_cols))
        for i, col in enumerate(numeric_cols):
            metrics_cols[i].metric(label=f"{col} Min", value=f"{df[col].min():.2f}")
            metrics_cols[i].metric(label=f"{col} Max", value=f"{df[col].max():.2f}")
            metrics_cols[i].metric(label=f"{col} Avg", value=f"{df[col].mean():.2f}")

else:
    st.info("Select or upload a data source to start exploring data.")