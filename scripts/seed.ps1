param(
  [int]$Subjects = 4,
  [int]$Days = 30,
  [string]$Profile = "healthy",
  [string]$HostName = "localhost"
)

function Resolve-Host {
  param([string]$PreferredHost)
  try {
    Invoke-RestMethod -Uri "http://$PreferredHost`:8002/health" -Method Get -TimeoutSec 4 | Out-Null
    return $PreferredHost
  } catch {
    if ($PreferredHost -ne "localhost") {
      throw
    }
    $wslIp = (wsl -d Ubuntu -e sh -lc "hostname -I | awk '{print `$1}'").Trim()
    if ([string]::IsNullOrWhiteSpace($wslIp)) {
      throw "Unable to determine WSL IP."
    }
    Invoke-RestMethod -Uri "http://$wslIp`:8002/health" -Method Get -TimeoutSec 4 | Out-Null
    return $wslIp
  }
}

$resolvedHost = Resolve-Host -PreferredHost $HostName
$uri = "http://$resolvedHost`:8002/v1/simulate-all?subjects=$Subjects&days=$Days&profile=$Profile"
Invoke-RestMethod -Method Post -Uri $uri | ConvertTo-Json -Depth 5
