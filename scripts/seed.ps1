param(
  [int]$Subjects = 4,
  [int]$Days = 30,
  [string]$Profile = "healthy"
)

Invoke-RestMethod -Method Post -Uri "http://localhost:8002/v1/simulate-all?subjects=$Subjects&days=$Days&profile=$Profile" | ConvertTo-Json -Depth 5
