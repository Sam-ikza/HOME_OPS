param(
    [string]$ApiHost = "127.0.0.1",
    [int]$ApiPort = 8000,
    [int]$WebPort = 5173,
    [switch]$ReinstallDeps
)

$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$apiPath = Join-Path $repoRoot "apps/api"
$webPath = Join-Path $repoRoot "apps/web"
$startScript = Join-Path $repoRoot "scripts/start-local.ps1"

if (-not (Test-Path $apiPath)) {
    throw "API folder not found at $apiPath"
}
if (-not (Test-Path $webPath)) {
    throw "Web folder not found at $webPath"
}
if (-not (Test-Path $startScript)) {
    throw "Start script not found at $startScript"
}

function Get-PythonLauncher {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "Python was not found on PATH. Install Python 3 first."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found on PATH. Install Node.js (includes npm) first."
}

$pythonExe = Join-Path $apiPath ".venv\Scripts\python.exe"
$venvExists = Test-Path $pythonExe

if (-not $venvExists -or $ReinstallDeps.IsPresent) {
    if ($ReinstallDeps.IsPresent -and (Test-Path (Join-Path $apiPath ".venv"))) {
        Write-Host "Removing existing backend virtual environment..."
        Remove-Item -Path (Join-Path $apiPath ".venv") -Recurse -Force
    }

    Write-Host "Creating backend virtual environment..."
    $launcher = Get-PythonLauncher
    Push-Location $apiPath
    try {
        & $launcher[0] $launcher[1..($launcher.Length - 1)] -m venv .venv
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path $pythonExe)) {
    throw "Backend virtual environment was not created successfully."
}

Write-Host "Installing backend dependencies..."
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r (Join-Path $apiPath "requirements.txt")

$nodeModulesPath = Join-Path $webPath "node_modules"
$lockFile = Join-Path $webPath "package-lock.json"

if ($ReinstallDeps.IsPresent -and (Test-Path $nodeModulesPath)) {
    Write-Host "Removing existing frontend node_modules..."
    Remove-Item -Path $nodeModulesPath -Recurse -Force
}

if (-not (Test-Path $nodeModulesPath) -or $ReinstallDeps.IsPresent) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $webPath
    try {
        if (Test-Path $lockFile) {
            npm ci
        } else {
            npm install
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Frontend dependencies already present; skipping install."
}

Write-Host "Launching API and web app..."
& $startScript -ApiHost $ApiHost -ApiPort $ApiPort -WebPort $WebPort
