import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re, unicodedata

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="🌍 Global GHG Impact Dashboard", layout="wide")
st.title("🌎 Global Greenhouse Gas (GHG) Impact Explorer")

# -----------------------------
# UTILITIES
# -----------------------------
def normalize_country(name):
    """Normalize country names for comparison only (lowercase, stripped, no accents/special chars)."""
    if pd.isna(name):
        return None
    name = str(name).strip().lower()
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    name = re.sub(r'[^a-z0-9\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name

# -----------------------------
# DATA LOAD
# -----------------------------
@st.cache_data
def load_data():
    df_country = pd.read_excel("./data/GHG_totals_by_country.xlsx")
    df_sector = pd.read_excel("./data/GHG_by_sector_and_country.xlsx")
    return df_country, df_sector

df_country, df_sector = load_data()

# --- Clean & reshape ---
df_country.columns = [str(c).strip() for c in df_country.columns]
df_sector.columns = [str(c).strip() for c in df_sector.columns]
years = [c for c in df_country.columns if c.isdigit()]
years_sector = [c for c in df_sector.columns if c.isdigit()]

df_country_long = df_country.melt(id_vars=["Country"], value_vars=years,
                                  var_name="Year", value_name="Emissions")
df_sector_long = df_sector.melt(id_vars=["Country", "Sector"], value_vars=years_sector,
                                var_name="Year", value_name="Emissions")

df_country_long["Year"] = df_country_long["Year"].astype(int)
df_sector_long["Year"] = df_sector_long["Year"].astype(int)

# Normalize countries for comparisons
for df in [df_country, df_country_long, df_sector_long]:
    df["norm_country"] = df["Country"].apply(normalize_country)

# Filter aggregates
exclude = ["global total", "world", "international transport", "statistical difference", "other"]
for df in [df_country, df_country_long, df_sector_long]:
    df.drop(df[df["norm_country"].isin(exclude)].index, inplace=True)

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("🔍 Filters")

latest_year = df_country_long["Year"].max()
country_totals = (
    df_country_long[df_country_long["Year"] == latest_year]
    .groupby(["Country", "norm_country"])["Emissions"].sum().reset_index()
    .sort_values("Emissions", ascending=False)
)

countries = country_totals["Country"].tolist()
norm_countries = country_totals["norm_country"].tolist()
default_index = norm_countries.index("united states") if "united states" in norm_countries else 0

selected_country = st.sidebar.selectbox(
    "🌎 Select a Country (sorted by total GHG emissions)",
    countries, index=default_index
)
selected_norm = normalize_country(selected_country)

selected_year = st.sidebar.slider(
    "📅 Select Year",
    int(df_country_long["Year"].min()),
    int(df_country_long["Year"].max()),
    latest_year
)

# -----------------------------
# COUNTRY-WISE VISUALS
# -----------------------------
st.header(f"Country-Wise Analysis: {selected_country}")

col1, col2 = st.columns(2)

# Trend
with col1:
    df_country_sel = df_country_long[df_country_long["norm_country"] == selected_norm]
    fig_trend = px.line(df_country_sel, x="Year", y="Emissions",
                        title=f"{selected_country} - GHG Emission Trend", markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

# Sunburst
with col2:
    df_sector_sel = df_sector_long[
        (df_sector_long["norm_country"] == selected_norm) &
        (df_sector_long["Year"] == selected_year)
    ]
    if df_sector_sel.empty:
        st.warning(f"No sectoral data for {selected_country} in {selected_year}.")
    else:
        fig_sunburst = px.sunburst(df_sector_sel, path=["Country", "Sector"], values="Emissions",
                                   title=f"{selected_country} - Sectoral Breakdown ({selected_year})")
        st.plotly_chart(fig_sunburst, use_container_width=True)

# Sector change
records = []
for sec, grp in df_sector_long[df_sector_long["norm_country"] == selected_norm].groupby("Sector"):
    if (selected_year in grp["Year"].values) and ((selected_year - 10) in grp["Year"].values):
        now, old = grp.loc[grp["Year"] == selected_year, "Emissions"].values[0], \
                   grp.loc[grp["Year"] == selected_year - 10, "Emissions"].values[0]
        if old != 0:
            records.append((sec, (now - old) / old * 100))
df_all = pd.DataFrame(records, columns=["Sector", "PercentChange"]).dropna()
if not df_all.empty:
    fig_arrow = px.bar(df_all.sort_values("PercentChange"),
                       x="PercentChange", y="Sector", orientation="h",
                       color="PercentChange", color_continuous_scale=["red", "yellow", "green"],
                       title=f"Sectors Increasing/Decreasing in {selected_country} ({selected_year-10}–{selected_year})")
    st.plotly_chart(fig_arrow, use_container_width=True)

# -----------------------------
# LULUCF
# -----------------------------
lulucf = pd.read_excel("./data/LULUCF_countries.xlsx", sheet_name="LULUCF_countries")
lulucf.columns = lulucf.columns.astype(str).str.strip()
years = [c for c in lulucf.columns if c.isdigit()]
lulucf_long = lulucf.melt(id_vars=["Country", "Sector", "Macro-region"],
                          value_vars=years, var_name="Year", value_name="Emissions")
lulucf_long["Year"] = lulucf_long["Year"].astype(int)
lulucf_long["norm_country"] = lulucf_long["Country"].apply(normalize_country)
df_lulucf = lulucf_long[lulucf_long["norm_country"] == selected_norm]
if not df_lulucf.empty:
    fig_bar = px.bar(df_lulucf, x="Year", y="Emissions", color="Sector",
                     title=f"{selected_country} - LULUCF Sector Emissions (Mt CO₂eq/yr)")
    st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------
# CROSS-COUNTRY COMPARISONS
# -----------------------------
st.header("🌐 Cross-Country Comparisons")
highlight_color = "#00FFAA"

# --- Choropleth (original style preserved) ---
df_latest = df_country_long[df_country_long["Year"] == selected_year].copy()
fig_map = px.choropleth(
    df_latest,
    locations="Country",
    locationmode="country names",
    color="Emissions",
    hover_name="Country",
    color_continuous_scale="YlOrRd",
    title=f"🌍 Global GHG Emissions ({selected_year})",
)
fig_map.update_layout(
    geo=dict(showframe=False, showcoastlines=True,
             projection_type="natural earth", projection_scale=1.3,
             center=dict(lat=10, lon=0)),
    height=800, margin=dict(l=0, r=0, t=60, b=0),
    font=dict(size=14, color="black"),
)
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

# --- Top emitters ---
top_n = 10
top_emit = df_latest.sort_values("Emissions", ascending=False).head(top_n).copy()
sel_row = df_latest[df_latest["norm_country"] == selected_norm]
if not sel_row.empty and selected_norm not in top_emit["norm_country"].values:
    top_emit = pd.concat([top_emit, sel_row]).sort_values("Emissions", ascending=False)
top_emit["color"] = top_emit["norm_country"].apply(
    lambda c: highlight_color if c == selected_norm else "#FFA500")
fig_top = px.bar(top_emit, x="Country", y="Emissions", color="color",
                 color_discrete_map="identity",
                 title=f"Top {top_n} Emitters + {selected_country} ({selected_year})")
st.plotly_chart(fig_top, use_container_width=True)

# --- Dominant sector ---
dom = df_sector_long[df_sector_long["Year"] == selected_year].groupby("norm_country")["Emissions"].idxmax().dropna()
df_dom = df_sector_long.loc[dom, ["Country", "Sector", "Emissions"]]
fig_dom = px.choropleth(df_dom, locations="Country", locationmode="country names",
                        color="Sector", title=f"Dominant Emission Sector by Country ({selected_year})")
fig_dom.update_layout(height=800)
st.plotly_chart(fig_dom, use_container_width=True)

# --- Temporal rank ---
df_rank = df_country_long.groupby(["norm_country", "Country", "Year"])["Emissions"].sum().reset_index()
df_rank["Rank"] = df_rank.groupby("Year")["Emissions"].rank(ascending=False, method="dense")
top_countries = df_rank[df_rank["Year"] == selected_year].sort_values("Rank").head(top_n)["norm_country"].tolist()
if selected_norm not in top_countries:
    top_countries.append(selected_norm)
df_bump = df_rank[df_rank["norm_country"].isin(top_countries)]
fig_bump = px.line(df_bump, x="Year", y="Rank", color="Country", markers=True,
                   title=f"Temporal Rank Change of Top {top_n} Emitters + {selected_country}")
fig_bump.update_yaxes(autorange="reversed")
for trace in fig_bump.data:
    if normalize_country(trace.name) == selected_norm:
        trace.update(line=dict(width=5, color=highlight_color))
st.plotly_chart(fig_bump, use_container_width=True)

# --- LULUCF map ---
country_sum = lulucf_long.groupby(["Country", "Year"])["Emissions"].sum().reset_index()
df_latest_lu = country_sum[country_sum["Year"] == selected_year]
fig_sink = px.choropleth(df_latest_lu, locations="Country", locationmode="country names",
                         color="Emissions",
                         color_continuous_scale=["darkgreen", "lightgreen", "yellow", "red"],
                         title=f"LULUCF Carbon Sink / Source Map ({selected_year})<br>(Negative = Sink, Positive = Source)")
fig_sink.update_layout(
    geo=dict(showframe=False, showcoastlines=True,
             projection_type="natural earth", projection_scale=1.3,
             center=dict(lat=10, lon=0)),
    height=800)
st.plotly_chart(fig_sink, use_container_width=True)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("""
---
**Data Source:**  
Crippa M. *et al.*, *GHG emissions of all world countries – JRC/IEA 2025 Report*, Luxembourg, 2025.  
[https://edgar.jrc.ec.europa.eu/report_2025](https://edgar.jrc.ec.europa.eu/report_2025) — DOI [10.2760/9816914](https://data.europa.eu/doi/10.2760/9816914) (JRC143227)  
© European Commission, Joint Research Centre (JRC) / International Energy Agency (IEA).
""")
