import requests
import json
import time

def run_system_test():
    """
    Test 1: Check System Health
    Test 2: Test Seattle (Urban/Loam - Expected Low Risk if Dry)
    Test 3: Test Medellin, Colombia (Mountainous/Rainy - Expected High Risk)
    """
    base_url = "http://localhost:8000"
    
    print("--- 🩺 TEST 1: System Health ---")
    try:
        resp = requests.get(f"{base_url}/v1/health")
        print(f"Health Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"FAILED: Backend not running? {e}")
        return

    test_cases = [
        {"name": "Seattle (Urban/Dry)", "latitude": 47.6062, "longitude": -122.3321, "radius": 5},
        {"name": "Medellin (Mountain/Landslide Prone)", "latitude": 6.2442, "longitude": -75.5812, "radius": 5},
        {"name": "Sapa, Vietnam (Steep Terrain)", "latitude": 22.3364, "longitude": 103.8438, "radius": 5}
    ]

    for case in test_cases:
        print(f"\n--- 🌍 TEST: {case['name']} ---")
        t0 = time.time()
        try:
            resp = requests.post(f"{base_url}/v1/analyze", json=case, timeout=45)
            elapsed = time.time() - t0
            
            if resp.status_code == 200:
                data = resp.json()
                score = data.get("risk_score")
                env = data.get("environment", {})
                flow_count = len(data.get("flow_paths", {}).get("features", [])) if data.get("flow_paths") else 0
                
                print(f"✅ Success ({elapsed:.1f}s)")
                print(f"   Risk Score: {score:.4f}")
                print(f"   Soil: {env.get('auto_soil_type')}")
                print(f"   Rain: {env.get('auto_rainfall_mm')}mm")
                print(f"   Flow Channels: {flow_count} points found")
                
                # Logic Validations
                if case['name'] == "Seattle (Urban/Dry)" and score > 0.6:
                    print("   ⚠️ WARNING: Seattle risk seems high. Checking calibration...")
                elif case['name'] == "Medellin (Mountain/Landslide Prone)" and score < 0.4:
                    print("   ⚠️ WARNING: Mountainous Medellin risk seems suspiciously low.")
            else:
                print(f"❌ Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"❌ Failed to reach API: {e}")

if __name__ == "__main__":
    run_system_test()
