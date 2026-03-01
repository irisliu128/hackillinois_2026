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
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ── Project-internal imports ────────────────────────────────────────────────
from src.risk_model import predict as risk_predict, load as load_risk_model
from src.weather_service import fetch_rainfall_data, fetch_rainfall_forecast
from src.soil_service import fetch_soil_type
from src.adaptive_scaler import AdaptiveScaler, run_adaptive_polling_loop
from src.intervention_scanner import InterventionScanner
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

# ── Pydantic schemas ──────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    latitude: float = Field(..., ge=-90,  le=90,   description="Decimal latitude")
    longitude: float = Field(..., ge=-180, le=180,  description="Decimal longitude")
    radius: float    = Field(..., gt=0,             description="Analysis radius in km")


class SimulateRequest(BaseModel):
    latitude: float  = Field(..., ge=-90,  le=90,   description="Analysis latitude")
    longitude: float = Field(..., ge=-180, le=180,  description="Analysis longitude")
    proposed_channel: dict = Field(..., description="GeoJSON LineString drawn by the user")
    intervention_strength: float = Field(0.5, ge=0.1, le=1.0,
        description="Multiplier applied to base risk downstream (0.5 = 50% reduction)")


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
    Run the full FloodGuard pipeline with Server-Sent Events (SSE).
    """
    async def event_generator():
        t0 = time.perf_counter()
        logger.info(f"→ /v1/analyze  lat={req.latitude:.4f} lon={req.longitude:.4f} radius={req.radius}km")
        
        yield f'data: {json.dumps({"log": "Locating Coordinates & Validating Geography..."})}\n\n'
        await asyncio.sleep(0.05)
        
        # ── Step 0: Auto-fetch Environment & Validate Geography ─────────────
        from global_land_mask import globe
        is_on_land = globe.is_land(req.latitude, req.longitude)
        if not is_on_land:
            logger.warning("   Coordinate is in the ocean. Exiting early.")
            yield f'data: {json.dumps({"error": "Coordinate is not on land", "detail": "Located in the ocean."})}\n\n'
            return
            
        yield f'data: {json.dumps({"log": "Fetching 7-Day Weather Forecast & Soil Data..."})}\n\n'
        await asyncio.sleep(0.05)
        rainfall_mm: float = fetch_rainfall_data(req.latitude, req.longitude)
        rainfall_forecast: list[float] = fetch_rainfall_forecast(req.latitude, req.longitude)
        soil_type: str = fetch_soil_type(req.latitude, req.longitude)
        
        yield f'data: {json.dumps({"log": "Fetching GEE Satellite Indices (NDVI, Moisture)..."})}\n\n'
        await asyncio.sleep(0.05)
        satellite_context = {"ndvi": 0.5, "soil_moisture": 0.2, "is_burn_zone": False}
        if _terrain_analyzer:
            try:
                satellite_context = await asyncio.to_thread(_terrain_analyzer.get_environmental_context, req.latitude, req.longitude)
            except Exception as e:
                logger.warning(f"   Satellite fetch failed, using defaults: {e}")
                
        env_data = {
            "auto_rainfall_mm": rainfall_mm,
            "auto_soil_type": soil_type,
            "ndvi": satellite_context["ndvi"],
            "soil_moisture": satellite_context["soil_moisture"],
            "is_burn_zone": satellite_context["is_burn_zone"]
        }
        
        yield f'data: {json.dumps({"log": "Calculating ML Predictive Risk Forecast..."})}\n\n'
        await asyncio.sleep(0.05)
        # ── Step 1: ML Risk Score ────────────────────
        try:
            risk_score: float = risk_predict(
                req.latitude, req.longitude, 
                rainfall_mm=rainfall_mm, soil_type=soil_type,
                ndvi=satellite_context["ndvi"], soil_moisture=satellite_context["soil_moisture"],
                is_burn_zone=satellite_context["is_burn_zone"]
            )
            
            risk_forecast = []
            cumulative_rain = rainfall_mm
            for daily_rain in rainfall_forecast:
                cumulative_rain += daily_rain
                forecast_score = risk_predict(
                    req.latitude, req.longitude, 
                    rainfall_mm=cumulative_rain, soil_type=soil_type,
                    ndvi=satellite_context["ndvi"], soil_moisture=satellite_context["soil_moisture"],
                    is_burn_zone=satellite_context["is_burn_zone"]
                )
                risk_forecast.append(forecast_score)
        except Exception as exc:
            logger.error(f"   Risk model prediction failed: {exc}")
            yield f'data: {json.dumps({"error": "Risk model unavailable", "detail": str(exc)})}\n\n'
            return

        # ── Step 2: Terrain Pipeline (slow / optional) ───────────────────────────
        flow_paths = None
        terrain_warning: str | None = None

        if _terrain_analyzer is None:
            terrain_warning = "TerrainAnalyzer not initialised — flow paths unavailable."
            yield f'data: {json.dumps({"log": "Terrain engine disabled. Skipping flow paths..."})}\n\n'
            await asyncio.sleep(0.05)
        else:
            yield f'data: {json.dumps({"log": "Running Hydrology Pipeline (GEE + WhiteboxTools) ... This may take 10-20 seconds."})}\n\n'
            await asyncio.sleep(0.05)
            try:
                geojson_path: str | None = await asyncio.to_thread(
                    _terrain_analyzer.run_full_pipeline, req.latitude, req.longitude
                )
                if geojson_path and os.path.exists(geojson_path):
                    with open(geojson_path, "r") as fh:
                        flow_paths = json.load(fh)
                    num_features = len(flow_paths.get('features', []))
                    yield f'data: {json.dumps({"log": f"Flow paths generated successfully ({num_features} features found)."})}\n\n'
                    await asyncio.sleep(0.05)
                else:
                    terrain_warning = "Terrain pipeline ran but produced no GeoJSON output."
            except Exception as exc:
                terrain_warning = f"Terrain pipeline error: {exc}"
                yield f'data: {json.dumps({"log": f"Terrain pipeline error: {exc}"})}\n\n'
                await asyncio.sleep(0.05)

        # ── Step 3: Intervention Scanner ─────────────────────────────────────
        recommendations: list[dict] = []
        try:
            yield f'data: {json.dumps({"log": "Running Intervention Scanner (River Nodes + Slope Intersection)..."})}\n\n'
            await asyncio.sleep(0.05)
            scanner = InterventionScanner(work_dir="./data/terrain_cache")
            recommendations = await asyncio.to_thread(scanner.run)
            critical_count = sum(1 for r in recommendations if r.get("critical_diversion_point"))
            yield f'data: {json.dumps({"log": f"Intervention scan complete: {len(recommendations)} recommendation(s) ({critical_count} critical diversion point(s))."})}\n\n'
            await asyncio.sleep(0.05)
        except Exception as exc:
            logger.warning(f"Intervention scanner failed (non-fatal): {exc}")
            yield f'data: {json.dumps({"log": f"Intervention scanner skipped: {exc}"})}\n\n'
            await asyncio.sleep(0.05)

        elapsed_total = time.perf_counter() - t0
        response = {
            "risk_score": risk_score,
            "risk_forecast": risk_forecast,
            "flow_paths": flow_paths,
            "recommendations": recommendations,
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
        
        yield f'data: {json.dumps(response)}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── What-If Simulation Endpoint ───────────────────────────────────────────────
@app.post("/v1/simulate", tags=["Simulation"])
async def simulate(req: SimulateRequest):
    """
    What-If Simulation: calculate the risk score reduction from a proposed
    diversion channel (LineString GeoJSON drawn by the user).

    The "Weight Hack": we do NOT re-run the full terrain pipeline.
    Instead, we apply `intervention_strength` as a multiplier to the base
    risk probability — demonstrating the downstream impact in real-time.
    """
    t0 = time.perf_counter()

    # Gather environment data quickly (cached by OSM/weather services)
    try:
        rainfall_mm: float = await asyncio.to_thread(fetch_rainfall_data, req.latitude, req.longitude)
        soil_type: str     = await asyncio.to_thread(fetch_soil_type, req.latitude, req.longitude)
    except Exception:
        rainfall_mm, soil_type = 0.0, "loam"

    # Compute baseline (pre-intervention) score
    pre_score = risk_predict(
        req.latitude, req.longitude,
        rainfall_mm=rainfall_mm,
        soil_type=soil_type,
    )

    # Extract downstream midpoint from the LineString
    coords = req.proposed_channel.get("coordinates", [])
    if len(coords) >= 2:
        mid_idx = len(coords) // 2
        ds_lon, ds_lat = float(coords[mid_idx][0]), float(coords[mid_idx][1])
    else:
        ds_lat, ds_lon = req.latitude, req.longitude

    # Compute post-intervention score using the weight hack
    post_score = risk_predict(
        ds_lat, ds_lon,
        rainfall_mm=rainfall_mm,
        soil_type=soil_type,
        intervention_multiplier=req.intervention_strength,
    )

    delta = round(pre_score - post_score, 4)
    pct_reduction = round((delta / max(pre_score, 0.001)) * 100, 1)
    elapsed = time.perf_counter() - t0

    # Run intervention scanner for extra context (non-blocking)
    recommendations: list[dict] = []
    try:
        scanner = InterventionScanner(work_dir="./data/terrain_cache")
        recommendations = await asyncio.to_thread(scanner.run)
    except Exception:
        pass

    return {
        "status": "success",
        "pre_intervention_score":  round(pre_score, 4),
        "post_intervention_score": round(post_score, 4),
        "risk_delta": delta,
        "pct_reduction": pct_reduction,
        "channel_coords": coords,
        "intervention_strength": req.intervention_strength,
        "recommendations": recommendations,
        "metadata": {
            "lat": req.latitude,
            "lon": req.longitude,
            "rainfall_mm": rainfall_mm,
            "soil_type": soil_type,
            "processing_time_s": round(elapsed, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


# ── Insurance Oracle Status ───────────────────────────────────────────────────
INSURANCE_RISK_THRESHOLD  = 0.75
INSURANCE_RAIN_THRESHOLD  = 30.0

@app.get("/v1/insurance/status", tags=["Insurance Oracle"])
async def insurance_status():
    """
    Returns the current parametric insurance oracle state.
    Reads the latest monitoring_sessions entries and evaluates dual-trigger.
    """
    try:
        result = (
            supabase.table("monitoring_sessions")
            .select("lat,lon,final_prob,rainfall_mm,risk_level,last_check")
            .order("last_check", desc=True)
            .limit(10)
            .execute()
        )
        sessions = result.data or []
    except Exception as exc:
        logger.warning(f"/v1/insurance/status DB query failed: {exc}")
        sessions = []

    triggered_sessions = []
    for s in sessions:
        prob      = s.get("final_prob", 0.0) or 0.0
        rain      = s.get("rainfall_mm", 0.0) or 0.0
        triggered = prob > INSURANCE_RISK_THRESHOLD and rain > INSURANCE_RAIN_THRESHOLD
        triggered_sessions.append({
            **s,
            "insurance_triggered": triggered,
            "trigger_prob_threshold":  INSURANCE_RISK_THRESHOLD,
            "trigger_rain_threshold":  INSURANCE_RAIN_THRESHOLD,
        })

    any_triggered = any(s["insurance_triggered"] for s in triggered_sessions)
    return {
        "oracle_status": "TRIGGERED" if any_triggered else "WATCHING",
        "sessions": triggered_sessions,
        "payout_narrative": (
            "DUAL THRESHOLD MET: Pre-disaster funding of $500,000 may now be released "
            "to registered NGO beneficiaries per parametric contract."
            if any_triggered else
            "No active triggers. Oracle monitoring all registered coordinates."
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

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
