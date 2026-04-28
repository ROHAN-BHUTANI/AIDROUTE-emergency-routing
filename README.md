# AIDRoute - AI-Powered Emergency Response System

> **Intelligent routing engine for emergency response with real-time disaster simulation and Gemini-powered AI decision making**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green)](https://nodejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🎯 Overview

AIDRoute is an intelligent emergency response system that uses AI to optimize ambulance routing during medical emergencies and disasters. It features real-time disaster simulation, AI-powered decision making with Gemini, and a beautiful React dashboard.

**Key Capabilities:**
- ✅ AI-Powered Route Optimization with risk scoring
- ✅ Disaster Simulation (floods, fires, accidents)
- ✅ Real-Time Decision Engine with Gemini AI
- ✅ Smart Emergency Alerts
- ✅ Responsive Dashboard with Leaflet Maps
- ✅ Hospital Context & ETA Estimation

---

## 🚀 Quick Start (Copy & Paste)

### Windows PowerShell
```powershell
# Clone repo
git clone https://github.com/yourusername/aidroute.git
cd aidroute

# Run everything automatically
powershell -ExecutionPolicy Bypass -File RUN_DEMO.ps1

# Open browser
start http://localhost:3000
```

### Manual Setup (3 steps)

**Step 1: Backend**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

**Step 2: Frontend** (new terminal)
```bash
cd frontend
npm install
npm run dev
```

**Step 3: Open**
- Dashboard: http://localhost:3000
- API: http://127.0.0.1:5000

---

## 📖 Demo Workflow

1. **Open dashboard** → http://localhost:3000
2. **Click "My Location"** → Grant geolocation permission
3. **Click "Optimize"** → AI calculates optimal emergency route
4. **Watch results** → See hospital info, ETA, risk level, AI justifications
5. **Click "Flood"** → Simulate disaster, blocks roads
6. **Watch re-routing** → AI automatically recalculates around blocked roads
7. **View AI Panel** → Gemini insights on why routes were selected

---

## 🏗️ Architecture

```
AIDRoute/
├── Backend (Flask)
│   ├── app.py                    # REST API + decision engine
│   ├── ai_engine.py              # Gemini AI wrapper + fallback
│   ├── routing.py                # NetworkX route optimization
│   └── requirements.txt           # Python dependencies
│
├── Frontend (Next.js)
│   ├── app/page.tsx              # Main dashboard
│   ├── components/               # React UI components
│   ├── lib/api.ts                # API client (typed)
│   └── package.json
│
├── Data & Config
│   ├── data/                     # Locations, hospitals
│   ├── cache/                    # OSRM response cache
│   ├── .env                      # Backend env vars
│   └── frontend/.env.local       # Frontend env vars
│
└── Docs
    ├── README.md                 # This file
    ├── QUICK_START.md            # Copy-paste commands
    ├── DEMO_SCRIPT.md            # Demo walkthrough
    └── DEPLOYMENT.md             # Production guide
```

---

## 📡 API Endpoints

### POST /optimize-route
Calculate optimal emergency route with risk analysis.

```bash
curl -X POST http://127.0.0.1:5000/optimize-route \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.61,
    "longitude": 77.20,
    "emergencyType": "medical"
  }'
```

**Response includes:**
- Hospital info (name, location, distance)
- Multiple route options (fastest, safest)
- Risk scores and explanations
- AI decision with justification

### POST /simulate-disaster
Inject a disaster, block roads, trigger re-routing.

```bash
curl -X POST http://127.0.0.1:5000/simulate-disaster \
  -H "Content-Type: application/json" \
  -d '{
    "type": "flood",
    "latitude": 28.61,
    "longitude": 77.20
  }'
```

**Response includes:**
- Blocked roads (exact coordinates)
- Disaster severity
- Rerouting triggered flag

See [QUICK_START.md](QUICK_START.md) for PowerShell examples.

---

## 💻 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Flask | REST API, decision engine |
| **Routing** | NetworkX | Graph-based pathfinding |
| **AI** | Gemini 1.5 Flash | Decision analysis & explanations |
| **Frontend** | Next.js 16.2 + React 19 | Dashboard UI |
| **Styling** | Tailwind CSS | Responsive design |
| **UI Library** | shadcn/ui | Pre-built components |
| **Maps** | Leaflet + OSM | Route visualization |
| **Language** | TypeScript | Type-safe frontend |
| **Notifications** | Sonner | Toast messages |
| **Deployment** | Render/Vercel | Hosting platforms |

---

## 🧠 AI Features

### Gemini Integration
- **Disaster Analysis**: Assesses severity and impact
- **Route Explanation**: Justifies route selection decisions
- **Resource Recommendations**: Suggests ambulances, staff, equipment
- **Fallback Mode**: Deterministic generator for testing (no API key required)

### Decision Engine
- **Risk Scoring**: Combines distance, traffic, disaster impact
- **Priority Balancing**: Adjusts speed vs. safety based on incident type
- **Hospital Awareness**: Considers proximity and capacity
- **Dynamic Re-routing**: Responds to blocked roads in real-time

---

## 🔧 Configuration

### Backend (.env)
```env
# Optional Gemini API key (leave empty for fallback)
GEMINI_API_KEY=

# Model settings
GEMINI_MODEL=gemini-1.5-flash

# Flask server
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=false
```

### Frontend (frontend/.env.local)
```env
# Backend URL (for dev: localhost, for prod: deployed API)
NEXT_PUBLIC_API_URL=http://localhost:5000
```

---

## 🎮 Features Checklist

- ✅ Route optimization with multiple options
- ✅ Disaster simulation (flood/fire/accident)
- ✅ Blocked road detection
- ✅ Hospital context & distance
- ✅ AI-powered decision making
- ✅ Gemini integration + fallback
- ✅ Smart alerts system
- ✅ Real-time re-routing
- ✅ Loading states
- ✅ Error handling
- ✅ Toast notifications
- ✅ Responsive UI
- ✅ Leaflet map integration
- ✅ TypeScript type safety

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| [QUICK_START.md](QUICK_START.md) | Copy-paste commands & troubleshooting |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Cinematic 2-minute demo walkthrough |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment guide |
| [RUN_DEMO.ps1](RUN_DEMO.ps1) | PowerShell automation script |

---

## 🐛 Troubleshooting

**Port 5000 already in use?**
```powershell
netstat -ano | findstr :5000
taskkill /PID <pid> /F
```

**Port 3000 already in use?**
```powershell
netstat -ano | findstr :3000
taskkill /PID <pid> /F
```

**Geolocation not working?**
- Ensure browser geolocation is enabled
- Works on localhost automatically
- HTTPS required for production

**API calls failing?**
- Check backend running: http://127.0.0.1:5000
- Verify .env files created
- Check NEXT_PUBLIC_API_URL in frontend/.env.local

See [QUICK_START.md](QUICK_START.md) for more solutions.

---

## 📋 Requirements

- Python 3.8+
- Node.js 18+
- npm 9+
- Modern browser (Chrome, Firefox, Edge, Safari)
- For Gemini AI: Optional Google API key

---

## 🚀 Deployment

### Quick Deploy (Render + Vercel)
1. Push to GitHub
2. Connect to Render (backend) → Deploy
3. Connect to Vercel (frontend) → Deploy
4. Set environment variables
5. Done!

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed steps.

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing`
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- Google Gemini API for AI capabilities
- OSRM for routing services
- OpenStreetMap for map data
- shadcn/ui for component library
- Vercel & Render for hosting

---

## 📞 Support

- 📖 Check [QUICK_START.md](QUICK_START.md)
- 🚀 See [DEPLOYMENT.md](DEPLOYMENT.md)
- 🐛 Open a GitHub Issue
- 💬 Review [DEMO_SCRIPT.md](DEMO_SCRIPT.md)

---

**Last Updated**: April 28, 2026  
**Version**: 1.0.0 Production Ready ✅
