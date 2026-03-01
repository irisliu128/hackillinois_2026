from src.risk_model import check_urban
import time

cities = [
    {"name": "Seattle, USA", "lat": 47.6062, "lon": -122.3321},
    {"name": "Tokyo, Japan", "lat": 35.6762, "lon": 139.6503},
    {"name": "London, UK", "lat": 51.5074, "lon": -0.1278},
    {"name": "Mumbai, India", "lat": 19.0760, "lon": 72.8777},
    {"name": "Rural Farm, Iowa", "lat": 42.0229, "lon": -93.6663}
]

print("Testing Global Cities for Urban Infrastructure Bonus...\n")

for city in cities:
    t0 = time.time()
    # First call - might hit OSM
    is_urban = check_urban(city["lat"], city["lon"])
    t1 = time.time()
    
    # Second call - should hit our local spatial cache (round to 2 decimals)
    # Let's offset the coordinates slightly to prove the spatial cache works
    is_urban_cached = check_urban(city["lat"] + 0.001, city["lon"] - 0.002)
    t2 = time.time()
    
    status = "🏙️ URBAN (Bonus Applied)" if is_urban else "🌾 RURAL (No Bonus)"
    print(f"[{city['name']}] -> {status}")
    print(f"   API Call: {t1 - t0:.2f}s | Spatial Cache Hit: {t2 - t1:.4f}s")
    print("-" * 50)
