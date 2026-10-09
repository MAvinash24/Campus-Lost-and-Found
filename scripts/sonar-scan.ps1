param(
    [string]$SonarUrl = 'http://localhost:9000',
    [switch]$PrepareOnly
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $projectRoot
try {
    $python = Join-Path $projectRoot '.tools/sonar-venv/Scripts/python.exe'
    $scanner = Join-Path $projectRoot '.tools/sonar-venv/Scripts/pysonar.exe'
    if (-not (Test-Path -LiteralPath $scanner)) {
        throw 'Scanner missing. Follow SONARQUBE.md to install the isolated scanner environment.'
    }
    New-Item -ItemType Directory -Path '.sonar-evidence' -Force | Out-Null
    & $python -c "from importlib.metadata import version; print('Official pysonar scanner ' + version('pysonar'))"
    if ($LASTEXITCODE -ne 0) { throw 'Scanner version check failed.' }
    & $python -m coverage run -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed; scan stopped.' }
    & $python -m coverage xml
    if ($LASTEXITCODE -ne 0) { throw 'Coverage XML generation failed.' }
    & $python -m coverage report
    if ($LASTEXITCODE -ne 0) { throw 'Coverage report failed.' }
    if ($PrepareOnly) { return }
    $status = Invoke-RestMethod "$($SonarUrl.TrimEnd('/'))/api/system/status" -TimeoutSec 15
    if ($status.status -ne 'UP') { throw "SonarQube is not ready: $($status.status)" }
    if (-not $env:SONAR_TOKEN) { throw 'Set SONAR_TOKEN using the masked prompt in SONARQUBE.md.' }
    $env:SONAR_HOST_URL = $SonarUrl
    $env:SONAR_USER_HOME = Join-Path $projectRoot '.tools/sonar-cache'
    # Token is inherited through the environment, never added to command arguments.
    & $scanner --sonar-scanner-metadata-filepath (Join-Path $projectRoot '.sonar-evidence/report-task.txt') 2>&1 | Tee-Object -FilePath '.sonar-evidence/scanner.log'
    $scannerExit = $LASTEXITCODE
    if ($scannerExit -ne 0) {
        throw "Scanner/quality gate returned $scannerExit. Review .sonar-evidence/scanner.log and the dashboard."
    }
    Write-Host "$($SonarUrl.TrimEnd('/'))/dashboard?id=College-Lost-and-Found"
    Write-Host 'Check .sonar-evidence/report-task.txt for the submitted background task and dashboard link.'
} finally {
    Pop-Location
}
