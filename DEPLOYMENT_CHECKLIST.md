# AIDRoute Deployment - Quick Checklist

> **Quick reference for deploying on Render + Vercel**

---

## ✅ Pre-Deployment Checklist

- [ ] All code committed to GitHub
- [ ] `requirements.txt` includes `gunicorn` and `python-dotenv`
- [ ] `frontend/.env.local` configured (can be empty, will update later)
- [ ] `README.md` updated
- [ ] No secrets in `.env` files (use platform env vars instead)

**Push to GitHub:**
```bash
git add .
git commit -m "chore: prepare for deployment"
git push origin main
```

---

## 🚀 Deploy Backend on Render (5 min)

### Quick Steps

1. **Go to:** https://render.com
2. **Sign up with GitHub** (if needed)
3. **Click:** New → Web Service
4. **Select:** Your AIDROUTE repo
5. **Fill in:**
   - Name: `aidroute-backend`
   - Environment: `Python 3`
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`

6. **Add Env Vars:**
   ```
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   FLASK_DEBUG=false
   GEMINI_MODEL=gemini-1.5-flash
   ```

7. **Click:** Create Web Service
8. **Wait:** 2-3 minutes for deployment
9. **Copy:** Your backend URL (e.g., `https://aidroute-backend.onrender.com`)

✅ **Backend is live!**

---

## 🎨 Deploy Frontend on Vercel (5 min)

### Quick Steps

1. **Go to:** https://vercel.com
2. **Sign up with GitHub** (if needed)
3. **Click:** Add New → Project
4. **Select:** Your AIDROUTE repo
5. **Fill in:**
   - Project Name: `aidroute`
   - Framework: `Next.js`
   - Root Directory: `./frontend`

6. **Add Environment:**
   ```
   NEXT_PUBLIC_API_URL=https://aidroute-backend.onrender.com
   ```
   *(Replace with your actual Render URL)*

7. **Click:** Deploy
8. **Wait:** 2-3 minutes for deployment
9. **Copy:** Your frontend URL (e.g., `https://aidroute.vercel.app`)

✅ **Frontend is live!**

---

## 🔗 Verify Everything Works

### Test Backend

```powershell
# Test API endpoint
curl https://aidroute-backend.onrender.com/optimize-route `
  -Method POST `
  -H "Content-Type: application/json" `
  -Body '{"latitude":28.61,"longitude":77.20,"emergencyType":"medical"}'
```

**Expected:** Returns JSON with routes ✅

### Test Frontend

1. Open: https://aidroute.vercel.app
2. Click: "My Location" (allow geolocation)
3. Click: "Optimize"
4. Should see: Routes, hospital info, AI decision

**Expected:** Dashboard loads and responds ✅

---

## 📋 Your Live URLs

```
Frontend:  https://aidroute.vercel.app
Backend:   https://aidroute-backend.onrender.com
GitHub:    https://github.com/ROHAN-BHUTANI/AIDROUTE-emergency-routing
```

---

## 🎯 Common Issues & Fixes

| Problem | Fix |
|---------|-----|
| Backend 502 error | Restart service in Render dashboard |
| Frontend "Failed to connect" | Update `NEXT_PUBLIC_API_URL` in Vercel env vars |
| Slow first load | Normal on free tier (cold start) |
| Build fails | Check logs in dashboard |

---

## 📤 Share Your Live Demo

**GitHub Issue/Discussion:**
```markdown
✅ AIDRoute is now live!

Try it: https://aidroute.vercel.app

Features:
- Route optimization with AI
- Real-time disaster simulation
- Gemini-powered decisions
- Beautiful interactive map

Backend: https://aidroute-backend.onrender.com
Source: https://github.com/ROHAN-BHUTANI/AIDROUTE-emergency-routing
```

**LinkedIn Post:**
```
🎉 Excited to announce: AIDRoute is LIVE!

A AI-powered emergency routing system that:
✅ Optimizes ambulance routes with NetworkX
✅ Simulates disasters (floods, fires, accidents)
✅ Uses Gemini AI for intelligent decisions
✅ Visualizes routes on interactive maps

Try it: https://aidroute.vercel.app
GitHub: https://github.com/ROHAN-BHUTANI/AIDROUTE-emergency-routing

#AI #EmergencyServices #FullStack
```

---

## 🚨 If Something Goes Wrong

### Check Render Logs
1. https://dashboard.render.com
2. Select your service
3. Click "Logs"
4. See what went wrong

### Check Vercel Logs
1. https://vercel.com/dashboard
2. Click your project
3. Click "Deployments"
4. See build logs

### Redeploy
- **Render:** Settings → Manual Deploy → Deploy Latest Commit
- **Vercel:** Deployments → Select deployment → Redeploy

---

## 💡 Tips

✅ **Keep free tier active:** Visit backend URL weekly (prevents spin-down)
✅ **Auto-redeploy:** Enable on Render (Settings) for auto-deploy on git push
✅ **Monitor:** Set alerts in dashboard for errors
✅ **Backup:** Keep backup in GitHub (already done!)

---

## 🎊 Final Checklist

- [ ] Backend deployed on Render
- [ ] Frontend deployed on Vercel
- [ ] Environment variables set correctly
- [ ] Backend responding (GET 200)
- [ ] Frontend loads (GET 200)
- [ ] Geolocation + Optimize works
- [ ] Disaster simulation works
- [ ] GitHub README updated with live URLs
- [ ] Shared with team/portfolio

---

## 📞 Support

- **Full Guide:** See `DEPLOYMENT_DETAILED.md`
- **Quick Start:** See `QUICK_START.md`
- **Local Testing:** See `READY_TO_RUN.md`

---

**Deployment Status: ✅ READY**

Deploy now and share your live project! 🚀
