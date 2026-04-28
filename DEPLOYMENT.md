# 🚀 AIDROUTE Deployment Guide

Complete steps to deploy the backend on **Render** and frontend on **Vercel**.

---

## 📋 Pre-Deployment Checklist

- [ ] GitHub repository created and code pushed
- [ ] `requirements.txt` contains all backend dependencies
- [ ] `.env.example` files created
- [ ] `render.yaml` and `vercel.json` in repository root
- [ ] Gemini API key obtained (optional but recommended)
- [ ] Vercel account created
- [ ] Render account created

---

## 🔧 PART 1: Backend Deployment (Render)

### Step 1: Prepare Backend for Deployment

1. **Verify `requirements.txt` contains gunicorn**:
   ```bash
   cat requirements.txt
   # Should include: gunicorn
   ```

2. **Verify `render.yaml` exists in project root**:
   ```bash
   ls -la render.yaml
   ```

3. **Create `.env` locally (for testing)**:
   ```bash
   cp .env.example .env
   ```

4. **Fill in sensitive variables** (optional):
   - `GEMINI_API_KEY` from https://aistudio.google.com/apikey
   - `OPENROUTER_API_KEY` from https://openrouter.ai

### Step 2: Push Code to GitHub

```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### Step 3: Create Render Web Service

1. Go to **https://render.com** → Sign in (create account if needed)
2. Click **New +** → **Web Service**
3. **Connect GitHub**:
   - Click **GitHub** to authorize
   - Select your AIDROUTE repository
   - Click **Connect**

### Step 4: Configure Render Service

On the deployment screen, set:

| Field | Value |
|-------|-------|
| **Name** | `aidroute-backend` |
| **Environment** | Python |
| **Region** | Choose closest to you (us-east-1, eu-west-1, etc.) |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| **Plan** | Free (or Starter if you need uptime) |

### Step 5: Add Environment Variables

In Render Dashboard **Settings** → **Environment**:

```
FLASK_HOST=0.0.0.0
FLASK_DEBUG=false
PYTHON_VERSION=3.11
GEMINI_API_KEY=your_actual_key_here (mark as Secret)
OPENROUTER_API_KEY=your_key_here (mark as Secret)
```

### Step 6: Deploy

1. Click **Deploy**
2. Monitor in the **Logs** tab
3. Wait for "Service is live" message
4. **Copy your backend URL**: `https://aidroute-backend.onrender.com` (example)

### Step 7: Verify Backend is Live

```bash
curl https://aidroute-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "success",
  "data": {
    "service": "ai-emergency-response-optimizer",
    "ok": true
  }
}
```

✅ **Backend is live!** Save this URL for the frontend.

---

## 🎨 PART 2: Frontend Deployment (Vercel)

### Step 1: Prepare Frontend Configuration

1. **Create `.env.local` for local development**:
   ```bash
   cd frontend
   cp ../.env.example .env.local
   ```

2. **Update `.env.local` with your Render backend URL**:
   ```env
   NEXT_PUBLIC_API_URL=https://aidroute-backend.onrender.com
   ```

3. **Test locally**:
   ```bash
   npm run dev
   # Open http://localhost:3000
   ```

4. **Verify map loads and API works**:
   - Enter lat/lon coordinates
   - Click "Optimize Route"
   - Check network tab for successful API calls to your backend

### Step 2: Push Code to GitHub

```bash
cd ..
git add frontend/.env.local
git commit -m "Update frontend with backend URL"
git push origin main
```

### Step 3: Create Vercel Project

1. Go to **https://vercel.com** → Sign in (create account if needed)
2. Click **Add New** → **Project**
3. **Import Repository**:
   - Click **Import Git Repository**
   - Select your AIDROUTE repository
   - Click **Import**

### Step 4: Configure Vercel Project

On the **Configure Project** screen:

| Field | Value |
|-------|-------|
| **Framework Preset** | Next.js ✓ (auto-detected) |
| **Project Name** | `aidroute-frontend` |
| **Root Directory** | `frontend/` ⚠️ **IMPORTANT** |
| **Build Command** | `npm run build` |
| **Install Command** | `npm install` |

### Step 5: Add Environment Variables

**BEFORE clicking Deploy**, add:

1. Click **Environment Variables** (or skip and add after)
2. Add variable:
   ```
   Name: NEXT_PUBLIC_API_URL
   Value: https://aidroute-backend.onrender.com
   Environments: All (Production, Preview, Development)
   ```

### Step 6: Deploy

1. Click **Deploy**
2. Wait for build to complete (~2-3 minutes)
3. **Copy frontend URL**: `https://aidroute-frontend.vercel.app` (example)

### Step 7: Test Frontend is Live

1. Open your Vercel frontend URL
2. Verify:
   - [ ] Input form loads
   - [ ] Map displays
   - [ ] No CORS errors in browser console
   - [ ] Can submit route optimization
   - [ ] Results display with AI recommendations

✅ **Frontend is live!**

---

## 🔗 PART 3: Verify API Connection

### Test in Browser Console

```javascript
fetch('https://aidroute-backend.onrender.com/health')
  .then(r => r.json())
  .then(d => console.log('Backend:', d))
```

### Test Route Optimization

```javascript
fetch('https://aidroute-backend.onrender.com/optimize-route', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    latitude: 28.61,
    longitude: 77.20,
    emergency_type: 'medical',
    risk_factor: 1.0,
    map_provider: 'osrm'
  })
})
.then(r => r.json())
.then(d => console.log('Route:', d))
```

### If API Calls Fail

**Problem**: CORS error or connection refused

**Solution**:
1. Verify `NEXT_PUBLIC_API_URL` in Vercel dashboard is correct
2. Re-deploy Vercel if env var was just updated:
   - Vercel Dashboard → **Deployments** → **Redeploy** (latest)
3. Check Render backend logs for errors
4. Verify backend URL is correct: `curl https://aidroute-backend.onrender.com/health`

---

## 🔐 Security Configuration

### 1. Update CORS in Backend (Optional)

Edit `app.py` line ~40:

```python
# Current (allows all origins):
CORS(app)

# Restricted (production):
CORS(app, resources={
    r"/*": {
        "origins": ["https://aidroute-frontend.vercel.app"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
```

Then re-deploy Render.

### 2. Environment Variables Best Practices

- ✅ `.env.example` is committed to Git
- ✅ `.env` and `.env.local` are in `.gitignore`
- ✅ Sensitive keys (GEMINI_API_KEY) stored only in Render/Vercel dashboards
- ✅ Use Render "Secrets" for API keys (not plain env vars)

### 3. HTTPS & Security

- ✅ Both Render and Vercel provide HTTPS by default
- ✅ Certificates auto-renewed
- ✅ No need for additional SSL setup

---

## 📊 Monitoring & Troubleshooting

### Check Render Backend Logs

1. Go to Render Dashboard → **aidroute-backend** service
2. Click **Logs** tab
3. Look for errors during startup or requests

### Check Vercel Frontend Logs

1. Go to Vercel Dashboard → **aidroute-frontend** project
2. Click **Deployments** tab
3. Click your latest deployment → **Logs**

### Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| 502 Bad Gateway | Backend crashed | Check Render logs; verify start command |
| API connection timeout | Render sleeping (free tier) | Upgrade to Starter tier or keep project active |
| CORS error in console | Wrong origin or missing var | Verify NEXT_PUBLIC_API_URL env var |
| Blank map | Leaflet import error | Check browser console; restart Vercel deployment |
| No AI recommendations | GEMINI_API_KEY not set | Add key to Render dashboard; re-deploy |
| Long cold start | First request to free tier | Normal; upgrade for better performance |

### View Network Requests

In browser DevTools (**F12**) → **Network** tab:
1. Submit a route optimization
2. Look for POST to `/optimize-route`
3. Check response status and data
4. Look for CORS errors if failing

---

## 🚀 Post-Deployment

### Monitor Application Health

1. **Render Dashboard**:
   - **Settings** → **Alerts** to get notified of crashes
   - **Metrics** tab to see CPU/memory usage

2. **Vercel Dashboard**:
   - **Analytics** tab to see traffic
   - **Deployments** for build history

3. **Test Daily**:
   ```bash
   curl https://aidroute-backend.onrender.com/health
   ```

### Scale Resources (if needed)

**Backend (Render)**:
- Render Dashboard → **aidroute-backend** → **Settings** → **Plan**
- Upgrade from Free ($0) to Starter ($7/month) for always-on performance

**Frontend (Vercel)**:
- Vercel Dashboard → **Settings** → **Plan**
- Pro plan ($20/month) for priority support and faster builds

### Update Backend URL on Frontend

If you change your Render URL:

1. Render Dashboard → **Settings** → **Custom Domain** (if purchased)
2. Or use the new Render URL
3. Update in Vercel:
   - Vercel Dashboard → **aidroute-frontend** → **Settings** → **Environment Variables**
   - Update `NEXT_PUBLIC_API_URL`
   - **Save**
   - Go to **Deployments** → **Redeploy**

---

## ✅ Final Checklist

- [ ] Backend deployed on Render and `/health` responds
- [ ] Frontend deployed on Vercel with correct `NEXT_PUBLIC_API_URL`
- [ ] Can submit route optimization from frontend
- [ ] Map renders and shows routes
- [ ] AI recommendations appear (if Gemini key configured)
- [ ] No CORS errors in browser console
- [ ] Both services are monitoring for errors
- [ ] Environment variables are NOT hardcoded in code

---

## 📞 Support Links

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Next.js Docs**: https://nextjs.org/docs
- **Flask Docs**: https://flask.palletsprojects.com
- **Gemini API**: https://ai.google.dev

**Your AIDROUTE application is now live! 🎉**

