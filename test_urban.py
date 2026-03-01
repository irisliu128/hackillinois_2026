from src.risk_model import check_urban
import logging
logging.basicConfig(level=logging.DEBUG)

def test_check_urban(lat: float, lon: float) -> bool:
    import requests
    import requests_cache
    from pathlib import Path
    
    is_urban = False
    try:
        cache_dir = Path("./data/terrain_cache") / "osm_cache"
        session = requests_cache.CachedSession(str(cache_dir), expire_after=86400)
        
        bbox = f"{lat - 0.01},{lon - 0.01},{lat + 0.01},{lon + 0.01}" 
        query = f"""
        [out:json][timeout:5];
        (
          way["highway"~"primary|secondary|tertiary|residential"]({bbox});
          way["building"]({bbox});
        );
        out count;
        """
        response = session.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=6)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response JSON:", data)
            count = int(data.get("elements", [{}])[0].get("tags", {}).get("ways", 0))
            print("Ways count:", count)
            if count > 50:
                 is_urban = True
        else:
            print("Error response:", response.text)
    except Exception as e:
        print("Exception:", e)
    return is_urban

print("Checking Seattle...")
res = test_check_urban(47.6062, -122.3321)
print(f"Is Urban: {res}")
