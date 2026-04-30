# Ecommerce Helm Chart

Complete Kubernetes deployment package for the 3-tier e-commerce application using Helm.

---

## Quick Deploy

```bash
# Install
helm install ecommerce . -n prod-ecommerce --create-namespace

# Upgrade
helm upgrade ecommerce . -n prod-ecommerce

# Uninstall
helm uninstall ecommerce -n prod-ecommerce
```

---

## Chart Overview

**Chart Name:** ecommerce-app  
**Chart Version:** 0.1.0  
**App Version:** 1.0.0  
**Type:** Application

### Components

| Component | Type | Count | Purpose |
|-----------|------|-------|---------|
| Namespace | K8s Resource | 1 | Isolated environment |
| ServiceAccount | RBAC | 1 | IRSA for AWS access |
| ConfigMaps | Config | 2 | App config + DB init |
| Secrets | Secrets | 2 | Placeholder (External Secrets override) |
| Services | Network | 3 | postgres, flask-api, nginx-frontend |
| Flask Deployment | Workload | 1 | 3 replicas |
| Nginx Deployment | Workload | 1 | 3 replicas |
| PostgreSQL StatefulSet | Workload | 1 | 1 replica with PVC |
| Ingress | Network | 1 | ALB routing |
| ExternalSecrets | App-specific | 2 | AWS Secrets Manager + Parameter Store |
| SecretStores | App-specific | 2 | AWS integrations |

---

## Prerequisites

- Kubernetes 1.19+
- Helm 3+
- External Secrets Operator (v2.1.0+)
- Terraform (for AWS resources)
- IRSA configured for EKS

### Setup

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace

# Configure AWS credentials (via Terraform or IAM)
cd ../terraform
terraform apply
```

---

## Configuration

### Values File

All settings are in `values.yaml`:

```yaml
# Namespace
namespace:
  create: true
  name: prod-ecommerce

# Database
database:
  replicas: 1
  storage: 10Gi

# Application
application:
  flask:
    replicas: 3
  nginx:
    replicas: 3

# AWS
awsRegion: eu-north-1
```

### Override Values

```bash
# Using command line
helm install ecommerce . \
  --set database.storage=50Gi \
  --set application.flask.replicas=5

# Using file
helm install ecommerce . -f values-prod.yaml
helm upgrade ecommerce . -f custom-values.yaml
```

### Environment-Specific Files

- `values.yaml` - Default
- `values-dev.yaml` - Development (1 replica, low resources)
- `values-prod.yaml` - Production (3 replicas, high resources)

Usage:

```bash
# Development
helm install ecommerce . -f values-dev.yaml -n dev-ecommerce --create-namespace

# Production
helm install ecommerce . -f values-prod.yaml -n prod-ecommerce --create-namespace
```

---

## Deployment

### Install Chart

```bash
# Dry-run (preview)
helm install ecommerce . -n prod-ecommerce --dry-run

# Install
helm install ecommerce . -n prod-ecommerce --create-namespace

# Verify
helm list -n prod-ecommerce
helm status ecommerce -n prod-ecommerce
kubectl get all -n prod-ecommerce
```

### Upgrade

```bash
# Edit values.yaml
vim values.yaml

# Upgrade
helm upgrade ecommerce . -n prod-ecommerce

# Verify
helm status ecommerce -n prod-ecommerce
```

### Rollback

```bash
# List versions
helm history ecommerce -n prod-ecommerce

# Rollback to previous
helm rollback ecommerce -n prod-ecommerce

# Rollback to specific revision
helm rollback ecommerce 3 -n prod-ecommerce
```

### Uninstall

```bash
helm uninstall ecommerce -n prod-ecommerce
```

---

## Template Details

### namespace.yaml

Creates isolated namespace with labels.

```yaml
metadata:
  name: prod-ecommerce
  labels:
    app: ecommerce
    environment: production
```

### configmap.yaml

Application configuration and database initialization script.

```yaml
# App config
FLASK_ENV: production
DEBUG: "false"
LOG_LEVEL: INFO

# DB init script
init.sql: |
  -- Database schema and product data
```

### secret.yaml

Placeholder K8s secrets (External Secrets overrides).

```yaml
# These are overridden by External Secrets Operator
ecommerce-secrets:
  DATABASE_URL: (from AWS Secrets Manager)
  SECRET_KEY: (from AWS Secrets Manager)
  DOCKER_CONFIG: (from AWS Secrets Manager)
```

### rbac.yaml

IRSA service account and role bindings for AWS access.

```yaml
ServiceAccount:
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::593067253640:role/ecommerce-external-secrets-role
```

### services.yaml

Three services: PostgreSQL, Flask API, Nginx Frontend.

```yaml
- PostgreSQL: ClusterIP :5432
- Flask API: ClusterIP :5000
- Nginx Frontend: LoadBalancer :80
```

### deployments.yaml

Flask (3 replicas) and Nginx (3 replicas).

```yaml
Flask:
  image: your-registry/ecommerce-app:latest
  replicas: 3
  port: 5000

Nginx:
  image: your-registry/ecommerce-presentation:latest
  replicas: 3
  port: 80
```

### statefulset-postgres.yaml

PostgreSQL with persistent volume.

```yaml
StatefulSet:
  replicas: 1
  storage: 10Gi
  image: postgres:15-alpine
```

### ingress.yaml

AWS ALB ingress routing.

```yaml
Ingress:
  className: alb
  rules:
    - /: nginx-frontend (:80)
    - /api: flask-api (:5000)
```

### external-secrets.yaml

External Secrets configuration for AWS integration.

```yaml
SecretStores:
  - aws-secrets-store (Secrets Manager)
  - aws-parameter-store (Parameter Store)

ExternalSecrets:
  - ecommerce-secrets (sync from AWS)
  - ecommerce-params (sync from AWS)
```

---

## Testing

### Template Rendering

```bash
# See what Helm will deploy
helm template ecommerce . -n prod-ecommerce

# Save rendered manifests
helm template ecommerce . > rendered.yaml
```

### Validation

```bash
# Lint chart
helm lint .

# Validate generated manifests
helm template ecommerce . | kubectl apply -f - --dry-run=client
```

---

## Troubleshooting

### Chart Installation Issues

```bash
# Check Helm releases
helm list -n prod-ecommerce

# Get release details
helm get values ecommerce -n prod-ecommerce
helm get manifest ecommerce -n prod-ecommerce

# View release history
helm history ecommerce -n prod-ecommerce
```

### Pod Issues

```bash
# Check pods
kubectl get pods -n prod-ecommerce

# Pod status
kubectl describe pod <pod-name> -n prod-ecommerce

# Logs
kubectl logs <pod-name> -n prod-ecommerce
```

### External Secrets Issues

```bash
# Check ExternalSecrets
kubectl get externalsecrets -n prod-ecommerce -o wide

# Debug
kubectl describe externalsecret ecommerce-secrets -n prod-ecommerce
```

### Reset/Reload

```bash
# Uninstall and reinstall
helm uninstall ecommerce -n prod-ecommerce
helm install ecommerce . -n prod-ecommerce --create-namespace

# Clean PVCs (careful!)
kubectl delete pvc postgres-storage-0 -n prod-ecommerce
```

---

## Integration with ArgoCD

```yaml
# ArgoCD Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ecommerce-app
  namespace: argocd
spec:
  source:
    path: infra/kubernetes/helm
    repoURL: https://github.com/your-username/your-repo.git
    helm:
      releaseName: ecommerce-app
      valueFiles:
        - values.yaml
  destination:
    namespace: prod-ecommerce
    server: https://kubernetes.default.svc
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

---

## Customization

### Add New Templates

1. Create template in `templates/`:

```yaml
# templates/configmap-extra.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: extra-config
data:
  key: {{ .Values.extraConfig.value }}
```

2. Add values to `values.yaml`:

```yaml
extraConfig:
  value: "some-value"
```

3. Deploy:

```bash
helm upgrade ecommerce .
```

### Override Docker Images

```bash
helm upgrade ecommerce . \
  --set application.flask.image.repository=my-registry/my-app \
  --set application.flask.image.tag=v1.2.3
```

### Change Replicas

```bash
helm upgrade ecommerce . \
  --set application.flask.replicas=5 \
  --set application.nginx.replicas=5
```

---

## Backup & Restore

### Backup Helm Release

```bash
# Get values
helm get values ecommerce -n prod-ecommerce > backup-values.yaml

# Get manifests
helm get manifest ecommerce -n prod-ecommerce > backup-manifest.yaml
```

### Restore

```bash
helm install ecommerce . -f backup-values.yaml -n prod-ecommerce
```

---

## References

- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [External Secrets](https://external-secrets.io/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
