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

def predict(lat: float, lon: float, model_path: str | Path | None = None) -> float:
    """
    Return landslide risk probability (0.0–1.0) for the given coordinate.
    Designed to be imported directly by the FastAPI backend.
    """
    art = load(model_path)
    model = art["model"]
    features = art["features"]
    X = _featurize(lat, lon, features)
    prob = float(model.predict_proba(X)[0, 1])
    return prob