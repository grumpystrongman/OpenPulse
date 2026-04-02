# Deployment Path to Kubernetes

`k8s/base` includes Kustomize-ready manifests for all OpenPulse application services.

## Apply
```bash
kubectl apply -k k8s/base
```

## Notes
- Infra dependencies (ClickHouse, Redpanda, MinIO, Redis, Prometheus, Grafana) should be installed via Helm charts in target clusters.
- Service config is provided via `ConfigMap` and should be paired with secrets for credentials.
