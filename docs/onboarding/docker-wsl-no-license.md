# Docker Without Docker Desktop License (WSL Engine)

This setup uses Docker Engine in Ubuntu WSL2, not Docker Desktop runtime/sign-in.

## What is used
- Docker Engine: Ubuntu package (`docker`, `dockerd`)
- Compose: Docker Compose plugin in Ubuntu
- OpenPulse orchestration: `docker compose` run inside WSL against `/mnt/c/Users/grump/OpenPulse`

## One-time checks
```powershell
wsl -d Ubuntu -- docker version
wsl -d Ubuntu -- docker compose version
```

## Run OpenPulse
```powershell
Copy-Item .env.example .env
./scripts/openpulse-up-wsl.ps1
./scripts/openpulse-status-wsl.ps1
```

## Programmatic operations
```powershell
# Docker command passthrough to WSL engine
./scripts/wsl-docker.ps1 ps

# Compose passthrough to WSL engine
./scripts/wsl-compose.ps1 ps
./scripts/wsl-compose.ps1 logs -f query-api
```

## Seed data
```powershell
$wslIp = (wsl -d Ubuntu -- hostname -I).Trim().Split(' ')[0]
Invoke-RestMethod -Method Post -Uri "http://$wslIp`:8002/v1/simulate-all?subjects=2&days=7&profile=healthy"
```

## Stop stack
```powershell
./scripts/openpulse-down-wsl.ps1
```

## Notes
- In this mode, service URLs use the current WSL IP (printed by status scripts).
- If WSL restarts, IP can change.
- If you later switch back to Docker Desktop, run Desktop and use existing `scripts/init.ps1`/`scripts/smoke.ps1` flow.
