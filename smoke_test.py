import requests
import json
import time

def smoke_test():
    print("🚀 Starting End-to-End Smoke Test...")
    
    # 1. Check Health
    try:
        health = requests.get("http://localhost:8000/v1/health")
        if health.status_code == 200:
            print("✅ Backend Health: OK")
        else:
            print(f"❌ Backend Health: Failed ({health.status_code})")
            return
    except Exception as e:
        print(f"❌ Backend unreachable: {e}")
        return

    # 2. Run Analysis
    payload = {
        "latitude": 21.710,
        "longitude": 104.878,
        "radius": 5.0,
        "rainfall_mm": 1850.0,
        "soil_type": "clay"
    }
    
    try:
        print(f"📤 Sending analysis request for ({payload['latitude']}, {payload['longitude']})...")
        resp = requests.post("http://localhost:8000/v1/analyze", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            risk_score = data.get("risk_score")
            print(f"✅ Analysis Success! Risk Score: {risk_score:.4f}")
            if 0 <= risk_score <= 1:
                print("💎 ML Integrity: PASSED (score in [0,1])")
            else:
                print("❌ ML Integrity: FAILED (score out of range)")
        else:
            print(f"❌ Analysis Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Analysis Request Failed: {e}")

if __name__ == "__main__":
    smoke_test()
