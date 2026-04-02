$wslIp = (wsl -d Ubuntu -- hostname -I).Trim().Split(' ')[0]
wsl -d Ubuntu -e sh -lc "cd /mnt/c/Users/grump/OpenPulse && docker compose ps"
Write-Output ""
Write-Output "Health checks via $wslIp"
$ports = 8001,8002,8003,8004,8005,8006,8007
foreach ($p in $ports) {
  try {
    $h = Invoke-RestMethod -Uri "http://$wslIp`:$p/health" -TimeoutSec 6
    Write-Output ("{0}: OK ({1})" -f $p, ($h.service))
  } catch {
    Write-Output ("{0}: DOWN" -f $p)
  }
}
