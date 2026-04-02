./scripts/init.ps1
Start-Sleep -Seconds 8
./scripts/seed.ps1 -Subjects 2 -Days 3 -Profile healthy
Start-Sleep -Seconds 8
Invoke-RestMethod -Method Get -Uri "http://localhost:8003/v1/cohorts/top-risk?limit=5" | ConvertTo-Json -Depth 5
