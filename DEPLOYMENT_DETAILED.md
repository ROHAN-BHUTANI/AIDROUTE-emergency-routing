# AIDRoute Deployment Guide - Render + Vercel

> **Complete step-by-step guide to deploy AIDRoute backend on Render and frontend on Vercel**

---

## 📋 Prerequisites

✅ GitHub account with your repo pushed  
✅ Render account (https://render.com - sign up with GitHub)  
✅ Vercel account (https://vercel.com - sign up with GitHub)  
✅ Google Gemini API key (optional, for AI features)

---

## 🚀 Part 1: Deploy Backend on Render

### Step 1: Create Render Account & Connect GitHub

1. Go to https://render.com
2. Click **"Sign up"** → Choose **"Continue with GitHub"**
3. Authorize Render to access your GitHub
4. You're now logged in ✅

### Step 2: Create Web Service

1. From dashboard, click **"New +"** → Select **"Web Service"**
2. Click **"Connect a repository"**
3. Search for and select: **"AIDROUTE-emergency-routing"**
4. Click **"Connect"**

### Step 3: Configure Service Settings

Fill in these exact fields:

| Field | Value |
|-------|-------|
| **Name** | `aidroute-backend` |
| **Environment** | `Python 3` |
| **Region** | `Frankfurt (EU Central)` or `Ohio (US East)` |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

**Screenshot reference:**
```
Name:             aidroute-backend
Environment:      Python 3
Region:           Frankfurt
Branch:           main
Build Command:    pip install -r requirements.txt
Start Command:    gunicorn app:app
```

### Step 4: Add Environment Variables

1. Scroll down to **"Environment"**
2. Click **"Add Environment Variable"**
3. Add these variables:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | *(leave empty for fallback)* |
| `GEMINI_MODEL` | `gemini-1.5-flash` |
| `FLASK_HOST` | `0.0.0.0` |
| `FLASK_PORT` | `5000` |
| `FLASK_DEBUG` | `false` |

**Or paste this in Advanced:**
```
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false
```

### Step 5: Deploy

1. Click **"Create Web Service"** (bottom right)
2. Render will build and deploy automatically
3. Wait ~2-3 minutes for build to complete
4. You'll see a URL like: `https://aidroute-backend.onrender.com`

✅ **Copy this URL** - you'll need it for frontend!

### Step 6: Verify Backend is Running

```powershell
# Test your backend
Invoke-RestMethod -Uri https://aidroute-backend.onrender.com/optimize-route `
  -Method POST `
  -Body '{"latitude":28.61,"longitude":77.20,"emergencyType":"medical"}' `
  -ContentType 'application/json'
```

Should return JSON with route data ✅

---

## 🎨 Part 2: Deploy Frontend on Vercel

### Step 1: Go to Vercel

1. Go to https://vercel.com
2. Click **"Sign Up"** → **"Continue with GitHub"**
3. Authorize Vercel
4. You're logged in ✅

### Step 2: Import Project

1. From dashboard, click **"Add New..."** → **"Project"**
2. Click **"Import Git Repository"**
3. Search: **"AIDROUTE-emergency-routing"** (or paste GitHub URL)
4. Click **"Import"**

### Step 3: Configure Project

Fill in these fields:

| Field | Value |
|-------|-------|
| **Project Name** | `aidroute` |
| **Framework Preset** | `Next.js` |
| **Root Directory** | `frontend` |

**Screenshot:**
```
Project Name:    aidroute
Framework:       Next.js
Root Directory:  ./frontend
```

### Step 4: Add Environment Variables

1. Scroll down to **"Environment Variables"**
2. Add this variable:

```
NEXT_PUBLIC_API_URL = https://aidroute-backend.onrender.com
```

⚠️ **Important:** Replace `aidroute-backend` with your actual Render backend name!

**Or individually:**
- Name: `NEXT_PUBLIC_API_URL`
- Value: `https://aidroute-backend.onrender.com`

### Step 5: Deploy

1. Click **"Deploy"** (bottom right)
2. Vercel will build and deploy (~2-3 minutes)
3. You'll see URL like: `https://aidroute.vercel.app`

✅ **Your frontend is live!**

### Step 6: Test Frontend

1. Open https://aidroute.vercel.app in browser
2. Click "My Location" (allow geolocation)
3. Click "Optimize"
4. Should show routes + hospital info ✅

---

## 🔄 Part 3: Link Frontend to Backend

### If Frontend Deployed BEFORE Backend

If Vercel deployed before Render was ready, you need to update the environment variable:

1. Go to Vercel dashboard
2. Select your `aidroute` project
3. Click **"Settings"** → **"Environment Variables"**
4. Find `NEXT_PUBLIC_API_URL`
5. Edit it to your Render backend URL
6. Click **"Save"**
7. Vercel will redeploy automatically ✅

---

## 🌐 Connecting Everything

### Your Live URLs

```
Backend API:     https://aidroute-backend.onrender.com
Frontend App:    https://aidroute.vercel.app
GitHub Repo:     https://github.com/ROHAN-BHUTANI/AIDROUTE-emergency-routing
```

### Full Workflow

```
User opens:
  https://aidroute.vercel.app
    ↓
Clicks "My Location"
    ↓
Frontend calls:
  https://aidroute-backend.onrender.com/optimize-route
    ↓
Backend returns routes + hospital info
    ↓
Frontend displays map + AI decision
```

---

## 🔧 Troubleshooting Deployment

### Backend Not Starting on Render

**Error:** `gunicorn: command not found`

**Solution:** Add `gunicorn` to requirements.txt:
```bash
pip freeze | grep -i gunicorn
# or manually add to requirements.txt:
echo "gunicorn" >> requirements.txt
git add requirements.txt
git commit -m "chore: add gunicorn for production"
git push
```

Then redeploy on Render (Settings → Manual Deploy → Deploy Latest Commit)

### Frontend Shows "Failed to Connect"

**Error:** API calls to backend fail

**Solution:**
1. Check `NEXT_PUBLIC_API_URL` in Vercel environment variables
2. Make sure it matches your Render backend URL exactly
3. Verify backend is running: `curl https://aidroute-backend.onrender.com`
4. Redeploy frontend: Vercel dashboard → Deployments → Redeploy

### 502 Bad Gateway Error

**Cause:** Backend crashed or not responding

**Solution:**
1. Go to Render dashboard
2. Select your service
3. Check "Logs" for errors
4. Click "Manual Deploy" to restart

### Slow First Load (Cold Start)

**Normal on Render free tier** - first request takes 30-60 seconds

**Solution:** Keep backend warm with periodic pings
```powershell
# Test it's working
Invoke-WebRequest -Uri https://aidroute-backend.onrender.com -TimeoutSec 60
```

---

## 📝 Update Your GitHub README

Add this section to your [README.md](README.md):

```markdown
## 🚀 Live Deployment

- **Frontend:** https://aidroute.vercel.app
- **Backend API:** https://aidroute-backend.onrender.com
- **GitHub:** https://github.com/ROHAN-BHUTANI/AIDROUTE-emergency-routing

### Quick Start

Visit https://aidroute.vercel.app and:
1. Click "My Location" to enable geolocation
2. Click "Optimize" to calculate emergency route
3. Click "Flood", "Fire", or "Crash" to simulate disaster
4. Watch AI re-route around blocked roads

No installation needed! 🎉
```

Then commit:
```bash
git add README.md
git commit -m "docs: add live deployment links"
git push
```

---

## 🎯 Optional: Setup Auto-Redeploy

### Render: Auto-Deploy on GitHub Push

1. Go to your Render Web Service
2. Click **"Settings"**
3. Scroll to **"Auto-Deploy"**
4. Select: **"No"** → change to **"Yes"** (redeploy on every push)
5. Save

Now every `git push` redeploys your backend automatically ✅

### Vercel: Auto-Deploy (Already Enabled)

Vercel auto-deploys on every push by default ✅

---

## 💰 Pricing

### Render (Backend)

| Plan | Price | Specs |
|------|-------|-------|
| **Free** | $0 | 0.5 GB RAM, spins down after 15 min inactivity |
| **Starter** | $7/month | 1 GB RAM, always on |
| **Standard** | $12/month | 2 GB RAM, always on |

**For demo:** Free tier works great  
**For production:** Starter ($7/month) recommended

### Vercel (Frontend)

| Plan | Price | Specs |
|------|-------|-------|
| **Free** | $0 | Perfect for Next.js |
| **Pro** | $20/month | Advanced features |
| **Enterprise** | Custom | Team features |

**For demo:** Free tier is unlimited ✅

---

## 📊 Monitor Your Deployments

### Render Dashboard

- Visit https://dashboard.render.com
- Select your service
- View: Logs, Metrics, Events
- Restart or redeploy anytime

### Vercel Dashboard

- Visit https://vercel.com/dashboard
- Select your project
- View: Deployments, Analytics, Logs
- Rollback to previous deployment if needed

---

## 🔐 Security Best Practices

### Render

1. ✅ Keep `.env` files in `.gitignore` (not in repo)
2. ✅ Use Render environment variables for secrets
3. ✅ Never commit `GEMINI_API_KEY` to GitHub
4. ✅ Rotate API keys regularly

### Vercel

1. ✅ Only use `NEXT_PUBLIC_*` for public variables
2. ✅ Use Vercel environment variables for private keys
3. ✅ Don't commit `.env.local` to GitHub
4. ✅ Review deployed URLs in security settings

### Example: Adding Gemini API Key Later

If you have a Gemini API key:

**Render:**
1. Dashboard → Service → Settings → Environment Variables
2. Add: `GEMINI_API_KEY=your-key-here`
3. Manual Deploy to apply

**Vercel:**
1. Dashboard → Project → Settings → Environment Variables
2. This is only for Vercel secrets (not frontend)

---

## ✅ Deployment Checklist

- [ ] Backend deployed on Render
- [ ] Backend URL: `https://aidroute-backend.onrender.com`
- [ ] Frontend deployed on Vercel
- [ ] Frontend URL: `https://aidroute.vercel.app`
- [ ] `NEXT_PUBLIC_API_URL` set to Render backend URL
- [ ] Backend test: API returns 200 response
- [ ] Frontend test: Geolocation + Optimize works
- [ ] Disaster simulation works (Flood/Fire/Crash)
- [ ] README updated with live URLs
- [ ] Auto-redeploy enabled (optional)

---

## 🎬 Final Testing

### Full End-to-End Test

```powershell
# 1. Test backend API
Write-Host "Testing backend..." -ForegroundColor Green
Invoke-RestMethod -Uri https://aidroute-backend.onrender.com/optimize-route `
  -Method POST `
  -Body '{"latitude":28.61,"longitude":77.20,"emergencyType":"medical"}' `
  -ContentType 'application/json' | ConvertTo-Json -Depth 2

# 2. Open frontend in browser
Write-Host "Opening frontend..." -ForegroundColor Green
start https://aidroute.vercel.app

# 3. Manually test:
# - Click "My Location"
# - Click "Optimize" (should see routes)
# - Click "Flood" (should see blocked roads)
# - Watch re-routing (routes should update)
```

---

## 🎉 You're Live!

Your AIDRoute system is now publicly accessible:

- **Try it:** https://aidroute.vercel.app
- **Share link:** https://github.com/ROHAN-BHUTANI/AIDROUTE-emergency-routing
- **See code:** GitHub repository has full source

---

## 🆘 Need Help?

| Issue | Solution |
|-------|----------|
| Backend won't start | Check Render logs for Python errors |
| Frontend shows "Failed" | Verify API URL in Vercel env vars |
| Geolocation not working | Must be HTTPS (Vercel/Render both use HTTPS) ✅ |
| Slow response | Normal on Render free tier (cold start) |
| Want custom domain | See "Custom Domains" in Render/Vercel settings |

---

## 🚀 Next Steps

1. ✅ Deploy backend on Render
2. ✅ Deploy frontend on Vercel
3. ✅ Test everything works
4. ✅ Share with team/portfolio
5. Optional: Add custom domain
6. Optional: Upgrade to paid plans if needed

---

**Deployment Complete!** 🎊

Your AIDRoute project is now live and shareable!

---

**Version**: 1.0.0 | **Last Updated**: April 28, 2026
