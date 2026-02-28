import requests
import logging

logger = logging.getLogger("FloodGuard.Soil")

def fetch_soil_type(lat: float, lon: float) -> str:
    """
    Fetches the soil texture class for the given coordinates from ISRIC SoilGrids.
    Maps it to a simplified category: "clay", "sandy", or "loam" (default).
    """
    # SoilGrids REST API to fetch mean clay, sand, silt at 0-5cm depth. [cite: 10]
    # We query for the nearest point.
    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&property=clay&property=sand&property=silt&depth=0-5cm&value=mean"
    
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            layers = data.get("properties", {}).get("layers", [])
            
            clay_val = 0
            sand_val = 0
            silt_val = 0
            
            for layer in layers:
                name = layer.get("name")
                mean_val = layer.get("depths", [{}])[0].get("values", {}).get("mean")
                if mean_val is None: mean_val = 0
                
                if name == "clay":
                    clay_val = mean_val
                elif name == "sand":
                    sand_val = mean_val
                elif name == "silt":
                    silt_val = mean_val
            
            clay_val = float(clay_val)
            sand_val = float(sand_val)
            silt_val = float(silt_val)

            # Simple heuristic mapping to our 3 types
            if clay_val > sand_val and clay_val > silt_val:
                result = "clay"
            elif sand_val > clay_val and sand_val > silt_val:
                result = "sandy"
            else:
                result = "loam"
            
            logger.info(f"Auto-detected soil: {result} at ({lat}, {lon}) (Clay: {clay_val}, Sand: {sand_val}, Silt: {silt_val})")
            return result
        else:
            logger.error(f"Soil API Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Soil Fetch Failed: {e}")
        
    return "loam" # Safe default
