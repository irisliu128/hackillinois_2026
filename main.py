from fastapi import FastAPI
from pydantic import BaseModel

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
    return {
        "message": "coming soon",
        "received": request
    }
