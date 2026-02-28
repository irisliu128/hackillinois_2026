# TerraSight — Project Context for Claude Code

## What We're Building
An API-first terrain analysis tool that takes satellite/elevation data + soil/rainfall
parameters for a rural farming region and returns:
- Recommended irrigation channel paths (where to dig, how deep/wide)
- Risk zones for oversaturation and mudslides
- A risk score per zone (0.0–1.0)

**Target users:** NGOs and government agricultural programs in the Global South —
not farmers directly. We're building the infrastructure layer they build on top of.

**Hackathon:** 36-hour sprint. Judges care about social impact + technical execution + demo quality.

---

## Team Structure (4 people, parallel vertical ownership)

| Person | Role | Deliverable |
|--------|------|-------------|
| P1 | Risk Profiler (Data & ML) | `predict(lat, lon)` → float (0.0–1.0) risk score, exported as `.pkl` Random Forest |
| P2 (Arul) | Terrain Engineer (GIS & Hydrology) | `get_water_paths(lat, lon, radius)` → GeoJSON using WhiteboxTools + Google Earth Engine |
| P3 | Architect (Backend & Integration) | FastAPI app, Supabase/PostGIS DB, live URL on Railway |
| **P4 (me)** | **UI/UX Storyteller (Frontend & Demo)** | **Streamlit app + pitch deck** |

---

## My Role — Person 4 Details

### Stack
- **Framework:** Streamlit (Python)
- **Map:** Pydeck (Mapbox dark-v11 style, 3D tilt)
- **Styling:** Custom CSS injected via `st.markdown` — Space Mono + DM Sans fonts, dark navy palette

### Files in this project
```
app.py            # Main Streamlit app — fully working with dummy data
requirements.txt  # streamlit>=1.35.0, pydeck>=0.9.0
CONTEXT.md        # This file
```

### To run
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Current State of app.py

### What's working (hardcoded dummy data)
- **Map** renders with Pydeck over Yen Bai Province, Vietnam (lat: 21.710, lon: 104.878)
- **4 water channel paths** — blue LineStrings, styled by flow volume (high/medium/low)
- **5 risk zones** — colored polygons (red = high risk, amber = medium, teal = low)
- **Sidebar** with coordinate inputs, rainfall slider, soil type selector, radius dropdown
- **Stats panel** on the right: overall risk score, channel count, at-risk area, channel spec table, risk zone table
- Hover tooltips on map features
- "Run Analysis" button (currently does nothing — needs API wiring)

### What's hardcoded and needs to be replaced
```python
WATER_CHANNELS = { ... }   # GeoJSON FeatureCollection — swap with API response
RISK_ZONES = { ... }       # GeoJSON FeatureCollection — swap with API response
```
The summary stats in the right panel (risk score 0.71, channel count 4, etc.)
are also hardcoded strings — these should pull from the API response too.

### How to wire the API (when Person 3's URL is live)
Replace the dummy data block with something like:
```python
import requests

def fetch_analysis(lat, lon, radius_km, rainfall_mm, soil):
    resp = requests.post("https://your-api-url/v1/analyze", json={
        "lat": lat, "lon": lon,
        "radius_km": radius_km,
        "rainfall_mm": rainfall_mm,
        "soil_type": soil
    })
    data = resp.json()
    return data["channel_geojson"], data["risk_zones"], data["summary"]
```
Then call this when the "Run Analysis" button is clicked and pass results into `make_layers()`.

---

## API Contract (agreed with Person 3)

### POST /v1/analyze
**Input:**
```json
{
  "lat": 21.710,
  "lon": 104.878,
  "radius_km": 5,
  "rainfall_mm": 1850,
  "soil_type": "clay_loam"
}
```
**Output:**
```json
{
  "analysis_id": "uuid",
  "channel_geojson": { "type": "FeatureCollection", "features": [...] },
  "risk_zones": { "type": "FeatureCollection", "features": [...] },
  "summary": {
    "overall_risk_score": 0.71,
    "channel_count": 4,
    "total_channel_length_km": 3.2,
    "high_risk_area_ha": 20.5
  }
}
```

### GET /v1/risk-zones/{analysis_id}
Returns the risk zone breakdown for a previous analysis.

### GET /v1/health
Health check — returns `{"status": "ok"}`.

---

## GeoJSON Feature Property Contracts

### Water Channels (LineString features)
```json
{
  "channel_id": "CH-001",
  "depth_m": 0.8,
  "width_m": 1.2,
  "flow_vol": "high"   // "high" | "medium" | "low"
}
```

### Risk Zones (Polygon features)
```json
{
  "zone_id": "RZ-01",
  "risk": "high",        // "high" | "medium" | "low"
  "risk_score": 0.87,    // 0.0–1.0
  "area_ha": 12.4
}
```
**These property names must stay consistent** — the Pydeck layer uses them for
color logic and tooltips. If P2/P3 change the schema, update the `get_line_color`
and `get_fill_color` expressions in `make_layers()` and the TOOLTIP html in app.py.

---

## My Remaining Tasks

- [ ] **Task 3 (Pitch Deck):** Build 5–6 slides around the NGO API narrative
  - Slide 1: The problem (smallholder farmers, climate risk, no infrastructure)
  - Slide 2: Our solution (TerraSight API)
  - Slide 3: Demo screenshot of the map
  - Slide 4: "What an NGO app looks like using our data" mockup
  - Slide 5: API endpoint overview + tech stack
  - Slide 6: Impact + scale potential
- [ ] Wire the "Run Analysis" button to a loading spinner + real API call (once P3 URL is live)
- [ ] Replace hardcoded summary stats with dynamic values from API response
- [ ] Polish: consider adding a "Download GeoJSON" button for the channel paths
- [ ] Consider: export/share analysis link using `analysis_id`

---

## Design System (don't break these)

```
Colors:
  --bg-base:      #0a0e14
  --bg-panel:     #111720
  --bg-card:      #161e2a
  --accent-teal:  #00d4aa   ← low risk / positive
  --accent-amber: #f5a623   ← medium risk / warning
  --accent-red:   #ff4d4d   ← high risk / danger
  --text-primary: #e8edf5
  --text-muted:   #6b7a96
  --border:       #1e2d42

Fonts:
  Space Mono  → headers, labels, code, monospaced elements
  DM Sans     → body text, descriptions

Map style: mapbox://styles/mapbox/dark-v11
Map center: lat 21.710, lon 104.878, zoom 12.5, pitch 35, bearing -10
```

---

## Demo Region
**Yen Bai Province, Northern Vietnam** — chosen because:
- High real-world landslide risk (Typhoon Yagi 2024 caused major mudslides here)
- Good elevation data coverage
- Compelling story for judges (Global South, climate impact)
- Coordinates: roughly 21.6–21.8°N, 104.8–104.95°E

---

## Key Technical Notes for Teammates

- P2 uses **WhiteboxTools** (`wbt.d8_flow_accumulation`, `wbt.fill_depressions`) for hydrology
- P1 uses **NASA Global Landslide Catalog** + Random Forest (scikit-learn) for risk scoring
- P3 uses **FastAPI** + **Supabase with PostGIS** extension for caching analysis results
- Elevation data source: **Google Earth Engine DEM** or **Copernicus** (both free)
- Flow routing algorithm: **D8** (deterministic, well-studied, no ML needed)
- P3 will deploy to **Railway** — that URL is what I wire my "Run Analysis" button to
