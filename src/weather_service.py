import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("FloodGuard.Weather")

def fetch_rainfall_data(lat: float, lon: float) -> float:
    """
    Fetches the last 24h accumulated rainfall (mm) using OpenWeatherMap API.
    If no rainfall data is found, it returns a default of 0.0.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or api_key == "PASTE_YOUR_KEY_HERE":
        logger.warning("OpenWeatherMap API Key not found. Defaulting rainfall to 0.0mm.")
        return 0.0
    
    # Fetch preceding 7 days of rainfall using Open-Meteo Historical API
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow().strftime('%Y-%m-%d')
    start_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&daily=precipitation_sum&timezone=auto"
    
    try:
        # We can use requests-cache here later, or simply fetch since Open-Meteo is free and fast
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            daily_rain = data.get("daily", {}).get("precipitation_sum", [])
            # Filter out None values just in case
            valid_rain = [r for r in daily_rain if r is not None]
            
            total_rain = sum(valid_rain)
            logger.info(f"Fetched weather: {total_rain}mm 7-day accumulated rain detected at ({lat}, {lon}).")
            return float(total_rain)
        else:
            logger.error(f"Weather API Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Weather Fetch Failed: {e}")
        
    return 0.0
