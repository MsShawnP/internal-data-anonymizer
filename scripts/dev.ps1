# Start both backend and frontend dev servers
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

Write-Host "Starting Data Anonymizer dev servers..." -ForegroundColor Cyan

# Start backend
$backend = Start-Process -PassThru -NoNewWindow powershell -ArgumentList @(
    "-Command",
    "Set-Location '$root\backend'; python -m uvicorn app.main:app --reload --port 8000"
)

# Start frontend
$frontend = Start-Process -PassThru -NoNewWindow powershell -ArgumentList @(
    "-Command",
    "Set-Location '$root\frontend'; npm run dev"
)

Write-Host "Backend PID: $($backend.Id) (http://localhost:8000)" -ForegroundColor Green
Write-Host "Frontend PID: $($frontend.Id) (http://localhost:5173)" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop both servers." -ForegroundColor Yellow

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -ErrorAction SilentlyContinue
}
