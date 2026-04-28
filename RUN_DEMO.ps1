# AIDRoute Demo - Complete Setup & Run Script (Windows PowerShell)
# This script sets up and runs the entire AIDRoute system with backend and frontend

param(
    [switch]$BackendOnly = $false
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "AIDRoute - Emergency Response AI System" -ForegroundColor Cyan
Write-Host "Demo Runner and Setup Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create venv if needed
Write-Host "[1/4] Checking Python environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv .venv
    Write-Host "Virtual environment created" -ForegroundColor Green
}
Write-Host "Activating venv..." -ForegroundColor Gray

# Step 2: Install Backend Dependencies
Write-Host "[2/4] Installing backend dependencies..." -ForegroundColor Yellow
& .\.venv\Scripts\pip.exe install -q -r requirements.txt
Write-Host "Backend dependencies installed" -ForegroundColor Green

# Step 3: Create .env files
Write-Host "[3/4] Setting up environment files..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    @"
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=false
"@ | Out-File -Encoding UTF8 ".env"
    Write-Host "Created .env file" -ForegroundColor Green
}

if (-not (Test-Path "frontend\.env.local")) {
    @"
NEXT_PUBLIC_API_URL=http://localhost:5000
"@ | Out-File -Encoding UTF8 "frontend\.env.local"
    Write-Host "Created frontend/.env.local" -ForegroundColor Green
}

# Step 4: Install Frontend Dependencies
Write-Host "[4/4] Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location "frontend"
npm install --quiet
Pop-Location
Write-Host "Frontend dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Setup Complete - Starting Servers" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

if ($BackendOnly) {
    Write-Host "Starting Backend Only" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Backend: http://127.0.0.1:5000" -ForegroundColor Green
    Write-Host "Press CTRL+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    & .venv\Scripts\Activate.ps1
    & .venv\Scripts\python.exe app.py
}
else {
    # Start Backend
    Write-Host "Starting Backend Server..." -ForegroundColor Green
    $backendCmd = "Set-Location '$projectRoot'; & .venv\Scripts\Activate.ps1; & .venv\Scripts\python.exe app.py"
    $backendProcess = Start-Process -FilePath powershell.exe -ArgumentList "-NoExit", "-Command", $backendCmd -PassThru
    
    Start-Sleep -Seconds 2
    
    # Start Frontend
    Write-Host "Starting Frontend Server..." -ForegroundColor Green
    $frontendCmd = "Set-Location '$projectRoot\frontend'; npm run dev"
    $frontendProcess = Start-Process -FilePath powershell.exe -ArgumentList "-NoExit", "-Command", $frontendCmd -PassThru
    
    Start-Sleep -Seconds 1
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "SERVERS STARTED" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Frontend Dashboard:" -ForegroundColor Cyan
    Write-Host "  http://localhost:3000" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend API:" -ForegroundColor Cyan
    Write-Host "  http://127.0.0.1:5000" -ForegroundColor Green
    Write-Host ""
    Write-Host "API Endpoints:" -ForegroundColor Cyan
    Write-Host "  POST /optimize-route" -ForegroundColor Gray
    Write-Host "  POST /simulate-disaster" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Demo Steps:" -ForegroundColor Cyan
    Write-Host "  1. Open http://localhost:3000 in browser" -ForegroundColor Gray
    Write-Host "  2. Click My Location to enable geolocation" -ForegroundColor Gray
    Write-Host "  3. Click Optimize to calculate route" -ForegroundColor Gray
    Write-Host "  4. Click Flood, Fire, or Crash to simulate disaster" -ForegroundColor Gray
    Write-Host "  5. Watch AI re-route around blocked roads" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press CTRL+C to stop both servers" -ForegroundColor Yellow
    Write-Host ""
    
    $backendProcess | Wait-Process
    $frontendProcess | Wait-Process
}
