param(
    [string]$SonarUrl = 'http://localhost:9000',
    [string]$Label = 'current'
)
$ErrorActionPreference = 'Stop'
if ($Label -notmatch '^[A-Za-z0-9_-]+$') { throw 'Label must contain only letters numbers underscores or hyphens.' }
if (-not $env:SONAR_TOKEN) { throw 'Set SONAR_TOKEN using the masked prompt in SONARQUBE.md.' }
$projectRoot = Split-Path $PSScriptRoot -Parent
$headers = @{ Authorization = "Bearer $env:SONAR_TOKEN" }
$baseUrl = $SonarUrl.TrimEnd('/')
$projectKey = 'College-Lost-and-Found'
function Get-SonarPages([string]$Endpoint, [string]$Collection) {
    $records = @()
    $pageNumber = 1
    do {
        $response = Invoke-RestMethod "$baseUrl/api/$Endpoint&p=$pageNumber&ps=100" -Headers $headers -TimeoutSec 30
        $records += @($response.$Collection)
        $total = if ($response.paging) { $response.paging.total } else { $response.total }
        $pageNumber++
    } while ($records.Count -lt $total)
    return $records
}
$issues = @(Get-SonarPages "issues/search?componentKeys=$projectKey" 'issues')
$hotspots = @(Get-SonarPages "hotspots/search?projectKey=$projectKey" 'hotspots')
$metrics = 'bugs,vulnerabilities,security_hotspots,coverage,duplicated_lines_density,ncloc,code_smells'
$measures = Invoke-RestMethod "$baseUrl/api/measures/component?component=$projectKey&metricKeys=$metrics" -Headers $headers -TimeoutSec 30
$gate = Invoke-RestMethod "$baseUrl/api/qualitygates/project_status?projectKey=$projectKey" -Headers $headers -TimeoutSec 30
$analyses = Invoke-RestMethod "$baseUrl/api/project_analyses/search?project=$projectKey&ps=10" -Headers $headers -TimeoutSec 30
$background = Invoke-RestMethod "$baseUrl/api/ce/component?component=$projectKey" -Headers $headers -TimeoutSec 30
$result = [ordered]@{
    project_key = $projectKey
    server_url = $baseUrl
    captured_utc = [DateTime]::UtcNow.ToString('o')
    label = $Label
    latest_background_task = $background.current
    queued_background_tasks = $background.queue
    latest_task_succeeded = ($background.current.status -eq 'SUCCESS')
    analyses = $analyses.analyses
    quality_gate = $gate.projectStatus
    measures = $measures.component.measures
    issues = $issues
    security_hotspots = $hotspots
}
$outputDir = Join-Path $projectRoot '.sonar-evidence'
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
$file = Join-Path $outputDir "$Label-results.json"
$result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $file -Encoding utf8
Write-Host "Saved $file"
Write-Host "Quality gate: $($gate.projectStatus.status); issues: $($issues.Count); hotspots: $($hotspots.Count)"
Write-Host "Latest background task: $($background.current.status)"
Write-Host 'Review issue statuses and analysis IDs before claiming a fix. Hotspots require manual context review.'
