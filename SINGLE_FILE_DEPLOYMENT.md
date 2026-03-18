# Single File Complete Deployment

## 📦 File: `ecommerce-complete.yaml`

Complete E-Commerce application deployment in a **single YAML file**. Contains everything:
- Namespace
- Secrets & ConfigMaps
- RBAC (ServiceAccount, Role, RoleBinding)
- Services (PostgreSQL, Application, Presentation)
- StatefulSet (PostgreSQL database)
- Deployments (Nginx frontend, Flask backend)
- Ingress (ALB)
- Network Policies
- Resource Quotas & Limits
- Pod Disruption Budgets
- Horizontal Pod Autoscalers (HPA)

## 🚀 Quick Start

### Prerequisites
```bash
# Ensure kubectl is configured for EKS
kubectl cluster-info

# Verify ALB controller is installed
kubectl get deployment -n kube-system aws-load-balancer-controller

# Check storage class exists
kubectl get storageclasses
# Should show: gp2 (default)
```

### Deploy Everything
```bash
# Apply single file with everything
kubectl apply -f ecommerce-complete.yaml

# Watch deployment progress
kubectl get all -n ecommerce -w
```

### Check Status
```bash
# Verify namespace
kubectl get namespace ecommerce

# Check all resources
kubectl get all -n ecommerce

# Expected:
# - 3 Presentation pods (Nginx)
# - 3 Application pods (Flask)
# - 1 PostgreSQL pod (postgres-0)
# - Services: postgres, application, presentation
# - Ingress: ecommerce-alb-ingress
```

### Get ALB DNS
```bash
# Get the ALB hostname (may take 2-3 minutes)
kubectl get ingress -n ecommerce -w

# Or directly:
kubectl get ingress ecommerce-alb-ingress -n ecommerce -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### Test Application
```bash
# Get ALB DNS
ALB_DNS=$(kubectl get ingress ecommerce-alb-ingress -n ecommerce -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test endpoints
curl http://$ALB_DNS/
curl http://$ALB_DNS/health
curl http://$ALB_DNS/api/products
```

## 📋 What's Included

### Namespace
- **ecommerce**: Isolated namespace for all resources

### Secrets (2)
- **ecommerce-secrets**: Database URL, SECRET_KEY
- **docker-hub-secret**: Docker registry credentials

### ConfigMaps (2)
- **ecommerce-config**: Flask configuration (FLASK_ENV, DEBUG, etc.)
- **postgres-init-scripts**: Database initialization SQL

### RBAC
- **ServiceAccount**: ecommerce-sa
- **Role**: Read-only permissions for configmaps, secrets, pods
- **RoleBinding**: Bind role to service account

### Services (3)
- **postgres**: ClusterIP:5432 (database)
- **application**: ClusterIP:8000 (Flask backend)
- **presentation**: ClusterIP:80,443 (Nginx frontend)

### Database
- **StatefulSet - postgres**:
  - 1 replica (can scale)
  - postgres:15-alpine image
  - 20Gi persistent volume (EBS gp2)
  - Health checks: pg_isready

### Deployments (2)

#### Presentation (Nginx Frontend)
- 3 replicas (auto-scales 3-10)
- Image: usernamenarendra/ecommerce-presentation:v1.0.0
- Port: 80
- CPU: 100m requests, 500m limits
- Memory: 128Mi requests, 512Mi limits
- Health: Liveness & Readiness on /

#### Application (Flask Backend)
- 3 replicas (auto-scales 3-10)
- Image: usernamenarendra/ecommerce-application:v1.0.0
- Port: 8000
- CPU: 200m requests, 1000m limits
- Memory: 256Mi requests, 1Gi limits
- Health: Liveness & Readiness on /health
- Environment: ConfigMap & Secrets injected

### Ingress
- **ALB Ingress**: ecommerce-alb-ingress
- Routes:
  - `/health` → application:8000
  - `/api/*` → application:8000
  - `/` → presentation:80

### Security & Policy
- **NetworkPolicy**: Restrict pod-to-pod traffic
- **ResourceQuota**: Namespace-level limits (10 CPU, 10Gi memory)
- **LimitRange**: Default container limits
- **PodDisruptionBudget**: Min 2 pods available
- **HorizontalPodAutoscaler**: Auto-scale based on CPU/memory (70%, 80%)

## ⚙️ Configuration

### Update Before Deploying

**1. Database Credentials** (line ~26-29)
```yaml
DATABASE_URL: "postgresql://ecommerce:password@postgres:5432/ecommerce"
SECRET_KEY: "your-production-secret-key-CHANGE-THIS"
```
Change `password` to actual secure password.

**2. Docker Registry** (line ~35-38)
```yaml
.dockerconfigjson: eyJhdXRocyI6eyJkb2NrZXIuaW8iOnsiYXV0aCI6InVzZXJuYW1lbmFyZW5kcmE6TmFyZW5kcmFAMTQzIn19fQ==
```
This is base64 encoded: `usernamenarendra:Narendra@143`

Generate new base64 if needed:
```bash
echo -n "your-docker-username:your-docker-password" | base64
```

**3. Image Tags** (lines ~387, ~492)
If using different image versions:
```yaml
image: usernamenarendra/ecommerce-presentation:v1.0.0
image: usernamenarendra/ecommerce-application:v1.0.0
```

**4. Database Password** (line ~183)
```yaml
POSTGRES_PASSWORD: "password"
```
Change to secure password (same as in DATABASE_URL).

## 💾 Modify & Reapply

### Update deployment with new image
```bash
kubectl set image deployment/application \
  flask=usernamenarendra/ecommerce-application:v1.0.1 \
  -n ecommerce
```

### Scale deployments
```bash
kubectl scale deployment presentation --replicas=5 -n ecommerce
kubectl scale deployment application --replicas=5 -n ecommerce
```

### Edit ConfigMap
```bash
kubectl edit configmap ecommerce-config -n ecommerce
```

### Re-apply with updates
```bash
kubectl apply -f ecommerce-complete.yaml
```

## 🔍 Troubleshooting

### Pods pending
```bash
kubectl describe pod <pod-name> -n ecommerce
# Check: insufficient resources, storage not provisioned
```

### View logs
```bash
kubectl logs -f deployment/application -n ecommerce
kubectl logs -f deployment/presentation -n ecommerce
kubectl logs -f pod/postgres-0 -n ecommerce
```

### Port forward
```bash
# Frontend
kubectl port-forward svc/presentation 8080:80 -n ecommerce

# Backend
kubectl port-forward svc/application 8000:8000 -n ecommerce

# Database
kubectl port-forward svc/postgres 5432:5432 -n ecommerce
```

### Check resource usage
```bash
kubectl top pods -n ecommerce
kubectl top nodes
```

## ✅ Verify Deployment

```bash
# 1. Check namespace
kubectl get namespace ecommerce

# 2. Check secrets & configs
kubectl get secrets -n ecommerce
kubectl get configmaps -n ecommerce

# 3. Check services
kubectl get svc -n ecommerce

# 4. Check deployments
kubectl get deploy -n ecommerce
# Should show 3/3 ready for presentation and application

# 5. Check database
kubectl get statefulset -n ecommerce
# Should show 1/1 ready

# 6. Check pods
kubectl get pods -n ecommerce
# Should show all pods in Running status

# 7. Check ingress
kubectl get ingress -n ecommerce
# Should show ALB DNS

# 8. Check HPA
kubectl get hpa -n ecommerce
# Should show current/desired replicas

# 9. Test connectivity
ALB_DNS=$(kubectl get ingress ecommerce-alb-ingress -n ecommerce -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$ALB_DNS/
```

## 🗑️ Delete Everything

```bash
# Delete namespace (cascades all resources)
kubectl delete namespace ecommerce

# Verify
kubectl get namespace ecommerce
# Should show: error
```

## 📊 Resource Summary

| Component | Requests | Limits |
|-----------|----------|--------|
| Presentation (3) | 300m / 384Mi | 1500m / 1536Mi |
| Application (3) | 600m / 768Mi | 3000m / 3Gi |
| PostgreSQL (1) | 250m / 512Mi | 2000m / 2Gi |
| **Total** | **1150m / 1.7Gi** | **6500m / 6.5Gi** |

## 🎯 Next Steps

1. **Deploy**: `kubectl apply -f ecommerce-complete.yaml`
2. **Wait**: 2-3 minutes for ALB creation
3. **Test**: Get ALB DNS and test endpoints
4. **Configure DNS**: Add Route53 CNAME or DNS record
5. **Monitor**: Watch logs and metrics
6. **Update Secrets**: Use AWS Secrets Manager in production
7. **Add monitoring**: Install Prometheus/Grafana or CloudWatch

---

**Single File Deployment**: Complete, self-contained, production-ready ✅
