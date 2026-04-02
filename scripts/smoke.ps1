param(
  [string]$HostName = "localhost"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ResolvedHost {
  param([string]$PreferredHost)

  try {
    Invoke-RestMethod -Uri "http://$PreferredHost`:8007/health" -Method Get -TimeoutSec 4 | Out-Null
    return $PreferredHost
  } catch {
    if ($PreferredHost -ne "localhost") {
      throw
    }
    try {
      $wslIp = (wsl -d Ubuntu -e sh -lc "hostname -I | awk '{print `$1}'").Trim()
      if ([string]::IsNullOrWhiteSpace($wslIp)) {
        throw "Unable to determine WSL IP."
      }
      Invoke-RestMethod -Uri "http://$wslIp`:8007/health" -Method Get -TimeoutSec 4 | Out-Null
      return $wslIp
    } catch {
      throw "Unable to reach OpenPulse via localhost or WSL host IP."
    }
  }
}

function Assert-Status200 {
  param(
    [Parameter(Mandatory = $true)][string]$Uri,
    [ValidateSet("GET", "POST")][string]$Method = "GET",
    [object]$Body = $null
  )

  $params = @{
    Uri = $Uri
    Method = $Method
    TimeoutSec = 20
  }

  if ($null -ne $Body) {
    $params.ContentType = "application/json"
    $params.Body = ($Body | ConvertTo-Json -Depth 8 -Compress)
  }

  try {
    Invoke-RestMethod @params | Out-Null
  } catch {
    throw "Expected HTTP 200 from $Uri but request failed: $($_.Exception.Message)"
  }
}

$resolvedHost = Get-ResolvedHost -PreferredHost $HostName
Write-Output "Running smoke checks against $resolvedHost"

$serviceHealths = @(
  "http://$resolvedHost`:8001/health",
  "http://$resolvedHost`:8002/health",
  "http://$resolvedHost`:8003/health",
  "http://$resolvedHost`:8004/health",
  "http://$resolvedHost`:8005/health",
  "http://$resolvedHost`:8006/health",
  "http://$resolvedHost`:8007/health"
)

foreach ($uri in $serviceHealths) {
  Assert-Status200 -Uri $uri
}

Assert-Status200 -Uri "http://$resolvedHost`:8007/"
Assert-Status200 -Uri "http://$resolvedHost`:8007/api/summary"
Assert-Status200 -Uri "http://$resolvedHost`:8007/api/health-summary"

Write-Output "Smoke checks passed."
