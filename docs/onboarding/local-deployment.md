# Local Deployment Guide

## Prerequisites
- Docker Desktop (with Compose v2)
- Python 3.11+

## First run
```powershell
Copy-Item .env.example .env
./scripts/init.ps1
./scripts/seed.ps1 -Subjects 3 -Days 7 -Profile healthy
./scripts/smoke.ps1
```

## Demo credentials
- Grafana: `admin` / `admin`
- MinIO Console: `openpulse` / `openpulse123`

## Reset environment
```powershell
./scripts/reset.ps1
```

## Query data quickly
```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8003/v1/observations?limit=20"
```
