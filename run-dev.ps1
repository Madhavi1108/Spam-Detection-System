# run-dev.ps1
# Windows Local Development Orchestrator

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Spam Detection System Dev Orchestrator..." -ForegroundColor Cyan

# 1. System Requirements Verification
function Verify-Command ($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "Required command '$name' is not installed or not in system PATH."
    }
}
Verify-Command "python"
Verify-Command "node"
Verify-Command "npm"

# 2. Setup Python Virtual Environment & Dependencies
$VENV_PATH = Join-Path $PSScriptRoot "venv"
if (-not (Test-Path $VENV_PATH)) {
    Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "🐍 Activating venv & installing Python dependencies..." -ForegroundColor Yellow
& "$VENV_PATH\Scripts\python.exe" -m pip install --upgrade pip
& "$VENV_PATH\Scripts\python.exe" -m pip install -r backend/requirements.txt

# 3. Setup Node Gateway Dependencies
$BACKEND_NODE_DIR = Join-Path $PSScriptRoot "backend"
if (-not (Test-Path (Join-Path $BACKEND_NODE_DIR "node_modules"))) {
    Write-Host "📦 Installing Node gateway dependencies..." -ForegroundColor Yellow
    Push-Location $BACKEND_NODE_DIR
    npm install
    Pop-Location
}

# 4. Setup React Frontend Dependencies
$FRONTEND_NODE_DIR = Join-Path $PSScriptRoot "frontend"
if (-not (Test-Path (Join-Path $FRONTEND_NODE_DIR "node_modules"))) {
    Write-Host "📦 Installing React frontend dependencies..." -ForegroundColor Yellow
    Push-Location $FRONTEND_NODE_DIR
    npm install
    Pop-Location
}

# 5. Run Concurrently
Write-Host "🔥 Starting Flask ML API, Node Gateway, and React Frontend..." -ForegroundColor Green

# Define jobs or processes
$FlaskProc = Start-Process "$VENV_PATH\Scripts\python.exe" -ArgumentList "backend/api.py" -NoNewWindow -PassThru
$NodeProc = Start-Process "node" -ArgumentList "backend/server.js" -WorkingDirectory $BACKEND_NODE_DIR -NoNewWindow -PassThru
$ViteProc = Start-Process "npm" -ArgumentList "run dev" -WorkingDirectory $FRONTEND_NODE_DIR -NoNewWindow -PassThru

Write-Host "💡 All services are running! Press Ctrl+C to terminate all services." -ForegroundColor Cyan

# Wait and handle cleanup on exit
try {
    while ($true) {
        if ($FlaskProc.HasExited) {
            Write-Host "⚠️ Flask ML API has exited." -ForegroundColor Yellow
            break
        }
        if ($NodeProc.HasExited) {
            Write-Host "⚠️ Node Gateway has exited." -ForegroundColor Yellow
            break
        }
        if ($ViteProc.HasExited) {
            Write-Host "⚠️ React Frontend has exited." -ForegroundColor Yellow
            break
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`n🛑 Shutting down all services..." -ForegroundColor Red
    Stop-Process -Id $FlaskProc.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $NodeProc.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $ViteProc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Clean shutdown completed." -ForegroundColor Green
}
