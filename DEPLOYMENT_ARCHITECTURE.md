# AIDRoute Deployment Architecture

> **Visual guide showing how AIDRoute is deployed across Render and Vercel**

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET USERS                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    https (port 443)
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
┌────────────────────────┐         ┌────────────────────────┐
│  VERCEL (Frontend)     │         │  GITHUB REPOSITORY     │
│  aidroute.vercel.app   │         │  ROHAN-BHUTANI/        │
├────────────────────────┤         │  AIDROUTE              │
│ Next.js React App      │         ├────────────────────────┤
│ TypeScript             │         │ - Source code          │
│ Tailwind CSS           │         │ - Docker configs       │
│ Leaflet Maps           │         │ - CI/CD triggers       │
├────────────────────────┤         └────────────────────────┘
│ Environment:           │                  ▲
│ NEXT_PUBLIC_API_URL    │                  │
│ = render-backend URL   │         Watches for push
└──────────┬─────────────┘                  │
           │                          git push origin main
           │
           │ API calls (HTTP POST)
           │ /optimize-route
           │ /simulate-disaster
           │
           ▼
┌────────────────────────┐
│  RENDER (Backend)      │
│ aidroute-backend       │
│ .onrender.com          │
├────────────────────────┤
│ Python Flask API       │
│ NetworkX Routing       │
│ Gemini AI Integration  │
├────────────────────────┤
│ Environment:           │
│ FLASK_HOST=0.0.0.0     │
│ FLASK_PORT=5000        │
│ GEMINI_API_KEY=...     │
│ FLASK_DEBUG=false      │
└────────────────────────┘
```

---

## 🚀 Deployment Flow

### Step 1: Push to GitHub
```
Your Machine
    ↓
git push origin main
    ↓
GitHub Repository
```

### Step 2: Render Auto-Deploy (Backend)
```
GitHub Repository (main branch)
    ↓
Webhook trigger
    ↓
Render receives notification
    ↓
Build: pip install -r requirements.txt
    ↓
Start: gunicorn app:app
    ↓
Live at: https://aidroute-backend.onrender.com
```

### Step 3: Vercel Auto-Deploy (Frontend)
```
GitHub Repository (main branch)
    ↓
Webhook trigger
    ↓
Vercel receives notification
    ↓
Build: npm run build (in ./frontend)
    ↓
Deploy: Next.js production build
    ↓
Live at: https://aidroute.vercel.app
```

### Step 4: Runtime Connection
```
User visits: https://aidroute.vercel.app
    ↓
Frontend loads (React + Next.js)
    ↓
User clicks "Optimize"
    ↓
Frontend calls: https://aidroute-backend.onrender.com/optimize-route
    ↓
Backend processes request (Flask + NetworkX)
    ↓
Backend returns: Routes + Hospital + AI Decision
    ↓
Frontend displays: Map + Analytics + Decision Panel
```

---

## 📊 Deployment Locations

### Frontend on Vercel

| Aspect | Details |
|--------|---------|
| **Hosting** | Vercel (US/EU CDN) |
| **Language** | TypeScript + React |
| **Build** | Next.js production build |
| **URL** | https://aidroute.vercel.app |
| **SSL** | ✅ HTTPS (automatic) |
| **Auto-Deploy** | ✅ On every git push |
| **Pricing** | Free tier (unlimited) |

### Backend on Render

| Aspect | Details |
|--------|---------|
| **Hosting** | Render (Frankfurt/Ohio) |
| **Language** | Python + Flask |
| **Server** | Gunicorn WSGI server |
| **URL** | https://aidroute-backend.onrender.com |
| **SSL** | ✅ HTTPS (automatic) |
| **Auto-Deploy** | ✅ Configurable |
| **Pricing** | Free tier ($0, sleeps after 15 min) |

---

## 🔄 Continuous Deployment (CD)

### GitHub → Render → Vercel Pipeline

```
You make changes locally
    ↓
git commit "feat: add new feature"
git push origin main
    ↓
GitHub receives push
    ↓
GitHub Webhooks trigger:
  • Render (backend)
  • Vercel (frontend)
    ↓
Render: Build + Deploy Backend
  → https://aidroute-backend.onrender.com
    ↓
Vercel: Build + Deploy Frontend
  → https://aidroute.vercel.app
    ↓
Both are LIVE (typically within 5 minutes)
```

---

## 📱 How Users Access Your App

### From Browser
```
User opens: https://aidroute.vercel.app
    ↓
Vercel CDN serves: index.html + CSS + JS
    ↓
Browser runs React app
    ↓
React app loads map, UI, buttons
    ↓
User clicks "My Location"
    ↓
Browser asks for geolocation
    ↓
User allows location access
    ↓
React calls backend API
    ↓
Backend processes at: https://aidroute-backend.onrender.com
    ↓
Returns routes + hospital data
    ↓
React displays results on map
```

---

## 🔐 Security Architecture

### Frontend Security (Vercel)
```
✅ HTTPS only (no HTTP)
✅ Content Security Policy
✅ DDoS protection
✅ Automatic SSL renewal
✅ No secrets in frontend code
  (only NEXT_PUBLIC_* variables safe)
```

### Backend Security (Render)
```
✅ HTTPS only (no HTTP)
✅ Environment variables for secrets
✅ No API keys in source code
✅ Automatic firewalls
✅ SSL certificate management
```

### Data Flow Security
```
Frontend (HTTPS)
    ↓
Backend (HTTPS)
    ↓
External APIs (HTTPS)
    • Gemini API (encrypted)
    • OSRM API (encrypted)
    • OpenStreetMap (encrypted)
```

---

## 🎯 Environment Variables

### Render Environment (Backend)

```env
FLASK_HOST=0.0.0.0              # Listen on all interfaces
FLASK_PORT=5000                 # Port (Render provides 5000)
FLASK_DEBUG=false               # Disable debug in production
GEMINI_MODEL=gemini-1.5-flash   # Which model to use
GEMINI_API_KEY=                 # Leave empty for fallback
```

### Vercel Environment (Frontend)

```env
NEXT_PUBLIC_API_URL=https://aidroute-backend.onrender.com
```

⚠️ **Important:** 
- `NEXT_PUBLIC_*` = public (visible in browser)
- Other vars = private (server-side only)

---

## 📊 Monitoring & Logging

### Render Logs
```
https://dashboard.render.com
    → Your Service → Logs
```

Shows:
- Build progress
- Python errors
- API requests
- Startup/shutdown events

### Vercel Logs
```
https://vercel.com/dashboard
    → Your Project → Deployments
```

Shows:
- Build logs
- Next.js build errors
- Edge function logs
- Deployment status

---

## 🔄 Update Process

### Making Changes

1. **Edit code locally**
   ```bash
   # Edit files
   code app.py          # backend
   code frontend/app/page.tsx   # frontend
   ```

2. **Test locally**
   ```bash
   # Terminal 1: Backend
   python app.py
   
   # Terminal 2: Frontend
   cd frontend && npm run dev
   
   # Test at http://localhost:3000
   ```

3. **Commit and push**
   ```bash
   git add .
   git commit -m "fix: your fix message"
   git push origin main
   ```

4. **Automatic deployment**
   - GitHub detects push
   - Render deploys backend (~3 min)
   - Vercel deploys frontend (~3 min)
   - Live immediately after

---

## 🚨 Deployment Issues & Recovery

### Backend Crashed

1. Go to: https://dashboard.render.com
2. Select your service
3. Check "Logs" for error
4. Click "Manual Deploy" → "Deploy Latest Commit"
5. Service restarts

### Frontend Build Failed

1. Go to: https://vercel.com/dashboard
2. Click your project
3. Click "Deployments"
4. View build log
5. Fix error locally
6. Push to GitHub
7. Auto-redeploy

### Rollback to Previous Version

**Vercel:**
1. Deployments tab
2. Select previous deployment
3. Click "Redeploy"

**Render:**
1. Settings
2. Manual Deploy
3. Select previous commit

---

## 💰 Cost Breakdown (Monthly)

### Free Tier
- Render Backend: $0 (sleeps after 15 min)
- Vercel Frontend: $0 (unlimited)
- **Total: $0/month**

### Production Tier
- Render Starter: $7/month (always on, 1GB RAM)
- Vercel Pro: $20/month (advanced features)
- **Total: $27/month**

### Scaling (High Traffic)
- Render Standard: $12/month (2GB RAM)
- Vercel Scale: Custom pricing
- Database: +$5-20/month (if needed)

---

## 📈 Performance Tips

### Speed Up Deployment

1. **Render:** Set auto-redeploy
   - Faster than manual deploy
   
2. **Vercel:** Optimize images
   - Next.js Image optimization enabled
   
3. **Frontend:** Use CDN
   - Vercel uses global CDN ✅
   
4. **Backend:** Keep warm
   - Visit URL weekly to prevent spin-down

---

## 🎓 Learning Resources

- **Render Docs:** https://render.com/docs
- **Vercel Docs:** https://vercel.com/docs
- **Flask Deployment:** https://flask.palletsprojects.com/deployment
- **Next.js Deployment:** https://nextjs.org/docs/deployment

---

## ✅ Production Readiness Checklist

- [ ] All tests pass locally
- [ ] No console errors
- [ ] No API key leaks (use env vars)
- [ ] HTTPS enabled (automatic on both platforms)
- [ ] Environment variables set correctly
- [ ] Backend and frontend URLs match
- [ ] Monitoring/alerts configured (optional)
- [ ] Backup strategy (GitHub is your backup!)

---

## 🎊 You're Deployed!

Your app is now:
- ✅ Live on the internet
- ✅ Accessible from anywhere
- ✅ Automatically deployed on every push
- ✅ Monitored by platform dashboards
- ✅ Protected with HTTPS
- ✅ Ready for demos and portfolio

**Share your live URLs:**
- Frontend: https://aidroute.vercel.app
- Backend: https://aidroute-backend.onrender.com
- GitHub: https://github.com/ROHAN-BHUTANI/AIDROUTE-emergency-routing

---

**Deployment Complete!** 🚀
