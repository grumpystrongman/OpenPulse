# Local Deployment Guide

## Prerequisites
- Option A: Docker Desktop (with Compose v2)
- Option B: Ubuntu WSL2 with Docker Engine + Docker Compose plugin (no Docker Desktop license/sign-in path)
- Python 3.11+

## First run
### Option A: Docker Desktop
```powershell
Copy-Item .env.example .env
./scripts/init.ps1
./scripts/seed.ps1 -Subjects 3 -Days 7 -Profile healthy
./scripts/smoke.ps1
```

### Option B: WSL Docker Engine (no Docker Desktop license)
```powershell
Copy-Item .env.example .env
./scripts/openpulse-up-wsl.ps1
./scripts/openpulse-status-wsl.ps1
```

`openpulse-up-wsl.ps1` prints the current WSL IP and all service URLs.

## Demo credentials
- Grafana: `admin` / `admin`
- MinIO Console: `openpulse` / `openpulse123`

## Reset environment
### Option A
```powershell
./scripts/reset.ps1
```

### Option B
```powershell
./scripts/openpulse-down-wsl.ps1
```

## Query data quickly
### Option A
```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8003/v1/observations?limit=20"
```

### Option B
```powershell
$wslIp = (wsl -d Ubuntu -- hostname -I).Trim().Split(' ')[0]
Invoke-RestMethod -Method Get -Uri "http://$wslIp`:8003/v1/observations?limit=20"
```
