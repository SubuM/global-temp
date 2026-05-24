"""Interactive Global Temperature Visualizer Streamlit App.

Main application entry point. Implements a dark premium dashboard with
multi-level drill-down (Global -> Country -> City) maps and animations.
"""

import time
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Import our custom utilities
import db_utils
import map_utils

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Global Temp Pulse — Climate Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INJECT PREMIUM CSS STYLING ---
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');
    
    /* Main Styles */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        color: #ffffff;
    }
    
    /* Dark Theme Layout */
    .stApp {
        background-color: #0d0d11;
        color: #d1d1e0;
    }
    
    /* Glassmorphic Container Cards */
    .glass-card {
        background: rgba(26, 26, 36, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        margin-bottom: 20px;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #12121a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    /* Glass metric block */
    .metric-card {
        background: rgba(255, 255, 255, 0.02);
        border-left: 4px solid #ff4b4b;
        padding: 12px 18px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        font-family: 'Outfit', sans-serif;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8c8ca3;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Custom button styling */
    .stButton>button {
        background: linear-gradient(135deg, #1e1e2d 0%, #2a2a3e 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
    }
    .stButton>button:hover {
        border-color: #ff4b4b !important;
        box-shadow: 0 0 12px rgba(255, 75, 75, 0.2) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Active breadcrumbs styling */
    .breadcrumb {
        font-size: 0.9rem;
        color: #8c8ca3;
        margin-bottom: 20px;
        font-weight: 500;
    }
    .breadcrumb-active {
        color: #ff4b4b;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# --- STATE INITIALIZATION ---
if "level" not in st.session_state:
    st.session_state.level = "global"  # global, country, city
if "selected_country" not in st.session_state:
    st.session_state.selected_country = None
if "selected_city" not in st.session_state:
    st.session_state.selected_city = None
if "active_year" not in st.session_state:
    st.session_state.active_year = 1850  # Start from the beginning of history
if "animating" not in st.session_state:
    st.session_state.animating = True  # Autoplay on load by default

# Year Boundaries in the historical records
MIN_YEAR, MAX_YEAR = 1850, 2013

# --- DATABASE / Fallback Connectivity check ---
db_ok, db_status = db_utils.test_db_connection()

# --- SIDEBAR DESIGN ---
with st.sidebar:
    st.image("https://img.icons8.com/isometric/512/globe.png", width=90)
    st.markdown("## Global Temp Pulse")
    st.markdown("<span style='color: #8c8ca3; font-size: 0.9rem;'>Visualizing historical climate change trends and anomalies from 1850 to 2013.</span>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Database status indicator card
    status_color = "🟢" if db_ok else "🟡"
    status_text = "Connected to SQL Server" if db_ok else "Database Offline"
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {'#4caf50' if db_ok else '#ff9800'};">
        <div class="metric-label">Data Engine Source</div>
        <div style="font-size: 1rem; font-weight: 600; color: #ffffff; margin-top: 4px;">{status_color} {status_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # If connection failed, show detail
    if not db_ok:
        with st.expander("Show Connection Diagnostics"):
            st.info("System is automatically running in fallback mode using local datasets or mock generators.")
            st.code(db_status, language="bash")
            st.markdown("Configure your database credentials in `.streamlit/secrets.toml` to connect.")

    st.markdown("### Navigation Controls")
    
    # Dynamic sidebar widgets to manually select locations (as robust fallback/override)
    if st.session_state.level == "global":
        st.markdown("*Currently on **Global View**. Click a country on the map or select below to drill down.*")
        
        # Load country list
        global_df, data_source = db_utils.get_global_yearly_temperatures()
        country_list = sorted(global_df['Country'].unique())
        
        selected_manual_country = st.selectbox("Drill down to Country:", ["Select..."] + country_list)
        if selected_manual_country != "Select...":
            st.session_state.selected_country = selected_manual_country
            st.session_state.level = "country"
            st.session_state.animating = False
            st.rerun()
            
    elif st.session_state.level == "country":
        st.markdown(f"**Country View**: *{st.session_state.selected_country}*")
        
        # Load city list for selected country
        country_df, data_source = db_utils.get_country_cities_temperatures(st.session_state.selected_country)
        city_list = sorted(country_df['City'].unique())
        
        selected_manual_city = st.selectbox("Drill down to City:", ["Select..."] + city_list)
        if selected_manual_city != "Select...":
            st.session_state.selected_city = selected_manual_city
            st.session_state.level = "city"
            st.session_state.animating = False
            st.rerun()
            
        if st.button("⬅ Return to World Map", use_container_width=True):
            st.session_state.level = "global"
            st.session_state.selected_country = None
            st.session_state.animating = False
            st.rerun()

    elif st.session_state.level == "city":
        st.markdown(f"**City View**: *{st.session_state.selected_city}*")
        st.markdown(f"Country: *{st.session_state.selected_country}*")
        
        if st.button("⬅ Return to Country Map", use_container_width=True):
            st.session_state.level = "country"
            st.session_state.selected_city = None
            st.session_state.animating = False
            st.rerun()
            
        if st.button("⬅ Return to World Map", use_container_width=True):
            st.session_state.level = "global"
            st.session_state.selected_country = None
            st.session_state.selected_city = None
            st.session_state.animating = False
            st.rerun()
            
    st.markdown("---")
    st.markdown("### Animation Settings")
    speed_option = st.select_slider(
        "Simulation Speed",
        options=["Slow", "Normal", "Fast"],
        value="Normal"
    )
    speed_map = {"Slow": 0.35, "Normal": 0.15, "Fast": 0.04}
    st.session_state.animation_speed = speed_map[speed_option]
    st.session_state.auto_repeat = st.checkbox("Auto-Repeat (Loop)", value=True)
    
    st.markdown("---")
    st.markdown("<span style='font-size: 0.8rem; color: #505066;'>Data range: 1850 - 2013<br>Coordinates are mapped using centroids and custom geographic markers.</span>", unsafe_allow_html=True)


# --- MAIN APPLICATION INTERFACE ---

# 1. Breadcrumbs Header
if st.session_state.level == "global":
    st.markdown('<div class="breadcrumb"><span class="breadcrumb-active">🌍 Global View</span></div>', unsafe_allow_html=True)
elif st.session_state.level == "country":
    st.markdown(f'<div class="breadcrumb">🌍 Global View  &nbsp;&gt;&nbsp;  <span class="breadcrumb-active">📍 {st.session_state.selected_country}</span></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="breadcrumb">🌍 Global View  &nbsp;&gt;&nbsp;  📍 {st.session_state.selected_country}  &nbsp;&gt;&nbsp;  <span class="breadcrumb-active">🏙️ {st.session_state.selected_city}</span></div>', unsafe_allow_html=True)


# 2. Main Title and Controls Row
st.title("Climate Anomalies & Historical Temperatures")
st.markdown("Animate global, national, and city-level temperature variations to view climate shifts over the last 150+ years.")

# Render Animation Controls in a Glassmorphic Card
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
col_play, col_slider = st.columns([1.5, 6])

with col_play:
    # Toggle button for animation state
    if st.session_state.animating:
        if st.button("⏸ Pause Animation", use_container_width=True):
            st.session_state.animating = False
            st.rerun()
    else:
        if st.button("▶ Play History (1850-2013)", use_container_width=True):
            st.session_state.animating = True
            st.rerun()

with col_slider:
    # Year slider - pauses animation when manually slid by user
    selected_year = st.slider(
        "Historical Year Range", 
        min_value=MIN_YEAR, 
        max_value=MAX_YEAR, 
        value=st.session_state.active_year,
        label_visibility="collapsed"
    )
    
    # If the user dragged the slider manually, capture the change and pause animation
    if selected_year != st.session_state.active_year:
        st.session_state.active_year = selected_year
        st.session_state.animating = False

st.markdown('</div>', unsafe_allow_html=True)


# --- VIEW LOGIC RENDERING ---

if st.session_state.level == "global":
    # --- LEVEL 1: GLOBAL WORLD VIEW ---
    global_df, data_source = db_utils.get_global_yearly_temperatures()
    
    # Display view header and stats
    df_active_year = global_df[global_df['Year'] == st.session_state.active_year]
    global_avg_temp = df_active_year['AvgTemp'].mean() if not df_active_year.empty else 0.0
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ff4b4b;">
            <div class="metric-label">Active Simulation Year</div>
            <div class="metric-value">{st.session_state.active_year}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_stat2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #00bcd4;">
            <div class="metric-label">Avg Global Temp (Land)</div>
            <div class="metric-value">{global_avg_temp:.2f} °C</div>
        </div>
        """, unsafe_allow_html=True)
    with col_stat3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #9c27b0;">
            <div class="metric-label">Data Pipeline Source</div>
            <div class="metric-value" style="font-size: 1.1rem; line-height: 2.2rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{data_source}</div>
        </div>
        """, unsafe_allow_html=True)

    # Render World Map
    world_fig = map_utils.render_world_map(global_df, st.session_state.active_year)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("#### Interactive World Temperature Map")
    st.markdown("*Tip: Click directly on any country on the map to drill down into its cities!*")
    
    # Display the plotly map and register selection events
    selected_data = st.plotly_chart(world_fig, use_container_width=True, on_select="rerun", key="world_map")
    
    # Handle direct map selection (Click drill-down)
    if selected_data and "points" in selected_data and len(selected_data["points"]) > 0:
        point = selected_data["points"][0]
        clicked_country = point.get("location") or point.get("hovertext")
        if clicked_country:
            # Clean matching in case hovertext contains coordinates
            st.session_state.selected_country = clicked_country
            st.session_state.level = "country"
            st.session_state.animating = False
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom Row: Global Warming Trend Line Chart
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("#### Global Land Temperature Trend over History (1850 - 2013)")
    
    # Calculate yearly global average across all countries in our dataset
    global_trend_df = global_df.groupby('Year')['AvgTemp'].mean().reset_index()
    # 10-year moving average to show long term climate cycles
    global_trend_df['RollingAvg'] = global_trend_df['AvgTemp'].rolling(10, min_periods=1).mean()
    
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=global_trend_df['Year'], y=global_trend_df['AvgTemp'],
        name="Yearly Average", mode="lines",
        line=dict(color="rgba(255, 75, 75, 0.4)", width=1.5)
    ))
    trend_fig.add_trace(go.Scatter(
        x=global_trend_df['Year'], y=global_trend_df['RollingAvg'],
        name="10-Year Trend", mode="lines",
        line=dict(color="#ff4b4b", width=3)
    ))
    # Vertical line representing currently active year
    trend_fig.add_vline(x=st.session_state.active_year, line_dash="dash", line_color="#ffffff", opacity=0.7)
    
    trend_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=10, b=40),
        height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(trend_fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


elif st.session_state.level == "country":
    # --- LEVEL 2: COUNTRY LEVEL VIEW ---
    st.subheader(f"National Level Temperature Dashboard: {st.session_state.selected_country}")
    
    # Load country cities data
    country_df, data_source = db_utils.get_country_cities_temperatures(st.session_state.selected_country)
    
    if country_df.empty:
        st.warning(f"No records found for country: {st.session_state.selected_country}. Returning to world view.")
        st.session_state.level = "global"
        st.session_state.selected_country = None
        st.rerun()

    # Stat rows
    df_active_year = country_df[country_df['Year'] == st.session_state.active_year]
    country_avg_temp = df_active_year['AvgTemp'].mean() if not df_active_year.empty else 0.0
    num_cities = country_df['City'].nunique()
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ff4b4b;">
            <div class="metric-label">Selected Country</div>
            <div class="metric-value">{st.session_state.selected_country}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_stat2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ff9800;">
            <div class="metric-label">Avg Temperature ({st.session_state.active_year})</div>
            <div class="metric-value">{country_avg_temp:.2f} °C</div>
        </div>
        """, unsafe_allow_html=True)
    with col_stat3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #3f51b5;">
            <div class="metric-label">Tracked Major Cities</div>
            <div class="metric-value">{num_cities}</div>
        </div>
        """, unsafe_allow_html=True)

    # Render country map
    country_fig = map_utils.render_country_map(country_df, st.session_state.selected_country, st.session_state.active_year)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"#### Interactive City Temperature Map of {st.session_state.selected_country}")
    st.markdown("*Tip: Click on a city point to zoom into its local neighborhood coordinates!*")
    
    # Display Plotly map and capture clicks
    selected_data = st.plotly_chart(country_fig, use_container_width=True, on_select="rerun", key="country_map")
    
    if selected_data and "points" in selected_data and len(selected_data["points"]) > 0:
        point = selected_data["points"][0]
        clicked_city = point.get("hovertext")
        if clicked_city:
            st.session_state.selected_city = clicked_city
            st.session_state.level = "city"
            st.session_state.animating = False
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom Row: Compare City Historical Trend Lines
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"#### Temperature History of Major Cities in {st.session_state.selected_country}")
    
    city_trend_fig = go.Figure()
    
    # Group by City and Year
    for city in country_df['City'].unique():
        df_city = country_df[country_df['City'] == city].sort_values('Year')
        # Smooth with rolling average
        df_city['Smooth'] = df_city['AvgTemp'].rolling(10, min_periods=1).mean()
        city_trend_fig.add_trace(go.Scatter(
            x=df_city['Year'], y=df_city['Smooth'],
            name=city, mode="lines",
            line=dict(width=2)
        ))
        
    city_trend_fig.add_vline(x=st.session_state.active_year, line_dash="dash", line_color="#ffffff", opacity=0.7)
    
    city_trend_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=10, b=40),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(city_trend_fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


elif st.session_state.level == "city":
    # --- LEVEL 3: CITY ZOOMED VIEW ---
    st.subheader(f"Neighborhood Zoom Dashboard: {st.session_state.selected_city}")
    
    # First, get the main city coordinates from country_df to know our center lat/lon
    country_df, _ = db_utils.get_country_cities_temperatures(st.session_state.selected_country)
    city_entry = country_df[country_df['City'] == st.session_state.selected_city]
    
    if not city_entry.empty:
        raw_lat = city_entry['Latitude'].iloc[0]
        raw_lon = city_entry['Longitude'].iloc[0]
        lat_float = map_utils.parse_coordinate(raw_lat)
        lon_float = map_utils.parse_coordinate(raw_lon)
    else:
        lat_float = 0.0
        lon_float = 0.0

    # Load surrounding cities from the massive cities database table (using coordinate query/fallback)
    surrounding_df, data_source = db_utils.get_surrounding_cities_temperatures(
        st.session_state.selected_country, st.session_state.selected_city, lat_float, lon_float
    )
    
    # Stat rows
    df_active_year = surrounding_df[surrounding_df['Year'] == st.session_state.active_year]
    center_city_row = df_active_year[df_active_year['City'] == st.session_state.selected_city]
    city_temp = center_city_row['AvgTemp'].iloc[0] if not center_city_row.empty else 0.0
    num_surrounding = surrounding_df['City'].nunique() - 1  # subtract the center city itself
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ff4b4b;">
            <div class="metric-label">Selected City</div>
            <div class="metric-value">{st.session_state.selected_city}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_stat2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #e91e63;">
            <div class="metric-label">Current Temp ({st.session_state.active_year})</div>
            <div class="metric-value">{city_temp:.2f} °C</div>
        </div>
        """, unsafe_allow_html=True)
    with col_stat3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #2196f3;">
            <div class="metric-label">Surrounding Areas Detected</div>
            <div class="metric-value">{max(num_surrounding, 0)}</div>
        </div>
        """, unsafe_allow_html=True)

    # Render zoomed in neighborhood map
    city_zoom_fig = map_utils.render_city_zoom_map(surrounding_df, st.session_state.selected_country, st.session_state.selected_city, st.session_state.active_year)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"#### Zoomed-in Map: {st.session_state.selected_city} and surrounding areas")
    st.plotly_chart(city_zoom_fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom Row: Focused City Temperature Trend Line
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"#### Century-Long Temperature Trend for {st.session_state.selected_city}")
    
    df_city_full = surrounding_df[surrounding_df['City'] == st.session_state.selected_city].sort_values('Year')
    df_city_full['Smooth'] = df_city_full['AvgTemp'].rolling(10, min_periods=1).mean()
    
    focused_fig = go.Figure()
    focused_fig.add_trace(go.Scatter(
        x=df_city_full['Year'], y=df_city_full['AvgTemp'],
        name="Yearly Average", mode="markers+lines",
        marker=dict(size=4),
        line=dict(color="rgba(0, 188, 212, 0.35)", width=1)
    ))
    focused_fig.add_trace(go.Scatter(
        x=df_city_full['Year'], y=df_city_full['Smooth'],
        name="10-Year Rolling Trend", mode="lines",
        line=dict(color="#00bcd4", width=3)
    ))
    
    # Calculate warming delta (comparing start/end of records)
    if len(df_city_full) > 20:
        start_temp = df_city_full['Smooth'].iloc[5] # 5th element to avoid initial smoothing anomalies
        end_temp = df_city_full['Smooth'].iloc[-1]
        delta = end_temp - start_temp
        st.markdown(f"**Climate Anomaly Analysis**: Between {df_city_full['Year'].iloc[5]} and 2013, the smoothed average temperature in **{st.session_state.selected_city}** shifted by **{delta:+.2f} °C**.")
    
    focused_fig.add_vline(x=st.session_state.active_year, line_dash="dash", line_color="#ffffff", opacity=0.7)
    
    focused_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=10, b=40),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(focused_fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# --- ANIMATION SCHEDULER BACKPLANE ---
# If animating state is active, run the script again and increment year
if st.session_state.animating:
    speed_delay = st.session_state.get("animation_speed", 0.15)
    if st.session_state.active_year < MAX_YEAR:
        st.session_state.active_year += 1
        time.sleep(speed_delay)
        st.rerun()
    else:
        if st.session_state.get("auto_repeat", True):
            st.session_state.active_year = MIN_YEAR
            time.sleep(0.4)  # Short visual pause before looping back
            st.rerun()
        else:
            st.session_state.animating = False
            st.rerun()
