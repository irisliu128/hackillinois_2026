# 🌍 TerraSight: Global Landslide Intelligence Platform (v4.0)

TerraSight is an autonomous, global-scale landslide risk and hydrological analysis tool designed for government agencies and NGOs. It combines **Machine Learning**, **Multi-Satellite Data (NASA/ESA)**, and **Physics-based Simulations** to predict regional hazards with zero manual input.

---

## 🛠️ Developer Status (Feb 2026)
**[COMPLETED] Person 1: Global Ecosystem & Climate Fusion**
- **Autonomous Weather**: Live 24h rainfall via OpenWeatherMap.
- **Micro-Soil Detection**: Global texture class via ISRIC SoilGrids.
- **Satellite Surveillance (NEW)**:
    - **NDVI (Sentinel-2)**: Detects vegetation root stability.
    - **Soil Moisture (NASA SMAP)**: Detects deep-ground saturation history.
    - **Burn Scars (MODIS)**: Detects high-risk post-wildfire zones.
- **Urban Calibration**: Applied "Infrastructure Engineering" dampening for major cities.

---

## 🚀 How to Run (For Prateek/Visualizer)

### 1. Setup Environment
Ensure your `.env` file has the following (Ask Arul or Tanish for keys):
```text
GEE_PROJECT_ID=hydroproject-488807
OPENWEATHER_API_KEY=your_key_here
```

### 2. Start the Integrated Backend
The backend serves the **FastAPI JSON API** and the **Satellite Dashboard**.
```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- **Access UI**: `http://localhost:8000`
- **Access API Docs**: `http://localhost:8000/docs`

---

## 🧠 Brain Logic (v4.0 Multi-Factor Fusion)
The Risk Score (`0.0 - 1.0`) is a weighted fusion of:
1. **Historical Baseline (ML)**: Geological history of the coordinates.
2. **Current Precipitation**: Multiplier spikes if Live Rain > 30mm.
3. **Vegetation Bonus**: Forests (High NDVI) reduce risk by ~30%.
4. **Saturation Penalty**: Saturated ground (NASA SMAP > 35%) increases risk by 1.5x.
5. **Urban Offset**: Major cities (e.g. SF/Seattle) get a 50% stability bonus for engineered drainage.

---

## 📡 API Reference (POST `/v1/analyze`)

**Request:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "radius": 5.0
}
```

**Response (Relevant for Visualizer):**
```json
{
  "risk_score": 0.4215,
  "environment": {
    "auto_rainfall_mm": 0.0,
    "auto_soil_type": "loam",
    "ndvi": 0.12,
    "soil_moisture": 0.15,
    "is_burn_zone": false
  },
  "flow_paths": { ... }
}
```

---

## 🧪 System Verification
To ensure your visualizer changes haven't broken the logic or API orchestration, run the global verification suite:
```powershell
.\venv\Scripts\python.exe verification_suite.py
```

---
*Created for HackIllinois 2026. Powered by AI and Global Satellite Constellations.*
