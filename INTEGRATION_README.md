# 🛠️ FloodGuard: Full-Stack Integration Update

This update integrates the **UI**, **Backend**, and **Machine Learning Model** into a single, cohesive workflow on the `dev` branch.

## 🚀 Key Updates

### 1. 🧠 ML Model Integration (`main.py`)
- The backend now uses the live `predict()` function from `src/risk_model.py`.
- It automatically loads the `models/risk_model.joblib` artifact into memory.
- Added a robust `/v1/analyze` endpoint that transforms geographic coordinates into ML-ready features.

### 2. 🎨 UI - Backend Connectivity (`app.py`)
- Replaced static "demo" values with real-time API calls to the local FastAPI server.
- The "Overall Risk Score" now reflects the actual ML prediction for the selected Latitude/Longitude.
- Added error handling for connection issues and non-200 API responses.

### 3. 📦 Dependency Management (`requirements.txt`)
- Standardized the environment with required packages: `fastapi`, `uvicorn`, `streamlit`, `pydeck`, `joblib`, `pandas`, `numpy`, and `scikit-learn`.

### 4. 🧪 Validation & Integrity Tools
- **`test_ml.py`**: Directly tests the ML prediction logic against known sample coordinates.
- **`smoke_test.py`**: Performs an end-to-end "heartbeat" check, verifying that the UI/API/ML pipeline is fully functional.

---

## 🚦 How to Run the Integrated Stack

### Step 1: Initialize Environment
```bash
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Step 2: Launch Backend (Terminal A)
```bash
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 3: Launch UI (Terminal B)
```bash
.\venv\Scripts\python.exe -m streamlit run app.py
```

### Step 4: Verify Integration
```bash
.\venv\Scripts\python.exe smoke_test.py
```

---

## ⚠️ Critical Information
- **Port Mapping**: The Backend defaults to port **8000**; the UI defaults to **8501**.
- **Model Path**: The app resolves `models/risk_model.joblib` relative to the project root. Ensure this file is present.
- **Python Path**: The `src` directory is treated as a module; avoid renaming it without updating imports in `main.py`.
