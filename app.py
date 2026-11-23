import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & CUSTOM STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ChristGreenCover | Campus Flora & Carbon Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.25rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #f8faf9;
        border: 1px solid #cbd5e1;
        padding: 14px 18px;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f3d24;
    }
    .badge-live {
        background-color: #ecfdf5;
        color: #065f46;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        border: 1px solid #a7f3d0;
        display: inline-block;
        text-transform: uppercase;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #cbd5e1 !important;
        border-radius: 8px !important;
        background-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATA LOADING & CACHING
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    trees = pd.read_csv("christ_campus_tree_inventory.csv")
    telemetry = pd.read_csv("christ_carbon_telemetry_365d.csv")
    telemetry["date"] = pd.to_datetime(telemetry["date"])
    return trees, telemetry

df_trees, df_telemetry = load_data()

# -----------------------------------------------------------------------------
# URL QUERY PARAMS & SIDEBAR FILTERS
# -----------------------------------------------------------------------------
query_params = st.query_params
default_period = query_params.get("period", "3M")
period_options = ["1M", "3M", "6M", "1Y"]
if default_period not in period_options:
    default_period = "3M"

with st.sidebar:
    st.markdown("### ChristGreenCover")
    st.caption("ChristGreenCover: Campus Flora, Tree Inventory & Carbon Offset Analytics Dashboard")
    st.divider()

    selected_period = st.segmented_control(
        "Telemetry Window",
        options=period_options,
        default=default_period,
        help="Synchronized with URL ?period= query parameter"
    )
    if selected_period:
        st.query_params["period"] = selected_period

    all_zones = sorted(df_trees["campus_zone"].unique())
    selected_zones = st.multiselect("Campus Zones", options=all_zones, default=all_zones)

    native_filter = st.multiselect(
        "Origin Classification",
        options=["Native", "Naturalized", "Exotic"],
        default=["Native", "Naturalized", "Exotic"]
    )

    health_filter = st.multiselect(
        "Tree Health Status",
        options=sorted(df_trees["health_status"].unique()),
        default=sorted(df_trees["health_status"].unique())
    )

# Apply Filters
filtered_trees = df_trees[
    (df_trees["campus_zone"].isin(selected_zones)) &
    (df_trees["native_status"].isin(native_filter)) &
    (df_trees["health_status"].isin(health_filter))
].copy()

period_days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}
days_window = period_days_map.get(selected_period or "3M", 90)
max_date = df_telemetry["date"].max()
filtered_ts = df_telemetry[df_telemetry["date"] >= (max_date - timedelta(days=days_window))].copy()

# Scale telemetry proportionally to selected zones
zone_share = len(filtered_trees) / max(len(df_trees), 1)
filtered_ts["zone_co2_seq_kg"] = (filtered_ts["co2_sequestered_kg"] * zone_share).round(2)

# -----------------------------------------------------------------------------
# HEADER BAR
# -----------------------------------------------------------------------------
latest_sync = df_telemetry["date"].max().strftime("%d %b %Y")
col_title, col_status = st.columns([4, 1])
with col_title:
    st.title("ChristGreenCover: Campus Flora & Carbon Analytics")
    st.caption("Ecological Inventory, Allometric Carbon Sequestration & Microclimate Telemetry")
with col_status:
    st.markdown(
        f"<div style='text-align:right; padding-top:14px;'><span class='badge-live'>IoT & GIS Synced ({latest_sync})</span></div>",
        unsafe_allow_html=True
    )

# -----------------------------------------------------------------------------
# TOP NAVIGATION TABS
# -----------------------------------------------------------------------------
tab_overview, tab_analytics, tab_spatial, tab_inventory = st.tabs([
    "Overview",
    "Carbon & Biodiversity Analytics",
    "Campus GIS Canopy Map",
    "Tree Inventory & QR Explorer"
])

# Precompute common KPI metrics
total_trees = len(filtered_trees)
unique_species = filtered_trees["botanical_name"].nunique()
total_stored_tonnes = filtered_trees["stored_co2_kg"].sum() / 1000.0
annual_seq_tonnes = filtered_trees["annual_co2_sequestration_kg"].sum() / 1000.0
canopy_hectares = filtered_trees["canopy_area_sqm"].sum() / 10000.0
native_pct = (filtered_trees["native_status"].eq("Native").mean() * 100) if total_trees > 0 else 0.0
annual_o2_tonnes = filtered_trees["annual_o2_production_kg"].sum() / 1000.0
stormwater_kl = filtered_trees["stormwater_intercepted_liters"].sum() / 1000.0

# -----------------------------------------------------------------------------
# TAB 1: OVERVIEW
# -----------------------------------------------------------------------------
with tab_overview:
    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric(
        label="Tagged Campus Trees",
        value=f"{total_trees:,}",
        delta=f"{unique_species} Botanical Species",
        chart_data=filtered_ts["new_saplings_added"].cumsum().tolist()[-20:],
        chart_type="area"
    )
    k2.metric(
        label="Cumulative Carbon Stock",
        value=f"{total_stored_tonnes:,.1f} tCO2e",
        delta=f"+{annual_seq_tonnes:.1f} t/yr Active Sink",
        chart_data=filtered_ts["zone_co2_seq_kg"].tolist()[-20:],
        chart_type="line"
    )
    k3.metric(
        label=f"Period Sequestration ({selected_period})",
        value=f"{filtered_ts['zone_co2_seq_kg'].sum()/1000:.2f} tCO2",
        delta=f"{filtered_ts['zone_co2_seq_kg'].mean():.1f} kg/day avg",
        chart_data=filtered_ts["zone_co2_seq_kg"].tolist()[-20:],
        chart_type="bar"
    )
    k4.metric(
        label="Green Canopy Cover",
        value=f"{canopy_hectares:.2f} ha",
        delta=f"-{filtered_ts['canopy_cooling_delta_c'].mean():.1f} C Heat Reduction"
    )
    k5.metric(
        label="Native Flora Index",
        value=f"{native_pct:.1f}%",
        delta="Biodiversity Target: 70%"
    )

    st.write("")

    # Quick Bio-Audit Simulator
    with st.container(border=True):
        st.subheader("Quick Bio-Audit Simulator — CSA Plantation Drive Planner")
        st.caption("Model the projected ecological impact of adding new saplings across CHRIST University campus zones.")
        sim_c1, sim_c2, sim_c3, sim_c4 = st.columns([2, 1, 1, 1])
        with sim_c1:
            sim_saplings = st.slider(
                "Simulate CSA Sapling Drive (+New Trees)",
                min_value=0,
                max_value=200,
                value=50,
                step=10
            )
        est_added_co2_tonnes = (sim_saplings * 21.8) / 1000.0
        projected_total_seq = annual_seq_tonnes + est_added_co2_tonnes
        est_added_o2_tonnes = (sim_saplings * 15.8) / 1000.0

        sim_c2.metric(
            label="Projected Annual Offset",
            value=f"+{est_added_co2_tonnes:.2f} tCO2/yr",
            delta="At tree maturity"
        )
        sim_c3.metric(
            label="New Campus Sink Rate",
            value=f"{projected_total_seq:.2f} tCO2/yr",
            delta=f"+{(est_added_co2_tonnes / max(annual_seq_tonnes, 0.01) * 100):.1f}% capacity"
        )
        sim_c4.metric(
            label="Extra Oxygen Release",
            value=f"+{est_added_o2_tonnes:.2f} tO2/yr",
            delta=f"Supports ~{int(sim_saplings * 2)} individuals/yr"
        )

    st.write("")

    ov_left, ov_right = st.columns([3, 2])
    with ov_left:
        with st.container(border=True):
            st.subheader(f"Net Carbon Offset Trajectory ({selected_period})")
            fig_ov_ts = go.Figure()
            fig_ov_ts.add_trace(go.Scatter(
                x=filtered_ts["date"], y=filtered_ts["zone_co2_seq_kg"],
                mode="lines", name="Flora CO2 Sequestered (kg/day)",
                line=dict(color="#15803d", width=2.5), fill="tozeroy",
                fillcolor="rgba(21, 128, 61, 0.12)"
            ))
            if sim_saplings > 0:
                daily_sim_bonus = (sim_saplings * 21.8) / 365.0
                fig_ov_ts.add_trace(go.Scatter(
                    x=filtered_ts["date"], y=filtered_ts["zone_co2_seq_kg"] + daily_sim_bonus,
                    mode="lines", name=f"Projected w/ +{sim_saplings} CSA Saplings",
                    line=dict(color="#0d9488", width=2, dash="dash")
                ))
            fig_ov_ts.add_trace(go.Scatter(
                x=filtered_ts["date"], y=filtered_ts["campus_operational_emissions_kg"],
                mode="lines", name="Campus Baseline Emissions (kg/day)",
                line=dict(color="#dc2626", width=1.8)
            ))
            fig_ov_ts.update_layout(
                height=340, margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title="", yaxis_title="kg CO2e / day",
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_ov_ts, use_container_width=True)

    with ov_right:
        with st.container(border=True):
            st.subheader("Ecosystem Services & Origin Mix")
            origin_counts = (
                filtered_trees.groupby("native_status", as_index=False)
                .agg(Trees=("tree_id", "count"), Stored_CO2_kg=("stored_co2_kg", "sum"))
            )
            fig_donut = px.pie(
                origin_counts,
                names="native_status",
                values="Trees",
                hole=0.55,
                color="native_status",
                color_discrete_map={"Native": "#166534", "Naturalized": "#0d9488", "Exotic": "#d97706"}
            )
            fig_donut.update_layout(
                height=235, margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

            es1, es2 = st.columns(2)
            es1.metric("Annual O2 Output", f"{annual_o2_tonnes:.1f} t/yr")
            es2.metric("Stormwater Captured", f"{stormwater_kl:,.0f} kL/yr")

# -----------------------------------------------------------------------------
# TAB 2: CARBON & BIODIVERSITY ANALYTICS
# -----------------------------------------------------------------------------
with tab_analytics:
    # Row 1: Time Series + Zone Bar Chart
    c_left, c_right = st.columns([3, 2])

    with c_left:
        with st.container(border=True):
            st.subheader(f"Daily Carbon Offset vs. Campus Emissions ({selected_period})")
            fig_ts = go.Figure()
            fig_ts.add_trace(go.Scatter(
                x=filtered_ts["date"], y=filtered_ts["zone_co2_seq_kg"],
                mode="lines", name="Flora CO2 Sequestered (kg/day)",
                line=dict(color="#15803d", width=2.5), fill="tozeroy",
                fillcolor="rgba(21, 128, 61, 0.12)"
            ))
            fig_ts.add_trace(go.Scatter(
                x=filtered_ts["date"], y=filtered_ts["solar_carbon_offset_kg"],
                mode="lines", name="Rooftop Solar Offset (kg/day)",
                line=dict(color="#0284c7", width=2, dash="dot")
            ))
            fig_ts.add_trace(go.Scatter(
                x=filtered_ts["date"], y=filtered_ts["campus_operational_emissions_kg"],
                mode="lines", name="Campus Baseline Emissions (kg/day)",
                line=dict(color="#dc2626", width=1.8)
            ))
            fig_ts.update_layout(
                height=350, margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title="", yaxis_title="kg CO2e / day",
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_ts, use_container_width=True)

    with c_right:
        with st.container(border=True):
            st.subheader("Carbon Storage by Campus Zone")
            zone_summary = (
                filtered_trees.groupby("campus_zone", as_index=False)
                .agg(
                    Trees=("tree_id", "count"),
                    Stored_CO2_Tonnes=("stored_co2_kg", lambda s: round(s.sum() / 1000, 2)),
                    Annual_Seq_Tonnes=("annual_co2_sequestration_kg", lambda s: round(s.sum() / 1000, 2)),
                    Canopy_Area_Sqm=("canopy_area_sqm", lambda s: round(s.sum(), 1)),
                    Avg_Age_Yrs=("age_years", lambda s: round(s.mean(), 1))
                )
                .sort_values("Stored_CO2_Tonnes", ascending=True)
            )
            fig_zone = px.bar(
                zone_summary, x="Stored_CO2_Tonnes", y="campus_zone",
                orientation="h", text="Stored_CO2_Tonnes",
                color="Stored_CO2_Tonnes", color_continuous_scale="Greens",
                labels={"Stored_CO2_Tonnes": "Stored CO2 (Tonnes)", "campus_zone": ""}
            )
            fig_zone.update_layout(
                height=350, margin=dict(l=10, r=10, t=20, b=10),
                coloraxis_showscale=False,
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_zone, use_container_width=True)

    st.write("")

    # Row 2: Species Bar Chart + Canopy Health Box Plot
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        with st.container(border=True):
            st.subheader("Top Carbon-Sequestering Campus Species")
            top_sp = (
                filtered_trees.groupby(["common_name", "botanical_name", "native_status"], as_index=False)
                .agg(
                    Tree_Count=("tree_id", "count"),
                    Total_CO2_kg=("stored_co2_kg", "sum"),
                    Annual_Seq_kg=("annual_co2_sequestration_kg", "sum"),
                    Avg_Canopy_m=("canopy_diameter_m", "mean")
                )
                .sort_values("Total_CO2_kg", ascending=False)
            )
            fig_sp = px.bar(
                top_sp.head(10), x="common_name", y="Total_CO2_kg", color="native_status",
                color_discrete_map={"Native": "#166534", "Naturalized": "#0d9488", "Exotic": "#d97706"},
                labels={"common_name": "Species", "Total_CO2_kg": "Cumulative CO2 Stored (kg)", "native_status": "Origin"}
            )
            fig_sp.update_layout(
                height=330, margin=dict(l=10, r=10, t=20, b=10),
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_sp, use_container_width=True)

    with c_b2:
        with st.container(border=True):
            st.subheader("Canopy Health & Soil Moisture Distribution")
            fig_box = px.box(
                filtered_trees, x="health_status", y="soil_moisture_pct", color="health_status",
                color_discrete_map={
                    "Healthy": "#16a34a", "Moderate": "#eab308",
                    "Needs Pruning": "#f97316", "Critical / Pest Alert": "#dc2626"
                },
                labels={"health_status": "Arborist Health Status", "soil_moisture_pct": "Root-Zone Soil Moisture (%)"}
            )
            fig_box.update_layout(
                height=330, margin=dict(l=10, r=10, t=20, b=10),
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_box, use_container_width=True)

    st.write("")

    # Row 3: Color-Styled Analytical Summary Tables with Inline Bar & Area Sparklines
    t_col1, t_col2 = st.columns(2)

    with t_col1:
        with st.container(border=True):
            st.subheader("Zone-Wise Carbon & Canopy Audit Summary")
            st.caption("Color-graded carbon stock, age distribution sparklines, and campus share bars.")
            zone_table = zone_summary.sort_values("Stored_CO2_Tonnes", ascending=False).copy()
            zone_table["Share_of_Stock_Pct"] = (
                zone_table["Stored_CO2_Tonnes"] / max(zone_table["Stored_CO2_Tonnes"].sum(), 0.01) * 100
            ).round(1)

            # Build inline sparkline list of stored CO2 per tree in each zone
            zone_spark_map = (
                filtered_trees.sort_values("age_years")
                .groupby("campus_zone")["stored_co2_kg"]
                .apply(list)
                .to_dict()
            )
            zone_table["CO2_Profile"] = zone_table["campus_zone"].map(lambda z: zone_spark_map.get(z, [0]))

            zone_display = zone_table[[
                "campus_zone", "Trees", "Stored_CO2_Tonnes",
                "Annual_Seq_Tonnes", "CO2_Profile", "Share_of_Stock_Pct"
            ]]
            styled_zone = (
                zone_display.style
                .background_gradient(subset=["Stored_CO2_Tonnes"], cmap="Greens")
                .background_gradient(subset=["Annual_Seq_Tonnes"], cmap="BuGn")
                .format({"Stored_CO2_Tonnes": "{:.2f}", "Annual_Seq_Tonnes": "{:.2f}"})
            )
            st.dataframe(
                styled_zone,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "campus_zone": "Campus Zone",
                    "Trees": st.column_config.NumberColumn("Trees", format="%d"),
                    "Stored_CO2_Tonnes": "Stored CO2 (t)",
                    "Annual_Seq_Tonnes": "Sink (t/yr)",
                    "CO2_Profile": st.column_config.AreaChartColumn(
                        "Age-to-Carbon Curve",
                        y_min=0,
                        y_max=float(df_trees["stored_co2_kg"].max())
                    ),
                    "Share_of_Stock_Pct": st.column_config.ProgressColumn(
                        "Carbon Share", min_value=0, max_value=100, format="%.1f%%"
                    )
                }
            )

    with t_col2:
        with st.container(border=True):
            st.subheader("Species Biodiversity & Sequestration Breakdown")
            st.caption("Color-coded origin tags, uptake heatmap, and DBH distribution sparklines.")
            sp_table = top_sp.copy()
            sp_table["Total_CO2_Tonnes"] = (sp_table["Total_CO2_kg"] / 1000.0).round(2)
            sp_table["Annual_Seq_kg"] = sp_table["Annual_Seq_kg"].round(1)

            # Build inline bar sparkline of tree DBH distribution per species
            sp_dbh_map = (
                filtered_trees.sort_values("dbh_cm")
                .groupby("common_name")["dbh_cm"]
                .apply(list)
                .to_dict()
            )
            sp_table["DBH_Trend"] = sp_table["common_name"].map(lambda s: sp_dbh_map.get(s, [0]))

            def style_origin(val):
                palette = {
                    "Native": "background-color: #dcfce7; color: #14532d; font-weight: 600;",
                    "Naturalized": "background-color: #ccfbf1; color: #115e59; font-weight: 600;",
                    "Exotic": "background-color: #fef3c7; color: #92400e; font-weight: 600;"
                }
                return palette.get(val, "")

            sp_display = sp_table[[
                "common_name", "native_status", "Tree_Count",
                "Total_CO2_Tonnes", "Annual_Seq_kg", "DBH_Trend"
            ]]
            styled_sp = (
                sp_display.style
                .map(style_origin, subset=["native_status"])
                .background_gradient(subset=["Total_CO2_Tonnes"], cmap="Greens")
                .format({"Total_CO2_Tonnes": "{:.2f}", "Annual_Seq_kg": "{:.1f}"})
            )
            st.dataframe(
                styled_sp,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "common_name": "Species",
                    "native_status": "Origin",
                    "Tree_Count": st.column_config.NumberColumn("Count", format="%d"),
                    "Total_CO2_Tonnes": "Stored CO2 (t)",
                    "Annual_Seq_kg": "Uptake (kg/yr)",
                    "DBH_Trend": st.column_config.BarChartColumn(
                        "Trunk Girth Spread",
                        y_min=0,
                        y_max=float(df_trees["dbh_cm"].max())
                    )
                }
            )

    st.write("")

    # Row 4: Color-Coded Arborist Health & Microclimate Telemetry Summary Table
    with st.container(border=True):
        st.subheader("Arborist Health Status & Ecological Condition Matrix")
        st.caption("Diagnostic status badges, soil moisture heatmap, moisture sparklines, and population share bars.")
        health_table = (
            filtered_trees.groupby("health_status", as_index=False)
            .agg(
                Tree_Count=("tree_id", "count"),
                Avg_Soil_Moisture=("soil_moisture_pct", lambda s: round(s.mean(), 1)),
                Avg_DBH_cm=("dbh_cm", lambda s: round(s.mean(), 1)),
                Stored_CO2_Tonnes=("stored_co2_kg", lambda s: round(s.sum() / 1000.0, 2)),
                Annual_O2_Tonnes=("annual_o2_production_kg", lambda s: round(s.sum() / 1000.0, 2)),
                Stormwater_kL=("stormwater_intercepted_liters", lambda s: round(s.sum() / 1000.0, 1))
            )
            .sort_values("Tree_Count", ascending=False)
        )
        health_table["Population_Pct"] = (
            health_table["Tree_Count"] / max(health_table["Tree_Count"].sum(), 1) * 100
        ).round(1)

        # Inline line sparkline of soil moisture readings per health category
        moisture_spark_map = (
            filtered_trees.groupby("health_status")["soil_moisture_pct"]
            .apply(lambda s: s.tolist()[:25])
            .to_dict()
        )
        health_table["Moisture_Samples"] = health_table["health_status"].map(
            lambda h: moisture_spark_map.get(h, [0])
        )

        def style_health_badge(val):
            palette = {
                "Healthy": "background-color: #dcfce7; color: #166534; font-weight: 600;",
                "Moderate": "background-color: #fef9c3; color: #854d0e; font-weight: 600;",
                "Needs Pruning": "background-color: #ffedd5; color: #9a3412; font-weight: 600;",
                "Critical / Pest Alert": "background-color: #fee2e2; color: #991b1b; font-weight: 600;"
            }
            return palette.get(val, "")

        health_display = health_table[[
            "health_status", "Tree_Count", "Population_Pct", "Avg_Soil_Moisture",
            "Moisture_Samples", "Stored_CO2_Tonnes", "Annual_O2_Tonnes", "Stormwater_kL"
        ]]
        styled_health = (
            health_display.style
            .map(style_health_badge, subset=["health_status"])
            .background_gradient(subset=["Avg_Soil_Moisture"], cmap="YlGnBu")
            .background_gradient(subset=["Stored_CO2_Tonnes"], cmap="Greens")
            .format({
                "Avg_Soil_Moisture": "{:.1f}%",
                "Stored_CO2_Tonnes": "{:.2f}",
                "Annual_O2_Tonnes": "{:.2f}",
                "Stormwater_kL": "{:.1f}"
            })
        )
        st.dataframe(
            styled_health,
            use_container_width=True,
            hide_index=True,
            column_config={
                "health_status": "Health Classification",
                "Tree_Count": st.column_config.NumberColumn("Tagged Trees", format="%d"),
                "Population_Pct": st.column_config.ProgressColumn(
                    "Share of Flora", min_value=0, max_value=100, format="%.1f%%"
                ),
                "Avg_Soil_Moisture": "Mean Moisture",
                "Moisture_Samples": st.column_config.LineChartColumn(
                    "Soil Moisture Variance",
                    y_min=10,
                    y_max=55
                ),
                "Stored_CO2_Tonnes": "Stored CO2 (t)",
                "Annual_O2_Tonnes": "Annual O2 (t/yr)",
                "Stormwater_kL": "Stormwater (kL/yr)"
            }
        )

# -----------------------------------------------------------------------------
# TAB 3: CAMPUS GIS CANOPY MAP
# -----------------------------------------------------------------------------
with tab_spatial:
    with st.container(border=True):
        st.subheader("CHRIST University Bengaluru Campus — Geospatial Tree Canopy & Carbon Map")
        st.caption("Circle diameter represents tree canopy spread (m); color intensity indicates annual CO2 sequestration rate (kg/yr).")
        if not filtered_trees.empty:
            fig_map = px.scatter_map(
                filtered_trees,
                lat="latitude",
                lon="longitude",
                size="canopy_diameter_m",
                color="annual_co2_sequestration_kg",
                color_continuous_scale="YlGn",
                hover_name="common_name",
                hover_data={
                    "tree_id": True,
                    "botanical_name": True,
                    "campus_zone": True,
                    "age_years": True,
                    "stored_co2_kg": True,
                    "health_status": True,
                    "latitude": False,
                    "longitude": False
                },
                center={"lat": 12.9344, "lon": 77.6058},
                zoom=16.5,
                height=520
            )
            fig_map.update_layout(
                map_style="open-street-map",
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("No trees match the current filter selection.")

# -----------------------------------------------------------------------------
# TAB 4: TREE INVENTORY & QR EXPLORER
# -----------------------------------------------------------------------------
with tab_inventory:
    with st.container(border=True):
        st.subheader("Searchable Campus Flora Registry & QR Audit Table")
        search_q = st.text_input(
            "Search by Tree ID, QR Tag, Common Name, or Botanical Name",
            placeholder="e.g., Honge, Ficus, CU-TREE-0042"
        )
        display_df = filtered_trees.copy()
        if search_q:
            mask = (
                display_df["tree_id"].str.contains(search_q, case=False, na=False) |
                display_df["qr_tag"].str.contains(search_q, case=False, na=False) |
                display_df["common_name"].str.contains(search_q, case=False, na=False) |
                display_df["botanical_name"].str.contains(search_q, case=False, na=False)
            )
            display_df = display_df[mask]

        st.dataframe(
            display_df[[
                "tree_id", "qr_tag", "common_name", "botanical_name", "native_status",
                "campus_zone", "age_years", "dbh_cm", "height_m", "stored_co2_kg",
                "annual_co2_sequestration_kg", "health_status", "last_audit_date"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "tree_id": "Tree ID",
                "qr_tag": "QR Tag",
                "common_name": "Common Name",
                "botanical_name": "Botanical Name",
                "native_status": "Origin",
                "campus_zone": "Campus Zone",
                "age_years": "Age (yrs)",
                "dbh_cm": "DBH (cm)",
                "height_m": "Height (m)",
                "stored_co2_kg": st.column_config.ProgressColumn(
                    "Stored CO2 (kg)", min_value=0, max_value=float(df_trees["stored_co2_kg"].max()), format="%.1f kg"
                ),
                "annual_co2_sequestration_kg": st.column_config.NumberColumn("Annual CO2 (kg/yr)", format="%.2f"),
                "health_status": "Health Status",
                "last_audit_date": "Last Audit"
            }
        )
