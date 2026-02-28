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

def predict(lat: float, lon: float, rainfall_mm: float = 0.0, soil_type: str = "loam", model_path: str | Path | None = None) -> float:
    """
    Return landslide risk probability (0.0–1.0) for the given coordinate.
    Calculates a base probability from the ML model, then applies a
    Live Calibration factor based on real-time Rainfall and Soil data.
    """
    art = load(model_path)
    model = art["model"]
    features = art["features"]
    X = _featurize(lat, lon, features)
    base_prob = float(model.predict_proba(X)[0, 1])
    
    # ── Live Calibration (Environmental Adjustment) ─────────────────────────
    # The ML model provides a 'Historical/Geological Baseline'. 
    # We adjust this for 'Live' conditions.
    
    multiplier = 1.0
    
    # 1. Rainfall Impact: Landslides are hydraulic events. 
    # If it's bone dry (0mm rain), we still respect the historical baseline 
    # but apply a slight reduction (e.g. 70% of baseline).
    if rainfall_mm < 1.0:
        multiplier *= 0.7 
    elif rainfall_mm > 5.0:  # Active precipitation
        multiplier *= 1.2
    elif rainfall_mm > 30.0: # Severe weather
        multiplier *= 1.8

    # 2. Soil Impact: Clay is slippery when wet; Sand drains.
    if soil_type == "clay":
        multiplier *= 1.2
    elif soil_type == "sandy":
        multiplier *= 0.8
    else: # Loam/Unknown
        multiplier *= 1.0

    final_prob = float(np.clip(base_prob * multiplier, 0.0, 1.0))
    return final_prob