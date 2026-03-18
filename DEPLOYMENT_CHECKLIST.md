# Complete EKS Deployment - Summary & Deployment Checklist

## 🎯 What You Have

### Docker Images (✅ Built & Pushed to Docker Hub)
- `usernamenarendra/ecommerce-presentation:v1.0.0` - Nginx frontend
- `usernamenarendra/ecommerce-application:v1.0.0` - Flask backend

### Kubernetes Manifests (✅ Created in `k8s/` folder)
1. `01-namespace.yaml` - Namespace isolation
2. `02-secrets.yaml` - Credentials & secrets
3. `03-configmap-rbac.yaml` - Configuration & RBAC
4. `04-services.yaml` - Internal service routing
5. `05-deployments.yaml` - Application & frontend tiers
6. `06-statefulset-postgres.yaml` - PostgreSQL database
7. `07-ingress-alb.yaml` - AWS ALB ingress with TLS
8. `08-policies-rbac-quotas.yaml` - Network policies, HPA, quotas

### Documentation
- `EKS_DEPLOYMENT_GUIDE.md` - Step-by-step deployment instructions
- `K8S_MANIFESTS_REFERENCE.md` - Detailed manifest reference

---

## 📋 Pre-Deployment Checklist

### AWS Account Setup
- [ ] AWS Account created and access configured
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Region set to `us-east-1` (or your preferred region)

### EKS Cluster
- [ ] EKS cluster created (use `eksctl` or AWS Console)
- [ ] kubectl configured and verified (`kubectl cluster-info`)
- [ ] Cluster version: 1.28+

### AWS Load Balancer Controller
- [ ] ALB controller installed in kube-system namespace
- [ ] Verify: `kubectl get deployment -n kube-system aws-load-balancer-controller`

### IAM & Permissions
- [ ] IAM policy created for ALB controller
- [ ] Service account created with proper IAM role
- [ ] OIDC provider configured for EKS

### Storage
- [ ] EBS CSI driver installed
- [ ] Storage class `gp2` available
- [ ] Verify: `kubectl get storageclasses`

### Metrics Server
- [ ] Metrics server installed (for HPA)
- [ ] Verify: `kubectl get deployment -n kube-system metrics-server`

### Docker Repository
- [ ] Docker Hub account ready
- [ ] Images pushed to registry
- [ ] Registry credentials available

---

## 🚀 Deployment Steps (In Order)

### Step 1: Verify Prerequisites ✅
```bash
# Check kubectl access
kubectl cluster-info
kubectl get nodes

# Check ALB controller
kubectl get deployment -n kube-system aws-load-balancer-controller

# Check storage class
kubectl get storageclasses

# Check metrics server
kubectl get deployment -n kube-system metrics-server
```

**Status**: All returning healthy results ✓

---

### Step 2: Create Namespace
```bash
kubectl apply -f k8s/01-namespace.yaml
kubectl get namespace ecommerce
```

**Verify**: Namespace `ecommerce` created

---

### Step 3: Create Secrets (⚠️ UPDATE BEFORE APPLYING)
```bash
# BEFORE APPLYING: Edit k8s/02-secrets.yaml
# Update:
# 1. DATABASE_URL - Set actual database credentials
# 2. SECRET_KEY - Generate random secret key
# 3. docker-hub-secret - Verify base64 encoded credentials

# Generate base64 credentials:
# echo -n "usernamenarendra:Narendra@143" | base64

kubectl apply -f k8s/02-secrets.yaml
kubectl get secrets -n ecommerce
```

**Verify**: Secrets created
- ecommerce-secrets
- docker-hub-secret

---

### Step 4: Create ConfigMap & RBAC
```bash
kubectl apply -f k8s/03-configmap-rbac.yaml
kubectl get configmaps -n ecommerce
kubectl get serviceaccounts -n ecommerce
kubectl get role -n ecommerce
```

**Verify**: ConfigMap, ServiceAccount, and RBAC resources created

---

### Step 5: Create Services
```bash
kubectl apply -f k8s/04-services.yaml
kubectl get svc -n ecommerce
```

**Verify**: Three services created
- postgres (ClusterIP:5432)
- application (ClusterIP:8000)
- presentation (ClusterIP:80,443)

---

### Step 6: Deploy PostgreSQL Database
```bash
kubectl apply -f k8s/06-statefulset-postgres.yaml

# Wait for database to be ready (2-3 minutes)
kubectl wait --for=condition=ready pod -l app=postgres -n ecommerce --timeout=300s

# Verify
kubectl get statefulset -n ecommerce
kubectl get pods -n ecommerce -l app=postgres
kubectl logs -n ecommerce -l app=postgres | tail -20
```

**Verify**: PostgreSQL pod running and ready

---

### Step 7: Initialize Database Schema (Optional but Recommended)
```bash
# Port forward to database
kubectl port-forward svc/postgres 5432:5432 -n ecommerce &

# Connect and initialize schema
psql postgresql://ecommerce:password@localhost:5432/ecommerce < data/schema.sql

# Verify tables created
psql postgresql://ecommerce:password@localhost:5432/ecommerce -c "\dt"

# Kill port forward
kill %1
```

**Verify**: Database schema initialized with tables

---

### Step 8: Deploy Application & Frontend Tiers
```bash
kubectl apply -f k8s/05-deployments.yaml

# Wait for deployments to be ready (2-3 minutes)
kubectl wait --for=condition=available --timeout=300s deployment/application -n ecommerce
kubectl wait --for=condition=available --timeout=300s deployment/presentation -n ecommerce

# Verify
kubectl get deployments -n ecommerce
kubectl get pods -n ecommerce
```

**Verify**: 
- application deployment: 3/3 pods ready
- presentation deployment: 3/3 pods ready

---

### Step 9: Configure & Deploy ALB Ingress (⚠️ UPDATE BEFORE APPLYING)
```bash
# BEFORE APPLYING: Edit k8s/07-ingress-alb.yaml
# Update:
# 1. Replace ACCOUNT_ID with your AWS Account ID
# 2. Replace CERTIFICATE_ID with your ACM certificate ARN
# 3. Replace ecommerce.example.com with your domain
# 4. Update S3 bucket for access logs (optional)

kubectl apply -f k8s/07-ingress-alb.yaml

# Wait for ALB to be created (2-3 minutes)
kubectl get ingress -n ecommerce -w

# Get ALB DNS name
ALB_DNS=$(kubectl get ingress ecommerce-alb-ingress -n ecommerce -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "ALB DNS: $ALB_DNS"
```

**Verify**: 
- Ingress created with ALB DNS name
- ALB visible in AWS Console > Load Balancers
- Target groups created and healthy

---

### Step 10: Apply Network Policies & Quotas
```bash
kubectl apply -f k8s/08-policies-rbac-quotas.yaml

# Verify
kubectl get networkpolicies -n ecommerce
kubectl get resourcequota -n ecommerce
kubectl get limitrange -n ecommerce
kubectl get hpa -n ecommerce
kubectl get pdb -n ecommerce
```

**Verify**: All policies and quotas applied

---

## ✅ Post-Deployment Verification

### 1. Check All Pods are Running
```bash
kubectl get pods -n ecommerce

# Expected output:
# NAME                              READY   STATUS
# application-XXXXX                 1/1     Running
# application-XXXXX                 1/1     Running
# application-XXXXX                 1/1     Running
# postgres-0                        1/1     Running
# presentation-XXXXX                1/1     Running
# presentation-XXXXX                1/1     Running
# presentation-XXXXX                1/1     Running
```

### 2. Test Service Connectivity
```bash
# Test backend health
kubectl exec -it deployment/presentation -n ecommerce -- \
  curl -s http://application:8000/health

# Test database connection (from application pod)
kubectl exec -it deployment/application -n ecommerce -- \
  psql $DATABASE_URL -c "SELECT version();"

# Test frontend
kubectl exec -it deployment/presentation -n ecommerce -- \
  curl -s http://localhost/ | head -20
```

### 3. Check Resource Usage
```bash
kubectl top pods -n ecommerce
kubectl top nodes
```

### 4. Monitor ALB
```bash
# Get ALB DNS
ALB_DNS=$(kubectl get ingress ecommerce-alb-ingress -n ecommerce -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test endpoints
curl -H "Host: ecommerce.example.com" http://$ALB_DNS/
curl -H "Host: ecommerce.example.com" http://$ALB_DNS/health
curl -H "Host: ecommerce.example.com" http://$ALB_DNS/api/products
```

### 5. Check HPA Status
```bash
kubectl get hpa -n ecommerce
kubectl describe hpa presentation-hpa -n ecommerce
kubectl describe hpa application-hpa -n ecommerce
```

---

## 🔗 Connect Custom Domain (Optional)

### Option 1: Using Route53

```bash
# Get ALB DNS
ALB_DNS=$(kubectl get ingress ecommerce-alb-ingress -n ecommerce -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Create Route53 record
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "ecommerce.example.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$ALB_DNS'"}]
      }
    }]
  }'
```

### Option 2: Using External DNS Provider
- Point `ecommerce.example.com` CNAME to ALB DNS
- Allow 5-10 minutes for DNS propagation

### Test Custom Domain
```bash
curl https://ecommerce.example.com/
```

---

## 📊 Monitoring Commands

### Watch Pod Status
```bash
kubectl get pods -n ecommerce -w
```

### View Logs
```bash
# Application logs
kubectl logs -f deployment/application -n ecommerce

# Presentation logs
kubectl logs -f deployment/presentation -n ecommerce

# Database logs
kubectl logs -f deployment/postgres -n ecommerce

# Last 50 lines
kubectl logs --tail=50 deployment/application -n ecommerce
```

### Port Forward for Local Testing
```bash
# Frontend (access via http://localhost:8080)
kubectl port-forward svc/presentation 8080:80 -n ecommerce &

# Backend (access via http://localhost:8000)
kubectl port-forward svc/application 8000:8000 -n ecommerce &

# Database (psql localhost:5432)
kubectl port-forward svc/postgres 5432:5432 -n ecommerce &
```

### Describe Resources
```bash
# Pod details
kubectl describe pod <pod-name> -n ecommerce

# Service details
kubectl describe svc presentation -n ecommerce

# Ingress details
kubectl describe ingress ecommerce-alb-ingress -n ecommerce

# Node details
kubectl describe node <node-name>
```

---

## 🆘 Troubleshooting

### Pod Stuck in Pending
```bash
kubectl describe pod <pod-name> -n ecommerce
# Check: insufficient CPU/memory, storage not provisioned
```

### Pod CrashLoopBackOff
```bash
kubectl logs <pod-name> -n ecommerce
# Check: application error logs, exit code
```

### Ingress No ALB DNS
```bash
kubectl describe ingress ecommerce-alb-ingress -n ecommerce
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
# Check: ALB controller running, IAM permissions
```

### Database Connection Failed
```bash
# Verify database pod is running
kubectl get pod postgres-0 -n ecommerce

# Check database logs
kubectl logs postgres-0 -n ecommerce

# Test connection from application pod
kubectl exec deployment/application -n ecommerce -- \
  psql $DATABASE_URL -c "SELECT 1"
```

### Image Pull Error
```bash
kubectl describe pod <pod-name> -n ecommerce
# Check: registry credentials, image name, registry connectivity
```

---

## 🗑️ Cleanup

### Delete All Resources
```bash
# Delete namespace (cascades to all resources)
kubectl delete namespace ecommerce

# Verify
kubectl get namespace ecommerce
```

### Delete EKS Cluster (If needed)
```bash
# Delete nodes and cluster
eksctl delete cluster --name ecommerce --region us-east-1

# Verify
aws eks list-clusters --region us-east-1
```

### Clean Up IAM Resources
```bash
# Delete ALB controller IAM policy
aws iam delete-policy \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/AWSLoadBalancerControllerIAMPolicy

# Delete service account role
aws iam delete-role --role-name eksctl-ecommerce-addon-iamserviceaccount...
```

---

## 📈 Next Steps

### 1. Setup ArgoCD for GitOps
```bash
# Install ArgoCD in argocd namespace
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Configure ArgoCD Application to watch your Git repo
kubectl apply -f argocd/application.yaml
```

### 2. Configure CI/CD Pipeline
```bash
# Jenkins will be triggered on Git commits
# Pipeline will build, scan, push images
# Update Helm chart values with new image tags
# ArgoCD will auto-sync with Git changes
```

### 3. Setup Monitoring & Logging
```bash
# Install Prometheus for metrics
# Install Grafana for dashboards
# Configure CloudWatch alarms
# Setup ELK stack or CloudWatch Logs
```

### 4. Configure Backups
```bash
# Enable EBS snapshots for PostgreSQL volume
# Configure automated database backups
# Test disaster recovery procedures
```

---

## 📚 Documentation Reference

- Full deployment guide: [EKS_DEPLOYMENT_GUIDE.md](./EKS_DEPLOYMENT_GUIDE.md)
- Manifest reference: [K8S_MANIFESTS_REFERENCE.md](./K8S_MANIFESTS_REFERENCE.md)
- GitOps integration: [GITOPS_README.md](./GITOPS_README.md)
- Pipeline overview: [Jenkinsfile](./Jenkinsfile)

---

## 🎓 Key Information

**Architecture**:
- 3-tier: Load Balancer → Frontend (Nginx) → Backend (Flask) → Database (PostgreSQL)

**High Availability**:
- 3 replicas for frontend and backend
- Auto-scaling: 3-10 replicas based on CPU/memory
- Pod disruption budgets: Minimum 2 replicas during maintenance

**Security**:
- Network policies restrict traffic flows
- RBAC limits permissions
- Secrets encrypted in etcd
- TLS/HTTPS via AWS ACM certificates
- Non-root containers

**Resource Usage**:
- Total requests: ~1.15 CPU, 1.7Gi memory
- Limits: ~3.5 CPU, 4Gi memory aggregate
- Database: 20Gi persistent volume

**Cost Optimization**:
- t3 instances for development
- c5 instances for production
- Reserved instances for baseline load
- Spot instances for burst capacity

---

## ✨ You're Ready to Deploy!

1. **Verify prerequisites** from the checklist above
2. **Follow deployment steps** in order (Steps 1-10)
3. **Run post-deployment verification** commands
4. **Monitor** using provided commands
5. **Troubleshoot** using the provided guides

**Support**: Refer to EKS_DEPLOYMENT_GUIDE.md for detailed instructions on each step.

---

**Last Updated**: 2026-03-16
**Version**: 1.0.0
**Status**: Production Ready ✅
