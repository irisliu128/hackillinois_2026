# src/risk_model.py
from __future__ import annotations

from pathlib import Path
import joblib
import numpy as np
import pandas as pd

_ARTIFACT = None

def _default_model_path() -> Path:
    # repo_root/models/risk_model.joblib
    return Path(__file__).resolve().parents[1] / "models" / "risk_model.joblib"

def load(model_path: str | Path | None = None):
    """Load the saved model artifact once and cache it in memory."""
    global _ARTIFACT
    if _ARTIFACT is not None:
        return _ARTIFACT
    path = Path(model_path) if model_path is not None else _default_model_path()
    _ARTIFACT = joblib.load(path)
    return _ARTIFACT

def _featurize(lat: float, lon: float, feature_order: list[str]) -> pd.DataFrame:
    lat = float(lat)
    lon = float(lon)
    row = {
        "lat": lat,
        "lon": lon,
        "lat_sin": float(np.sin(np.radians(lat))),
        "lat_cos": float(np.cos(np.radians(lat))),
        "lon_sin": float(np.sin(np.radians(lon))),
        "lon_cos": float(np.cos(np.radians(lon))),
    }
    return pd.DataFrame([row])[feature_order]

def predict(
    lat: float, 
    lon: float, 
    rainfall_mm: float = 0.0, 
    soil_type: str = "loam",
    ndvi: float = 0.5,
    soil_moisture: float = 0.2,
    is_burn_zone: bool = False,
    model_path: str | Path | None = None
) -> float:
    """
    Return landslide risk probability (0.0–1.0) for the given coordinate.
    Version 3.0: Multi-Factor Fusion (ML + Climate + GEE Satellite Indices).
    """
    art = load(model_path)
    model = art["model"]
    features = art["features"]
    X = _featurize(lat, lon, features)
    base_prob = float(model.predict_proba(X)[0, 1])
    
    # ── High-Fidelity Calibration ──────────────────────────────────────────
    multiplier = 1.0
    
    # 1. Rainfall Thresholds
    if rainfall_mm < 1.0:
        multiplier *= 0.7 
    elif rainfall_mm > 30.0: 
        multiplier *= 2.0 # Severe weather spike

    # 2. Soil Type (Clay is high risk)
    if soil_type == "clay":
        multiplier *= 1.2

    # 3. 🌳 Vegetation Stability (NDVI: 0 to 1)
    if ndvi > 0.6:
        multiplier *= 0.7 
    elif ndvi < 0.25:
        multiplier *= 1.2 # Slightly lower penalty for low vegetation

    # 4. 🪵 Soil Moisture History (Saturation Index)
    if soil_moisture > 0.35:
        multiplier *= 1.5 

    # 5. 🔥 Burn Scar Impact
    if is_burn_zone:
        multiplier *= 2.0 

    # 6. 🏗️ Urban Infrastructure
    import requests
    is_urban = False
    try:
        # Check OpenStreetMap for urban infrastructure (buildings or major roads) within a 1km radius
        # Overpass API uses format: (south, west, north, east)
        bbox = f"{lat - 0.01},{lon - 0.01},{lat + 0.01},{lon + 0.01}" 
        query = f"""
        [out:json][timeout:5];
        (
          way["highway"~"primary|secondary|tertiary|residential"]({bbox});
          way["building"]({bbox});
        );
        out count;
        """
        response = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=6)
        if response.status_code == 200:
            data = response.json()
            if int(data.get("elements", [{}])[0].get("tags", {}).get("ways", 0)) > 50:
                 is_urban = True
    except Exception:
        pass # If OSM fails, safely default back to rural
        
    if is_urban:
        multiplier *= 0.4 # 60% safety bonus for engineered cities

    # logger.info(f"CALC: base={base_prob:.2f} multi={multiplier:.2f} ndvi={ndvi:.2f} soil={soil_type}")
    final_prob = float(np.clip(base_prob * multiplier, 0.0, 1.0))
    return final_prob
