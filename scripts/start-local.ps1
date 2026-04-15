param(
    [string]$ApiHost = "127.0.0.1",
    [int]$ApiPort = 8000,
    [int]$WebPort = 5173
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiPath = Join-Path $repoRoot "apps/api"
$webPath = Join-Path $repoRoot "apps/web"

if (-not (Test-Path $apiPath)) {
    throw "API folder not found at $apiPath"
}
if (-not (Test-Path $webPath)) {
    throw "Web folder not found at $webPath"
}

Write-Host "Starting HomeOps API on http://$ApiHost`:$ApiPort ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$apiPath'; uvicorn main:app --host $ApiHost --port $ApiPort --reload"

Write-Host "Starting HomeOps web app on http://127.0.0.1`:$WebPort ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$webPath'; `$env:VITE_BACKEND_TARGET='http://$ApiHost`:$ApiPort'; npm run dev -- --host 127.0.0.1 --port $WebPort"

Write-Host "Both services started in separate terminals."
