# AIDRoute - Ready-to-Run Commands & Demo Setup

> **All copy-paste commands to get AIDRoute running and record your demo**

---

## 🎯 Ultra-Quick Start (ONE Command)

### Windows PowerShell - Everything in One Go

```powershell
powershell -ExecutionPolicy Bypass -File RUN_DEMO.ps1
```

**What it does:**
- ✅ Creates Python venv
- ✅ Installs backend dependencies
- ✅ Installs frontend dependencies
- ✅ Creates .env files
- ✅ Starts backend on http://127.0.0.1:5000
- ✅ Starts frontend on http://localhost:3000
- ✅ Opens browser automatically

Then go to: **http://localhost:3000**

---

## 📋 Manual Step-by-Step (if you prefer)

### Terminal 1: Backend Setup & Run

```powershell
# Navigate to project root
cd C:\Users\bhuta\OneDrive\Desktop\AIDROUTE

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\Activate.ps1

# Or on macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python app.py
```

**Expected output:**
```
* Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### Terminal 2: Frontend Setup & Run

```powershell
# New terminal, navigate to project
cd C:\Users\bhuta\OneDrive\Desktop\AIDROUTE\frontend

# Install npm packages
npm install

# Start dev server
npm run dev
```

**Expected output:**
```
- Local:         http://localhost:3000
✓ Ready in 795ms
```

### Terminal 3: Open Browser

```powershell
start http://localhost:3000
```

---

## 🧪 Test API Endpoints Directly

### Test 1: Optimize Route

```powershell
$body = @{
    latitude = 28.61
    longitude = 77.20
    emergencyType = "medical"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:5000/optimize-route `
  -Method POST `
  -Body $body `
  -ContentType 'application/json' | ConvertTo-Json -Depth 5
```

### Test 2: Simulate Disaster

```powershell
$body = @{
    type = "flood"
    latitude = 28.61
    longitude = 77.20
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:5000/simulate-disaster `
  -Method POST `
  -Body $body `
  -ContentType 'application/json' | ConvertTo-Json -Depth 5
```

### Test 3: Full Workflow (Optimize → Simulate → Re-optimize)

```powershell
# Test API responses directly
Write-Host "Testing /optimize-route..." -ForegroundColor Green
$opt1 = Invoke-RestMethod -Uri http://127.0.0.1:5000/optimize-route `
  -Method POST `
  -Body '{"latitude":28.61,"longitude":77.20,"emergencyType":"medical"}' `
  -ContentType 'application/json'
Write-Host "✓ Route calculated: $(($opt1.data.routes[0].type)) option available"

Write-Host "Testing /simulate-disaster..." -ForegroundColor Green
$sim = Invoke-RestMethod -Uri http://127.0.0.1:5000/simulate-disaster `
  -Method POST `
  -Body '{"type":"flood","latitude":28.61,"longitude":77.20}' `
  -ContentType 'application/json'
Write-Host "✓ Disaster simulated: $($sim.data.blocked_roads.Count) roads blocked"

Write-Host "Testing re-optimization..." -ForegroundColor Green
$opt2 = Invoke-RestMethod -Uri http://127.0.0.1:5000/optimize-route `
  -Method POST `
  -Body '{"latitude":28.61,"longitude":77.20,"emergencyType":"flood"}' `
  -ContentType 'application/json'
Write-Host "✓ Route recalculated: Decision score: $($opt2.data.final_decision.score)"
```

---

## 🎬 Recording Your Demo

### Best Demo Flow (2-3 minutes)

1. **Open dashboard** → http://localhost:3000
2. **Click "My Location"** → Grant geolocation
3. **Click "Optimize"** → Watch AI calculate route
4. **Show results** → Highlight hospital, ETA, AI decision
5. **Click "Flood"** → Simulate disaster
6. **Show re-routing** → Watch map update with blocked roads
7. **View AI Panel** → Show Gemini justifications

### Tools for Recording

#### Windows: Built-in Screen Recorder
```powershell
# Start with Win+G, then click "Start recording"
# Or use PowerToys Screen Sketch (Win+Shift+S)
# Save to: Videos folder
```

#### OBS Studio (Free & Professional)
1. Download: https://obsproject.com
2. Add Source → Window Capture
3. Select Chrome/Edge with http://localhost:3000
4. Start Recording
5. File → Export Video → MP4

#### Loom (Free, Cloud-based)
1. Go to https://www.loom.com
2. Click "Start recording"
3. Select browser window
4. Record demo
5. Share link automatically

#### ffmpeg (Command-line)
```powershell
# Install: choco install ffmpeg
ffmpeg -f gdigrab -i desktop -vcodec libx264 -crf 0 -preset ultrafast demo.mp4
```

---

## 📸 Screenshots for Documentation

### Capture Dashboard Screenshots

```powershell
# Using PowerShell screenshot function
function Take-ScreenShot {
    param(
        [string]$Path = ".\screenshot_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').png"
    )
    
    Add-Type -Assembly System.Windows.Forms
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bmp = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bmp)
    $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
    $bmp.Save($Path)
    Write-Host "Screenshot saved: $Path" -ForegroundColor Green
}

# Take screenshot
Take-ScreenShot -Path ".\demo_screenshot_1_initial.png"
```

---

## 🚀 Publishing Your Demo (Step-by-Step)

### Option A: GitHub + YouTube

#### 1. Prepare Repository
```bash
git log --oneline  # Show commit history
git remote -v      # Show GitHub URL
```

#### 2. Create GitHub Release
```bash
# On GitHub.com:
1. Click "Releases" tab
2. Click "Create a new release"
3. Tag: v1.0.0
4. Title: "AIDRoute v1.0.0 - AI Emergency Routing System"
5. Description: Include demo video link + features
6. Attach: demo.mp4 or link to YouTube
```

#### 3. Upload Demo to YouTube
```
1. Go to https://www.youtube.com/studio
2. Click "Create" → "Upload video"
3. Select demo.mp4
4. Title: "AIDRoute - AI-Powered Emergency Routing Demo"
5. Description: 
   - GitHub: https://github.com/yourusername/aidroute
   - Features: Route optimization, Disaster simulation, AI decision engine
   - Setup: See README.md or QUICK_START.md
6. Tags: emergency routing, AI, disaster response
7. Publish
```

#### 4. Share Links
```
GitHub: https://github.com/yourusername/aidroute
YouTube: https://youtube.com/watch?v=your_video_id
README: https://github.com/yourusername/aidroute#readme
```

---

### Option B: Deploy Live (Try These)

#### Deploy Backend to Render.com (Free)
```bash
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +"
4. Select "Web Service"
5. Connect your GitHub repo
6. Build: pip install -r requirements.txt
7. Start: gunicorn app:app
8. Deploy
9. Get URL: https://aidroute-backend.onrender.com
```

#### Deploy Frontend to Vercel (Free)
```bash
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "Add New Project"
4. Select aidroute repository
5. Root Directory: ./frontend
6. Environment: NEXT_PUBLIC_API_URL=https://aidroute-backend.onrender.com
7. Deploy
8. Get URL: https://aidroute.vercel.app
```

#### Update Frontend for Production
```bash
# In frontend/.env.local
NEXT_PUBLIC_API_URL=https://aidroute-backend.onrender.com

# Commit and push
git add frontend/.env.local
git commit -m "chore: update API URL for production"
git push origin main
```

---

## 📊 GitHub Repository Setup

### Initialize if not already initialized

```bash
git init
git add .
git commit -m "Initial commit: AIDRoute AI Emergency Routing System"
git branch -M main
git remote add origin https://github.com/yourusername/aidroute.git
git push -u origin main
```

### Push Latest Changes

```bash
git status                    # Check what changed
git add .                     # Stage all changes
git commit -m "Your message"  # Commit
git push                      # Push to GitHub
```

---

## 📝 Perfect Demo Script (Copy-Paste)

**Before starting, have ready:**
- ✅ Backend running
- ✅ Frontend running
- ✅ Browser at http://localhost:3000
- ✅ Screen recorder ready

**Demo narration (2 minutes):**

```
[0:00-0:10] "Welcome to AIDRoute, an AI-powered emergency routing system"
  - Show title, feature list on screen

[0:10-0:30] "It uses intelligent algorithms to optimize ambulance routes during disasters"
  - Click "My Location" to enable geolocation
  - Highlight the input form

[0:30-1:00] "First, we'll optimize a route for an emergency"
  - Click "Optimize" button
  - Wait for results
  - Show: hospital info, ETA, routes on map

[1:00-1:30] "Now watch what happens when we simulate a disaster"
  - Click "Flood" button
  - Show: roads turning red on map
  - Highlight: blocked_roads in response

[1:30-2:00] "The AI automatically recalculates a safer route avoiding the disaster"
  - Show updated routes
  - Highlight: AI Decision panel
  - Read Gemini justification

[2:00-2:10] "Check out the code on GitHub"
  - Show GitHub link
  - Mention: Next.js, Flask, Gemini AI

[2:10+] End, thankyou, subscribe
```

---

## 🔗 Share Your Demo

### Markdown Template for README

```markdown
## 🎬 Demo Video

[![Watch Demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)

**[Click to watch 2-minute demo on YouTube](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)**

### Features Demonstrated:
- ✅ Route optimization with multiple options
- ✅ Disaster simulation (flood)
- ✅ Real-time re-routing
- ✅ AI decision explanations
- ✅ Responsive dashboard

### Live Deployment:
- Frontend: [https://aidroute.vercel.app](https://aidroute.vercel.app)
- Backend: [https://aidroute-backend.onrender.com](https://aidroute-backend.onrender.com)
- Repository: [https://github.com/yourusername/aidroute](https://github.com/yourusername/aidroute)
```

---

## ✅ Demo Checklist

- [ ] Backend running on http://127.0.0.1:5000
- [ ] Frontend running on http://localhost:3000
- [ ] Geolocation working (allow permission)
- [ ] /optimize-route returns valid response
- [ ] /simulate-disaster updates blocked roads
- [ ] Map displays routes correctly
- [ ] AI Decision panel shows Gemini text
- [ ] Disaster simulation re-routes correctly
- [ ] All UI elements responsive
- [ ] No console errors
- [ ] Demo recorded (2-3 minutes)
- [ ] Video uploaded to YouTube
- [ ] GitHub repo updated with links
- [ ] README includes demo video
- [ ] Share links working

---

## 🎯 Next Steps

1. ✅ **Run demo locally** → Use RUN_DEMO.ps1
2. ✅ **Test endpoints** → Use PowerShell test commands above
3. ✅ **Record demo** → Use OBS or built-in Windows recorder
4. ✅ **Upload to YouTube** → Share with team
5. ✅ **Deploy live** → Use Render + Vercel
6. ✅ **Update GitHub** → Add video link to README
7. ✅ **Share everywhere** → LinkedIn, Twitter, portfolio

---

**Ready to run?** Copy this command:
```powershell
powershell -ExecutionPolicy Bypass -File RUN_DEMO.ps1
```

**Questions?** Check [QUICK_START.md](QUICK_START.md) or [README.md](README.md)

---

**Version**: 1.0.0 | **Last Updated**: April 28, 2026
