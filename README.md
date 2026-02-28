# 🌍 TerraSight | Terrain Intelligence for Agricultural NGOs

**TerraSight** is a high-tech decision support tool designed to optimize field safety and irrigation strategy. It combines machine learning risk prediction with live hydrological terrain analysis.

---

## 📍 Current Project Status
**Stage: Full-Stack Integrated (V2)**

The project is now a complete end-to-end system where the **Brain (ML)**, **Physics (Terrain Engine)**, and **Interface (UIs)** communicate in real-time.

| Component | Status | Details |
| :--- | :--- | :--- |
| **Brain (ML)** | ✅ **Active** | Trained scikit-learn model predicting landslide probabilities. |
| **Terrain Engine**| ✅ **Active** | **NEW:** Real-time NASA DEM ingestion and Whitebox water flow simulations. |
| **Backend (API)** | ✅ **Active** | FastAPI server orchestrating ML and Terrain pipelines. |
| **Streamlit UI**  | ✅ **Active** | Professional 3D dashboard with dynamic layer injection. |
| **Leaflet UI**    | ✅ **Active** | Lightweight satellite map with real-time SVG flow paths. |

---

## 🔑 Important: Terrain Engine Authentication
The **Terrain & Hydrology Engine** uses Google Earth Engine (GEE).
- **Access**: GEE is restricted by Google account permissions.
- **Tanish's Account**: Tanish should ensure he has a `.env` file in the root directory with `GEE_PROJECT_ID="your-project-id"`.
- **How to Run**: Tanish should run the backend because he has the GEE permissions.
- **Fail-Safe**: If the engine cannot authenticate, the system will automatically fallback to providing only the ML Risk Score, ensuring the UI never crashes for other users.

---

## 🚀 Getting Started (Run the Project)

### 1. Environment Sync
Ensure your environment has the new GIS and Physics libraries:
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Start the Backend API (Terminal 1)
```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
*Verify: Once it starts, the ML and Terrain Engine are live.*

### 3. Choose Your UI (Terminal 2)
*   **For the 3D Dashboard (Recommended)**:
    ```powershell
    .\venv\Scripts\python.exe -m streamlit run app.py
    ```
*   **For the Satellite Web Interface**: 
    Simply open **`index.html`** in your browser.

---

## 🛠️ Recent Integration Updates
- **Neural-Physics Fusion**: The `/v1/analyze` endpoint now merges ML risk probabilities with physical water flow pathfinding.
- **Dynamic Layer Injection**: UI maps now "listen" to the API and render sub-pixel flow points in real-time.
- **Robust Session Handling**: Streamlit now uses internal session states to prevent UI threading issues.
- **Async Feedback**: Added visual spinners and loading states while the system pulls live satellite data.

---

## 👥 Contributors
- **HackIllinois 2026 Team**
- Built with ❤️ for sustainable agriculture and community safety.
