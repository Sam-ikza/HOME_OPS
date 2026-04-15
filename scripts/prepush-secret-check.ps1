$ErrorActionPreference = "Stop"

# Scan staged changes for obvious secrets before push.
$patterns = @(
    'AKIA[0-9A-Z]{16}',
    'AIza[0-9A-Za-z\-_]{35}',
    'sk-[A-Za-z0-9]{20,}',
    'xox[baprs]-[A-Za-z0-9-]{10,}',
    '(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*["''][^"''\s]{8,}["'']'
)

$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "No staged files found. Secret scan skipped."
    exit 0
}

$failures = @()
foreach ($file in $staged) {
    if (-not (Test-Path $file)) {
        continue
    }

    # Skip binaries and minified bundles.
    if ($file -match '\.(png|jpg|jpeg|gif|webp|ico|pdf|zip|gz|min\.js|min\.css)$') {
        continue
    }

    $patch = git diff --cached -- $file
    foreach ($pattern in $patterns) {
        if ($patch -match $pattern) {
            $failures += "Possible secret pattern detected in $file"
            break
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Push blocked: potential secrets found in staged changes." -ForegroundColor Red
    $failures | Sort-Object -Unique | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
    Write-Host "Review staged changes with: git diff --cached" -ForegroundColor Yellow
    exit 1
}

Write-Host "Secret scan passed." -ForegroundColor Green
exit 0
