# 🚀 Deploying TerraSight to Railway

Deploying this FastAPI backend to **Railway.app** is incredibly simple and takes less than 3 minutes.

Since we have already provided the `railway.json` and a frozen `requirements.txt`, Railway will automatically figure out how to build the Python environment.

## Step 1: Connect your GitHub
1. Go to [railway.app](https://railway.app/) and sign in with GitHub.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your `landslideAPI` (or `hackillinois_2026`) repository.
4. Select the `main` or `feature/risk-profiler` branch.

## Step 2: Set Environment Variables
It will start deploying immediately and it will **FAIL**. This is expected because `.env` files are ignored by git for security, so we haven't given it your secret API keys yet!

1. Click on the deployed Service block.
2. Go to the **Variables** tab.
3. Add the keys from your local `.env` file one by one:
```text
GEE_PROJECT_ID=hydroproject-488807
OPENWEATHER_API_KEY=yourkey
```
*(Add SUPABASE keys if they are currently being used)*

## Step 3: Wait 60 Seconds
Once you enter the variables, Railway will automatically trigger a new deployment. 

1. Go to the **Settings** tab.
2. Scroll down to **Networking** -> **Public Networking**.
3. Click "Generate Domain".

That URL is your new live endpoint!

---

## ⚡ Connecting the Live API to your Frontend
Once you have the Railway URL (e.g., `https://terrasight-production.up.railway.app`), open your React frontend (`frontend/src/App.tsx`).

Replace this code:
```javascript
const response = await fetch('http://localhost:8000/v1/analyze', { ...
```

With your new live URL:
```javascript
const response = await fetch('https://YOUR_RAILWAY_URL.up.railway.app/v1/analyze', { ...
```

**Congrats! Your backend is now live on the internet and accessible anywhere. 🎉**
