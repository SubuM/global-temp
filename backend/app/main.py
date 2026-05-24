from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from app import db

app = FastAPI(
    title="Global Temp Pulse API",
    description="Backend API serving historical climate data from SQL Server or Fallback Generators.",
    version="1.0.0"
)

# Configure CORS so the React frontend can fetch data without security errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this down to your specific frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
def get_status():
    """Check the health of the database connection."""
    is_connected, message = db.test_db_connection()
    return {
        "status": "online" if is_connected else "fallback",
        "database_connected": is_connected,
        "message": message
    }

@app.get("/api/temperatures/global")
def get_global_data():
    """Fetch global yearly temperatures for all countries."""
    data, source = db.get_global_yearly_temperatures()
    return {
        "source": source,
        "data": data
    }

@app.get("/api/temperatures/country/{country_name}")
def get_country_data(country_name: str):
    """Fetch historical temperature data for major cities within a specific country."""
    data, source = db.get_country_cities_temperatures(country_name)
    return {
        "country": country_name,
        "source": source,
        "data": data
    }

@app.get("/api/temperatures/city/{country_name}/{city_name}")
def get_city_data(
    country_name: str, 
    city_name: str, 
    lat: float = Query(0.0, description="Center Latitude"), 
    lon: float = Query(0.0, description="Center Longitude")
):
    """Fetch temperature data for a specific city and its surrounding coordinates."""
    data, source = db.get_surrounding_cities_temperatures(country_name, city_name, lat, lon)
    return {
        "country": country_name,
        "city": city_name,
        "source": source,
        "data": data
    }