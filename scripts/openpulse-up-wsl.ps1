param(
  [switch]$NoBuild
)

if (!(Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}

if ($NoBuild) {
  wsl -d Ubuntu -e sh -lc "cd /mnt/c/Users/grump/OpenPulse && docker compose up -d"
} else {
  wsl -d Ubuntu -e sh -lc "cd /mnt/c/Users/grump/OpenPulse && docker compose up -d --build"
}

$wslIp = (wsl -d Ubuntu -- hostname -I).Trim().Split(' ')[0]
Write-Output "OpenPulse Docker stack is up via WSL Docker Engine."
Write-Output "Base access IP: $wslIp"
Write-Output "Ingestion:      http://$wslIp:8001"
Write-Output "Connector:      http://$wslIp:8002"
Write-Output "Query API:      http://$wslIp:8003"
Write-Output "Consent:        http://$wslIp:8004"
Write-Output "Governor Jeff:  http://$wslIp:8005"
Write-Output "EHR API:        http://$wslIp:8006"
Write-Output "Ops Console:    http://$wslIp:8007"
Write-Output "Grafana:        http://$wslIp:3000"
Write-Output "Prometheus:     http://$wslIp:9090"
Write-Output "MinIO Console:  http://$wslIp:9001"
