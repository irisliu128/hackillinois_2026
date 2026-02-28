"""
FloodGuard API — main.py
FastAPI backend that orchestrates the ML risk model and GEE/WhiteboxTools
terrain engine, then serves the static Leaflet UI.

Run with:
    uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 120
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ── Project-internal imports ────────────────────────────────────────────────
from src.risk_model import predict as risk_predict, load as load_risk_model
from src.weather_service import fetch_rainfall_data
from src.soil_service import fetch_soil_type
from src.adaptive_scaler import AdaptiveScaler, run_adaptive_polling_loop
from terrain_engine import TerrainAnalyzer
import uuid
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("FloodGuard.API")

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="FloodGuard API",
    description="Landslide & flood risk analysis powered by ML + GEE terrain hydrology.",
    version="1.0.0",
)

# ── CORS — allow the Leaflet UI (served locally or from any origin) ──────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singleton initialisation at startup ─────────────────────────────────────
#    Both the ML model and the Terrain Engine are heavy; we load them once.

_terrain_analyzer: TerrainAnalyzer | None = None
_adaptive_scaler: AdaptiveScaler | None = None

# Default monitoring targets — add coordinates you want to watch continuously.
# Person 4: populate this list (or load from DB) to register active targets.
_POLL_TARGETS: list[dict] = [
    {"lat": 40.1164, "lon": -88.2434, "session_id": None},
    {"lat": 37.7749, "lon": -122.4194, "session_id": "some-session-uuid"},
]


@app.on_event("startup")
async def _startup():
    global _terrain_analyzer, _adaptive_scaler

    # 1. Warm up the ML model (caches internally via _ARTIFACT global)
    try:
        load_risk_model()
        logger.info("✅  Risk model loaded and cached.")
    except Exception as exc:
        logger.error(f"❌  Risk model failed to load: {exc}")

    # 2. Initialise TerrainAnalyzer (also triggers GEE auth)
    try:
        _terrain_analyzer = TerrainAnalyzer(work_dir="./data/terrain_cache")
        logger.info("✅  TerrainAnalyzer initialised.")
    except Exception as exc:
        logger.warning(f"⚠️  TerrainAnalyzer init failed — terrain features disabled: {exc}")
        _terrain_analyzer = None

    # 3. Start the Adaptive Polling Engine background loop
    _adaptive_scaler = AdaptiveScaler(supabase)
    if _POLL_TARGETS:
        asyncio.create_task(run_adaptive_polling_loop(supabase, _POLL_TARGETS))
        logger.info(f"✅  Adaptive polling loop started — {len(_POLL_TARGETS)} target(s).")
    else:
        logger.info("ℹ️   No poll targets registered; adaptive loop idle (add targets to _POLL_TARGETS).")


# ── Static files — serve index.html from the project root ───────────────────
#    Mount after routes so /v1/* is matched first.
_STATIC_DIR = Path(__file__).parent  # directory that contains index.html

# ── Pydantic schema ───────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    latitude: float = Field(..., ge=-90,  le=90,   description="Decimal latitude")
    longitude: float = Field(..., ge=-180, le=180,  description="Decimal longitude")
    radius: float    = Field(..., gt=0,             description="Analysis radius in km")


# ── Health endpoint ───────────────────────────────────────────────────────────
@app.get("/v1/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "terrain_engine": _terrain_analyzer is not None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Primary analysis endpoint (POST /v1/analyze) ────────────────────────────
@app.post("/v1/analyze", tags=["Analysis"])
async def analyze(req: AnalyzeRequest):
    """
    Run the full FloodGuard pipeline:
      1. ML risk score (fast, always available)
      2. Terrain hydrology / flow paths via GEE + WhiteboxTools (may be slow or unavailable)
    
    If the terrain pipeline fails for any reason the endpoint still returns the
    ML risk score with flow_paths: null and a warning in metadata.
    """
    t0 = time.perf_counter()
    logger.info(
        f"→ /v1/analyze  lat={req.latitude:.4f} lon={req.longitude:.4f} radius={req.radius}km"
    )

    # ── Step 0: Auto-fetch Environment (Arul's Automation) ───────────────────
    logger.info("   Auto-detecting regional environmental data...")
    rainfall_mm: float = fetch_rainfall_data(req.latitude, req.longitude)
    soil_type: str = fetch_soil_type(req.latitude, req.longitude)
    
    # NEW: Fetch satellite indices from Terrain Engine (GEE)
    satellite_context = {"ndvi": 0.5, "soil_moisture": 0.2, "is_burn_zone": False}
    if _terrain_analyzer:
        try:
            satellite_context = _terrain_analyzer.get_environmental_context(req.latitude, req.longitude)
        except Exception as e:
            logger.warning(f"   Satellite fetch failed, using defaults: {e}")

    logger.info(f"   Environment detected: {rainfall_mm}mm rain, soil={soil_type}, ndvi={satellite_context['ndvi']:.2f}")
    
    env_data = {
        "auto_rainfall_mm": rainfall_mm,
        "auto_soil_type": soil_type,
        "ndvi": satellite_context["ndvi"],
        "soil_moisture": satellite_context["soil_moisture"],
        "is_burn_zone": satellite_context["is_burn_zone"]
    }

    # ── Step 1: ML Risk Score (synchronous but very fast) ────────────────────
    try:
        # Fusion: ML + Weather + GEE Satellite Indices
        risk_score: float = risk_predict(
            req.latitude, 
            req.longitude, 
            rainfall_mm=rainfall_mm, 
            soil_type=soil_type,
            ndvi=satellite_context["ndvi"],
            soil_moisture=satellite_context["soil_moisture"],
            is_burn_zone=satellite_context["is_burn_zone"]
        )
        logger.info(f"   ML risk score (Live Calibrated v3.0): {risk_score:.4f}")
    except Exception as exc:
        logger.error(f"   Risk model prediction failed: {exc}")
        # Return a structured error so the frontend can degrade gracefully
        return JSONResponse(
            status_code=503,
            content={
                "error": "Risk model unavailable",
                "detail": str(exc),
                "risk_score": None,
                "flow_paths": None,
                "metadata": _build_metadata(req, elapsed=time.perf_counter() - t0),
            },
        )

    # ── Step 2: Terrain Pipeline (slow / optional) ───────────────────────────
    flow_paths = None
    terrain_warning: str | None = None

    if _terrain_analyzer is None:
        terrain_warning = "TerrainAnalyzer not initialised — flow paths unavailable."
        logger.warning(f"   {terrain_warning}")
    else:
        try:
            logger.info("   Starting terrain pipeline (GEE + WhiteboxTools) …")
            t_terrain = time.perf_counter()

            # run_full_pipeline is a blocking GIS call that can take 10-20 s.
            # We run it directly inside the async handler; FastAPI/uvicorn uses
            # a thread pool for the event loop so the server remains responsive.
            geojson_path: str | None = _terrain_analyzer.run_full_pipeline(
                req.latitude, req.longitude
            )

            elapsed_terrain = time.perf_counter() - t_terrain
            logger.info(f"   Terrain pipeline finished in {elapsed_terrain:.1f}s")

            if geojson_path and os.path.exists(geojson_path):
                with open(geojson_path, "r") as fh:
                    flow_paths = json.load(fh)
                logger.info(
                    f"   Loaded GeoJSON: {len(flow_paths.get('features', []))} features"
                )
            else:
                terrain_warning = "Terrain pipeline ran but produced no GeoJSON output."
                logger.warning(f"   {terrain_warning}")

        except Exception as exc:
            terrain_warning = f"Terrain pipeline error: {exc}"
            logger.error(f"   {terrain_warning}")
            # flow_paths stays None — we still return the ML score below

    # ── Build response ────────────────────────────────────────────────────────
    elapsed_total = time.perf_counter() - t0
    logger.info(f"← /v1/analyze completed in {elapsed_total:.2f}s")

    response = {
        "risk_score": risk_score,
        "flow_paths": flow_paths,
        "environment": env_data,
        "status": "success",
        "input_params": {
            "latitude": req.latitude,
            "longitude": req.longitude,
            "radius": req.radius,
        },
        "metadata": {
            **_build_metadata(req, elapsed=elapsed_total),
            **({"warning": terrain_warning} if terrain_warning else {}),
        },
    }
    return response

# ── User settings (Person 3's endpoint) ─────────────────────────────────────

class UserSettings(BaseModel):
    polling_interval_minutes: int = Field(1440, ge=1, description="Manual poll interval in minutes")
    auto_scale: bool = Field(True, description="When True, AdaptiveScaler emergency logic overrides manual interval")


@app.post("/v1/settings", tags=["Settings"])
async def create_settings(settings: UserSettings):
    """Create a new user settings session. Returns a session_id for future updates."""
    session_id = str(uuid.uuid4())
    supabase.table("user_settings").insert({
        "session_id": session_id,
        "polling_interval_minutes": settings.polling_interval_minutes,
        "auto_scale": settings.auto_scale,
    }).execute()
    return {
        "session_id": session_id,
        "polling_interval_minutes": settings.polling_interval_minutes,
        "auto_scale": settings.auto_scale,
        "message": "Settings saved successfully",
    }


@app.get("/v1/settings/{session_id}", tags=["Settings"])
async def get_settings(session_id: str):
    """Retrieve settings for the given session."""
    result = supabase.table("user_settings").select("*").eq("session_id", session_id).execute()
    if not result.data:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return result.data[0]


@app.put("/v1/settings/{session_id}", tags=["Settings"])
async def update_settings(session_id: str, settings: UserSettings):
    """Update polling settings. When auto_scale=True, AdaptiveScaler overrides manual interval."""
    supabase.table("user_settings").update({
        "polling_interval_minutes": settings.polling_interval_minutes,
        "auto_scale": settings.auto_scale,
        "updated_at": "now()",
    }).eq("session_id", session_id).execute()
    return {
        "session_id": session_id,
        "polling_interval_minutes": settings.polling_interval_minutes,
        "auto_scale": settings.auto_scale,
        "message": "Settings updated successfully",
    }


# ── On-demand poll trigger (Person 4's hook) ─────────────────────────────────

class PollRequest(BaseModel):
    latitude:   float = Field(..., ge=-90,  le=90)
    longitude:  float = Field(..., ge=-180, le=180)
    session_id: Optional[str] = Field(None, description="Optional user session for auto_scale lookup")


@app.post("/v1/poll", tags=["Adaptive Polling"])
async def trigger_poll(req: PollRequest, background_tasks: BackgroundTasks):
    """
    Manually trigger an adaptive poll evaluation for a specific coordinate.
    Useful for testing or one-off risk checks outside the background loop.
    Runs the scaler in the background so the response is immediate.
    """
    if _adaptive_scaler is None:
        return JSONResponse(status_code=503, content={"error": "AdaptiveScaler not initialised"})

    async def _run():
        interval = await _adaptive_scaler.calculate_next_poll_interval(
            req.latitude, req.longitude, req.session_id
        )
        logger.info(
            f"/v1/poll → ({req.latitude}, {req.longitude}) next interval: "
            f"{int(interval.total_seconds() // 3600)}h"
        )

    background_tasks.add_task(_run)
    return {
        "status": "queued",
        "message": f"Adaptive poll evaluation queued for ({req.latitude}, {req.longitude}).",
    }


# ── Helper ────────────────────────────────────────────────────────────────────
def _build_metadata(req: AnalyzeRequest, elapsed: float) -> dict:
    return {
        "lat": req.latitude,
        "lon": req.longitude,
        "radius_km": req.radius,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processing_time_s": round(elapsed, 3),
    }


# ── Mount static files LAST so API routes take priority ─────────────────────
app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
