# Kubernetes Deployment Manifests - Quick Reference

## Overview

This document provides a quick reference for all Kubernetes manifest files used for deploying the e-commerce application on AWS EKS.

## Manifest Files Structure

### File Organization

```
k8s/
├── 01-namespace.yaml           # Namespace and cluster initialization
├── 02-secrets.yaml             # Secrets for DB credentials and Docker registry
├── 03-configmap-rbac.yaml      # Configuration and RBAC resources
├── 04-services.yaml            # Service definitions (ClusterIP)
├── 05-deployments.yaml         # Nginx (presentation) and Flask (application)
├── 06-statefulset-postgres.yaml # PostgreSQL database
├── 07-ingress-alb.yaml         # ALB ingress and TLS configuration
├── 08-policies-rbac-quotas.yaml # Network policies, quotas, HPA, PDB
```

### Deployment Order

Always apply manifests in this order:

1. `01-namespace.yaml` - Creates ecommerce namespace
2. `02-secrets.yaml` - Database and registry credentials
3. `03-configmap-rbac.yaml` - Application config and RBAC
4. `04-services.yaml` - Service definitions
5. `06-statefulset-postgres.yaml` - Database (deploy first for app dependencies)
6. `05-deployments.yaml` - Application and presentation tiers
7. `07-ingress-alb.yaml` - Ingress and routing
8. `08-policies-rbac-quotas.yaml` - Policies and autoscaling

## File Details

### 01-namespace.yaml
- **Purpose**: Create isolated namespace for all resources
- **Resources**: 1 Namespace
- **Key Settings**:
  - Name: `ecommerce`
  - Labels: Environment, Project metadata

### 02-secrets.yaml
- **Purpose**: Store sensitive data (encrypted in etcd)
- **Resources**: 2 Secrets
  1. `ecommerce-secrets` (Opaque) - Database URL, SECRET_KEY
  2. `docker-hub-secret` (docker.io) - Docker Hub registry credentials
- **Key Settings**:
  - DATABASE_URL: `postgresql://ecommerce:password@postgres:5432/ecommerce`
  - SECRET_KEY: Must be changed in production
  - Docker credentials: Base64 encoded

**IMPORTANT**: Update the following before applying:
- `DATABASE_URL` - Use Secrets Manager for production
- `SECRET_KEY` - Generate a strong random key
- Docker credentials - Encode actual Docker Hub credentials

### 03-configmap-rbac.yaml
- **Purpose**: Store non-sensitive configuration and RBAC permissions
- **Resources**: 3 resources
  1. ConfigMap `ecommerce-config` - Flask configuration
  2. ServiceAccount `ecommerce-sa` - Pod identity
  3. Role & RoleBinding - Permissions for service account
- **Key Settings**:
  - FLASK_ENV: production
  - DEBUG: false (must be false in production)
  - RBAC: Read-only access to configmaps, secrets, pods

### 04-services.yaml
- **Purpose**: Internal routing between pods
- **Resources**: 3 ClusterIP Services
  1. `postgres` (port 5432) - Internal database access
  2. `application` (port 8000) - Internal Flask API
  3. `presentation` (port 80/443) - Internal Nginx frontend
- **Key Settings**:
  - Type: ClusterIP (internal only)
  - Service discovery via DNS names
  - Session affinity for PostgreSQL

### 05-deployments.yaml
- **Purpose**: Deploy application and frontend tiers
- **Resources**: 2 Deployments
  1. **Presentation** (Nginx)
     - Replicas: 3 (configurable)
     - Image: usernamenarendra/ecommerce-presentation:v1.0.0
     - Probes: Liveness and Readiness for /
     - Security: Non-root user (101), read-only filesystem
     - Resources: Requests (100m CPU, 128Mi memory)
     - Anti-affinity: Prefer different nodes
  
  2. **Application** (Flask)
     - Replicas: 3 (configurable)
     - Image: usernamenarendra/ecommerce-application:v1.0.0
     - Probes: Liveness and Readiness for /health endpoint
     - Security: Non-root user (1000)
     - Resources: Requests (200m CPU, 256Mi memory)
     - Environment: ConfigMap and Secrets references
     - Anti-affinity: Prefer different nodes

- **Key Settings**:
  - RollingUpdate strategy with maxSurge=1, maxUnavailable=0
  - Health checks: 30s initial delay, 20s period
  - Security context: runAsNonRoot, allowPrivilegeEscalation=false

### 06-statefulset-postgres.yaml
- **Purpose**: Stateful deployment of PostgreSQL database
- **Resources**: 2 resources
  1. StatefulSet `postgres` - Database server
  2. ConfigMap `postgres-init-scripts` - Initialization SQL
- **Key Settings**:
  - Replicas: 1 (can be increased for HA)
  - Image: postgres:15-alpine
  - Storage: 20Gi EBS volume (gp2 storage class)
  - Probes: pg_isready for liveness/readiness
  - Security: Non-root user (999)
  - Initialization: Creates extensions (uuid-ossp, pg_trgm)

**IMPORTANT**: 
- Storage class must be set to `gp2` (AWS EBS default)
- For HA: Use managed RDS PostgreSQL instead
- Backup/restore procedures needed for production

### 07-ingress-alb.yaml
- **Purpose**: External access via AWS ALB with TLS
- **Resources**: 1 Ingress, 1 TLS Secret, 1 LoadBalancer Service
- **Key Settings**:
  - IngressClass: `alb`
  - Scheme: internet-facing
  - Target type: `ip`
  - Routes:
    - `/api/*` → application:8000
    - `/health` → application:8000
    - `/` → presentation:80
  - TLS: HTTPS redirect enabled
  - ALB annotations: Cross-zone LB, HTTP/2, XFF client port

**REQUIRED Updates**:
- Replace `ACCOUNT_ID` with your AWS Account ID
- Replace `CERTIFICATE_ID` with your ACM certificate ARN
- Replace `ecommerce.example.com` with your domain
- Update S3 bucket name for access logs (if enabled)

**AWS Prerequisites**:
- ACM certificate created for your domain
- Route53 hosted zone (if using custom domain)
- ALB controller installed (aws-load-balancer-controller)

### 08-policies-rbac-quotas.yaml
- **Purpose**: Network security, resource limits, and autoscaling
- **Resources**: 8 resources
  1. NetworkPolicy - Pod-to-pod and egress restrictions
  2. ResourceQuota - Namespace-level resource limits
  3. LimitRange - Pod/container resource defaults
  4. PodDisruptionBudget (2) - HA during maintenance
  5. HorizontalPodAutoscaler (2) - Auto-scaling based on metrics
- **Key Settings**:
  - Network: Allow presentation→application→database flows
  - Quotas: 10 CPU, 10Gi memory max per namespace
  - Pod limits: 50 max pods in namespace
  - HPA: Min 3, Max 10 replicas, 70% CPU target
  - PDB: Min 2 pods available during disruptions

## Application Flow

```
Internet
    ↓
  ALB (Ingress) [07]
    ↓
Presentation Service [04] → Nginx Pods [05]
    ↓
Application Service [04] → Flask Pods [05]
    ↓
Database Service [04] → PostgreSQL Pod [06]
```

## Environment Variables & Configuration

### Injected from ConfigMap
- FLASK_APP: app.py
- FLASK_ENV: production
- DEBUG: false
- LOG_LEVEL: INFO

### Injected from Secrets
- DATABASE_URL: Connection string for PostgreSQL
- SECRET_KEY: Flask encryption key

### Pod Environment
- FLASK_APP_SERVICE: Nginx → application hostname

## Resource Requirements

### Total Resource Requests (all running pods)

**CPU**:
- Presentation: 3 pods × 100m = 300m
- Application: 3 pods × 200m = 600m
- PostgreSQL: 1 pod × 250m = 250m
- **Total: ~1.15 CPU**

**Memory**:
- Presentation: 3 pods × 128Mi = 384Mi
- Application: 3 pods × 256Mi = 768Mi
- PostgreSQL: 1 pod × 512Mi = 512Mi
- **Total: ~1.7Gi**

### Recommended Node Configuration

For **development**:
- 3 × t3.medium (2 CPU, 4GB each)
- EBS: 20Gi for database, 10Gi for application logs

For **production**:
- 5-10 × c5.large (2 CPU, 4GB each) with autoscaling
- Multi-AZ deployment
- Managed RDS PostgreSQL
- EBS volumes with encryption

## Storage

### StatefulSet Volumes

**postgres-storage**: EBS PersistentVolumeClaim
- Size: 20Gi
- StorageClass: gp2
- AccessMode: ReadWriteOnce
- Mount point: /var/lib/postgresql/data

### Temporary Volumes

**presentation**: emptyDir for nginx cache/run
**application**: No persistent storage

## DNS & Service Discovery

### Internal DNS Names (within cluster)

```
postgres.ecommerce.svc.cluster.local:5432
application.ecommerce.svc.cluster.local:8000
presentation.ecommerce.svc.cluster.local:80
ecommerce-alb-ingress (hostname from ALB)
```

### External DNS

**ALB DNS Name** (auto-generated):
```
ecommerce-alb-XXXXXXXX.us-east-1.elb.amazonaws.com
```

**Custom Domain** (requires Route53):
```
CNAME: ecommerce.example.com → ALB DNS name
```

## Probes Configuration

### Liveness Probes
- Presentation: GET / on port 80 (15s initial, 20s period)
- Application: GET /health on port 8000 (30s initial, 20s period)
- PostgreSQL: pg_isready (30s initial, 10s period)

### Readiness Probes
- Presentation: GET / on port 80 (10s initial, 10s period)
- Application: GET /health on port 8000 (15s initial, 10s period)
- PostgreSQL: pg_isready (10s initial, 5s period)

## Security Considerations

### Applied Security Measures
1. **Network Policies**: Restrict traffic to required flows only
2. **RBAC**: Minimal permissions for service accounts
3. **Pod Security**: Non-root users, read-only filesystems
4. **Resource Limits**: Prevent resource exhaustion
5. **Secrets**: Encrypted storage for sensitive data
6. **TLS/HTTPS**: ALB with ACM certificates
7. **Image Pull Secrets**: Private registry authentication

### Additional Production Security
- [ ] Enable pod security policies
- [ ] Use network policies for all namespaces
- [ ] Implement security scanning in CI/CD (Trivy)
- [ ] Enable audit logging
- [ ] Use AWS KMS for etcd encryption
- [ ] Implement RBAC for all users
- [ ] Enable container runtime security (Falco)
- [ ] Regular security assessments

## Monitoring & Logging

### Metrics Available
- Pod CPU and memory usage (Metrics Server installed)
- HPA decisions (scaling events)
- ALB access logs (S3 bucket)
- Application logs (stdout/stderr)

### Commands for Monitoring

```bash
# View HPA status
kubectl get hpa -n ecommerce -w

# View resource usage
kubectl top pods -n ecommerce
kubectl top nodes

# View logs
kubectl logs -f deployment/application -n ecommerce
kubectl logs -f deployment/presentation -n ecommerce

# View events
kubectl get events -n ecommerce --sort-by='.lastTimestamp'
```

## Common Operations

### Update Image Version

```bash
kubectl set image deployment/application \
  flask=usernamenarendra/ecommerce-application:v1.0.1 \
  -n ecommerce

kubectl rollout status deployment/application -n ecommerce
```

### Scale Deployment

```bash
kubectl scale deployment presentation --replicas=5 -n ecommerce
```

### Execute Commands in Pod

```bash
kubectl exec -it pod/presentation-xxx -n ecommerce -- bash
```

### Port Forward

```bash
kubectl port-forward svc/application 8000:8000 -n ecommerce
```

### View Logs

```bash
kubectl logs -f deployment/application -n ecommerce --all-containers=true
```

## Troubleshooting Commands

```bash
# Check pod status
kubectl get pods -n ecommerce

# Describe pod for events
kubectl describe pod <pod-name> -n ecommerce

# Check service endpoints
kubectl get endpoints -n ecommerce

# Verify network connectivity
kubectl exec pod/application-xxx -n ecommerce -- \
  nc -zv postgres 5432

# Check resource quota usage
kubectl describe quota -n ecommerce

# View ingress details
kubectl describe ingress -n ecommerce
```

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS EKS User Guide](https://docs.aws.amazon.com/eks/)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [StatefulSet Best Practices](https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/)
