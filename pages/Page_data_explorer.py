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

# ---- SESSION STATE FOR CACHE ----
if "df_cache" not in st.session_state:
    st.session_state["df_cache"] = {}  # key = data source identifier, value = DataFrame

# ---- SIDEBAR ----
st.sidebar.header("Data Source")

data_source = st.sidebar.radio(
    "Select data source:",
    ["Internal CSV", "Database"]
)
#"Upload CSV", 
df = None
source_key = None  # key for caching

# ---- UPLOAD CSV ----
# if data_source == "Upload CSV":
#     uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
#     if uploaded_file:
#         source_key = f"upload::{uploaded_file.name}"
#         if source_key in st.session_state["df_cache"]:
#             df = st.session_state["df_cache"][source_key]
#         else:
#             df = pd.read_csv(uploaded_file)
#             st.session_state["df_cache"][source_key] = df

# ---- INTERNAL CSV ----
if data_source == "Internal CSV":
    csv_folder = Path("data")
    csv_files = list(csv_folder.glob("*.csv"))
    if csv_files:
        file_choice = st.sidebar.selectbox(
            "Select a CSV file", 
            [f.name for f in csv_files]
        )
        source_key = f"internal::{file_choice}"
        if source_key in st.session_state["df_cache"]:
            df = st.session_state["df_cache"][source_key]
        else:
            df = pd.read_csv(csv_folder / file_choice)
            st.session_state["df_cache"][source_key] = df
    else:
        st.sidebar.info("No internal CSV files found in 'data/' folder.")
# ---- DATABASE ----
elif data_source == "Database":
    db_path = st.sidebar.text_input("SQLite DB path", value="data/local.db")
    table_name = st.sidebar.text_input("Table name", value="my_table")
    if Path(db_path).exists() and table_name:
        source_key = f"db::{db_path}::{table_name}"
        if source_key in st.session_state["df_cache"]:
            df = st.session_state["df_cache"][source_key]
        else:
            conn = sqlite3.connect(db_path)
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                st.session_state["df_cache"][source_key] = df
            except Exception as e:
                st.error(f"Error reading table: {e}")
            finally:
                conn.close()
    else:
        st.sidebar.info("Database file not found or table name missing.")

# ---- PROCESS CSV / DB DATA ----
if df is not None:

    # ---- CLEANING ----
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

    if 'Volume' in df.columns:
        df['Volume'] = df['Volume'].astype(str).str.replace(',', '').astype(float)

    if '% Change' not in df.columns or df['% Change'].isnull().all():
        if 'Close' in df.columns:
            df['% Change'] = df['Close'].pct_change() * 100

    if '% Change vs Average' not in df.columns or df['% Change vs Average'].isnull().all():
        if 'Close' in df.columns:
            df['% Change vs Average'] = (df['Close'] - df['Close'].rolling(window=20).mean()) / df['Close'].rolling(window=20).mean() * 100

    numeric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist()
    all_cols = df.columns.tolist()

    # ---- FILTERS ----
    st.sidebar.subheader("Filters (optional)")
    filter_col = st.sidebar.selectbox("Filter column", [None] + all_cols)
    filter_val = None
    if filter_col:
        unique_vals = df[filter_col].unique().tolist()
        filter_val = st.sidebar.selectbox(f"Select {filter_col}", unique_vals)
    if filter_col and filter_val is not None:
        df = df[df[filter_col] == filter_val]

    # ---- DATA TABLE ----
    st.subheader("Data Table")
    st.dataframe(df, use_container_width=True)

    # ---- VISUALIZATIONS ----
    st.subheader("Visualizations")
    chart_type = st.radio("Chart type", ["Line", "Bar", "Scatter", "Candlestick"])

    if chart_type in ["Line", "Bar", "Scatter"]:
        if len(numeric_cols) >= 2:
            x_col = st.selectbox("X axis", numeric_cols, index=0)
            y_col = st.selectbox("Y axis", numeric_cols, index=1)
            if chart_type == "Line":
                fig = px.line(df, x=x_col, y=y_col)
            elif chart_type == "Bar":
                fig = px.bar(df, x=x_col, y=y_col)
            else:
                fig = px.scatter(df, x=x_col, y=y_col)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough numeric columns for this chart type.")

    elif chart_type == "Candlestick":
        required_cols = ['Open', 'High', 'Low', 'Close']
        if all(col in df.columns for col in required_cols):
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close']
            )])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Candlestick chart requires columns: Open, High, Low, Close.")

    # ---- NUMERIC METRICS ----
    if numeric_cols:
        st.subheader("Summary Metrics")
        metrics_cols = st.columns(len(numeric_cols))
        for i, col in enumerate(numeric_cols):
            col_min = df[col].min()
            col_max = df[col].max()
            col_avg = df[col].mean()
            metrics_cols[i].metric(label=f"{col} Min", value=f"{col_min:.2f}")
            metrics_cols[i].metric(label=f"{col} Max", value=f"{col_max:.2f}")
            metrics_cols[i].metric(label=f"{col} Avg", value=f"{col_avg:.2f}")

else:
    st.info("Select or upload a data source to start exploring data.")