# AIDROUTE Frontend - Next.js Integration Guide

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ installed
- Python 3.11+ with Flask backend running

### Installation

```bash
cd frontend
npm install
```

### Configuration

Create/update `frontend/.env.local`:

```env
# Backend API Configuration
NEXT_PUBLIC_API_URL=http://localhost:5000
```

For production, update to your deployed backend URL:

```env
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

### Running the Development Server

```bash
npm run dev
```

Visit `http://localhost:3000` in your browser.

## 📁 Project Structure

```
frontend/
├── app/
│   ├── globals.css           # Global Tailwind styles
│   ├── layout.tsx            # Root layout with metadata
│   └── page.tsx              # Main dashboard page (Nextly integrated!)
├── components/
│   ├── dashboard/
│   │   ├── sidebar.tsx                    # Navigation sidebar
│   │   ├── input-card.tsx                 # Route input with geo location
│   │   ├── map-component.tsx              # Leaflet map component (NEW)
│   │   ├── map-section.tsx                # Map container (updated)
│   │   ├── analytics-cards.tsx            # Real-time metrics (updated)
│   │   ├── route-comparison.tsx           # Route switcher (updated)
│   │   └── theme-provider.tsx             # Dark mode provider
│   └── ui/                               # Radix UI components
├── lib/
│   ├── api.ts                            # Backend API client (NEW)
│   └── utils.ts                          # Utility functions
├── hooks/
├── public/
├── styles/
├── .env.local                            # Environment config (NEW)
├── next.config.mjs
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## 🔄 Integration Points

### 1. **API Service Layer** (`lib/api.ts`)

Centralized HTTP client for backend communication:

- `optimizeRoute(lat, lon, emergencyType)` - Main endpoint
- `predictRisk(lat, lon)` - Risk assessment
- `getNearestHospital(lat, lon)` - Hospital lookup

```typescript
import { optimizeRoute } from '@/lib/api'

const response = await optimizeRoute(28.6139, 77.2090, 'medical')
// Returns: { hospital, routes: [...] }
```

### 2. **Main Dashboard** (`app/page.tsx`)

Connected Features:
- ✅ Real API calls (no mock data)
- ✅ Geolocation button integration
- ✅ Error handling with toast notifications
- ✅ Loading states with spinners
- ✅ Real-time route display

### 3. **Components Updated**

| Component | Changes |
|-----------|---------|
| `input-card.tsx` | Added "My Location" button, validation |
| `map-section.tsx` | Integrated Leaflet mapping with real data |
| `analytics-cards.tsx` | Real metrics (ETA, distance, risk) |
| `route-comparison.tsx` | Interactive fastest/safest switcher |

### 4. **Leaflet Map** (`components/dashboard/map-component.tsx`)

Features:
- Real-time route visualization
- Hospital destination marker (red)
- Start point marker (blue)
- Risk zone circles with risk-based coloring
- Auto-fit bounds on route load
- Dark theme CartoDB basemap

## 🌍 Geolocation Features

### How It Works

1. User clicks "My Location" button
2. Browser requests permission
3. GPS coordinates auto-fill form
4. Backend route optimization triggered
5. Results displayed in real-time

### Browser Support

- ✅ Chrome/Chromium (90+)
- ✅ Firefox (88+)
- ✅ Safari (13+)
- ✅ Edge (90+)

### Error Handling

- Permission denied → User-friendly message
- Timeout (>12s) → Retry suggestion
- Unavailable → Fallback instructions
- Unsupported → Manual entry option

## 📊 API Contract

### Request: POST /optimize-route

```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "emergency_type": "medical"
}
```

### Response: 200 OK

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
      "path": [[28.6139, 77.2090], [28.6180, 77.2100], ...],
      "distance": 2.5,
      "eta": 8,
      "risk_score": 6.2,
      "risk_level": "medium",
      "recommendation": "Heavy traffic on main highway. Consider residential route."
    },
    {
      "type": "safest",
      "path": [[28.6139, 77.2090], [28.6150, 77.2080], ...],
      "distance": 3.1,
      "eta": 11,
      "risk_score": 3.5,
      "risk_level": "low",
      "recommendation": "Clear path through residential areas. Safest option."
    }
  ],
  "status": "success"
}
```

## 🎨 Styling System

### Color Scheme

- **Primary** (Blue): #2563eb
- **Low Risk** (Green): #10b981
- **Medium Risk** (Amber): #f59e0b
- **High Risk** (Red): #dc2626
- **Background**: Dark theme via Radix UI

### Responsive Breakpoints

- **Mobile**: 360px and up
- **Tablet**: 760px and up
- **Desktop**: 1120px and up

## 🔐 Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:5000` |

## 📦 Dependencies Added

```json
{
  "leaflet": "^1.9.4",
  "react-leaflet": "^4.2.3",
  "sonner": "^1.7.1"
}
```

## 🚀 Deployment

### Build for Production

```bash
npm run build
npm start
```

### Environment Setup

Update `.env.local` with production backend URL before deployment.

### Vercel Deployment

```bash
vercel --prod
```

Environment variables can be set in Vercel dashboard:
```
NEXT_PUBLIC_API_URL = https://your-production-api.com
```

## 🐛 Troubleshooting

### Map Not Loading
- Ensure `NEXT_PUBLIC_API_URL` is correct
- Check browser console for CORS errors
- Verify Flask backend is running

### API Errors
- Check network tab for failed requests
- Verify backend is accessible
- Check Flask server logs

### Geolocation Not Working
- Confirm HTTPS or localhost
- Check browser permissions
- Verify browser supports Geolocation API

## 📝 Development Tips

### Running Flask Backend

```bash
cd ..
python app.py  # Runs on http://localhost:5000
```

### Frontend Debug Mode

```bash
npm run dev -- --verbose
```

## 🎯 Next Steps

- [ ] Integrate real hospital database
- [ ] Add real-time traffic data
- [ ] Implement user authentication
- [ ] Add dispatch history tracking
- [ ] Mobile app version (React Native)
- [ ] WebSocket for live updates

## 📞 Support

For issues or questions, check:
1. Terminal console for errors
2. Browser DevTools (F12)
3. Flask server logs
4. Network tab for API calls
