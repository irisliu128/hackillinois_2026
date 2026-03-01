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

def check_urban(lat: float, lon: float) -> bool:
    import requests
    import requests_cache
    from pathlib import Path
    
    is_urban = False
    try:
        # Resilient Caching: Only query OSM Overpass if we haven't checked this area recently
        cache_dir = Path("./data/terrain_cache") / "osm_cache"
        session = requests_cache.CachedSession(str(cache_dir), expire_after=86400) # 24 hour cache
        
        grid_lat = round(lat, 2)
        grid_lon = round(lon, 2)
        
        # Check OpenStreetMap for urban infrastructure (buildings or major roads) within a ~1km radius
        bbox = f"{grid_lat - 0.01},{grid_lon - 0.01},{grid_lat + 0.01},{grid_lon + 0.01}" 
        query = f"""
        [out:json][timeout:5];
        (
          way["highway"~"primary|secondary|tertiary|residential"]({bbox});
          way["building"]({bbox});
        );
        out count;
        """
        response = session.post(
            "https://overpass-api.de/api/interpreter", 
            data={"data": query}, 
            headers={"User-Agent": "TerraSight-Hydrology/1.0 (hackillinois2026; contact@example.com)"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if int(data.get("elements", [{}])[0].get("tags", {}).get("ways", 0)) > 50:
                 is_urban = True
    except Exception:
        pass # If OSM fails or rate-limits, safely default back to rural
    return is_urban

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
    is_urban = check_urban(round(lat, 3), round(lon, 3))
        
    if is_urban:
        multiplier *= 0.4 # 60% safety bonus for engineered cities

    # logger.info(f"CALC: base={base_prob:.2f} multi={multiplier:.2f} ndvi={ndvi:.2f} soil={soil_type}")
    final_prob = float(np.clip(base_prob * multiplier, 0.0, 1.0))
    return final_prob
