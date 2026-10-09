$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$runtimePython = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) {
    throw 'Create .venv and install requirements.lock first. Follow README.md.'
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.local-secrets.json'))) {
    throw 'Initialize the demo first: .\.venv\Scripts\python.exe scripts/setup_local.py'
}
$localState = Get-Content (Join-Path $PSScriptRoot '../.local-secrets.json') -Raw | ConvertFrom-Json
$env:APP_SECRET = $localState.APP_SECRET
Set-Location $projectRoot
& $runtimePython app.py
