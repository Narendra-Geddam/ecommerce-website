# Kubernetes Manifests - Reference Guide

**Status:** ⚠️ **Deprecated for deployment** — Use Helm (`../helm-chart/`) instead  
**Purpose:** Educational reference — understand individual K8s resources

---

## Overview

This directory contains individual Kubernetes manifest files as **learning examples**. They show how different K8s components work together.

For **production deployment**, use **Helm** (`../helm-chart/`).

## Directory Structure

```
k8s/
├── 01-namespace.yaml                  # Namespace: prod-ecommerce
├── 02-configmaps.yaml                 # App config + DB init SQL
├── 03-secrets.yaml                    # K8s secrets (placeholder)
├── 04-services.yaml                   # postgres, flask-api, nginx services
├── 05-statefulset-postgres.yaml       # PostgreSQL with PVC
├── 06-deployments.yaml                # Flask (3x) + Nginx (3x)
├── 07-ingress.yaml                    # ALB ingress routing
├── 09-external-secrets-setup.yaml     # External Secrets + SecretStores
├── kustomization.yaml                 # Kustomize orchestration
└── README.md                          # This file
```

## What Each File Does

| File | Type | Shows | Count |
|------|------|-------|-------|
| `01-namespace.yaml` | Namespace | Isolated environment | 1 |
| `02-configmaps.yaml` | ConfigMaps | Configuration management | 2 |
| `03-secrets.yaml` | Secrets | Credential storage | 1 |
| `04-services.yaml` | Services | Internal networking | 3 |
| `05-statefulset-postgres.yaml` | StatefulSet | Stateful workload | 1 |
| `06-deployments.yaml` | Deployments | Stateless workloads | 2 |
| `07-ingress.yaml` | Ingress | External routing (ALB) | 1 |
| `09-external-secrets-setup.yaml` | ExternalSecrets | AWS integration | 3 |

## Learning: Understanding K8s Resources

### Namespace (01-namespace.yaml)
Groups related resources in isolated environment:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prod-ecommerce
```

### ConfigMaps (02-configmaps.yaml)
Stores non-sensitive config:
- App environment: FLASK_ENV, DEBUG
- Database init SQL with product data

### Secrets (03-secrets.yaml)
Stores sensitive data (overridden by External Secrets):
- Database credentials
- Application secret key

### Services (04-services.yaml)
Internal networking between pods:
- PostgreSQL (ClusterIP :5432)
- Flask API (ClusterIP :5000)
- Nginx frontend (LoadBalancer :80)

### StatefulSet (05-statefulset-postgres.yaml)
Persistent database:
- 1 replica
- Persistent volume for data
- Liveness/readiness probes

### Deployments (06-deployments.yaml)
Scalable applications:
- Flask API: 3 replicas
- Nginx frontend: 3 replicas
- Auto-restart on failure

### Ingress (07-ingress.yaml)
External routing via AWS ALB:
- `/` → Nginx (port 80)
- `/api` → Flask (port 5000)

### External Secrets (09-external-secrets-setup.yaml)
AWS integration:
- ServiceAccount with IRSA
- SecretStore for AWS Secrets Manager
- SecretStore for Parameter Store
- ExternalSecrets to sync values

## Manual Deployment (Not Recommended)

If you need to deploy without Helm (for learning):

```bash
# All at once
kubectl apply -k k8s/

# Or step by step
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-configmaps.yaml
kubectl apply -f k8s/03-secrets.yaml
kubectl apply -f k8s/04-services.yaml
kubectl apply -f k8s/05-statefulset-postgres.yaml
kubectl apply -f k8s/06-deployments.yaml
kubectl apply -f k8s/07-ingress.yaml
kubectl apply -f k8s/09-external-secrets-setup.yaml
```

## Recommended: Use Helm

For deployment, use Helm (covers all these files automatically):

```bash
# Deploy everything
helm install ecommerce ../helm-chart -n prod-ecommerce --create-namespace

# Update
helm upgrade ecommerce ../helm-chart -n prod-ecommerce

# Remove
helm uninstall ecommerce -n prod-ecommerce
```

See `../helm-chart/README.md` for details.

## Verification

```bash
# Check all resources
kubectl get all -n prod-ecommerce

# Check External Secrets status
kubectl get externalsecrets -n prod-ecommerce -o wide

# View pod logs
kubectl logs -n prod-ecommerce -l app=flask-api
```

## Key Concepts Demonstrated

#### StatefulSets vs Deployments
- **StatefulSet** (PostgreSQL): Persistent identity + storage
- **Deployment** (Flask, Nginx): Stateless + scalable

#### Service Types
- **ClusterIP**: Internal only (default)
- **LoadBalancer**: External access

#### External Secrets
Automatically syncs from AWS:
1. ServiceAccount with IRSA pulls from AWS
2. SecretStores connect to Secrets Manager/Parameter Store
3. ExternalSecrets watches and syncs
4. K8s pods get updated secrets

#### Ingress
Defines external routing:
- AWS ALB controller reads this
- Creates actual load balancer
- Routes traffic by path/hostname

---

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Chart](../helm-chart/README.md)
- [Main Setup Guide](../README.md)
- [Terraform Configuration](../terraform/)

```
┌─────────────────────────────────────────────────┐
│         AWS ALB (External Traffic)              │
└────────────────────┬────────────────────────────┘
                     │
         ┌───────────▼──────────────┐
         │  07-ingress.yaml         │
         │  (ecommerce-alb-ingress) │
         └───────────┬──────────────┘
                     │
      ┌──────────────┴──────────────┐
      │                             │
┌─────▼──────────────────┐   ┌──────▼──────────────────┐
│ 06-deployments.yaml    │   │ 04-services.yaml       │
├─────────────────────────┤   ├────────────────────────┤
│ nginx-frontend (3x)     │   │ Service: nginx-svc     │
│ flask-api (3x)          │   │ Service: flask-svc     │
└─────────────────────────┘   │ Service: postgres-svc  │
                              └────────┬───────────────┘
                                       │
                         ┌─────────────▼──────────┐
                         │ 05-statefulset.yaml    │
                         ├────────────────────────┤
                         │ postgres-db (1x)       │
                         │ Database: ecommerce    │
                         └────────────────────────┘

Supported by:
├─ 01-namespace.yaml (prod-ecommerce)
├─ 02-configmaps.yaml (config + init script)
├─ 03-secrets.yaml (credentials - replaces with 09-external-secrets)
└─ 09-external-secrets-setup.yaml (AWS integration)
```

## Next Steps

1. **Deploy:** `kubectl apply -k k8s/`
2. **Monitor:** `kubectl get pods -n prod-ecommerce -w`
3. **Access:** Get ALB DNS from ingress and open in browser
4. **Secrets:** Follow [WINDOWS_SETUP_GUIDE.md](../WINDOWS_SETUP_GUIDE.md) or [LINUX_MAC_SETUP_GUIDE.md](../LINUX_MAC_SETUP_GUIDE.md) for External Secrets setup

---

**Last Updated:** March 19, 2026  
**Kubernetes Version:** 1.21+  
**AWS Region:** eu-north-1  
**Namespace:** prod-ecommerce
