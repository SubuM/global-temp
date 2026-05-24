# Global Temp Pulse — Interactive Climate Dashboard

**Global Temp Pulse** is a high-performance, premium interactive dashboard built in Python using **Streamlit** and **Plotly**. It visualizes over 160 years of global land temperature variations (from 1850 to 2013). The application supports fully dynamic multi-level maps with fluid temporal animations, allowing users to drill down from global trends directly to specific cities and local neighborhoods.

---

## 🚀 Key Features

* **Multi-Level Drill-Down Navigation:**
  - **Level 1: Global View:** Animated World Choropleth Map coloring countries by annual temperature. Click on a country to dive deeper.
  - **Level 2: Country View:** City-level Scatter Mapbox displaying the major cities within a country. Click on a city to zoom in.
  - **Level 3: City View:** Zoomed-in Mapbox focused on the selected city and surrounding neighborhood coordinates.
* **Temporal Animations:** Play or step through historical years using a custom timing loop that updates maps automatically.
* **Trend Analysis:** Century-long line charts with 10-year rolling averages to clearly isolate long-term climate anomalies and warming patterns.
* **Optimized Database Aggregations:** Caches queries via Streamlit and aggregates raw monthly metrics into yearly averages on the database level (`MS SQL Server`) using `pymssql` for peak responsiveness.
* **Resilient Fallback Engine:** If database credentials are missing or the server is offline, the app automatically falls back to generating realistic, high-fidelity synthetic mock datasets (covering global, country, and city levels) to remain fully interactive.

---

## 📁 Project Structure

```
├── .streamlit/
│   └── secrets.toml          # Database connection credentials (git-ignored)
├── .venv/                    # Python virtual environment (git-ignored)
├── .gitignore                # Excludes secrets, venv, and cache files
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies (Streamlit, pymssql, pandas, plotly)
├── db_utils.py               # SQL queries, caching, and fallback data logic
├── map_utils.py              # Coordinate parsing and Plotly visualization builders
├── streamlit_app.py          # Main Streamlit dashboard interface & UI styling
└── pymssql_v1.py             # Database connectivity test script (kept for reference)
```

---

## 🛠️ Getting Started

### 1. Set Up the Virtual Environment
Create and activate the virtual environment, then install the dependencies:
```bash
# Create venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Database Credentials (Optional)
To connect to your SQL Server instance, edit `.streamlit/secrets.toml` with your database connection parameters:
```toml
[sqlserver]
server = "your-database-server.database.windows.net"
database = "your-database-name"
username = "your-username"
password = "your-password"
driver = "ODBC Driver 18 for SQL Server"
port = 1433
```
*Note: If this file is not configured, the dashboard automatically starts in fallback mode using local datasets or mock data.*

### 3. Run the Dashboard
Start the Streamlit application:
```bash
streamlit run streamlit_app.py
```
Open your browser at [http://localhost:8501](http://localhost:8501) to explore the visualizer!
