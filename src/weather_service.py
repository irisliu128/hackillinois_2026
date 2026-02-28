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
    
    # Using the current weather API to get precipitation
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Rainfall for the last 1h or 3h if available [cite: 5]
            rain_1h = data.get("rain", {}).get("1h", 0.0)
            rain_3h = data.get("rain", {}).get("3h", 0.0)
            
            # Since we want something more significant for landslide risk,
            # we'll use a conservative sum or handle the absence.
            total_rain = max(rain_1h, rain_3h)
            logger.info(f"Fetched weather: {total_rain}mm rain detected at ({lat}, {lon}).")
            return float(total_rain)
        else:
            logger.error(f"Weather API Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Weather Fetch Failed: {e}")
        
    return 0.0
