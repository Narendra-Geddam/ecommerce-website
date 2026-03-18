# Kubernetes Manifests - Complete List

All Kubernetes manifest files for EKS deployment are located in the `k8s/` directory.

## Manifest Files

### 1️⃣ Namespace & Foundation
**File**: `k8s/01-namespace.yaml`
**Resources**: 1 Namespace
**Purpose**: Create isolated namespace for all ecommerce resources
```
ecommerce
  └── Isolated namespace with RBAC boundaries
```

---

### 2️⃣ Secrets & Credentials
**File**: `k8s/02-secrets.yaml`
**Resources**: 2 Secrets
**Purpose**: Store sensitive data (encrypted)

```
Secrets:
├── ecommerce-secrets (Opaque)
│   ├── DATABASE_URL: PostgreSQL connection string
│   └── SECRET_KEY: Flask secret key
├── docker-hub-secret (docker.io)
    ├── .dockerconfigjson: Docker registry credentials
```

**⚠️ IMPORTANT**: Update before deploying:
- DATABASE_URL
- SECRET_KEY
- docker-hub-secret credentials

---

### 3️⃣ Configuration & RBAC
**File**: `k8s/03-configmap-rbac.yaml`
**Resources**: 3 (ConfigMap, ServiceAccount, Role, RoleBinding)
**Purpose**: Application configuration and access control

```
Resources:
├── ConfigMap: ecommerce-config
│   ├── FLASK_APP: app.py
│   ├── FLASK_ENV: production
│   ├── DEBUG: false
│   └── LOG_LEVEL: INFO
├── ServiceAccount: ecommerce-sa
├── Role: ecommerce-role
│   └── Permissions: read configmaps, secrets, pods
└── RoleBinding: ecommerce-rolebinding
```

---

### 4️⃣ Services (Internal Routing)
**File**: `k8s/04-services.yaml`
**Resources**: 3 Services (ClusterIP)
**Purpose**: Internal service discovery and routing

```
Services:
├── postgres (ClusterIP)
│   ├── Port: 5432
│   └── Selector: app=postgres
├── application (ClusterIP)
│   ├── Port: 8000
│   └── Selector: app=application
└── presentation (ClusterIP)
    ├── Ports: 80, 443
    └── Selector: app=presentation
```

---

### 5️⃣ Deployments (Frontend & Backend)
**File**: `k8s/05-deployments.yaml`
**Resources**: 2 Deployments
**Purpose**: Deploy application and presentation tiers

```
Deployments:
├── presentation (Nginx Frontend)
│   ├── Replicas: 3
│   ├── Image: usernamenarendra/ecommerce-presentation:v1.0.0
│   ├── Ports: 80, 443
│   ├── Health Checks: Liveness & Readiness on /
│   ├── Resources: 100m CPU, 128Mi memory (requests)
│   ├── Security: Non-root user (101), read-only FS
│   └── Anti-affinity: Spread across nodes
└── application (Flask Backend)
    ├── Replicas: 3
    ├── Image: usernamenarendra/ecommerce-application:v1.0.0
    ├── Port: 8000
    ├── Health Checks: Liveness & Readiness on /health
    ├── Resources: 200m CPU, 256Mi memory (requests)
    ├── Security: Non-root user (1000)
    ├── Environment: ConfigMap & Secrets injected
    └── Anti-affinity: Spread across nodes
```

---

### 6️⃣ Database (PostgreSQL StatefulSet)
**File**: `k8s/06-statefulset-postgres.yaml`
**Resources**: 2 (StatefulSet, ConfigMap)
**Purpose**: Stateful database deployment

```
Resources:
├── StatefulSet: postgres
│   ├── Replicas: 1
│   ├── Image: postgres:15-alpine
│   ├── Port: 5432
│   ├── Storage: 20Gi EBS (gp2)
│   ├── Mount: /var/lib/postgresql/data
│   ├── Health Checks: pg_isready
│   ├── Security: Non-root user (999)
│   └── Initialization: uuid-ossp, pg_trgm extensions
└── ConfigMap: postgres-init-scripts
    └── init.sql: Database initialization SQL
```

**Storage**: 
- PersistentVolumeClaim: 20Gi
- StorageClass: gp2 (AWS EBS)
- Backup: Manual snapshots required

---

### 7️⃣ Ingress (AWS ALB) & TLS
**File**: `k8s/07-ingress-alb.yaml`
**Resources**: 2 (Ingress, TLS Secret, Service)
**Purpose**: External access via Application Load Balancer

```
Resources:
├── Ingress: ecommerce-alb-ingress
│   ├── IngressClass: alb
│   ├── Scheme: internet-facing
│   ├── Routes:
│   │   ├── /api/* → application:8000
│   │   ├── /health → application:8000
│   │   └── / → presentation:80
│   ├── TLS: HTTPS redirect enabled
│   └── Annotations: Cross-zone LB, HTTP/2, security headers
├── Secret: ecommerce-tls-cert (TLS Certificate)
└── Service: ecommerce-alb-nlb (Optional NLB)
```

**Configuration**:
- ACM certificate ARN required
- Custom domain name required
- AWS account ID required

---

### 8️⃣ Network Policies, Quotas & HPA
**File**: `k8s/08-policies-rbac-quotas.yaml`
**Resources**: 8+ (NetworkPolicy, ResourceQuota, LimitRange, PDB, HPA)
**Purpose**: Security, resource limits, and autoscaling

```
Resources:
├── NetworkPolicy: ecommerce-network-policy
│   ├── Ingress: Allow pod-to-pod communication
│   └── Egress: Allow DNS, database, external APIs
├── ResourceQuota: ecommerce-quota
│   ├── CPU: 10 requests, 20 limits
│   ├── Memory: 10Gi requests, 20Gi limits
│   ├── Pods: 50 max
│   └── Services: 10 max
├── LimitRange: ecommerce-limits
│   ├── Pod limits: 50m-2 CPU, 64Mi-2Gi memory
│   └── Container defaults: 100m CPU, 128Mi memory
├── PodDisruptionBudget: presentation-pdb
│   └── Min available: 2 pods
├── PodDisruptionBudget: application-pdb
│   └── Min available: 2 pods
├── HorizontalPodAutoscaler: presentation-hpa
│   ├── Min: 3, Max: 10 replicas
│   ├── CPU target: 70%
│   └── Memory target: 80%
└── HorizontalPodAutoscaler: application-hpa
    ├── Min: 3, Max: 10 replicas
    ├── CPU target: 70%
    └── Memory target: 80%
```

---

## Deployment Architecture

```
Internet (External Traffic)
    │
    ▼
┌─────────────────────────┐
│   AWS Application       │
│   Load Balancer (ALB)   │  (07-ingress-alb.yaml)
│                         │
│ ┌─────────────────────┐ │
│ │ HTTPS (443) ◄──────┤─┼──TLS termination
│ │ HTTP (80)          │ │    (ACM Certificate)
│ └─────────────────────┘ │
└────────────┬────────────┘
             │
    ┌────────▼───────────────┐
    │  Rules/Routing         │
    │  ├─ /api/* → port 8000 │
    │  ├─ /health → port 8000│
    │  └─ / → port 80        │
    └────┬───────────────────┘
         │
    ┌────┴───────────────────────────┐
    │                                 │
    ▼                                 ▼
┌──────────────────┐     ┌──────────────────────┐
│  Presentation    │     │    Application       │
│ (04-services,    │     │  (04-services,       │
│  05-deployments) │     │   05-deployments)    │
│                  │     │                      │
│ ┌──────────────┐ │     │ ┌──────────────────┐ │
│ │ Nginx:80     │─┼─────┼─│ Flask:8000       │ │
│ ├──────────────┤ │     │ ├──────────────────┤ │
│ │ 3 Replicas   │ │     │ │ 3 Replicas       │ │
│ │ (HPA: 3-10)  │ │     │ │ (HPA: 3-10)      │ │
│ │              │ │     │ │                  │ │
│ │ Anti-affinity│ │     │ │ Anti-affinity    │ │
│ │ PDB: min 2   │ │     │ │ PDB: min 2       │ │
│ └──────────────┘ │     │ └────────┬─────────┘ │
└──────────────────┘     └─────────┬┘───────────┘
                                   │
                                   │(DATABASE_URL)
                                   │
                           ┌───────▼──────────┐
                           │  PostgreSQL DB   │
                           │ (06-statefulset) │
                           │                  │
                           │ ┌──────────────┐ │
                           │ │ postgres:5432│ │
                           │ ├──────────────┤ │
                           │ │ 1 Replica    │ │
                           │ │ (StatefulSet)│ │
                           │ │              │ │
                           │ │ 20Gi EBS Vol │ │
                           │ │ (gp2)        │ │
                           │ └──────────────┘ │
                           └──────────────────┘

Namespace: ecommerce (01-namespace.yaml)
Security: NetworkPolicy (08-policies-rbac-quotas.yaml)
RBAC: ServiceAccount, Role, RoleBinding (03-configmap-rbac.yaml)
Config: ConfigMap, Secrets (02-secrets.yaml, 03-configmap-rbac.yaml)
Quotas: ResourceQuota, LimitRange (08-policies-rbac-quotas.yaml)
```

---

## Resource Requirements Summary

### CPU Usage
```
Component          Requests    Limits      Replicas
────────────────────────────────────────────────────
Presentation       100m        500m        3 (HPA 3-10)
Application        200m        1000m       3 (HPA 3-10)
PostgreSQL         250m        2000m       1
────────────────────────────────────────────────────
Total (baseline)   1150m       3500m
Total (max HPA)    2150m       5500m
```

### Memory Usage
```
Component          Requests    Limits      Replicas
────────────────────────────────────────────────────
Presentation       128Mi       512Mi       3 (HPA 3-10)
Application        256Mi       1Gi         3 (HPA 3-10)
PostgreSQL         512Mi       2Gi         1
────────────────────────────────────────────────────
Total (baseline)   1.7Gi       3.5Gi
Total (max HPA)    3.0Gi       5.5Gi
```

### Storage
```
Component          Size        Type        AccessMode
────────────────────────────────────────────────────
PostgreSQL Volume  20Gi        gp2 EBS     ReadWriteOnce
Nginx Cache        emptyDir    Ephemeral   ReadWriteOnce
App Logs           emptyDir    Ephemeral   ReadWriteOnce
```

---

## Deployment Order

🔢 **Always follow this order**:

1. ✅ `01-namespace.yaml` → Creates namespace
2. ✅ `02-secrets.yaml` → Database credentials & registry auth
3. ✅ `03-configmap-rbac.yaml` → Configuration & permissions
4. ✅ `04-services.yaml` → Service definitions
5. ✅ `06-statefulset-postgres.yaml` → Database (before app)
6. ✅ `05-deployments.yaml` → Application tiers
7. ✅ `07-ingress-alb.yaml` → External access
8. ✅ `08-policies-rbac-quotas.yaml` → Policies & scaling

---

## Key Features Implemented

### ✅ High Availability
- 3 replicas for frontend and backend
- Pod disruption budgets (min 2 pods)
- Multi-zone spreading (anti-affinity)
- Horizontal pod autoscaling (3-10 replicas)

### ✅ Security
- Network policies (restrict traffic)
- RBAC (least privilege)
- Non-root containers
- Read-only root filesystem (presentation)
- TLS/HTTPS (ACM certificates)
- Secrets encryption (at-rest in etcd)

### ✅ Observability
- Health checks (liveness & readiness)
- Pod logs available via kubectl
- Metrics server for monitoring
- Resource quotas for namespace isolation
- Events tracking via kubectl

### ✅ Reliability
- Rolling updates (maxSurge=1, maxUnavailable=0)
- Health probes with configurable timeouts
- Service mesh ready (can add Istio)
- PersistentVolume for database
- StatefulSet for database ordering

### ✅ Scalability
- Horizontal pod autoscaling based on CPU/memory
- Load balancing via ALB
- Database ready for connection pooling
- Service discovery via DNS

---

## Next Steps

1. **Pre-deployment verification**: See DEPLOYMENT_CHECKLIST.md
2. **Deploy manifests**: Follow EKS_DEPLOYMENT_GUIDE.md
3. **Configure DNS**: Add Route53 CNAME or update domain registrar
4. **Monitor deployment**: Use provided kubectl commands
5. **Setup ArgoCD**: For GitOps continuous deployment
6. **Configure monitoring**: Add Prometheus/Grafana or CloudWatch

---

## Quick Reference Commands

```bash
# Apply all manifests in order
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-secrets.yaml
kubectl apply -f k8s/03-configmap-rbac.yaml
kubectl apply -f k8s/04-services.yaml
kubectl apply -f k8s/06-statefulset-postgres.yaml
kubectl apply -f k8s/05-deployments.yaml
kubectl apply -f k8s/07-ingress-alb.yaml
kubectl apply -f k8s/08-policies-rbac-quotas.yaml

# Watch deployment progress
kubectl get all -n ecommerce -w

# Check specific resources
kubectl get deployments -n ecommerce
kubectl get statefulsets -n ecommerce
kubectl get services -n ecommerce
kubectl get ingress -n ecommerce
kubectl get pods -n ecommerce

# View logs
kubectl logs -f deployment/application -n ecommerce
kubectl logs -f deployment/presentation -n ecommerce
kubectl logs -f pod/postgres-0 -n ecommerce

# Port forward for testing
kubectl port-forward svc/presentation 8080:80 -n ecommerce
kubectl port-forward svc/application 8000:8000 -n ecommerce
kubectl port-forward svc/postgres 5432:5432 -n ecommerce

# Monitor resources
kubectl top pods -n ecommerce
kubectl top nodes

# Delete all resources
kubectl delete namespace ecommerce
```

---

**Status**: ✅ All manifests created and ready for deployment
**Last Updated**: 2026-03-16
**Version**: 1.0.0
