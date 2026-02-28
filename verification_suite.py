import requests
import time
from datetime import datetime

DIVERSE_LOCATIONS = [
    {"name": "Urban Canyon (NYC, USA)", "latitude": 40.7128, "longitude": -74.0060},
    {"name": "Steep Tropical (Medellin, COL)", "latitude": 6.2442, "longitude": -75.5812},
    {"name": "Arid Sparse (Cairo, EGY)", "latitude": 30.0444, "longitude": 31.2357},
    {"name": "Recent Burn Zone (Maui, HI)", "latitude": 20.880, "longitude": -156.680},
    {"name": "High Forest (Manaus, BRA)", "latitude": -3.119, "longitude": -60.021}
]

def run_verification():
    base_url = "http://127.0.0.1:8000"
    print(f"🚀 Launching Global Verification Suite (v4.0)...")
    print("-" * 50)
    
    success_count = 0

    for i, loc in enumerate(DIVERSE_LOCATIONS):
        print(f"📡 Analyzing ecosystem {i+1}/5: {loc['name']}...")
        start_t = time.time()
        
        try:
            # High 120s timeout for satellite reducers
            resp = requests.post(f"{base_url}/v1/analyze", json={
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "radius": 5
            }, timeout=120)
            
            elapsed = time.time() - start_t
            
            if resp.status_code == 200:
                data = resp.json()
                score = data.get("risk_score", 0)
                env = data.get("environment", {})
                
                print(f"   ✅ SUCCESS ({elapsed:.1f}s)")
                print(f"      Risk Score: {score:.4f}")
                print(f"      Satellite NDVI: {env.get('ndvi', 0)*100:.1f}%")
                print(f"      Saturation: {env.get('soil_moisture', 0)*100:.1f}%")
                if env.get('is_burn_zone'):
                    print(f"      🔥 BURN ZONE DETECTED")
                success_count += 1
            else:
                print(f"   ❌ API ERROR: {resp.status_code}")
        except Exception as e:
            print(f"   ⚠️ TIMEOUT or NETWORK ERROR: {e}")
        
        # Avoid GEE rate limiting
        time.sleep(3)

    print("-" * 50)
    print(f"🏁 Verification Complete: {success_count}/5 sites passed.")

if __name__ == "__main__":
    run_verification()
