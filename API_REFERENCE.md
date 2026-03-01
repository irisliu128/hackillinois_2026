# TerraSight API Reference Manual

TerraSight provides RESTful endpoints for real-time hydrological routing and landslide risk assessment in topographically complex regions. Powered by FastAPI, WhiteboxTools, and Google Earth Engine (GEE), the platform bridges raw satellite data and actionable field intelligence to provide sub-20 second processing.

---

## System

### Health Check
**`GET /v1/health`**

Validates system status and checks if the Terrain Engine is active.

**Response (`200 OK`)**
```json
{
  "status": "ok",
  "terrain_engine": true,
  "timestamp": "2026-03-01T07:53:24.590531+00:00"
}
```

---

## Analysis

### 1. Execute Analysis Pipeline
**`POST /v1/analyze`**

The primary ingress for geospatial risk analysis. Evaluates a geographic point combining machine learning likelihood (Random Forest + NASA Landslide Catalog data), live weather tracking, satellite vegetation indices (NDVI), and soil moisture.

**Request Body (JSON Schema)**
```json
{
  "latitude": 22.57,
  "longitude": 88.36,
  "radius": 5.0
}
```
*(Note: `latitude` and `longitude` must reside on land).*

**Successful Response (`200 OK`)**
Returns the computed risk score and immediate metadata.
```json
{
  "risk_score": 0.84,
  "flow_paths": null,
  "environment": {
    "auto_rainfall_mm": 45.5,
    "auto_soil_type": "clay",
    "ndvi": 0.35,
    "soil_moisture": 0.45,
    "is_burn_zone": false
  },
  "status": "success",
  "input_params": {
    "latitude": 22.57,
    "longitude": 88.36,
    "radius": 5.0
  },
  "metadata": {
    "lat": 22.57,
    "lon": 88.36,
    "radius_km": 5.0,
    "timestamp": "2026-03-01T01:30:00Z",
    "processing_time_s": 14.21
  }
}
```

---

## Settings

### 1. Create Settings
**`POST /v1/settings`**

Create a new user settings session. Returns a session_id for future updates.

**Request Body**
```json
{
  "polling_interval_minutes": 1440,
  "auto_scale": true
}
```

**Response (`200 OK`)**
```json
{
  "session_id": "8f8b9e...",
  "polling_interval_minutes": 1440,
  "auto_scale": true,
  "message": "Settings saved successfully"
}
```

### 2. Get Settings
**`GET /v1/settings/{session_id}`**

Retrieve settings for the given session.

**Response (`200 OK`)**
```json
{
  "session_id": "8f8b9e...",
  "polling_interval_minutes": 1440,
  "auto_scale": true,
  "updated_at": "2026-03-01T10:00:00Z"
}
```

### 3. Update Settings
**`PUT /v1/settings/{session_id}`**

Update polling settings. When `auto_scale=True`, the AdaptiveScaler overrides the manual interval during high-risk conditions.

**Request Body**
```json
{
  "polling_interval_minutes": 720,
  "auto_scale": true
}
```

**Response (`200 OK`)**
```json
{
  "session_id": "8f8b9e...",
  "polling_interval_minutes": 720,
  "auto_scale": true,
  "message": "Settings updated successfully"
}
```

---

## Adaptive Polling

### Trigger Poll
**`POST /v1/poll`**

Manually trigger an adaptive poll evaluation for a specific coordinate. Useful for testing or one-off risk checks outside the background loop. Runs the scaler in the background so the response is immediate.

**Request Body**
```json
{
  "latitude": 22.57,
  "longitude": 88.36,
  "session_id": "optional-session-id"
}
```

**Response (`200 OK`)**
```json
{
  "status": "queued",
  "message": "Adaptive poll evaluation queued for (22.57, 88.36)."
}
```

---

## Data Models

**Environment Context Schema**
```json
{
  "type": "object",
  "properties": {
    "auto_rainfall_mm": { "type": "number", "description": "Millimeters of rain accumulated/forecasted" },
    "auto_soil_type": { "type": "string", "enum": ["loam", "clay", "sand", "silt"] },
    "ndvi": { "type": "number", "minimum": -1.0, "maximum": 1.0, "description": "Normalized Difference Vegetation Index" },
    "soil_moisture": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "is_burn_zone": { "type": "boolean" }
  }
}
```

**Risk Score Detail**
The `risk_score` is a float between `0.0` and `1.0`. Scores $>0.7$ conventionally designate severe landslide susceptibility and automatically trigger aggressive adaptive polling.

---

## Error Handling

### Data Patchiness (Rural or Ocean Areas)

**`400 Bad Request` — Non-Land Coordinates**
Thrown exclusively when analysis coordinates fall into marine boundaries. Landslide metrics are irrelevant outside terrestrial zones.
```json
{
  "error": "Coordinate is not on land",
  "detail": "Coordinate (x, y) is located in the ocean. Landslide risk is completely entirely inapplicable.",
  "risk_score": 0.0,
  "flow_paths": null,
  "metadata": {}
}
```

**`503 Service Unavailable` — Terrain Engine Degraded**
In regions where satellite altimetry (SRTM / Copernicus) patchiness occurs, GEE fetching may timeout or WhiteboxTools may fail. 
Instead of a hard failure, the `/v1/analyze` endpoint gracefully degrades. It will return `"flow_paths": null` and append a `warning` key in `metadata`, but *will* still yield the ML `risk_score` based on coordinate heuristics.
