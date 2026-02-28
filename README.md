# 🌍 TerraSight: Environmental Intelligence Platform

TerraSight is an autonomous, global-scale landslide risk and hydrological analysis tool designed for government agencies and NGOs. It combines **Machine Learning**, **Live Satellite Data**, and **Physics-based Simulations** to predict regional hazards with zero manual input.

---

## 🛠️ Developer Status (Feb 2026)
**[COMPLETED] Person 1: Weather & Soil Automation**
- Integrated **OpenWeatherMap API** (Live Rainfall).
- Integrated **ISRIC SoilGrids API** (Global Soil Texture).
- Updated **ML Calibration Engine** to use Live Saturation data.
- Built **Professional Leaflet UI** with High-Contrast Satellite Mapping.

---

## 🚀 How to Run (For Prateek/Visualizer)

### 1. Setup Environment
Ensure your `.env` file has the following (Ask Arul or Tanish for keys):
```text
GEE_PROJECT_ID=hydroproject-488807
OPENWEATHER_API_KEY=your_key_here
```

### 2. Start the Integrated Backend
The backend now serves the **FastAPI JSON API** AND the **Map UI** from the same port.
```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- **Access UI**: `http://localhost:8000`
- **Access API Docs**: `http://localhost:8000/docs`

---

## 🧠 Brain Logic (The Calibration Engine)
The Risk Score (`0.0 - 1.0`) is no longer just a historical number. It is **Live-Calibrated** in `src/risk_model.py`:
- **Historical Baseline**: Determined by the Scikit-Learn model based on coordinates.
- **Rainfall Adjustment**: Risk is automatically reduced by **30%** on dry days and increased during storms.
- **Soil Adjustment**: Clay-heavy soils receive a risk penalty; sandy soils receive a drainage bonus.

---

## 📡 API Reference (POST `/v1/analyze`)

**Request:**
```json
{
  "latitude": 47.6062,
  "longitude": -122.3321,
  "radius": 5.0
}
```

**Response (Relevant for Visualizer):**
```json
{
  "risk_score": 0.6704,
  "environment": {
    "auto_rainfall_mm": 0.0,
    "auto_soil_type": "loam"
  },
  "flow_paths": { "type": "FeatureCollection", "features": [...] },
  "metadata": { ... }
}
```

---

## 🧪 System Verification
To ensure your visualizer changes haven't broken the risk logic or API orchestration, always run the smoke test:
```powershell
.\venv\Scripts\python.exe smoke_test.py
```

---
*Created for HackIllinois 2026. Powered by AI and Geospatial Science.*
