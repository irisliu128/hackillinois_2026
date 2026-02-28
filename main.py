from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pathlib import Path
from src.risk_model import predict
from terrain_engine import TerrainAnalyzer
import uuid
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

app = FastAPI(title="FloodGuard API")

# Initialize Terrain Engine
# Use a relative path or a common temp path for the working directory
try:
    terrain_engine = TerrainAnalyzer(work_dir="./data/terrain_cache")
except Exception as e:
    print(f"Warning: Terrain Engine failed to initialize: {e}")
    terrain_engine = None

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    # 1. Call the ML Risk Model
    risk_score = predict(request.latitude, request.longitude)
    
    # 2. Call the Terrain Engine for Hydrology (Flow Paths)
    flow_paths = None
    if terrain_engine:
        try:
            # Note: This might take 5-15 seconds as it fetches from Google Earth Engine
            geojson_path = terrain_engine.run_full_pipeline(request.latitude, request.longitude)
            if geojson_path and os.path.exists(geojson_path):
                with open(geojson_path, "r") as f:
                    flow_paths = json.load(f)
        except Exception as e:
            print(f"Terrain Engine Error during analysis: {e}")

    return {
        "risk_score": float(risk_score),
        "flow_paths": flow_paths,
        "status": "success",
        "input_params": request
    }
class UserSettings(BaseModel):
    polling_interval_minutes: int = 60  # default 60 mins

@app.post("/v1/settings")
async def create_settings(settings: UserSettings):
    session_id = str(uuid.uuid4())
    
    supabase.table("user_settings").insert({
        "session_id": session_id,
        "polling_interval_minutes": settings.polling_interval_minutes
    }).execute()
    
    return {
        "session_id": session_id,
        "polling_interval_minutes": settings.polling_interval_minutes,
        "message": "Settings saved successfully"
    }

@app.get("/v1/settings/{session_id}")
async def get_settings(session_id: str):
    result = supabase.table("user_settings").select("*").eq("session_id", session_id).execute()
    return result.data[0]

@app.put("/v1/settings/{session_id}")
async def update_settings(session_id: str, settings: UserSettings):
    supabase.table("user_settings").update({
        "polling_interval_minutes": settings.polling_interval_minutes,
        "updated_at": "now()"
    }).eq("session_id", session_id).execute()
    
    return {
        "session_id": session_id,
        "polling_interval_minutes": settings.polling_interval_minutes,
        "message": "Settings updated successfully"
    }
