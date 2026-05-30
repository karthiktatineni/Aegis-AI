$ErrorActionPreference = "Stop"

Write-Host "Starting Aegis AI API on http://localhost:8000"
Start-Process -WindowStyle Hidden powershell -ArgumentList "-NoProfile -Command `"cd apps/api; python -m uvicorn app.main:app --reload --port 8000`""

Write-Host "Starting Aegis AI web app on http://localhost:3000"
npm run dev:web
