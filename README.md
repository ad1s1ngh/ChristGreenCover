# ChristGreenCover: Campus Flora, Tree Inventory & Carbon Offset Analytics Dashboard

**ChristGreenCover** is an interactive environmental analytics web application built with **Python** and **Streamlit** for **CHRIST (Deemed to be University), Bengaluru Central Campus**. It tracks campus tree biodiversity, allometric carbon sequestration, microclimate cooling, and sustainability projections.

---

## Project Structure

```text
ChristGreenCover/
├── app.py                              # Main Streamlit dashboard application (app_v5.py)
├── requirements.txt                    # Python package dependencies
├── christ_campus_tree_inventory.csv    # Dataset of 450 tagged trees across 8 campus zones
├── christ_carbon_telemetry_365d.csv    # 365-day daily carbon, solar, and microclimate time series
└── README.md                           # Project documentation
```

---

## Key Features

1. **Executive Overview & KPI Sparklines**
   * Tracks **Tagged Campus Trees**, **Cumulative Carbon Stock ($\text{tCO}_2\text{e}$)**, **Period Sequestration**, **Green Canopy Cover ($\text{ha}$)**, and the **Native Flora Index (%)** with embedded trend sparklines.
   * Includes a **Quick Bio-Audit Simulator** to model the long-term $\text{CO}_2$ and $\text{O}_2$ impact of planting new saplings during Centre for Social Action (CSA) plantation drives.

2. **Carbon & Biodiversity Analytics**
   * **Time-Series Offset Comparison:** Plots daily flora carbon sequestration and rooftop solar offsets against baseline campus emissions.
   * **Zone & Species Breakdowns:** Visualizes carbon storage by campus zone, top sequestering native/exotic species, and root-zone soil moisture distributions.
   * **Styled Diagnostic Tables:** Features color-graded heatmaps, status badges, progress bars, and inline sparkline charts (`AreaChartColumn`, `BarChartColumn`, `LineChartColumn`).

3. **Campus GIS Canopy Map**
   * Interactive OpenStreetMap spatial visualization centered on the Bengaluru Central Campus (`12.9344° N, 77.6058° E`), scaling points by canopy diameter and coloring by annual sequestration rate.

4. **Tree Inventory & QR Explorer**
   * Searchable registry allowing instant lookup by **Tree ID**, **QR Tag**, **Common Name**, or **Botanical Name**, dynamically filtered by the sidebar controls (`Telemetry Window`, `Campus Zones`, `Origin Classification`, and `Tree Health Status`).

---

## Datasets Overview

* **`christ_campus_tree_inventory.csv` (450 records, 18 species):** Contains geolocation (`latitude`, `longitude`), trunk diameter (`dbh_cm`), height (`height_m`), canopy spread, health status, soil moisture, and carbon metrics calculated via tropical allometric biomass equations ($AGB = 0.0673 \times (\rho \cdot D^2 \cdot H)^{0.976}$).
* **`christ_carbon_telemetry_365d.csv` (365 records):** Contains daily flora carbon uptake, rooftop solar carbon offsets, baseline campus emissions, ambient temperature, canopy cooling delta, and campus AQI.

---

## Installation & Running Locally

1. **Install the required libraries:**
   ```bash
   pip install -r requirements.txt
   pip install matplotlib
   ```
   *(Note: `matplotlib` is required for Pandas background gradient styling in the analytical tables.)*

2. **Launch the Streamlit application:**
   ```bash
   streamlit run app.py
   ```

3. Open the local URL shown in your terminal (typically `http://localhost:8501`) in your browser.
