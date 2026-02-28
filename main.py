from fastapi import FastAPI
from pydantic import BaseModel
import sys
from pathlib import Path
from src.risk_model import predict

app = FastAPI(title="FloodGuard API")

class AnalyzeRequest(BaseModel):
    latitude: float
    longitude: float
    radius: float
    rainfall_mm: float
    soil_type: str  # "clay", "sandy", "loam"

@app.get("/v1/health")
def health():
    return {"status": "ok"}

@app.post("/v1/analyze")
async def analyze(request: AnalyzeRequest):
    # Call the ML model
    risk_score = predict(request.latitude, request.longitude)
    
    return {
        "risk_score": float(risk_score),
        "status": "success",
        "input_params": request
    }
