# 🌍 Global Greenhouse Gas (GHG) Impact Dashboard

An interactive **Streamlit dashboard** for visualizing greenhouse gas (GHG) emissions across countries and sectors using the **EDGAR / JRC–IEA 2025 dataset**.  
The dashboard allows users to explore historical trends, sectoral contributions, and land-use (LULUCF) carbon sinks at both national and global scales.

---

## 🚀 Features

### 🔹 Country-Level Analysis
- Trend of total GHG emissions over time  
- Sectoral breakdown using an interactive **sunburst chart**  
- Top sectors increasing or decreasing in emissions over the past decade  
- LULUCF (Land Use, Land-Use Change, and Forestry) sector trends  

### 🔹 Cross-Country Comparisons
- Global choropleth map showing total GHG emissions per country  
- Top 10 emitters bar chart (with the selected country always highlighted)  
- Dominant emission sector by country  
- Temporal rank change of top emitters (bump chart)  
- Global carbon sink/source map from the LULUCF dataset  

### 🔹 Highlights
- Interactive filters: select any country or year  
- Dynamic highlighting of the selected country across all visualizations  
- Microstates and small islands supported via marker overlays  
- Data-driven sorting of countries by total emissions  
- Modern, wide-layout Streamlit UI  

---

## 📦 Project Structure

```

ghg_dashboard/
│
├── app.py                         # Main Streamlit application
├── requirements.txt               # Required Python packages
├── README.md                      # Project documentation
│
└── data/
├── GHG_totals_by_country.xlsx
├── GHG_by_sector_and_country.xlsx
└── LULUCF_countries.xlsx

````

---

## 🧩 Data Source

**EDGAR – Emissions Database for Global Atmospheric Research**

Crippa M., Guizzardi D., Pagani F., Banja M., Muntean M., Schaaf E., Quadrelli R., Risquez Martin A.,  
Taghavi-Moharamli P., Grassi G., Rossi S., Melo J., Oom D., Branco A., Suarez Moreno M.,  
Sedano F., San-Miguel J., Manca G., Pisoni E., Pekar F.  
> *GHG emissions of all world countries – JRC/IEA 2025 Report*, Luxembourg, 2025.  
> [https://edgar.jrc.ec.europa.eu/report_2025](https://edgar.jrc.ec.europa.eu/report_2025)  
> DOI: [https://data.europa.eu/doi/10.2760/9816914](https://data.europa.eu/doi/10.2760/9816914) — JRC143227  

**Publisher:**  
European Commission, Joint Research Centre (JRC) and International Energy Agency (IEA).

**License & Use:**  
© European Commission, Joint Research Centre (JRC).  
Data provided under the conditions described in the “Citation and References” sheet of the EDGAR 2025 dataset.
---


## 👩‍💻 Contributors

Developed by **Jinal Vyas**
Supervised by **Arizona State University]**

---

## 🧠 Acknowledgements

* European Commission – Joint Research Centre (JRC)
* International Energy Agency (IEA)
* Plotly, Streamlit, and Graphistry for interactive visualization libraries

---

## 🪪 Citation

If you use this dashboard or adapt it for research/publication, please cite:

> Crippa M. *et al.*, *GHG emissions of all world countries – JRC/IEA 2025 Report*,
> European Commission, Joint Research Centre (JRC), 2025.
> DOI: [10.2760/9816914](https://data.europa.eu/doi/10.2760/9816914)
