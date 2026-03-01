# TerraSight API Reference Manual (v1.0.0)

TerraSight provides RESTful endpoints for real-time hydrological routing and landslide risk assessment. By bridging Google Earth Engine (GEE) terrain data with Random Forest ML models, the platform delivers actionable intelligence for topographically complex regions in under 20 seconds.

---

## 🏥 System

### Health Check
**`GET /v1/health`**

Validates system connectivity and confirms the Terrain Engine (WhiteboxTools/GEE) is ready for processing.

**Response (200 OK)**
```json
{
  "status": "ok",
  "terrain_engine": true,
  "timestamp": "2026-03-01T07:53:24.590531+00:00"
}
```

---

## 🛰 Analysis

### Execute Analysis Pipeline
**`POST /v1/analyze`**

The core engine of TerraSight. It calculates landslide susceptibility by merging NASA Landslide Catalog heuristics with live environmental data.

**Request Body (JSON)**

| Parameter | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `latitude` | number | [−90.0, 90.0] | Geographic latitude (Must be on land). |
| `longitude` | number | [−180.0, 180.0] | Geographic longitude. |
| `radius` | number | > 0 | Search radius in kilometers. |

**Successful Response (200 OK)**
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

## ⚙️ Settings

### 1. Create Settings
**`POST /v1/settings`**

Initializes a new user session. Returns a `session_id` required for updates and adaptive polling.

**Request Body**
- `polling_interval_minutes`: integer (≥1). Default is usually 1440 (24 hours).
- `auto_scale`: boolean. If true, the system adjusts frequency based on risk.

### 2. Get Settings
**`GET /v1/settings/{session_id}`**

Retrieve the configuration for a specific session.

### 3. Update Settings
**`PUT /v1/settings/{session_id}`**

Allows manual overrides. Note that if `auto_scale` is active, the AdaptiveScaler will prioritize high-risk triggers over the manual `polling_interval_minutes`.

---

## 🔄 Adaptive Polling

### Trigger Poll
**`POST /v1/poll`**

Manually forces an adaptive evaluation. This is an asynchronous "fire and forget" call that queues the task in the background.

**Request Body**
```json
{
  "latitude": 22.57,
  "longitude": 88.36,
  "session_id": "string (optional)"
}
```

---

## 📊 Data Models

### Environment Context
- `auto_rainfall_mm`: Float. Accumulated or forecasted precipitation.
- `auto_soil_type`: String Enum: `["loam", "clay", "sand", "silt"]`.
- `ndvi`: Float ([−1.0, 1.0]). Vegetation density index.
- `soil_moisture`: Float ([0.0, 1.0]).

### Risk Score Heuristics
The `risk_score` is a float between 0.0 and 1.0.
- **Scores > 0.7**: Designate severe susceptibility.
- **Scores ≤ 0.3**: Designate nominal/stable conditions.

---

## ⚠️ Error Handling

### 422 Unprocessable Entity — Schema Violation
Thrown when inputs fall outside defined ranges (e.g., a latitude of 110 or a negative radius).
```json
{
  "detail": [
    {
      "loc": ["body", "latitude"],
      "msg": "Input should be less than or equal to 90",
      "type": "less_than_equal_to_threshold"
    }
  ]
}
```

### 400 Bad Request — Non-Land Coordinates
Thrown when the coordinate resides in the ocean.
- Landslide risk is entirely inapplicable for marine environments.

### 503 Service Unavailable — Terrain Engine Degraded
Occurs during SRTM/Copernicus data patchiness or GEE timeouts.
- **Behavior**: The API will still return a `risk_score` (based on ML heuristics), but `flow_paths` will be null and a warning will be added to the metadata.
