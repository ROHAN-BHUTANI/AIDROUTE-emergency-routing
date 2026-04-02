# 🚑 AIDROUTE - AI Emergency Response Optimizer

**SaaS-Grade Emergency Route Optimization with Real-Time Risk Assessment**

[![Next.js](https://img.shields.io/badge/Next.js-16.2-black)](https://nextjs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9-green)](https://leafletjs.com/)

## 🎯 Problem Statement

Emergency response systems are slowed by:
- **Traffic Congestion** - Ambulances stuck in gridlock
- **Inefficient Routing** - Using pre-planned routes instead of optimized ones
- **Risk Assessment** - No real-time analysis of route safety factors
- **Manual Coordination** - Operators spending time on routing instead of dispatch

**Result**: Precious minutes wasted, lives at risk, emergency response delayed.

## ✅ Our Solution

**AIDROUTE** uses AI-powered algorithms to:

1. **Find Optimal Routes** - Dijkstra algorithm for fastest and safest paths
2. **Assess Risk in Real-Time** - 0.6×traffic + 0.4×accident formula
3. **Auto-Detect Hospitals** - Haversine distance to nearest facility
4. **Provide AI Recommendations** - Context-aware dispatch suggestions
5. **One-Click Geolocation** - Browser geolocation for instant coordinates

## 🏗️ Architecture

### Frontend (Next.js 16 + Tailwind + Radix UI)
```
┌─────────────────────────────────────────────┐
│         AIDROUTE Dashboard (SaaS)           │
├─────────────────────────────────────────────┤
│ Input Card    │  Map Section (Leaflet)      │
│ + Geolocation │  + Route Visualization      │
├─────────────────────────────────────────────┤
│ Analytics Cards (Real-time metrics)        │
│ Route Comparison (Fastest vs Safest)       │
└─────────────────────────────────────────────┘
           ↓
    [API Client - Sonner Toasts]
           ↓
```

### Backend (Flask + Python)
```
┌──────────────┐
│ /optimize-route (POST)
├──────────────┤
│ Route Finder │ ← Dijkstra Algorithm
│ Risk Model   │ ← Traffic + Accident Probability
│ Hospital DB  │ ← Haversine Distance
└──────────────┘
       ↓
   Returns: {
     hospital: { name, distance, coords },
     routes: [{
       type: "fastest|safest",
       path: [[lat, lon], ...],
       distance: km,
       eta: minutes,
       risk_score: 0-10,
       risk_level: "low|medium|high",
       recommendation: "AI-powered text"
     }]
   }
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- npm/pip package managers

### Environment Configuration
- Copy `.env.example` to `.env` if you want to override the Flask host, port, or debug mode.
- Copy `frontend/.env.example` to `frontend/.env.local` to point the dashboard at a non-default API URL.
- The frontend defaults to `http://localhost:5000` when `NEXT_PUBLIC_API_URL` is not set.

### 1️⃣ Backend Setup
```bash
pip install -r requirements.txt
python app.py  # Runs on http://localhost:5000
```

### 2️⃣ Frontend Setup
```bash
cd frontend
npm install
npm run dev     # Runs on http://localhost:3000
```

### 3️⃣ Open Dashboard
Visit `http://localhost:3000` in your browser

## 📋 Project Structure

```
AIDROUTE/
├── Backend (Flask)
│   ├── app.py                    # Main Flask app
│   ├── routing.py                # Dijkstra algorithm
│   ├── risk_model.py             # Risk assessment engine
│   ├── bayesian_risk.py          # Advanced risk modeling
│   ├── data_processing.py        # Data utilities
│   ├── utils.py                  # Helper functions
│   ├── requirements.txt
│   ├── roads.csv                 # Road network data
│   ├── data/                     # Hospital/location data
│   └── cache/                    # Route caching
│
└── Frontend (Next.js)
    ├── app/
    │   ├── page.tsx              # Main dashboard ✨ INTEGRATED
    │   ├── layout.tsx
    │   └── globals.css
    ├── components/dashboard/
    │   ├── input-card.tsx        # ✨ With geolocation
    │   ├── map-component.tsx     # ✨ NEW - Leaflet map
    │   ├── map-section.tsx       # ✨ Updated with real data
    │   ├── analytics-cards.tsx   # ✨ Real metrics
    │   ├── route-comparison.tsx  # ✨ Interactive switcher
    │   └── sidebar.tsx
    ├── lib/
    │   ├── api.ts                # ✨ NEW - Backend client
    │   └── utils.ts
    ├── .env.local                # ✨ NEW - Config
    ├── package.json              # ✨ Updated dependencies
    └── INTEGRATION_GUIDE.md       # ✨ Full documentation
```

## 🎨 Features

### 🗺️ Dual Route Optimization
- **Fastest Route** - Minimizes travel time
- **Safest Route** - Prioritizes risk safety
- Interactive Leaflet map with polylines
- Risk zones visualized with circles

### 📊 Real-Time Analytics
- **ETA** - Estimated time of arrival
- **Distance** - Total route length in km
- **Risk Level** - Low/Medium/High classification
- **Risk Score** - Numerical 0-10 rating
- **Hospital Info** - Destination details
- **AI Recommendation** - Smart dispatch suggestions

### 📍 Geolocation Integration
- One-click "Use My Location" button
- High-accuracy browser geolocation API
- Auto-fill coordinates
- Automatic route optimization

### 🎯 Emergency Type Support
- Medical Emergency
- Fire Emergency
- Traffic Accident
- Flood Emergency
- Earthquake
- Landslide

### 🔐 Error Handling
- Input validation (lat/lon ranges, emergency types)
- Geolocation error messages
- Network error recovery
- Toast notifications for user feedback

## 📊 API Endpoints

### POST /optimize-route
**Request:**
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "emergency_type": "medical"
}
```

**Response:**
```json
{
  "hospital": {
    "name": "City Medical Center",
    "latitude": 28.6245,
    "longitude": 77.2064,
    "distance_km": 1.2
  },
  "routes": [
    {
      "type": "fastest",
      "path": [[28.6139, 77.2090], ...],
      "distance": 2.5,
      "eta": 8,
      "risk_score": 6.2,
      "risk_level": "medium",
      "recommendation": "..."
    },
    {
      "type": "safest",
      "path": [[28.6139, 77.2090], ...],
      "distance": 3.1,
      "eta": 11,
      "risk_score": 3.5,
      "risk_level": "low",
      "recommendation": "..."
    }
  ],
  "status": "success"
}
```

## 💡 Algorithm Details

### Route Finding: Dijkstra Algorithm
- Graph-based shortest path computation
- Programmable risk factor (0.0 = distance-only, 2.2 = risk-heavy)
- Guaranteed optimal solution

### Risk Assessment Formula
```
risk_score = 0.6 × traffic_density + 0.4 × accident_probability

Risk Levels:
- Low: 0-3.99
- Medium: 4-6.99
- High: 7-10
```

### Hospital Detection: Haversine Distance
- Great-circle distance calculation
- Finds nearest hospital from database
- Distance-based ranking

## 🎨 UI/UX Design

### Modern SaaS Dashboard
- Dark theme with gradient accents (blue to green)
- Responsive grid layout (mobile/tablet/desktop)
- Smooth animations and transitions
- Professional typography (Poppins font)
- Radix UI components for accessibility

### Color System
- **Primary**: #2563eb (Blue)
- **Success**: #10b981 (Green)
- **Warning**: #f59e0b (Amber)
- **Danger**: #dc2626 (Red)

## 🔧 Tech Stack

### Frontend
- **Framework**: Next.js 16 (React 19)
- **Styling**: Tailwind CSS 4.2
- **UI Components**: Radix UI, Lucide Icons
- **Mapping**: Leaflet 1.9.4
- **Forms**: React Hook Form
- **Notifications**: Sonner
- **Language**: TypeScript 5.7

### Backend
- **Framework**: Flask 3.1
- **Algorithms**: NetworkX 3.6, Pandas 3.0
- **Geospatial**: Haversine formula (built-in)
- **Environment**: Python 3.11+
- **CORS**: Flask-CORS 6.0

## 📦 Installation

### Backend Dependencies
```bash
pip install -r requirements.txt
```

**Key packages:**
- flask==3.1.3
- flask-cors==6.0.2
- pandas==3.0.2
- networkx==3.6.1

### Frontend Dependencies
```bash
cd frontend && npm install
```

**Key packages:**
- next@16.2.0
- react@19
- tailwindcss@4.2.0
- leaflet@1.9.4
- sonner@1.7.1

## 🚀 Deployment

### Backend (Flask)
```bash
# Local
python app.py

# Production (Heroku/AWS/GCP)
gunicorn app:app
```

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
```

**Environment Variables:**
```env
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

## 📚 Documentation

- **[FRONTEND_QUICKSTART.md](FRONTEND_QUICKSTART.md)** - 3-step setup guide
- **[frontend/INTEGRATION_GUIDE.md](frontend/INTEGRATION_GUIDE.md)** - Detailed integration docs

## 🔒 Security

- Input validation on all endpoints
- Coordinate range checking (-90/90 lat, -180/180 lon)
- Emergency type whitelist
- CORS enabled for web clients
- Error messages without sensitive data

## 📈 Performance

- **Map**: Lazy-loaded client-side
- **Routes**: < 100ms computation
- **API**: < 500ms response time
- **Frontend**: Optimized React renders

## 🐛 Known Limitations

- Real-time traffic data not integrated (use mock)
- Simulated accident probability (replace with real data)
- Single hospital database (extensible)
- Limited to demonstrated routes

## 🔮 Future Enhancements

- [ ] Real-time traffic API integration (Google Maps, HERE)
- [ ] WebSocket for live updates
- [ ] Multi-hospital routing options
- [ ] Ambulance fleet tracking
- [ ] Dispatch history analytics
- [ ] Mobile app (React Native)
- [ ] ML-powered risk prediction
- [ ] Alternative language support

## 🤝 Contributing

Contributors welcome! Areas to enhance:
- Real traffic data integration
- Machine learning models
- Database optimization
- Mobile app development
- Additional emergency types

## 📄 License

MIT License - Feel free to use for teaching, commercial, or personal projects.

## 👥 Authors

Built for **emergency response optimization** and **SaaS hackathon demonstrations**.

---

**🚑 Save Time. Save Lives. Optimize Routes. 🚑**

*AIDROUTE - AI Emergency Response Optimizer*
```

3. Open the app in your browser:

```text
http://localhost:5000
```

## Impact
This system helps reduce emergency response time by combining routing optimization with risk-aware decision-making, ultimately helping save lives.
