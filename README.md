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

## 🧠 Brain Logic (v4.1 Multi-Factor Fusion)
The Risk Score (`0.0 - 1.0`) is a weighted fusion of:
1. **Historical Baseline (ML)**: Geological history tracked via `nasa_glc.csv`.
2. **Saturation Memory**: 7-day rainfall accumulation (Open-Meteo API).
3. **Vegetation Bonus**: Forests (High NDVI) reduce risk by ~30%.
4. **Saturation Penalty**: Saturated ground (NASA SMAP > 35%) increases risk by 1.5x.
5. **Urban Safety Bonus**: Dynamic OSM checks for "Infrastructure Stability" bonuses (roads/buildings).
6. **Geography Guard**: Returns `0.0` immediately for ocean/polar ice coordinates.

---

## 🚀 How to Run (For Team Members / Fresh Clones)

### 1. Setup Environment
Copy the example environment file and fill in your actual keys (Ask Arul or Tanish for keys if you don't have them):
```powershell
cp .env.example .env
```
Ensure your `.env` file has the following populated:
```text
SUPABASE_URL="your_supabase_url_here"
SUPABASE_KEY="your_supabase_anon_key_here"
GEE_PROJECT_ID=hydroproject-488807
OPENWEATHER_API_KEY=your_key_here
```

### 2. Start the Integrated Backend
The backend serves the **FastAPI JSON API** and powers the ML Risk Model. Open a terminal in the root directory:
```powershell
# Create and activate virtual environment (Windows)
python -m venv venv
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Run the server
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- **Access API Docs**: `http://localhost:8000/docs`

### 3. Start the React Frontend
The frontend is a Vite + React application. Open a *second* terminal window and navigate to the frontend folder:
```powershell
cd frontend
npm install
npm run dev
```
- **Access UI**: Usually `http://localhost:5173` (Check your terminal output for the exact local URL).

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
