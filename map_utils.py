"""Map rendering and coordinate parsing utilities.

Converts coordinate string representations (like '57.05N', '10.33E') into numeric values
and constructs animated Plotly charts for world, country, and zoomed city views.
"""

import numpy as np
import pandas as pd
import plotly.express as px


def parse_coordinate(coord_str):
    """Convert coordinate strings (e.g., '57.05N', '10.33E', '23.55S') to float values.
    
    Returns None if parsing fails.
    """
    if pd.isna(coord_str) or not isinstance(coord_str, (str, bytes)):
        return None
        
    if isinstance(coord_str, bytes):
        coord_str = coord_str.decode('utf-8')
        
    coord_str = coord_str.strip().upper()
    if not coord_str:
        return None
        
    try:
        # Check last character for direction
        direction = coord_str[-1]
        if direction in ('N', 'E'):
            return float(coord_str[:-1])
        elif direction in ('S', 'W'):
            return -float(coord_str[:-1])
        return float(coord_str)
    except ValueError:
        return None


def prepare_map_data(df):
    """Parse Latitude and Longitude columns in a DataFrame if they exist."""
    df_clean = df.copy()
    
    if 'Latitude' in df_clean.columns:
        df_clean['lat_num'] = df_clean['Latitude'].apply(parse_coordinate)
    if 'Longitude' in df_clean.columns:
        df_clean['lon_num'] = df_clean['Longitude'].apply(parse_coordinate)
        
    # Drop rows with invalid coordinates if we need coordinates
    if 'lat_num' in df_clean.columns and 'lon_num' in df_clean.columns:
        df_clean = df_clean.dropna(subset=['lat_num', 'lon_num'])
        
    return df_clean


def render_world_map(df, active_year):
    """Build a world choropleth map for the selected year.
    
    Returns a Plotly Figure.
    """
    # Filter by year
    df_year = df[df['Year'] == active_year].copy()
    
    # Render choropleth
    fig = px.choropleth(
        df_year,
        locations="Country",
        locationmode="country names",
        color="AvgTemp",
        color_continuous_scale="RdYlBu_r",  # Red-Yellow-Blue reversed (Hot is Red, Cold is Blue)
        # We can dynamically fit the scale range or use standard global temp boundaries
        range_color=[-15, 30],
        labels={"AvgTemp": "Temp (°C)"},
        hover_name="Country",
        hover_data={"AvgTemp": ":.2f"}
    )
    
    # Dark premium design update
    fig.update_layout(
        clickmode="event+select",
        title=dict(
            text=f"Global Temperatures — {active_year}",
            x=0.5,
            xanchor="center",
            font=dict(size=20, color="#ffffff", family="Outfit, sans-serif")
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=60, b=0),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type="natural earth",
            bgcolor="rgba(0,0,0,0)",
            landcolor="#1e1e24",
            lakecolor="#0f0f12",
            coastlinecolor="#3d3d4d"
        ),
        coloraxis_colorbar=dict(
            title="Temperature (°C)",
            thicknessmode="pixels", thickness=15,
            lenmode="fraction", len=0.6,
            yanchor="middle", y=0.5,
            ticks="outside"
        )
    )
    
    return fig


def render_country_map(df, selected_country, active_year):
    """Build a country level Mapbox scatter plot of major cities for the selected year."""
    # Ensure coordinates are clean
    df_clean = prepare_map_data(df)
    
    # Filter by year
    df_year = df_clean[df_clean['Year'] == active_year].copy()
    
    # Add constant size for markers
    df_year['MarkerSize'] = 15
    
    # Compute constant center for map view using all unique cities inside df_clean (across all years) to prevent jumping
    unique_cities = df_clean.drop_duplicates(subset=['City'])
    center_lat = unique_cities['lat_num'].mean() if not unique_cities.empty else 0.0
    center_lon = unique_cities['lon_num'].mean() if not unique_cities.empty else 0.0
    
    # Plotly Mapbox scatter
    fig = px.scatter_mapbox(
        df_year,
        lat="lat_num",
        lon="lon_num",
        color="AvgTemp",
        size="MarkerSize",
        size_max=12,
        color_continuous_scale="Thermal",
        range_color=[df_clean['AvgTemp'].min(), df_clean['AvgTemp'].max()],
        hover_name="City",
        hover_data={
            "AvgTemp": ":.2f", 
            "Latitude": True, 
            "Longitude": True,
            "lat_num": False,
            "lon_num": False,
            "MarkerSize": False
        }
    )
    
    fig.update_layout(
        clickmode="event+select",
        title=dict(
            text=f"Major Cities in {selected_country} — {active_year}",
            x=0.5,
            xanchor="center",
            font=dict(size=20, color="#ffffff", family="Outfit, sans-serif")
        ),
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=3.0
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=60, b=0),
        coloraxis_colorbar=dict(
            title="Temp (°C)",
            thicknessmode="pixels", thickness=15,
            lenmode="fraction", len=0.6,
            yanchor="middle", y=0.5
        )
    )
    
    return fig


def render_city_zoom_map(df, selected_country, center_city, active_year):
    """Build a highly zoomed map centering on the target city and showing surrounding cities."""
    # Prepare coordinates
    df_clean = prepare_map_data(df)
    
    # Find center coordinates for the target city
    city_coords = df_clean[df_clean['City'] == center_city]
    if not city_coords.empty:
        center_lat = city_coords['lat_num'].iloc[0]
        center_lon = city_coords['lon_num'].iloc[0]
    else:
        center_lat = 0.0
        center_lon = 0.0

    # Filter to bounding box of center coordinates +- 5.0 degrees for surrounding cities
    lat_min, lat_max = center_lat - 5.0, center_lat + 5.0
    lon_min, lon_max = center_lon - 5.0, center_lon + 5.0
    
    df_surrounding = df_clean[
        (df_clean['lat_num'] >= lat_min) & (df_clean['lat_num'] <= lat_max) &
        (df_clean['lon_num'] >= lon_min) & (df_clean['lon_num'] <= lon_max)
    ].copy()
    
    # Filter by year
    df_year = df_surrounding[df_surrounding['Year'] == active_year].copy()
    
    # Make main city marker much larger than suburbs
    df_year['MarkerSize'] = df_year['City'].apply(lambda x: 22 if x == center_city else 10)
    
    # Build Mapbox scatter
    fig = px.scatter_mapbox(
        df_year,
        lat="lat_num",
        lon="lon_num",
        color="AvgTemp",
        size="MarkerSize",
        size_max=18,
        color_continuous_scale="Jet",
        hover_name="City",
        hover_data={
            "AvgTemp": ":.2f",
            "Latitude": True,
            "Longitude": True,
            "lat_num": False,
            "lon_num": False,
            "MarkerSize": False
        }
    )
    
    fig.update_layout(
        title=dict(
            text=f"{center_city} & Surrounding Cities — {active_year}",
            x=0.5,
            xanchor="center",
            font=dict(size=20, color="#ffffff", family="Outfit, sans-serif")
        ),
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=6.0
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=60, b=0),
        coloraxis_colorbar=dict(
            title="Temp (°C)",
            thicknessmode="pixels", thickness=15,
            lenmode="fraction", len=0.6,
            yanchor="middle", y=0.5
        )
    )
    
    return fig
