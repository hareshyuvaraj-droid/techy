# CrowdGuard EC-9 — Quick Deploy Guide

## RENDER DEPLOY (3-5 min)

### Step 1 — Push to GitHub
Push this entire folder to your GitHub repo.

### Step 2 — Backend on Render
1. Go to render.com → New → Web Service
2. Connect your GitHub repo
3. Settings:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Runtime: Python 3

4. Environment Variables (add these):
   - `MONGO_URL` → your MongoDB Atlas connection string
   - `JWT_SECRET` → any random string e.g. `crowdguard_secret_2024`
   - `DB_NAME` → `crowdguard`
   - `FRONTEND_URL` → your frontend URL (add after frontend is deployed)

### Step 3 — Frontend on Render
1. New → Static Site
2. Root Directory: `frontend`
3. Build Command: `echo done`
4. Publish Directory: `.`

### Step 4 — Connect them
1. Copy your backend URL (e.g. `https://crowdguard-backend.onrender.com`)
2. Open `frontend/index.html`
3. Find this line:
   ```
   : 'https://YOUR-BACKEND.onrender.com';
   ```
4. Replace with your actual backend URL
5. Push to GitHub → Render auto-redeploys frontend

---

## LOCAL (VS Code)

### Backend
```bash
cd backend
pip install -r requirements.txt
# Create .env file:
echo "MONGO_URL=mongodb+srv://..." > .env
echo "JWT_SECRET=any_secret" >> .env
echo "DB_NAME=crowdguard" >> .env
python -m uvicorn main:app --reload
```

### Frontend
Open `frontend/index.html` with Live Server in VS Code.
(The API_URL auto-detects localhost when running locally)
