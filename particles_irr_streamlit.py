from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "particles_irr_analysis.db"

st.set_page_config(
    page_title="Particles / IRR — Problem Solving",
    layout="wide"
)

st.title("🔬 Particles / IRR — Manufacturing Problem Solving")
st.caption(
    "SUB30 • AOI20 • ICT40 | Operators A–D | Shifts 1–5 | "
    "Two product lines | Metallic / Non-metallic"
)

REQUIRED_TABLES = {
    "silver_particles_irr",
    "gold_station_summary",
    "gold_python_statistics",
    "gold_adjusted_model_coefficients",
    "gold_final_findings",
    "gold_sql_where_high_risk",
    "gold_sql_having_hotspots",
    "gold_sql_lag_lead_sequence",
    "gold_particle_temporal_proxy",
}

if not DB_PATH.exists():
    st.error(
        f"Database not found: {DB_PATH}. "
        "Keep particles_irr_analysis.db in the same folder as this Streamlit app."
    )
    st.stop()

def get_tables():
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    return {r[0] for r in rows}

missing = REQUIRED_TABLES - get_tables()
if missing:
    st.error(
        "The database exists but is missing required analytical tables: "
        + ", ".join(sorted(missing))
        + ". Re-run the updated notebook from top to bottom."
    )
    st.stop()

@st.cache_data
def read_sql(query):
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query(query, con)

data = read_sql("SELECT * FROM silver_particles_irr")
stats_table = read_sql("SELECT * FROM gold_python_statistics")
adjusted = read_sql("SELECT * FROM gold_adjusted_model_coefficients")
station_summary = read_sql("SELECT * FROM gold_station_summary")
where_risk = read_sql("SELECT * FROM gold_sql_where_high_risk")
hotspots = read_sql(
    "SELECT * FROM gold_sql_having_hotspots "
    "ORDER BY avg_particle_metric DESC"
)
lag_lead = read_sql("SELECT * FROM gold_sql_lag_lead_sequence")
temporal = read_sql("SELECT * FROM gold_particle_temporal_proxy")
findings = read_sql("SELECT * FROM gold_final_findings")

temporal["synthetic_timestamp"] = pd.to_datetime(
    temporal["synthetic_timestamp"]
)

# ------------------------
# Sidebar filters
# ------------------------
st.sidebar.header("Filters")

stations = st.sidebar.multiselect(
    "Station",
    sorted(data["station"].unique()),
    default=sorted(data["station"].unique())
)
operators = st.sidebar.multiselect(
    "Operator",
    sorted(data["operator_id"].unique()),
    default=sorted(data["operator_id"].unique())
)
shifts = st.sidebar.multiselect(
    "Shift",
    sorted(data["shift"].unique()),
    default=sorted(data["shift"].unique())
)
products = st.sidebar.multiselect(
    "Product line",
    sorted(data["product_line"].unique()),
    default=sorted(data["product_line"].unique())
)
particle_types = st.sidebar.multiselect(
    "Particle type",
    sorted(data["particle_type"].unique()),
    default=sorted(data["particle_type"].unique())
)
bands = st.sidebar.multiselect(
    "Particle size band",
    sorted(data["particle_size_band"].unique()),
    default=sorted(data["particle_size_band"].unique())
)

filtered = data[
    data["station"].isin(stations)
    & data["operator_id"].isin(operators)
    & data["shift"].isin(shifts)
    & data["product_line"].isin(products)
    & data["particle_type"].isin(particle_types)
    & data["particle_size_band"].isin(bands)
].copy()

if filtered.empty:
    st.warning("The selected filters return no observations.")
    st.stop()

# ------------------------
# 1. Context
# ------------------------
st.header("1. Problem context")
st.write(
    "Identify where particle contamination is highest and determine whether "
    "station, operator, shift, product line, particle type and particle size "
    "contribute to the observed variation and its relationship with IRR."
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Samples", f"{len(filtered):,}")
c2.metric("Avg particle count", f"{filtered['particle_count'].mean():.1f}")
c3.metric("Avg size (µm)", f"{filtered['particle_size_um'].mean():.1f}")
c4.metric("Avg particle metric", f"{filtered['particle_metric'].mean():.2f}")
c5.metric("Avg IRR", f"{filtered['irr'].mean():.2f}")

# ------------------------
# 2. EDA
# ------------------------
st.header("2. Exploratory analysis")

fig = px.histogram(
    filtered,
    x="particle_size_um",
    color="particle_type",
    facet_col="product_line",
    nbins=28,
    marginal="box",
    title="Particle Size by Type and Product Line"
)
st.plotly_chart(fig, width="stretch")

fig = px.box(
    filtered,
    x="station",
    y="particle_metric",
    color="product_line",
    points="outliers",
    title="Particle Metric by Station and Product Line"
)
st.plotly_chart(fig, width="stretch")

fig = px.box(
    filtered,
    x="operator_id",
    y="particle_metric",
    color="station",
    title="Operator Comparison within Stations"
)
st.plotly_chart(fig, width="stretch")

shift_summary = (
    filtered.groupby(["station","shift"], as_index=False)["particle_metric"]
    .mean()
)
fig = px.line(
    shift_summary,
    x="shift",
    y="particle_metric",
    color="station",
    markers=True,
    title="Average Particle Metric by Shift"
)
st.plotly_chart(fig, width="stretch")

fig = px.scatter(
    filtered,
    x="particle_metric",
    y="irr",
    color="station",
    symbol="particle_type",
    hover_data=[
        "operator_id","shift","product_line",
        "particle_size_um","particle_count"
    ],
    title="Particle Metric vs IRR"
)
st.plotly_chart(fig, width="stretch")

# ------------------------
# 3. Statistical conclusions
# ------------------------
st.header("3. Statistical evidence and conclusions")
st.dataframe(
    stats_table[["analysis","factor","statistic","p_value"]],
    column_config={
        "p_value": st.column_config.NumberColumn(format="%.2e")
    },
    width="stretch",
    hide_index=True
)

st.subheader("Adjusted multi-factor model")
st.dataframe(
    adjusted,
    column_config={
        "p_value": st.column_config.NumberColumn(format="%.2e")
    },
    width="stretch",
    hide_index=True
)

# ------------------------
# 4. Advanced SQL
# ------------------------
st.header("4. SQL problem solving")

tab_where, tab_having, tab_lag = st.tabs(
    ["WHERE — record screening", "HAVING — group hotspots", "LAG / LEAD"]
)

with tab_where:
    st.write(
        "`WHERE` isolates individual rows before aggregation. "
        "Here it screens above-average particle-metric observations "
        "that are large or metallic."
    )
    st.dataframe(
        where_risk.sort_values("particle_metric", ascending=False),
        width="stretch",
        hide_index=True
    )

with tab_having:
    st.write(
        "`HAVING` filters after `GROUP BY`. These are station/operator/shift "
        "combinations with at least 10 samples and an average particle metric "
        "above the overall process average."
    )
    st.dataframe(
        hotspots,
        width="stretch",
        hide_index=True
    )

with tab_lag:
    st.write(
        "`LAG` and `LEAD` compare the current observation with the previous "
        "and next observation inside the same station."
    )
    selected_station = st.selectbox(
        "Station for sequence table",
        sorted(lag_lead["station"].unique()),
        key="lag_station"
    )
    st.dataframe(
        lag_lead[lag_lead["station"] == selected_station].head(100),
        width="stretch",
        hide_index=True
    )

# ------------------------
# 5. SQL curated tables
# ------------------------
st.header("6. Database analytical tables")
st.subheader("Station summary")
st.dataframe(
    station_summary.sort_values("avg_particle_metric", ascending=False),
    width="stretch",
    hide_index=True
)

# ------------------------
# 6. Final conclusion
# ------------------------
st.header("7. Final conclusions")
for _, row in findings.iterrows():
    st.markdown(f"**{row['topic']}** — {row['result']}")
    st.caption(row["interpretation"])

st.subheader("Problem-solving conclusion")
st.markdown(
    """
The strongest current evidence points to **station** as the dominant process
segmentation, with **ICT40** showing the highest average particle metric in
this training dataset. Operator, shift, product line, particle type and
particle size also remain relevant and should be controlled when investigating
the physical mechanism.

The strong particle-metric/IRR association supports prioritising particle
contamination as a quality hypothesis, but it does **not** prove causation.

**Next steps**
1. Add cleaning, maintenance, material-lot and product-change events.
3. Add rejection/defect type and relate exposure to the defect outcome.
4. Validate particle measurement and classification with an MSA.
5. Investigate metallic-particle source/composition.
6. Run controlled before/after actions at the dominant station.
7. Use DOE where feasible.
"""
)
