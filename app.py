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

# Initialize global Defaults
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
        }
    ]
}

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = {
        "risk_score": 0.71,
        "flow_paths": WATER_CHANNELS,
        "risk_msg": "High",
        "risk_class": "risk-high"
    }

# Variables for the UI
risk_score = st.session_state.analysis_result["risk_score"]
risk_msg = st.session_state.analysis_result["risk_msg"]
risk_class = st.session_state.analysis_result["risk_class"]
current_flow = st.session_state.analysis_result["flow_paths"]

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

# Variables are now initialized at the top

# ── Pydeck Layers ──────────────────────────────────────────────────────────────
def make_layers(risk_data=RISK_ZONES, flow_data=WATER_CHANNELS):
    risk_layer = pdk.Layer(
        "GeoJsonLayer",
        data=risk_data,
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
        data=flow_data,
        pickable=True,
        stroked=True,
        filled=False,
        get_line_color="""
            properties.intensity ? [0, 242, 255, 200] :
            properties.flow_vol === 'high'   ? [0, 180, 255, 255] :
            properties.flow_vol === 'medium' ? [0, 140, 210, 220] :
                                               [0, 110, 180, 180]
        """,
        get_line_width="""properties.intensity ? (properties.intensity * 40) : (properties.flow_vol === 'high' ? 60 : properties.flow_vol === 'medium' ? 40 : 25)""",
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

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div class='hero-title'>Terra<span>Sight</span></div>", unsafe_allow_html=True)
    lat = st.number_input("Latitude", value=21.710, format="%.4f")
    lon = st.number_input("Longitude", value=104.878, format="%.4f")
    radius_km = st.selectbox("Analysis Radius", ["5 km"], index=0)
    rainfall_mm = st.slider("Rainfall (mm)", 800, 3000, 1850)
    soil = st.selectbox("Soil", ["Clay Loam"])
    analyze = st.button("▶ Run Analysis")

# ── Main Content ───────────────────────────────────────────────────────────────
if analyze:
    with st.spinner("🔄 Running Deep Terrain Analysis..."):
        try:
            payload = {"latitude": lat, "longitude": lon, "radius": 5.0, "rainfall_mm": float(rainfall_mm), "soil_type": soil}
            # Increased timeout for terrain extraction
            resp = requests.post("http://localhost:8000/v1/analyze", json=payload, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                res = {
                    "risk_score": data.get("risk_score", 0.71),
                    "flow_paths": data.get("flow_paths") if data.get("flow_paths") else WATER_CHANNELS,
                }
                res["risk_msg"] = "High" if res["risk_score"] > 0.7 else "Medium" if res["risk_score"] > 0.4 else "Low"
                res["risk_class"] = "risk-high" if res["risk_score"] > 0.7 else "risk-medium" if res["risk_score"] > 0.4 else "risk-low"
                
                st.session_state.analysis_result = res
                # Update local loop variables
                risk_score = res["risk_score"]
                risk_msg = res["risk_msg"]
                risk_class = res["risk_class"]
                current_flow = res["flow_paths"]
            else:
                st.error(f"Backend Error: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("🚀 BACKEND DOWN: Please start the FastAPI server on port 8000.")
        except Exception as e:
            st.error(f"Error: {e}")

col_map, col_stats = st.columns([3, 1])

with col_map:
    deck = pdk.Deck(
        layers=make_layers(flow_data=current_flow),
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=12.5,
            pitch=35,
            bearing=-10,
        )
    )
    st.pydeck_chart(deck, use_container_width=True)

with col_stats:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>Risk Score</div><div class='metric-value {risk_class}'>{risk_score:.2f}</div><div class='metric-sub'>{risk_msg}</div></div>", unsafe_allow_html=True)
