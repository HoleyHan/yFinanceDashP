import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# -------------------------------
# SESSION STATE CACHE
# -------------------------------
if "df_cache" not in st.session_state:
    st.session_state["df_cache"] = {}  # key = source_key, value = DataFrame

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def prettify(name: str) -> str:
    """Convert snake_case to Title Case for UI display."""
    return name.replace("_", " ").title()

# -------------------------------
# PAGE CONTAINER
# -------------------------------
with st.container():
    st.header("Data Explorer")

    # ---- DATA SOURCE SELECTION ----
    data_source = st.radio(
        "Select data source:",
        ["Internal CSV", "Database"]
    )

    df = None
    source_key = None

    # ---- INTERNAL CSV ----
    if data_source == "Internal CSV":
        csv_folder = Path("data")
        csv_files = list(csv_folder.glob("*.csv"))
        file_choice = None
        if csv_files:
            file_choice = st.selectbox(
                "Select CSV file",
                [f.name for f in csv_files]
            )

        if file_choice:
            source_key = f"internal::{file_choice}"
            if source_key in st.session_state["df_cache"]:
                df = st.session_state["df_cache"][source_key]
            else:
                df = pd.read_csv(csv_folder / file_choice)
                st.session_state["df_cache"][source_key] = df

    # ---- DATABASE ----
    elif data_source == "Database":
        db_path = st.text_input("SQLite DB path", value="data/local.db")
        table_name = st.text_input("Table name", value="my_table")

        if db_path and table_name and Path(db_path).exists():
            source_key = f"db::{db_path}::{table_name}"
            if source_key in st.session_state["df_cache"]:
                df = st.session_state["df_cache"][source_key]
            else:
                conn = sqlite3.connect(db_path)
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                finally:
                    conn.close()
                st.session_state["df_cache"][source_key] = df

# -------------------------------
# DATA PROCESSING & FILTERS
# -------------------------------
if df is not None:
    # Convert Date column if exists
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    numeric_cols = df.select_dtypes(include=["float", "int"]).columns.tolist()
    all_cols = df.columns.tolist()

    # ---- FILTERS ----
    display_to_col = {prettify(col): col for col in all_cols}
    with st.container():
        st.subheader("Filters")
        filter_display_col = st.selectbox("Filter column", [None] + list(display_to_col.keys()))
        filter_val = None
        if filter_display_col:
            col_name = display_to_col[filter_display_col]
            filter_val = st.selectbox(f"Select {filter_display_col}", df[col_name].unique())
        if filter_display_col and filter_val is not None:
            df = df[df[col_name] == filter_val]

    # ---- CHART OPTIONS ----
    with st.container():
        st.subheader("Chart Options")
        chart_type = st.selectbox("Select chart type", ["Line", "Bar", "Scatter", "Candlestick"])

        if numeric_cols:
            # Y-axis
            y_display_to_col = {prettify(col): col for col in numeric_cols}
            y_display = st.selectbox("Y axis", list(y_display_to_col.keys()))
            y_col = y_display_to_col[y_display]

            # X-axis: Date first if exists, then numeric excluding Y
            x_options = ["Date"] if "Date" in df.columns else []
            x_options += [col for col in numeric_cols if col != y_col]
            x_display_to_col = {prettify(col): col for col in x_options if col != "Date"}
            if "Date" in df.columns:
                x_display_to_col["Date"] = "Date"

            x_display = st.selectbox("X axis", list(x_display_to_col.keys()), index=0)
            x_col = x_display_to_col[x_display]
            x_data = df[x_col] if x_col in df.columns else df.index

            # ---- PLOTTING ----
            if chart_type == "Line":
                fig = px.line(df, x=x_data, y=y_col)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Bar":
                fig = px.bar(df, x=x_data, y=y_col)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Scatter":
                fig = px.scatter(df, x=x_data, y=y_col)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Candlestick":
                required_cols = ["Open", "High", "Low", "Close"]
                if all(col in df.columns for col in required_cols):
                    fig = go.Figure(data=[go.Candlestick(
                        x=df["Date"] if "Date" in df.columns else df.index,
                        open=df["Open"],
                        high=df["High"],
                        low=df["Low"],
                        close=df["Close"]
                    )])
                    st.plotly_chart(fig, use_container_width=True)

    # ---- DATA TABLE ----
    with st.container():
        st.subheader("Data Table")
        st.dataframe(df, use_container_width=True)

    # ---- SUMMARY METRICS ----
    if numeric_cols:
        with st.container():
            st.subheader("Summary Metrics")
            metrics_cols = st.columns(len(numeric_cols))
            for i, col in enumerate(numeric_cols):
                metrics_cols[i].metric(label=f"{prettify(col)} Min", value=f"{df[col].min():.2f}")
                metrics_cols[i].metric(label=f"{prettify(col)} Max", value=f"{df[col].max():.2f}")
                metrics_cols[i].metric(label=f"{prettify(col)} Avg", value=f"{df[col].mean():.2f}")
else:
    st.info("Select or upload a data source to start exploring data.")