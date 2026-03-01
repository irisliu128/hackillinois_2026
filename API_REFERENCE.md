# TerraSight API Reference Manual

TerraSight provides RESTful endpoints for real-time hydrological routing and landslide risk assessment in topographically complex regions. Powered by FastAPI, WhiteboxTools, and Google Earth Engine (GEE), the platform bridges raw satellite data and actionable field intelligence to provide sub-20 second processing.


## Authentication

Authentication is required for all data and analytics endpoints.

**Mechanism**: Bearer Token
**Header Format**: 
```http
Authorization: Bearer <YOUR_API_TOKEN>
```

---

## Core Endpoints

### 1. Execute Analysis Pipeline
**`POST /v1/analyze`**

The primary ingress for geospatial risk analysis. Evaluates a geographic point combining machine learning likelihood (Random Forest + NASA Landslide Catalog data), live weather tracking, satellite vegetation indices (NDVI), and soil moisture.

**Request Body (JSON Schema)**
```json
{
  "latitude": 22.57,
  "longitude": 88.36,
  "radius": 5.0,
  "rainfall_forecast": 45.5 // Optional, overrides active weather API
}
```

**Successful Response (`200 OK`)**
Returns the computed risk score and immediate metadata. Note: for heavier geo-computation, `flow_paths` metadata represents initial surface accumulation paths, deferring to the separate `/v1/flow-paths/{analysis_id}` endpoint for full vector geometry.
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
    "processing_time_s": 14.21,
    "analysis_id": "an_c8d21ea4f"
  }
}
```

### 2. Retrieve Risk Zones
**`GET /v1/risk-zones/{analysis_id}`**

Returns a GeoJSON FeatureCollection of high-risk polygons generated directly from the ML engine's inference over the buffered radius, factored against historical NASA Landslide Catalog topography.

**Response (`200 OK`)**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[88.35, 22.56], [88.36, 22.56], [88.36, 22.57], [88.35, 22.57], [88.35, 22.56]]]
      },
      "properties": {
        "risk_level": "critical",
        "soil_type": "clay",
        "model_confidence": 0.91
      }
    }
  ]
}
```

### 3. Retrieve Flow Accumulation Paths
**`GET /v1/flow-paths/{analysis_id}`**

Returns a GeoJSON containing LineStrings representing the D8 Flow Accumulation paths routed through the analyzed terrain. Computation relies on WhiteboxTools extracting digital elevation hydrology profiles.

**Response (`200 OK`)**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[88.355, 22.565], [88.358, 22.562], [88.360, 22.559]]
      },
      "properties": {
        "stream_order": 3,
        "accumulation_value": 4500
      }
    }
  ]
}
```

---

## Adaptive Polling Logic

To mitigate polling fatigue while ensuring safety during critical weather events, TerraSight implements an Adaptive Scaler. Connected frontend applications should respect the API's returned **`x-polling-interval`** header.

By default, an inactive coordinate evaluates to a safe state polling every 24 hours (`1440` minutes).

When the backend identifies "High Risk" triggers—such as a terrain `slope > 30%` coinciding with intense rainfall—the response header dynamically scales down the recommended interval.
* **Normal**: `x-polling-interval: 1440` (24h)
* **Elevated**: `x-polling-interval: 360` (6h)
* **Critical**: `x-polling-interval: 60` (1h)

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
  "risk_score": 0.0
}
```

**`503 Service Unavailable` — Terrain Engine Degraded**
In regions where satellite altimetry (SRTM / Copernicus) patchiness occurs, GEE fetching may timeout or WhiteboxTools may fail. 
Instead of a hard failure, the `/v1/analyze` endpoint gracefully degrades. It will return `"flow_paths": null` and append a `warning` key in `metadata`, but *will* still yield the ML `risk_score` based on coordinate heuristics.

```json
{
  "risk_score": 0.42,
  "flow_paths": null,
  "status": "success",
  "metadata": {
    "lat": -10.5,
    "lon": 40.2,
    "warning": "TerrainAnalyzer not initialised — flow paths unavailable."
  }
}
```
