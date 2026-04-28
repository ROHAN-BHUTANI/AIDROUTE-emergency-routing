# AIDRoute Demo - Complete Setup & Run Script (Windows PowerShell)
# This script sets up and runs the entire AIDRoute system with backend and frontend

param(
    [switch]$SkipInstall = $false,
    [switch]$BackendOnly = $false
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          AIDRoute - Emergency Response AI System               ║" -ForegroundColor Cyan
Write-Host "║                     Demo Runner & Setup                        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install Backend Dependencies
if (-not $SkipInstall) {
    Write-Host "[1/4] Installing backend dependencies..." -ForegroundColor Yellow
    Write-Host "Creating/activating virtual environment..." -ForegroundColor Gray
    
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
    }
    
    Write-Host "Installing Python packages..." -ForegroundColor Gray
    & .venv\Scripts\pip.exe install -q -r requirements.txt 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Backend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to install backend dependencies" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Create .env file if it doesn't exist
Write-Host "[2/4] Setting up environment variables..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    @"
# Backend environment variables
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=false
"@ | Out-File -Encoding UTF8 ".env"
    Write-Host "✓ Created .env file (set GEMINI_API_KEY for AI features)" -ForegroundColor Green
} else {
    Write-Host "✓ .env file exists" -ForegroundColor Green
}

if (-not (Test-Path "frontend\.env.local")) {
    @"
NEXT_PUBLIC_API_URL=http://localhost:5000
"@ | Out-File -Encoding UTF8 "frontend\.env.local"
    Write-Host "✓ Created frontend/.env.local" -ForegroundColor Green
} else {
    Write-Host "✓ frontend/.env.local exists" -ForegroundColor Green
}

# Step 3: Install Frontend Dependencies
if (-not $SkipInstall) {
    Write-Host "[3/4] Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location "frontend"
    
    Write-Host "Running npm install..." -ForegroundColor Gray
    npm install --quiet 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to install frontend dependencies" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
}

# Step 4: Start Services
Write-Host "[4/4] Starting services..." -ForegroundColor Yellow
Write-Host ""

# Set execution policy for this session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force | Out-Null

if ($BackendOnly) {
    Write-Host "Starting Backend Only Mode" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Backend: http://127.0.0.1:5000" -ForegroundColor Green
    Write-Host "API Endpoint: POST /optimize-route" -ForegroundColor Gray
    Write-Host "API Endpoint: POST /simulate-disaster" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press CTRL+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    & .venv\Scripts\Activate.ps1
    & .venv\Scripts\python.exe app.py
} else {
    # Start Backend in a new PowerShell process
    Write-Host "Starting Backend Server..." -ForegroundColor Green
    $backendProcess = Start-Process -FilePath powershell.exe -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$projectRoot'; & .venv\Scripts\Activate.ps1; & .venv\Scripts\python.exe app.py"
    ) -PassThru
    
    Start-Sleep -Seconds 2
    
    # Start Frontend in a new PowerShell process
    Write-Host "Starting Frontend Server..." -ForegroundColor Green
    $frontendProcess = Start-Process -FilePath powershell.exe -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$projectRoot\frontend'; npm run dev"
    ) -PassThru
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                    SERVERS STARTED                             ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 Frontend Dashboard:" -ForegroundColor Cyan
    Write-Host "   http://localhost:3000" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 Backend API:" -ForegroundColor Cyan
    Write-Host "   http://127.0.0.1:5000" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 API Endpoints:" -ForegroundColor Cyan
    Write-Host "   POST /optimize-route" -ForegroundColor Gray
    Write-Host "   POST /simulate-disaster" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📌 Demo Steps:" -ForegroundColor Cyan
    Write-Host "   1. Open http://localhost:3000 in your browser" -ForegroundColor Gray
    Write-Host "   2. Click 'My Location' to enable geolocation" -ForegroundColor Gray
    Write-Host "   3. Click 'Optimize' to calculate emergency route" -ForegroundColor Gray
    Write-Host "   4. Click 'Flood', 'Fire', or 'Crash' to simulate disaster" -ForegroundColor Gray
    Write-Host "   5. Watch AI re-route around blocked roads" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press CTRL+C in this window to stop both servers" -ForegroundColor Yellow
    Write-Host ""
    
    # Wait for processes
    $backendProcess | Wait-Process
    $frontendProcess | Wait-Process
}
