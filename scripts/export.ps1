param(
  [string]$Output = "exports/openpulse_export.json"
)

if (!(Test-Path "exports")) { New-Item -ItemType Directory -Path "exports" | Out-Null }
$payload = @{ sql = "SELECT * FROM openpulse.observation ORDER BY event_time DESC LIMIT 10000" } | ConvertTo-Json
$response = Invoke-RestMethod -Method Post -Uri "http://localhost:8003/v1/sql" -Body $payload -ContentType "application/json"
$response | ConvertTo-Json -Depth 10 | Set-Content -Path $Output
Write-Output "Exported to $Output"
