
# Start Creative AI Platform Live via ngrok

Write-Host "Starting Creative AI Platform deployment..." -ForegroundColor Cyan

# 1. Start Backend
Write-Host "1. Starting Backend Server..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "uvicorn" -ArgumentList "app.api.main:app --host 0.0.0.0 --port 8000" -PassThru -NoNewWindow
Start-Sleep -Seconds 5

# 2. Start ngrok
Write-Host "2. Starting ngrok tunnels..." -ForegroundColor Yellow
# Ensure ngrok.yml exists
if (-not (Test-Path "ngrok.yml")) {
    Write-Error "ngrok.yml not found! Please create it first."
    exit 1
}

# Start ngrok in background
$ngrokProcess = Start-Process -FilePath ".\ngrok.exe" -ArgumentList "start --all --config=$env:LOCALAPPDATA\ngrok\ngrok.yml --config=ngrok.yml" -PassThru -WindowStyle Minimized
Start-Sleep -Seconds 10

# 3. Get Public URL
Write-Host "3. Fetching public URLs..." -ForegroundColor Yellow
try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
    $backendTunnel = $tunnels.tunnels | Where-Object { $_.config.addr -match "8000" } | Select-Object -First 1
    $frontendTunnel = $tunnels.tunnels | Where-Object { $_.config.addr -match "5173" } | Select-Object -First 1

    $backendUrl = $backendTunnel.public_url
    $frontendUrl = $frontendTunnel.public_url

    Write-Host "Backend Live at: $backendUrl" -ForegroundColor Green
    Write-Host "Frontend Live at: $frontendUrl" -ForegroundColor Green
}
catch {
    Write-Error "Failed to get ngrok URLs. Is ngrok running?"
    Stop-Process -Id $backendProcess.Id
    if ($ngrokProcess) { Stop-Process -Id $ngrokProcess.Id }
    exit 1
}

# 4. Start Frontend
Write-Host "4. Starting Frontend..." -ForegroundColor Yellow
$env:VITE_API_BASE_URL = $backendUrl
Set-Location "frontend"
# Build first? User said "Deploy completed... locally". Typically involves dev server for live testing.
# But "Live via ngrok" implies maybe production build? User said "Start dev server".
npm run dev

# Cleanup on exit
Write-Host "Stopping services..."
Stop-Process -Id $backendProcess.Id
Stop-Process -Id $ngrokProcess.Id
