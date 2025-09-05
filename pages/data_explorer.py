import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import altair as alt

# -------------------------------
# SESSION STATE CACHE
# -------------------------------
if "df_cache" not in st.session_state:
    st.session_state["df_cache"] = {}

st.title("Data Explorer")

# -------------------------------
# PAGE LAYOUT: Side-by-side
# -------------------------------
source_col, display_col = st.columns([1, 3])

# -------------------------------
# DATA SOURCE SELECTION
# -------------------------------
df = None
source_key = None

with source_col:
    data_source = st.radio("Select data source:", ["Internal CSV/Parquet", "Database"])

    if data_source == "Internal CSV/Parquet":
        data_folder = Path("data")
        data_files = list(data_folder.glob("*.csv")) + list(data_folder.glob("*.parquet"))
        file_choice = st.selectbox("Select file", [f.name for f in data_files])
        if file_choice:
            source_key = f"internal::{file_choice}"
            if source_key in st.session_state["df_cache"]:
                df = st.session_state["df_cache"][source_key]
            else:
                path = data_folder / file_choice
                if path.suffix == ".csv":
                    df = pd.read_csv(path)
                else:
                    df = pd.read_parquet(path)
                st.session_state["df_cache"][source_key] = df

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
# DATA PROCESSING
# -------------------------------
if df is not None and not df.empty:
    # Handle Date column safely
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], utc=True)
        df = df.sort_values("Date").reset_index(drop=True)
        df["_Date_naive"] = df["Date"].dt.tz_convert(None)  # internal only

    numeric_cols = df.select_dtypes(include=["float", "int"]).columns.tolist()
    all_cols = df.columns.tolist()

    # -------------------------------
    # FILTERS (collapsible)
    # -------------------------------
    with display_col:
        with st.expander("Filters", expanded=False):
            filter_col = st.selectbox("Filter column", [None] + [c for c in all_cols if c != "Date"])
            filter_val = None
            if filter_col:
                filter_val = st.selectbox(f"Select {filter_col}", df[filter_col].unique())
            if st.button("Reset Filters"):
                filter_col = None
                filter_val = None

    # Apply filters
    df_filtered = df.copy()
    if filter_col and filter_val is not None:
        df_filtered = df_filtered[df_filtered[filter_col] == filter_val]

    # -------------------------------
    # CHART OPTIONS
    # -------------------------------
    with display_col:
        st.subheader("Chart Options")
        chart_type = st.selectbox("Chart type", ["Line", "Scatter"])
        y_cols = st.multiselect("Y-axis (select one or more)", numeric_cols, default=numeric_cols[:1])

    # -------------------------------
    # DATE PICKERS UNDER CHART
    # -------------------------------
    if "Date" in df.columns:
        col1, col2 = st.columns(2)
        start_date = col1.date_input("Start date", df["_Date_naive"].min().date())
        end_date = col2.date_input("End date", df["_Date_naive"].max().date())
        df_filtered = df_filtered[
            (df_filtered["_Date_naive"].dt.date >= start_date) &
            (df_filtered["_Date_naive"].dt.date <= end_date)
        ]

    # -------------------------------
    # PLOTTING (Altair)
    # -------------------------------
    if y_cols and not df_filtered.empty:
        # Melt numeric columns for Altair
        df_plot = df_filtered.melt(
            id_vars=["_Date_naive"],
            value_vars=y_cols,
            var_name="Metric",
            value_name="Value"
        )

        # Optional: color by daily delta
        df_plot["Delta"] = df_plot.groupby("Metric")["Value"].diff()
        df_plot["Color"] = df_plot["Delta"].apply(lambda x: "green" if x >= 0 else "red")

        # Auto-scale points and line width
        n_points = len(df_filtered)
        base_point_size = 20
        point_size = max(3, min(base_point_size, base_point_size * (100 / n_points)**0.5))
        line_width = max(1, point_size * 0.3)

        # Line chart
        line_chart = alt.Chart(df_plot).mark_line(interpolate='monotone', size=line_width).encode(
            x=alt.X('_Date_naive:T', title='Date'),
            y=alt.Y('Value:Q', title=', '.join(y_cols)),
            color='Metric:N',
            tooltip=['Metric:N', 'Value:Q', alt.Tooltip('_Date_naive:T', title='Date')]
        )

        # Points chart
        points = alt.Chart(df_plot).mark_point(filled=True, size=point_size).encode(
            x='_Date_naive:T',
            y='Value:Q',
            color='Metric:N',
            tooltip=['Metric:N', 'Value:Q', alt.Tooltip('_Date_naive:T', title='Date')]
        )

        # Combine line + points
        final_chart = (line_chart + points).interactive(bind_x=False)
        final_chart = final_chart.configure(background='black').configure_axis(
            labelColor='amber', titleColor='amber'
        ).configure_legend(
            labelColor='amber', titleColor='amber'
        ).configure_title(
            color='amber'
        )

        st.altair_chart(final_chart, use_container_width=True)

    # -------------------------------
    # HORIZONTAL DIVIDER
    # -------------------------------
    st.markdown("---")

    # -------------------------------
    # DATA TABLE
    # -------------------------------
    st.subheader("Data Table")

    # Styler: numeric columns formatted, text centered
    styler = df_filtered.style.set_properties(**{'text-align': 'center'})
    if numeric_cols:
        styler = styler.format({col: "{:.2f}" for col in numeric_cols}, na_rep="-")

    st.dataframe(styler, use_container_width=True)

    # -------------------------------
    # SUMMARY METRICS
    # -------------------------------
    st.subheader("Summary Metrics")
    metrics_cols = st.columns(len(y_cols))
    for i, col in enumerate(y_cols):
        val_min = df_filtered[col].min()
        val_max = df_filtered[col].max()
        val_avg = df_filtered[col].mean()
        metrics_cols[i].metric(label=f"{col} Min", value=f"{val_min:.2f}", delta=f"{val_min:.2f}")
        metrics_cols[i].metric(label=f"{col} Max", value=f"{val_max:.2f}", delta=f"{val_max:.2f}")
        metrics_cols[i].metric(label=f"{col} Avg", value=f"{val_avg:.2f}", delta=f"{val_avg:.2f}")

else:
    st.info("Select a file or database table to start exploring data.")