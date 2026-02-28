# 🌍 TerraSight | Irrigation Intelligence

**TerraSight** is an AI-powered decision support tool designed for agricultural NGOs and landowners. It provides real-time landslide risk assessment and terrain intelligence to optimize irrigation and safety in high-risk regions.

---

## 📍 Current Project Status
**Stage: Integrated Prototype (MVP)**

We have moved beyond a simple ML model to a fully integrated full-stack application. The data flows seamlessly from user input to AI prediction and back to the visual dashboard.

| Component | Status | Details |
| :--- | :--- | :--- |
| **Brain (ML)** | ✅ **Active** | Scikit-learn model trained on NASA Global Landslide Catalog data. |
| **Backend (API)** | ✅ **Active** | FastAPI server providing specialized `/v1/analyze` endpoints. |
| **Frontend (UI)** | ✅ **Active** | Dual-UI approach: Interactive Streamlit Dashboard & Custom Leaflet Map. |
| **Connectivity** | ✅ **Active** | Real-time connection between UI sliders/inputs and ML predictions. |

---

## 🎨 Choose Your Interface

We currently maintain two frontend experiences on the `dev` branch:

1.  **Streamlit Dashboard (`app.py`)**: A rapid-prototyping environment featuring 3D pydeck map visualizations and statistical summaries. Best for deep-dive analysis.
2.  **Leaflet Web UI (`index.html`)**: A lightweight, high-performance satellite-view interface using Leaflet.js. Ideal for low-bandwidth field use.

---

## 🚀 Getting Started

### 1. Environment Setup
Ensure you have the latest dependencies installed in your virtual environment:
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Start the Backend API
The FastAPI server must be running for either UI to function:
```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
*Verify at: [http://localhost:8000/v1/health](http://localhost:8000/v1/health)*

### 3. Start the UI
*   **For Streamlit**:
    ```powershell
    .\venv\Scripts\python.exe -m streamlit run app.py
    ```
*   **For Leaflet**: Simply open `index.html` in your browser.

---

## 🛠️ Recent Updates (`dev` branch)
- **Full-Stack Integration**: Connected the UI sliders directly to the ML `predict()` module.
- **CORS Support**: Added security middleware to Allow the browser-based UI to communicate with the local API.
- **Dynamic Risk Scaling**: UI metrics now automatically transition colors (Green → Amber → Red) based on probability scores.
- **Validation Suite**: Added `smoke_test.py` and `test_ml.py` for automated health checks.

---

## 🗺️ Roadmap: What's Next?

### 🌟 Phase 1: Dynamic Visualizations
- [ ] **Heatmap Generation**: Replace static map polygons with dynamic risk heatmaps based on the selected analysis radius.
- [ ] **Topography Layers**: Add elevation and slope gradient overlays.

### 🧪 Phase 2: Feature Expansion
- [ ] **Environmental Feedback**: Integrate `Rainfall` and `Soil Type` sliders directly into the ML model feature vector.
- [ ] **Live Weather**: Connect to OpenWeatherMap API to auto-fill rainfall data based on GPS.

### 🌐 Phase 3: Deployment
- [ ] **Cloud Hosting**: Deploy to Streamlit Cloud or AWS/GCP for public access.
- [ ] **Mobile Optimization**: Progressive Web App (PWA) support for offline usage in remote areas.

---

## 👥 Contributors
- **HackIllinois 2026 Team**
- Built with ❤️ for terrain safety and sustainable agriculture.
