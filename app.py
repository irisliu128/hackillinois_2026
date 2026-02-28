import streamlit as st
import pydeck as pdk
import json
import requests

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TerraSight | Irrigation Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

  :root {
    --bg-base:      #0a0e14;
    --bg-panel:     #111720;
    --bg-card:      #161e2a;
    --accent-teal:  #00d4aa;
    --accent-amber: #f5a623;
    --accent-red:   #ff4d4d;
    --text-primary: #e8edf5;
    --text-muted:   #6b7a96;
    --border:       #1e2d42;
  }

  html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-base) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text-primary);
  }

  [data-testid="stSidebar"] {
    background-color: var(--bg-panel) !important;
    border-right: 1px solid var(--border);
  }

  [data-testid="stSidebar"] * { color: var(--text-primary) !important; }

  .stTextInput input, .stNumberInput input, .stSelectbox select {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 6px !important;
  }

  .stButton > button {
    background: linear-gradient(135deg, var(--accent-teal), #00a884) !important;
    color: #0a0e14 !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.6rem 1.4rem !important;
    width: 100%;
    letter-spacing: 0.05em;
    transition: opacity 0.2s;
  }
  .stButton > button:hover { opacity: 0.85 !important; }

  .metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.75rem;
  }
  .metric-label {
    font-size: 0.7rem;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.12em;
    color: var(--text-muted);
    text-transform: uppercase;
    margin-bottom: 0.25rem;
  }
  .metric-value {
    font-size: 1.6rem;
    font-weight: 600;
    line-height: 1.1;
  }
  .metric-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.2rem;
  }
  .risk-high   { color: var(--accent-red); }
  .risk-medium { color: var(--accent-amber); }
  .risk-low    { color: var(--accent-teal); }

  .section-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    color: var(--text-muted);
    text-transform: uppercase;
    margin: 1.4rem 0 0.6rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--border);
  }

  .legend-dot {
    display: inline-block;
    width: 10px; height: 10px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
  }
  .legend-row { font-size: 0.8rem; margin-bottom: 0.35rem; color: var(--text-muted); }

  .hero-title {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
    line-height: 1.2;
  }
  .hero-title span { color: var(--accent-teal); }
  .hero-sub {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: 0.4rem;
    margin-bottom: 1.5rem;
  }

  .status-badge {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    margin-bottom: 1rem;
  }
  .badge-live { background: rgba(0,212,170,0.12); color: var(--accent-teal); border: 1px solid rgba(0,212,170,0.3); }
  .badge-demo { background: rgba(245,166,35,0.12); color: var(--accent-amber); border: 1px solid rgba(245,166,35,0.3); }

  .channel-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
    margin-top: 0.5rem;
  }
  .channel-table th {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    padding: 0.4rem 0.5rem;
    border-bottom: 1px solid var(--border);
    text-align: left;
  }
  .channel-table td {
    padding: 0.45rem 0.5rem;
    border-bottom: 1px solid rgba(30,45,66,0.6);
    color: var(--text-primary);
  }
  .channel-table tr:hover td { background: rgba(255,255,255,0.02); }

  div[data-testid="stHorizontalBlock"] { gap: 1.2rem; }

  /* Hide streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Dummy GeoJSON Data ─────────────────────────────────────────────────────────
# Simulated region: Northern Vietnam highlands (Yen Bai province area)
# These are the hardcoded dummy paths / zones — swap for API response later

WATER_CHANNELS = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"channel_id": "CH-001", "depth_m": 0.8, "width_m": 1.2, "flow_vol": "high"},
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [104.872, 21.724], [104.878, 21.718], [104.885, 21.711],
                    [104.891, 21.705], [104.899, 21.698], [104.907, 21.692]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {"channel_id": "CH-002", "depth_m": 0.5, "width_m": 0.8, "flow_vol": "medium"},
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [104.862, 21.719], [104.869, 21.714], [104.875, 21.708],
                    [104.881, 21.701], [104.886, 21.695]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {"channel_id": "CH-003", "depth_m": 0.4, "width_m": 0.6, "flow_vol": "low"},
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [104.855, 21.710], [104.861, 21.706], [104.868, 21.700],
                    [104.874, 21.694]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {"channel_id": "CH-004", "depth_m": 0.9, "width_m": 1.4, "flow_vol": "high"},
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [104.891, 21.730], [104.894, 21.722], [104.897, 21.714],
                    [104.899, 21.705], [104.901, 21.698]
                ]
            }
        }
    ]
}

RISK_ZONES = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"zone_id": "RZ-01", "risk": "high", "risk_score": 0.87, "area_ha": 12.4},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [104.875, 21.722], [104.883, 21.722], [104.883, 21.715],
                    [104.875, 21.715], [104.875, 21.722]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {"zone_id": "RZ-02", "risk": "high", "risk_score": 0.79, "area_ha": 8.1},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [104.860, 21.713], [104.867, 21.713], [104.867, 21.707],
                    [104.860, 21.707], [104.860, 21.713]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {"zone_id": "RZ-03", "risk": "medium", "risk_score": 0.51, "area_ha": 18.7},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [104.888, 21.707], [104.898, 21.707], [104.898, 21.699],
                    [104.888, 21.699], [104.888, 21.707]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {"zone_id": "RZ-04", "risk": "medium", "risk_score": 0.44, "area_ha": 22.3},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [104.853, 21.703], [104.862, 21.703], [104.862, 21.696],
                    [104.853, 21.696], [104.853, 21.703]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {"zone_id": "RZ-05", "risk": "low", "risk_score": 0.21, "area_ha": 31.5},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [104.870, 21.696], [104.882, 21.696], [104.882, 21.688],
                    [104.870, 21.688], [104.870, 21.696]
                ]]
            }
        }
    ]
}

# ── Pydeck Layers ──────────────────────────────────────────────────────────────
def make_layers():
    risk_layer = pdk.Layer(
        "GeoJsonLayer",
        data=RISK_ZONES,
        pickable=True,
        stroked=True,
        filled=True,
        get_fill_color="""
            properties.risk === 'high'   ? [255, 77,  77,  90] :
            properties.risk === 'medium' ? [245, 166, 35,  70] :
                                           [0,   212, 170, 50]
        """,
        get_line_color="""
            properties.risk === 'high'   ? [255, 77,  77,  200] :
            properties.risk === 'medium' ? [245, 166, 35,  200] :
                                           [0,   212, 170, 180]
        """,
        get_line_width=40,
    )

    channel_layer = pdk.Layer(
        "GeoJsonLayer",
        data=WATER_CHANNELS,
        pickable=True,
        stroked=True,
        filled=False,
        get_line_color="""
            properties.flow_vol === 'high'   ? [0, 180, 255, 255] :
            properties.flow_vol === 'medium' ? [0, 140, 210, 220] :
                                               [0, 110, 180, 180]
        """,
        get_line_width="""properties.flow_vol === 'high' ? 60 : properties.flow_vol === 'medium' ? 40 : 25""",
        line_width_min_pixels=2,
    )

    return [risk_layer, channel_layer]


VIEW_STATE = pdk.ViewState(
    latitude=21.710,
    longitude=104.878,
    zoom=12.5,
    pitch=35,
    bearing=-10,
)

TOOLTIP = {
    "html": """
        <div style='
            font-family: "DM Sans", sans-serif;
            background: #111720;
            border: 1px solid #1e2d42;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
            color: #e8edf5;
            min-width: 160px;
        '>
            <b style='font-family:Space Mono,monospace;font-size:11px;color:#6b7a96;letter-spacing:0.1em'>
                {zone_id}{channel_id}
            </b><br>
            <span style='color:#6b7a96'>Risk Score: </span>
            <b>{risk_score}</b><br>
            <span style='color:#6b7a96'>Area: </span><b>{area_ha} ha</b>
            <span style='color:#6b7a96'>Depth: </span><b>{depth_m}m</b>
            <span style='color:#6b7a96'>Width: </span><b>{width_m}m</b>
        </div>
    """,
    "style": {"backgroundColor": "transparent", "border": "none"},
}


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div class='hero-title'>Terra<span>Sight</span></div>
        <div class='hero-sub'>Terrain Intelligence for Agricultural NGOs</div>
        <span class='status-badge badge-demo'>● DEMO MODE</span>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Target Region</div>", unsafe_allow_html=True)
    lat  = st.number_input("Latitude",  value=21.710,  format="%.4f", step=0.001)
    lon  = st.number_input("Longitude", value=104.878, format="%.4f", step=0.001)
    radius_km = st.selectbox("Analysis Radius", ["2 km", "5 km", "10 km", "25 km"], index=1)

    st.markdown("<div class='section-header'>Rainfall Parameters</div>", unsafe_allow_html=True)
    rainfall_mm = st.slider("Expected Annual Rainfall (mm)", 800, 3000, 1850, 50)
    season = st.selectbox("Season", ["Monsoon (Jun–Sep)", "Dry (Oct–Feb)", "Transition (Mar–May)"])

    st.markdown("<div class='section-header'>Soil Type</div>", unsafe_allow_html=True)
    soil = st.selectbox("Soil Classification", [
        "Clay Loam (high runoff)",
        "Sandy Loam (high drainage)",
        "Silty Clay (moderate)",
        "Auto-detect from coordinates",
    ], index=3)

    st.markdown("<br>", unsafe_allow_html=True)
    analyze = st.button("▶ Run Analysis")

    st.markdown("<div class='section-header'>Legend</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='legend-row'><span class='legend-dot' style='background:#ff4d4d'></span>High Risk Zone (mudslide)</div>
        <div class='legend-row'><span class='legend-dot' style='background:#f5a623'></span>Medium Risk Zone</div>
        <div class='legend-row'><span class='legend-dot' style='background:#00d4aa'></span>Low Risk Zone</div>
        <div class='legend-row'><span class='legend-dot' style='background:#00b4ff'></span>Recommended Channel Path</div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>API Endpoint</div>", unsafe_allow_html=True)
    st.code("POST /v1/analyze\nGET  /v1/risk-zones/{id}", language="bash")


# ── Main Content ───────────────────────────────────────────────────────────────
col_map, col_stats = st.columns([3, 1])

with col_map:
    st.markdown("""
        <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:0.6rem'>
            <div>
                <div class='section-header' style='margin-top:0;border:none;margin-bottom:0.1rem'>
                    ANALYSIS MAP
                </div>
                <span style='font-size:0.8rem;color:#6b7a96'>
                    Yen Bai Province, Vietnam — 5km radius
                </span>
            </div>
            <span class='status-badge badge-demo'>DEMO DATA</span>
        </div>
    """, unsafe_allow_html=True)

    deck = pdk.Deck(
        layers=make_layers(),
        initial_view_state=VIEW_STATE,
        tooltip=TOOLTIP,
        map_style="mapbox://styles/mapbox/dark-v11",
        parameters={"depthTest": False},
    )
    st.pydeck_chart(deck, use_container_width=True, height=580)

with col_stats:
    st.markdown("<div class='section-header' style='margin-top:0'>ANALYSIS SUMMARY</div>", unsafe_allow_html=True)

    # Call backend if button clicked
    risk_score = 0.71  # Default demo value
    risk_msg = "High — immediate attention advised"
    risk_class = "risk-high"
    
    if analyze:
        try:
            payload = {
                "latitude": lat,
                "longitude": lon,
                "radius": float(radius_km.split()[0]),
                "rainfall_mm": float(rainfall_mm),
                "soil_type": soil
            }
            resp = requests.post("http://localhost:8000/v1/analyze", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                risk_score = data.get("risk_score", 0.71)
                if risk_score > 0.7:
                    risk_msg = "High — immediate attention advised"
                    risk_class = "risk-high"
                elif risk_score > 0.4:
                    risk_msg = "Medium — monitor closely"
                    risk_class = "risk-medium"
                else:
                    risk_msg = "Low — normal operations"
                    risk_class = "risk-low"
            else:
                st.error(f"Backend Error: {resp.status_code}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Overall Risk Score</div>
            <div class='metric-value {risk_class}'>{risk_score:.2f}</div>
            <div class='metric-sub'>{risk_msg}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class='metric-card'>
            <div class='metric-label'>Channel Paths Found</div>
            <div class='metric-value' style='color:#00b4ff'>4</div>
            <div class='metric-sub'>Total length: 3.2 km</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class='metric-card'>
            <div class='metric-label'>At-Risk Area</div>
            <div class='metric-value risk-medium'>20.5 ha</div>
            <div class='metric-sub'>High + medium risk combined</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class='metric-card'>
            <div class='metric-label'>Rainfall Input</div>
            <div class='metric-value' style='color:#e8edf5;font-size:1.2rem'>1,850 mm/yr</div>
            <div class='metric-sub'>Monsoon season · Clay loam soil</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>CHANNEL SPECS</div>", unsafe_allow_html=True)
    st.markdown("""
        <table class='channel-table'>
            <tr>
                <th>ID</th><th>Depth</th><th>Width</th><th>Flow</th>
            </tr>
            <tr><td>CH-001</td><td>0.8 m</td><td>1.2 m</td><td style='color:#00b4ff'>High</td></tr>
            <tr><td>CH-002</td><td>0.5 m</td><td>0.8 m</td><td style='color:#00b4ff;opacity:0.7'>Med</td></tr>
            <tr><td>CH-003</td><td>0.4 m</td><td>0.6 m</td><td style='color:#00b4ff;opacity:0.5'>Low</td></tr>
            <tr><td>CH-004</td><td>0.9 m</td><td>1.4 m</td><td style='color:#00b4ff'>High</td></tr>
        </table>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>RISK ZONES</div>", unsafe_allow_html=True)
    st.markdown("""
        <table class='channel-table'>
            <tr><th>Zone</th><th>Score</th><th>Area</th></tr>
            <tr><td>RZ-01</td><td style='color:#ff4d4d'>0.87</td><td>12.4 ha</td></tr>
            <tr><td>RZ-02</td><td style='color:#ff4d4d'>0.79</td><td>8.1 ha</td></tr>
            <tr><td>RZ-03</td><td style='color:#f5a623'>0.51</td><td>18.7 ha</td></tr>
            <tr><td>RZ-04</td><td style='color:#f5a623'>0.44</td><td>22.3 ha</td></tr>
            <tr><td>RZ-05</td><td style='color:#00d4aa'>0.21</td><td>31.5 ha</td></tr>
        </table>
    """, unsafe_allow_html=True)
