"""Database utilities for global temperature visualization app.

Handles connecting to MS SQL Server using credentials from Streamlit secrets,
performing aggregated SQL queries, caching results, and falling back to
local CSV files or generated mock data when database connection is not available.
"""

import os
import pathlib
import sys
import numpy as np
import pandas as pd
import streamlit as st

# Attempt to import pymssql
try:
    import pymssql
except ImportError:
    pymssql = None


def get_db_connection():
    """Establish a connection to the MS SQL Server using Streamlit secrets."""
    if pymssql is None:
        raise ImportError("pymssql package is not installed.")

    # Retrieve secrets
    if hasattr(st, "secrets") and "sqlserver" in st.secrets:
        secrets = st.secrets["sqlserver"]
    else:
        raise ValueError("Database credentials not found in Streamlit secrets.")

    server = secrets.get("server")
    database = secrets.get("database")
    username = secrets.get("username")
    password = secrets.get("password")
    port = secrets.get("port", 1433)

    if not server or not database:
        raise ValueError("Missing server or database configuration in secrets.")

    conn = pymssql.connect(
        server=server,
        user=username,
        password=password,
        database=database,
        port=int(port),
        timeout=10,
        login_timeout=5
    )
    return conn


def test_db_connection():
    """Test if database connection can be established."""
    if pymssql is None:
        return False, "pymssql package is not installed."
    try:
        conn = get_db_connection()
        conn.close()
        return True, "Connection successful."
    except Exception as e:
        return False, str(e)


# Generate mock data when no database or CSV is available
def generate_mock_global_data():
    """Generate realistic global temperature mock data from 1850 to 2013."""
    countries = ["United States", "China", "India", "Brazil", "United Kingdom", 
                 "Germany", "Australia", "South Africa", "Egypt", "Canada", 
                 "Japan", "Russia", "Argentina", "France", "Spain"]
    
    years = list(range(1850, 2014))
    records = []
    
    # Base temperatures for countries
    base_temps = {
        "United States": 11.5, "China": 12.0, "India": 24.5, "Brazil": 25.0,
        "United Kingdom": 8.5, "Germany": 8.0, "Australia": 22.0, 
        "South Africa": 17.5, "Egypt": 22.5, "Canada": -5.0, "Japan": 12.5,
        "Russia": -5.5, "Argentina": 14.5, "France": 12.0, "Spain": 15.0
    }
    
    for year in years:
        # Global warming trend: average temp increases slightly over time (+1.5 degrees over 163 years)
        warming_trend = (year - 1850) / 163.0 * 1.5
        for country in countries:
            base = base_temps[country]
            # Add some cyclic variation and random noise
            cycle = np.sin((year - 1850) * 0.1) * 0.4
            noise = np.random.normal(0, 0.3)
            avg_temp = base + warming_trend + cycle + noise
            records.append({
                "Year": year,
                "Country": country,
                "AvgTemp": round(avg_temp, 3)
            })
            
    return pd.DataFrame(records)


def generate_mock_major_cities(country):
    """Generate realistic major cities data for a country."""
    # Dict of major cities, their coordinates, and baseline temperature offsets
    city_data = {
        "United States": [("New York", "40.71N", "74.00W", 0), ("Los Angeles", "34.05N", "118.24W", 7), ("Chicago", "41.87N", "87.62W", -2), ("Miami", "25.76N", "80.19W", 12)],
        "China": [("Beijing", "39.90N", "116.40E", 0), ("Shanghai", "31.23N", "121.47E", 4), ("Guangzhou", "23.12N", "113.26E", 10), ("Harbin", "45.75N", "126.63E", -8)],
        "India": [("Delhi", "28.61N", "77.20E", 0), ("Mumbai", "19.07N", "72.87E", 2), ("Bangalore", "12.97N", "77.59E", -1), ("Kolkata", "22.57N", "88.36E", 1)],
        "Brazil": [("São Paulo", "23.55S", "46.63W", -4), ("Rio de Janeiro", "22.90S", "43.17W", -1), ("Salvador", "12.97S", "38.50W", 2), ("Manaus", "3.11S", "60.02W", 3)],
        "United Kingdom": [("London", "51.50N", "0.12W", 0), ("Edinburgh", "55.95N", "3.18W", -2), ("Manchester", "53.48N", "2.24W", -0.5)],
        "Germany": [("Berlin", "52.52N", "13.40E", 0), ("Munich", "48.13N", "11.57E", -2), ("Hamburg", "53.55N", "9.99E", -0.5)],
        "Australia": [("Sydney", "33.86S", "151.20E", -4), ("Melbourne", "37.81S", "144.96E", -6), ("Brisbane", "27.46S", "153.02E", 0), ("Darwin", "12.46S", "130.84E", 6)],
        "Canada": [("Toronto", "43.65N", "79.38W", 5), ("Vancouver", "49.28N", "123.12W", 7), ("Montreal", "45.50N", "73.56W", 3), ("Ottawa", "45.42N", "75.69W", 2)],
        "Russia": [("Moscow", "55.75N", "37.61E", 5), ("Saint Petersburg", "59.93N", "30.33E", 4), ("Novosibirsk", "55.00N", "82.93E", 0), ("Vladivostok", "43.11N", "131.87E", 2)],
        "Japan": [("Tokyo", "35.67N", "139.65E", 0), ("Osaka", "34.69N", "135.50E", 1), ("Sapporo", "43.06N", "141.35E", -6), ("Fukuoka", "33.59N", "130.40E", 2)]
    }
    
    # Fallback default cities if country is not in the list
    default_cities = [("Capital City", "40.00N", "10.00E", 0), ("Coastal City", "38.00N", "8.00E", 2), ("Northern City", "44.00N", "12.00E", -4)]
    cities = city_data.get(country, default_cities)
    
    years = list(range(1850, 2014))
    records = []
    
    # Database level base temperature of the country
    base_temps = {
        "United States": 11.5, "China": 12.0, "India": 24.5, "Brazil": 25.0,
        "United Kingdom": 8.5, "Germany": 8.0, "Australia": 22.0, "Canada": -5.0,
        "Russia": -5.5, "Japan": 12.5
    }
    country_base = base_temps.get(country, 15.0)
    
    for year in years:
        warming_trend = (year - 1850) / 163.0 * 1.6
        for city, lat, lon, offset in cities:
            cycle = np.sin((year - 1850) * 0.15) * 0.5
            noise = np.random.normal(0, 0.4)
            avg_temp = country_base + offset + warming_trend + cycle + noise
            records.append({
                "Year": year,
                "City": city,
                "Country": country,
                "Latitude": lat,
                "Longitude": lon,
                "AvgTemp": round(avg_temp, 3)
            })
            
    return pd.DataFrame(records)


def generate_mock_surrounding_cities(country, center_lat_float, center_lon_float, center_city):
    """Generate mock surrounding smaller cities relative to a major city."""
    # Create 4 smaller cities scattered around the main coordinate
    offsets = [
        ("North-Suburb", 0.3, 0.1, -0.5),
        ("East-Town", -0.1, 0.4, 0.2),
        ("South-Village", -0.4, -0.2, -0.8),
        ("West-District", 0.2, -0.3, 0.4)
    ]
    
    years = list(range(1850, 2014))
    records = []
    
    # Base temp for center city
    base_temps = {"New York": 11.0, "Los Angeles": 18.0, "Chicago": 9.0, "Miami": 23.0}
    city_base = base_temps.get(center_city, 14.0)
    
    # Add the main city itself
    for year in years:
        warming_trend = (year - 1850) / 163.0 * 1.5
        cycle = np.sin((year - 1850) * 0.1) * 0.4
        noise = np.random.normal(0, 0.3)
        
        # Helper to convert float coordinate to N/S E/W format
        def to_lat_str(val):
            return f"{abs(val):.2f}N" if val >= 0 else f"{abs(val):.2f}S"
        def to_lon_str(val):
            return f"{abs(val):.2f}E" if val >= 0 else f"{abs(val):.2f}W"
            
        # Add center city
        records.append({
            "Year": year,
            "City": center_city,
            "Country": country,
            "Latitude": to_lat_str(center_lat_float),
            "Longitude": to_lon_str(center_lon_float),
            "AvgTemp": round(city_base + warming_trend + cycle + noise, 3)
        })
        
        # Add suburbs
        for sub_name, lat_off, lon_off, temp_off in offsets:
            sub_noise = np.random.normal(0, 0.45)
            records.append({
                "Year": year,
                "City": f"{center_city} {sub_name}",
                "Country": country,
                "Latitude": to_lat_str(center_lat_float + lat_off),
                "Longitude": to_lon_str(center_lon_float + lon_off),
                "AvgTemp": round(city_base + temp_off + warming_trend + cycle + sub_noise, 3)
            })
            
    return pd.DataFrame(records)


# Cached data query wrappers
@st.cache_data
def get_global_yearly_temperatures():
    """Fetch global yearly temperatures from SQL Server or fallback to CSV/Mock."""
    db_connected, _ = test_db_connection()
    
    if db_connected:
        try:
            conn = get_db_connection()
            query = """
                SELECT YEAR(dt) as Year, Country, AVG(AverageTemperature) as AvgTemp
                FROM dbo.GlobalLandTemperatures
                WHERE AverageTemperature IS NOT NULL
                GROUP BY YEAR(dt), Country
                ORDER BY Year, Country
            """
            df = pd.read_sql(query, conn)
            conn.close()
            return df, "SQL Server Database"
        except Exception as e:
            # Fall back if query fails
            pass

    # Fallback to local CSV file
    csv_path = pathlib.Path("datasource/cleaned_global_temperatures_for_sql.csv")
    if csv_path.exists():
        try:
            df_raw = pd.read_csv(csv_path)
            # Aggregate by year
            df_raw['Year'] = pd.to_datetime(df_raw['dt']).dt.year
            df_agg = df_raw.groupby(['Year', 'Country'])['AverageTemperature'].mean().reset_index()
            df_agg.rename(columns={'AverageTemperature': 'AvgTemp'}, inplace=True)
            return df_agg, "Local CSV (dbo.GlobalLandTemperatures)"
        except Exception:
            pass

    # Ultimate fallback to synthetic mock data
    return generate_mock_global_data(), "Mock Generated Data (No Database/CSV Found)"


@st.cache_data
def get_country_cities_temperatures(country):
    """Fetch yearly city temperatures and coordinates for a country."""
    db_connected, _ = test_db_connection()
    
    if db_connected:
        try:
            conn = get_db_connection()
            query = """
                SELECT YEAR(dt) as Year, City, Country, Latitude, Longitude, AVG(AverageTemperature) as AvgTemp
                FROM dbo.GlobalLandTemperaturesByMajorCity
                WHERE Country = %s AND AverageTemperature IS NOT NULL
                GROUP BY YEAR(dt), City, Country, Latitude, Longitude
                ORDER BY Year, City
            """
            # pymssql uses %s as placeholder
            cursor = conn.cursor()
            cursor.execute(query, (country,))
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
            conn.close()
            if not df.empty:
                return df, "SQL Server Database"
        except Exception:
            pass

    # Fallback to local CSV
    csv_path = pathlib.Path("datasource/cleaned_global_temperatures_major_city_for_sql.csv")
    if csv_path.exists():
        try:
            df_raw = pd.read_csv(csv_path)
            df_filtered = df_raw[df_raw['Country'] == country].copy()
            if not df_filtered.empty:
                df_filtered['Year'] = pd.to_datetime(df_filtered['dt']).dt.year
                df_agg = df_filtered.groupby(['Year', 'City', 'Country', 'Latitude', 'Longitude'])['AverageTemperature'].mean().reset_index()
                df_agg.rename(columns={'AverageTemperature': 'AvgTemp'}, inplace=True)
                return df_agg, "Local CSV (dbo.GlobalLandTemperaturesByMajorCity)"
        except Exception:
            pass

    # Ultimate fallback to mock cities
    return generate_mock_major_cities(country), "Mock Generated Data (No Database/CSV Found)"


@st.cache_data
def get_surrounding_cities_temperatures(country, center_city, center_lat_float, center_lon_float, radius_deg=4.0):
    """Fetch temperatures of target city and surrounding cities inside a bounding box."""
    db_connected, _ = test_db_connection()
    
    if db_connected:
        try:
            conn = get_db_connection()
            # Fetch surrounding cities in the same country. We will filter by bounding box in python 
            # to accommodate coordinate formats or do it in SQL if we had simple floats.
            # Since SQL columns are N/S E/W string representations, it is cleaner to query all cities 
            # for that country and filter coordinates dynamically in Python.
            query = """
                SELECT YEAR(dt) as Year, City, Country, Latitude, Longitude, AVG(AverageTemperature) as AvgTemp
                FROM dbo.GlobalLandTemperaturesByCity
                WHERE Country = %s AND AverageTemperature IS NOT NULL
                GROUP BY YEAR(dt), City, Country, Latitude, Longitude
                ORDER BY Year, City
            """
            cursor = conn.cursor()
            cursor.execute(query, (country,))
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
            conn.close()
            
            if not df.empty:
                return df, "SQL Server Database"
        except Exception:
            pass

    # Fallback to local CSV (large file)
    csv_path = pathlib.Path("datasource/cleaned_global_temperatures_by_city_for_sql.csv")
    if csv_path.exists():
        try:
            # Efficiently read CSV in chunks to filter for the country to conserve memory
            chunks = []
            for chunk in pd.read_csv(csv_path, chunksize=150000):
                filtered = chunk[chunk['Country'] == country].copy()
                if not filtered.empty:
                    chunks.append(filtered)
            
            if chunks:
                df_filtered = pd.concat(chunks)
                df_filtered['Year'] = pd.to_datetime(df_filtered['dt']).dt.year
                df_agg = df_filtered.groupby(['Year', 'City', 'Country', 'Latitude', 'Longitude'])['AverageTemperature'].mean().reset_index()
                df_agg.rename(columns={'AverageTemperature': 'AvgTemp'}, inplace=True)
                return df_agg, "Local CSV (dbo.GlobalLandTemperaturesByCity)"
        except Exception:
            pass

    # Ultimate fallback to mock surrounding cities
    return generate_mock_surrounding_cities(country, center_lat_float, center_lon_float, center_city), "Mock Generated Data (No Database/CSV Found)"
