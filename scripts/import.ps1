param(
  [string]$Input = "exports/openpulse_export.json"
)

if (!(Test-Path $Input)) {
  throw "Input file not found: $Input"
}

$data = Get-Content $Input -Raw | ConvertFrom-Json
$data.rows | ConvertTo-Json -Depth 20 | Set-Content -Path "imports/last_import_preview.json"
Write-Output "Import preview created at imports/last_import_preview.json. Use connector-service for canonical ingest replay."
