# 🌍 TerraSight: Global Landslide Intelligence Platform (v4.1)

TerraSight is an autonomous, global-scale landslide risk and hydrological analysis tool designed for government agencies and NGOs. It combines **Machine Learning**, **Multi-Satellite Data (NASA/ESA)**, and **Physics-based Simulations** to predict regional hazards with zero manual input.

---

## 🛠️ Developer Status (Feb 2026 - v4.1 Improvements)
**[COMPLETED] Risk Pipeline Optimization**
- **Ocean Interception (NEW)**: Integrates `global-land-mask` to prevent risk hallucinations in water bodies.
- **7-Day Temporal Weather (NEW)**: Switched to Open-Meteo Historical API for a 7-day rolling rain accumulation memory.
- **Dynamic Urban Tracking (NEW)**: Global OSM Overpass integration detects infrastructure density anywhere on Earth.
- **Resilient GEE Caching (NEW)**: 24-hour result persistence to prevent Earth Engine API timeouts.
- **Satellite Surveillance**:
    - **NDVI (Sentinel-2)**: Detects vegetation root stability.
    - **Soil Moisture (NASA SMAP)**: Detects ground saturation history.
    - **Burn Scars (MODIS)**: Detects post-wildfire instability.

---

## 🧠 Brain Logic (v4.2 Multi-Factor Predictive Fusion)
The Risk Score (`0.0 - 1.0`) is a weighted fusion of:
1. **Historical Baseline (ML)**: Geological history tracked via `nasa_glc.csv`.
2. **Forecasted Precipitation**: Open-Meteo API for 7-day rolling precipitation forecast.
3. **Vegetation Bonus**: Forests (High NDVI) reduce risk by ~30%.
4. **Saturation Penalty**: Saturated ground (NASA SMAP > 35%) increases risk by 1.5x.
5. **Urban Safety Bonus**: Dynamic OSM checks for "Infrastructure Stability" bonuses (roads/buildings).
6. **Geography Guard**: Returns `0.0` immediately for ocean/polar ice coordinates.

---

## 🚀 How to Run (For Team Members)

### 1. Setup Environment
Ensure your `.env` file has the following (Ask Arul or Tanish for keys):
```text
GEE_PROJECT_ID=hydroproject-488807
OPENWEATHER_API_KEY=your_key_here
```
> **Note on Backup/Clones**: The `.env` file is intentionally ignored by `.gitignore` for security. If you clone this repository to a new machine or pull it from the backup personal branch, you **must manually transfer** or recreate the `.env` file.

### 2. Start the Integrated Backend
The backend serves the **FastAPI Streaming API** and the frontend application connects to it.
```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- **Access API Docs**: `http://localhost:8000/docs`

### 3. Start the Frontend
In a new terminal:
```powershell
cd frontend
npm install
npm run dev
```
- **Access UI**: `http://localhost:3000` (or the port Vite provides)

---

## 📡 API Reference (POST `/v1/analyze`)

The backend now uses **Server-Sent Events (SSE)** via FastAPI's `StreamingResponse` to push real-time pipeline progress to the client, solving UX blockers during 10-20 second Earth Engine/Hydrology analyses.

**Request:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "radius": 5.0
}
```

**Streamed Response (SSE `text/event-stream`):**
```text
data: {"log": "Locating Coordinates & Validating Geography..."}

data: {"log": "Fetching 7-Day Weather Forecast & Soil Data..."}

data: {"log": "Calculating ML Predictive Risk Forecast..."}

data: {"log": "Running Hydrology Pipeline (GEE + WhiteboxTools) ... This may take 10-20 seconds."}

data: {
  "risk_score": 0.4215,
  "risk_forecast": [0.4215, 0.4503, 0.4901, 0.6850, 0.8012, 0.8012, 0.7915],
  "environment": {
    "auto_rainfall_mm": 0.0,
    "auto_soil_type": "loam",
    "ndvi": 0.12,
    "soil_moisture": 0.15,
    "is_burn_zone": false
  },
  "flow_paths": { ... },
  "status": "success"
}
```

---

## 🧪 System Verification
To ensure your visualizer changes haven't broken the logic or API orchestration, run the global verification and smoke tests:
```powershell
.\venv\Scripts\python.exe verification_suite.py
.\venv\Scripts\python.exe smoke_test.py
```

---
*Created for HackIllinois 2026. Powered by AI and Global Satellite Constellations.*
