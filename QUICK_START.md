# Quick Start Commands

## 🚀 Ultra-Quick Start (Copy & Paste)

### Windows PowerShell
```powershell
# Clone (if you don't have it)
git clone https://github.com/yourusername/aidroute.git
cd aidroute

# Run everything (backend + frontend)
powershell -ExecutionPolicy Bypass -File RUN_DEMO.ps1

# Open browser
start http://localhost:3000
```

### Or Manual Step-by-Step

**Terminal 1 - Backend:**
```powershell
# From project root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

**Terminal 2 - Frontend:**
```powershell
# From project root
cd frontend
npm install
npm run dev
```

**Then open:** http://localhost:3000

---

## 🧪 Test API Endpoints Directly (PowerShell)

### Optimize Route
```powershell
$body = @{
    latitude = 28.61
    longitude = 77.20
    emergencyType = "medical"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:5000/optimize-route `
  -Method POST `
  -Body $body `
  -ContentType 'application/json'
```

### Simulate Disaster
```powershell
$body = @{
    type = "flood"
    latitude = 28.61
    longitude = 77.20
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:5000/simulate-disaster `
  -Method POST `
  -Body $body `
  -ContentType 'application/json'
```

---

## 📋 Demo Workflow

1. **Start servers** (see above)
2. **Open dashboard** at http://localhost:3000
3. **Click "My Location"** - browser geolocation (allow permission)
4. **Click "Optimize"** - AI calculates emergency route + hospital
5. **Click "Flood"** - simulates disaster, blocks roads
6. **Watch re-route** - AI automatically avoids blocked areas
7. **View AI Decision Panel** - Gemini justifications & recommendations

---

## 🔧 Environment Variables

### Backend (.env)
```
GEMINI_API_KEY=your-api-key-here  # Optional, uses fallback if empty
GEMINI_MODEL=gemini-1.5-flash
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

### Frontend (frontend/.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:5000
```

---

## 📝 Requirements

- **Python**: 3.8+
- **Node.js**: 18+
- **npm**: 9+
- **Browser**: Modern (Chrome, Firefox, Edge, Safari)

---

## 🎯 Feature Checklist

- ✅ Route optimization with NetworkX
- ✅ Disaster simulation (Flood/Fire/Accident)
- ✅ Blocked road detection
- ✅ Hospital context & ETA
- ✅ Gemini AI explanations + fallback
- ✅ Real-time re-routing
- ✅ Loading states & error handling
- ✅ Toast notifications
- ✅ Leaflet map integration
- ✅ Responsive UI

---

## 🐛 Troubleshooting

**Port 5000 already in use:**
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Port 3000 already in use:**
```powershell
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Geolocation not working:**
- Ensure HTTPS or localhost (browser requirement)
- Check browser permissions

**API calls failing:**
- Verify backend running at http://127.0.0.1:5000
- Check .env files configured
- Review NEXT_PUBLIC_API_URL in frontend/.env.local
