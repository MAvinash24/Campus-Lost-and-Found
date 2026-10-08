$ErrorActionPreference = 'Stop'
$runtimePython = 'C:/Users/NAANI/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$env:PYTHONPATH = Join-Path $PSScriptRoot '../.runtime_v2'
$localState = Get-Content (Join-Path $PSScriptRoot '../.local-secrets.json') -Raw | ConvertFrom-Json
$env:APP_SECRET = $localState.APP_SECRET
Set-Location (Join-Path $PSScriptRoot '..')
& $runtimePython app.py
