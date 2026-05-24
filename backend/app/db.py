import os
import pathlib
import functools
import numpy as np
import pandas as pd

try:
    import pymssql
except ImportError:
    pymssql = None

def get_db_connection():
    """Establish a connection to the MS SQL Server using environment variables."""
    if pymssql is None:
        raise ImportError("pymssql package is not installed.")

    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    port = int(os.getenv("DB_PORT", 1433))

    if not server or not database:
        raise ValueError("Missing database configuration in environment variables.")

    conn = pymssql.connect(
        server=server,
        user=username,
        password=password,
        database=database,
        port=port,
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


# --- MOCK DATA GENERATORS (Fallback Engine) ---

def generate_mock_global_data():
    countries = ["United States", "China", "India", "Brazil", "United Kingdom", 
                 "Germany", "Australia", "South Africa", "Egypt", "Canada", 
                 "Japan", "Russia", "Argentina", "France", "Spain"]
    years = list(range(1850, 2014))
    records = []
    base_temps = {
        "United States": 11.5, "China": 12.0, "India": 24.5, "Brazil": 25.0,
        "United Kingdom": 8.5, "Germany": 8.0, "Australia": 22.0, 
        "South Africa": 17.5, "Egypt": 22.5, "Canada": -5.0, "Japan": 12.5,
        "Russia": -5.5, "Argentina": 14.5, "France": 12.0, "Spain": 15.0
    }
    
    for year in years:
        warming_trend = (year - 1850) / 163.0 * 1.5
        for country in countries:
            base = base_temps[country]
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
    city_data = {
        "United States": [("New York", "40.71N", "74.00W", 0), ("Los Angeles", "34.05N", "118.24W", 7), ("Chicago", "41.87N", "87.62W", -2), ("Miami", "25.76N", "80.19W", 12)],
        "China": [("Beijing", "39.90N", "116.40E", 0), ("Shanghai", "31.23N", "121.47E", 4), ("Guangzhou", "23.12N", "113.26E", 10)],
        "United Kingdom": [("London", "51.50N", "0.12W", 0), ("Edinburgh", "55.95N", "3.18W", -2), ("Manchester", "53.48N", "2.24W", -0.5)]
    }
    default_cities = [("Capital City", "40.00N", "10.00E", 0), ("Coastal City", "38.00N", "8.00E", 2)]
    cities = city_data.get(country, default_cities)
    
    years = list(range(1850, 2014))
    records = []
    country_base = 15.0
    
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
    offsets = [
        ("North-Suburb", 0.3, 0.1, -0.5),
        ("East-Town", -0.1, 0.4, 0.2),
        ("South-Village", -0.4, -0.2, -0.8),
        ("West-District", 0.2, -0.3, 0.4)
    ]
    years = list(range(1850, 2014))
    records = []
    city_base = 14.0
    
    def to_lat_str(val): return f"{abs(val):.2f}N" if val >= 0 else f"{abs(val):.2f}S"
    def to_lon_str(val): return f"{abs(val):.2f}E" if val >= 0 else f"{abs(val):.2f}W"
            
    for year in years:
        warming_trend = (year - 1850) / 163.0 * 1.5
        cycle = np.sin((year - 1850) * 0.1) * 0.4
        noise = np.random.normal(0, 0.3)
        
        records.append({
            "Year": year, "City": center_city, "Country": country,
            "Latitude": to_lat_str(center_lat_float), "Longitude": to_lon_str(center_lon_float),
            "AvgTemp": round(city_base + warming_trend + cycle + noise, 3)
        })
        
        for sub_name, lat_off, lon_off, temp_off in offsets:
            records.append({
                "Year": year, "City": f"{center_city} {sub_name}", "Country": country,
                "Latitude": to_lat_str(center_lat_float + lat_off), "Longitude": to_lon_str(center_lon_float + lon_off),
                "AvgTemp": round(city_base + temp_off + warming_trend + cycle + np.random.normal(0, 0.45), 3)
            })
    return pd.DataFrame(records)


# --- DATA FETCHING (With Caching and Dictionary Conversions) ---

@functools.lru_cache(maxsize=1)
def get_global_yearly_temperatures():
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
            return df.to_dict(orient='records'), "SQL Server Database"
        except Exception:
            pass

    # Fallback
    df = generate_mock_global_data()
    return df.to_dict(orient='records'), "Mock Generated Data"


@functools.lru_cache(maxsize=32)
def get_country_cities_temperatures(country):
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
            cursor = conn.cursor()
            cursor.execute(query, (country,))
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
            conn.close()
            if not df.empty:
                return df.to_dict(orient='records'), "SQL Server Database"
        except Exception:
            pass

    df = generate_mock_major_cities(country)
    return df.to_dict(orient='records'), "Mock Generated Data"


@functools.lru_cache(maxsize=32)
def get_surrounding_cities_temperatures(country, center_city, lat_float, lon_float):
    db_connected, _ = test_db_connection()
    if db_connected:
        try:
            conn = get_db_connection()
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
                # Note: Coordinate bounding box logic happens on the frontend React app for speed
                return df.to_dict(orient='records'), "SQL Server Database"
        except Exception:
            pass

    df = generate_mock_surrounding_cities(country, lat_float, lon_float, center_city)
    return df.to_dict(orient='records'), "Mock Generated Data"