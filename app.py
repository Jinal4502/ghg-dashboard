import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import graphistry
import pycountry
import plotly.graph_objects as go

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="🌍 Global GHG Impact Dashboard", layout="wide")
st.title("🌎 Global Greenhouse Gas (GHG) Impact Explorer")
# -----------------------------
# DATA LOAD
# -----------------------------
@st.cache_data
def load_data():
    df_country = pd.read_excel("./data/GHG_totals_by_country.xlsx")
    df_sector = pd.read_excel("./data/GHG_by_sector_and_country.xlsx")
    return df_country, df_sector

df_country, df_sector = load_data()

# --- Clean and prepare columns ---
df_country.columns = [str(c).strip() for c in df_country.columns]
df_sector.columns = [str(c).strip() for c in df_sector.columns]

# --- Identify which columns are years ---
years = [c for c in df_country.columns if c.isdigit()]
years_sector = [c for c in df_sector.columns if c.isdigit()]

# --- Melt into long format ---
df_country_long = df_country.melt(
    id_vars=["Country"],  # non-year columns
    value_vars=years,
    var_name="Year",
    value_name="Emissions"
)

df_sector_long = df_sector.melt(
    id_vars=["Country", "Sector"],
    value_vars=years_sector,
    var_name="Year",
    value_name="Emissions"
)

# --- Ensure Year is numeric ---
df_country_long["Year"] = df_country_long["Year"].astype(int)
df_sector_long["Year"] = df_sector_long["Year"].astype(int)

# --- Clean & Filter Countries ---
df_country["Country"] = df_country["Country"].astype(str).str.strip().str.upper()

# Remove global/aggregate entries
exclude_countries = [
    "GLOBAL TOTAL", "WORLD", "INTERNATIONAL TRANSPORT", 
    "STATISTICAL DIFFERENCE", "OTHER"
]
df_country = df_country[~df_country["Country"].isin(exclude_countries)]

# Also apply to long-form data (for charts)
df_country_long["Country"] = df_country_long["Country"].astype(str).str.strip().str.upper()
df_country_long = df_country_long[~df_country_long["Country"].isin(exclude_countries)]

# Re-normalize capitalization for display
df_country["Country"] = df_country["Country"].str.title()
df_country_long["Country"] = df_country_long["Country"].str.title()


# Sidebar
st.sidebar.header("🔍 Filters")
# Clean the Country column
# --- Clean Country Names ---
df_country["Country"] = df_country["Country"].astype(str).str.strip()
df_country = df_country[df_country["Country"].notna() & (df_country["Country"] != "nan")]

# --- Sort Countries by Total Emissions (latest year) ---
latest_year = df_country_long["Year"].max()
country_totals = (
    df_country_long[df_country_long["Year"] == latest_year]
    .groupby("Country")["Emissions"]
    .sum()
    .reset_index()
    .sort_values("Emissions", ascending=False)
)

# List sorted by emissions
countries = country_totals["Country"].tolist()

# --- Sidebar controls ---
default_index = countries.index("United States") if "UNITED STATES" in [c.upper() for c in countries] else 0
selected_country = st.sidebar.selectbox(
    "🌎 Select a Country (sorted by total GHG emissions)",
    countries,
    index=default_index
)

selected_year = st.sidebar.slider(
    "📅 Select Year",
    int(df_country_long["Year"].min()),
    int(df_country_long["Year"].max()),
    2024
)

# -----------------------------
# COUNTRY-WISE VISUALS
# -----------------------------
st.header(f"Country-Wise Analysis: {selected_country}")

col1, col2 = st.columns(2)

# Trend over time
with col1:
    df_country_sel = df_country_long[df_country_long["Country"] == selected_country]
    fig_trend = px.line(df_country_sel, x="Year", y="Emissions", title=f"{selected_country} - GHG Emission Trend", markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

# Sectoral breakdown - sunburst
with col2:
    df_sector_sel = df_sector_long[(df_sector_long["Country"] == selected_country) & (df_sector_long["Year"] == selected_year)]
    fig_sunburst = px.sunburst(df_sector_sel, path=["Country", "Sector"], values="Emissions",
                               title=f"{selected_country} - Sectoral Breakdown ({selected_year})")
    st.plotly_chart(fig_sunburst, use_container_width=True)

# Increasing and Decreasing Sectors
df_all = (
    df_sector_long[df_sector_long["Country"] == selected_country]
    .groupby("Sector")
    .apply(lambda x: (x.loc[x["Year"] == selected_year, "Emissions"].values[0] -
                      x.loc[x["Year"] == selected_year - 10, "Emissions"].values[0]) /
                     x.loc[x["Year"] == selected_year - 10, "Emissions"].values[0] * 100
           if (selected_year - 10) in x["Year"].values else np.nan)
    .reset_index(name="PercentChange")
    .dropna()
)
fig_arrow = px.bar(
    df_all.sort_values("PercentChange"),
    x="PercentChange", y="Sector", orientation="h",
    color="PercentChange",
    color_continuous_scale=["red", "yellow", "green"],
    title=f"Sectors Increasing or Decreasing in {selected_country} ({selected_year-10}–{selected_year})",
)
st.plotly_chart(fig_arrow, use_container_width=True)
# --- Load LULUCF sheet ---
lulucf = pd.read_excel("./data/LULUCF_countries.xlsx", sheet_name="LULUCF_countries")

# --- Clean ---
lulucf.columns = lulucf.columns.astype(str).str.strip()
years = [c for c in lulucf.columns if c.isdigit()]
lulucf_long = lulucf.melt(
    id_vars=["Country", "Sector", "Macro-region"],
    value_vars=years,
    var_name="Year",
    value_name="Emissions"
)
lulucf_long["Year"] = lulucf_long["Year"].astype(int)

# --- Within-country breakdown ---
df_country = lulucf_long[(lulucf_long["Country"] == selected_country)]
fig_bar = px.bar(
    df_country,
    x="Year",
    y="Emissions",
    color="Sector",
    title=f"{selected_country} - LULUCF Sector Emissions (Mt CO₂eq/yr)"
)
st.plotly_chart(fig_bar, use_container_width=True)


# -----------------------------
# 🌐 CROSS-COUNTRY COMPARISONS
# -----------------------------
st.header("🌐 Cross-Country Comparisons")

highlight_color = "#00FFAA"  # bright teal for emphasis

# --- Choropleth: Global GHG Emissions ---
df_latest = df_country_long[df_country_long["Year"] == selected_year].copy()

# --- Choropleth: Global GHG Emissions (fixed for Russia and small countries) ---
df_latest = df_country_long[df_country_long["Year"] == selected_year].copy()

fig_map = px.choropleth(
    df_latest,
    locations="Country",
    locationmode="country names",  # direct name matching (no ISO)
    color="Emissions",
    hover_name="Country",
    color_continuous_scale="YlOrRd",
    title=f"🌍 Global GHG Emissions ({selected_year})",
)

# Larger, clearer map layout
fig_map.update_layout(
    geo=dict(
        showframe=False,
        showcoastlines=True,
        projection_type="natural earth",
        projection_scale=1.3,
        center=dict(lat=10, lon=0),
    ),
    height=800,
    margin=dict(l=0, r=0, t=60, b=0),
    font=dict(size=14, color="black"),
)

# Highlight selected country
if selected_country:
    fig_map.add_scattergeo(
        locations=[selected_country],
        locationmode="country names",
        text=[selected_country],
        mode="markers+text",
        marker=dict(size=10, color=highlight_color, line=dict(width=2, color="black")),
        textfont=dict(color="black", size=12, family="Arial Black"),
        name=f"{selected_country} (selected)"
    )

st.plotly_chart(fig_map, use_container_width=True)

# --- Top Emitters Bar (always include selected country) ---
top_n = 10
top_emitters = df_latest.sort_values("Emissions", ascending=False).head(top_n).copy()

# Add the selected country if it’s not already in top_n
selected_row = df_latest[df_latest["Country"].str.upper() == selected_country.upper()]
if not selected_row.empty and selected_country.upper() not in top_emitters["Country"].str.upper().values:
    # Append and re-sort properly by Emissions
    top_emitters = (
        pd.concat([top_emitters, selected_row])
        .sort_values("Emissions", ascending=False)
        .head(top_n + 1)  # Keep top_n + selected
    )

# Assign highlight color
top_emitters["color"] = top_emitters["Country"].apply(
    lambda c: highlight_color if c.upper() == selected_country.upper() else "#FFA500"
)

# Keep correct rank order (largest → smallest)
fig_top = px.bar(
    top_emitters.sort_values("Emissions", ascending=False),
    x="Country",
    y="Emissions",
    title=f"Top {top_n} Emitting Countries + {selected_country} ({selected_year})",
    color="color",
    color_discrete_map="identity"
)

fig_top.update_layout(
    height=500,
    xaxis=dict(categoryorder="total descending"),  # preserves emission order
)
st.plotly_chart(fig_top, use_container_width=True)

# --- Dominant Emission Sector Map ---
dominant = (
    df_sector_long[df_sector_long["Year"] == selected_year]
    .groupby("Country")["Emissions"]
    .idxmax()
)
df_dom = df_sector_long.loc[dominant, ["Country", "Sector", "Emissions"]]

fig_dom = px.choropleth(
    df_dom,
    locations="Country",
    locationmode="country names",
    color="Sector",
    title=f"Dominant Emission Sector by Country ({selected_year})",
)
fig_dom.update_layout(height=800, geo=dict(projection_type="natural earth", projection_scale=1.3))
if selected_country:
    fig_dom.add_scattergeo(
        locations=[selected_country],
        locationmode="country names",
        text=[selected_country],
        mode="markers+text",
        marker=dict(size=10, color=highlight_color, line=dict(width=2, color="black")),
        textfont=dict(color="black", size=12, family="Arial Black"),
        name=f"{selected_country} (selected)",
        showlegend=False
    )
st.plotly_chart(fig_dom, use_container_width=True)

# --- Temporal Rank Change (Bump Chart) ---
df_country_long["Country"] = df_country_long["Country"].astype(str).str.strip().str.upper()
df_rank = df_country_long[df_country_long["Country"] != "GLOBAL TOTAL"].copy()
df_rank = df_rank.groupby(["Country", "Year"])["Emissions"].sum().reset_index()
df_rank["Rank"] = df_rank.groupby("Year")["Emissions"].rank(ascending=False, method="dense")

top_n = 10
top_countries = (
    df_rank[df_rank["Year"] == selected_year]
    .sort_values("Rank")
    .head(top_n)["Country"]
    .tolist()
)
if selected_country.upper() not in top_countries:
    top_countries.append(selected_country.upper())

df_bump = df_rank[df_rank["Country"].isin(top_countries)]

fig_bump = px.line(
    df_bump, x="Year", y="Rank", color="Country", markers=True,
    title=f"Temporal Rank Change of Top {top_n} Emitters + {selected_country}"
)
fig_bump.update_yaxes(autorange="reversed")

for trace in fig_bump.data:
    if trace.name == selected_country.upper():
        trace.update(line=dict(width=5, color=highlight_color), marker=dict(size=10))
    else:
        trace.update(line=dict(width=1), marker=dict(size=4, opacity=0.6))

st.plotly_chart(fig_bump, use_container_width=True)

# --- LULUCF Carbon Sink / Source Map ---
country_sum = lulucf_long.groupby(["Country", "Year"])["Emissions"].sum().reset_index()
latest_year = selected_year
df_latest = country_sum[country_sum["Year"] == latest_year]

fig_sink = px.choropleth(
    df_latest,
    locations="Country",
    locationmode="country names",
    color="Emissions",
    color_continuous_scale=["darkgreen", "lightgreen", "yellow", "red"],
    title=f"LULUCF Carbon Sink / Source Map ({latest_year})<br>(Negative = Sink, Positive = Source)",
)
fig_sink.update_layout(
    geo=dict(
        showframe=False,
        showcoastlines=True,
        projection_type="natural earth",
        projection_scale=1.3,
        center=dict(lat=10, lon=0),
    ),
    height=800,
)

if selected_country:
    fig_sink.add_scattergeo(
        locations=[selected_country],
        locationmode="country names",
        text=[selected_country],
        mode="markers+text",
        marker=dict(size=10, color=highlight_color, line=dict(width=2, color="black")),
        textfont=dict(color="black", size=12, family="Arial Black"),
        name=f"{selected_country} (selected)",
        showlegend=False
    )

st.plotly_chart(fig_sink, use_container_width=True)

st.markdown("""
---
**Data Source:**  
Crippa M., Guizzardi D., Pagani F., Banja M., Muntean M., Schaaf E., Quadrelli R., Risquez Martin A.,  
Taghavi-Moharamli P., Grassi G., Rossi S., Melo J., Oom D., Branco A., Suarez Moreno M.,  
Sedano F., San-Miguel J., Manca G., Pisoni E., Pekar F.  
*GHG emissions of all world countries – JRC/IEA 2025 Report*, Luxembourg, 2025.  
[https://edgar.jrc.ec.europa.eu/report_2025](https://edgar.jrc.ec.europa.eu/report_2025) — [https://data.europa.eu/doi/10.2760/9816914](https://data.europa.eu/doi/10.2760/9816914) (JRC143227)

**Publisher:**  
European Commission, Joint Research Centre (JRC) and International Energy Agency (IEA).

**License & Use:**  
© European Commission, Joint Research Centre (JRC).  
Data provided under the conditions described in the “Citation and References” sheet of the EDGAR 2025 dataset.
""")
