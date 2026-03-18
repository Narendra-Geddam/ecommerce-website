# EKS Deployment Guide - E-Commerce Application

## Prerequisites

### 1. AWS Account & EKS Cluster Setup

```bash
# Create EKS cluster (if not already created)
eksctl create cluster \
  --name ecommerce \
  --version 1.28 \
  --region us-east-1 \
  --nodegroup-name ecommerce-nodes \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed \
  --with-oidc

# Configure kubectl context
aws eks update-kubeconfig \
  --region us-east-1 \
  --name ecommerce

# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

### 2. Install AWS Load Balancer Controller

```bash
# Create IAM policy for ALB controller
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.0/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam-policy.json

# Create IAM role and service account
eksctl create iamserviceaccount \
  --cluster=ecommerce \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::ACCOUNT_ID:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Install ALB controller via Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=ecommerce \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set vpcId=vpc-XXXXXXXXX \
  --set region=us-east-1

# Verify ALB controller
kubectl get deployment -n kube-system aws-load-balancer-controller
```

### 3. Configure Storage Class (EBS)

```bash
# EBS storage class should be available by default in EKS
# Verify with:
kubectl get storageclasses

# If not present, create it:
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp2
provisioner: ebs.csi.aws.com
allowVolumeExpansion: true
parameters:
  type: gp2
  iops: "3000"
  throughput: "125"
  deleteOnTermination: "true"
EOF
```

### 4. Install Metrics Server (for HPA)

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify
kubectl get deployment -n kube-system metrics-server
```

### 5. Configure Docker Pull Secrets

```bash
# Create Docker registry secret for pulling images
kubectl create secret docker-registry docker-hub-secret \
  --docker-server=docker.io \
  --docker-username=usernamenarendra \
  --docker-password=Narendra@143 \
  --docker-email=your-email@example.com \
  -n ecommerce
```

## Deployment Steps

### Step 1: Create Namespace

```bash
kubectl apply -f k8s/01-namespace.yaml

# Verify
kubectl get namespace ecommerce
```

### Step 2: Create Secrets & Configuration

```bash
# Create secrets
kubectl apply -f k8s/02-secrets.yaml

# Create ConfigMap and RBAC
kubectl apply -f k8s/03-configmap-rbac.yaml

# Verify
kubectl get secrets -n ecommerce
kubectl get configmaps -n ecommerce
kubectl get serviceaccounts -n ecommerce
```

### Step 3: Create Services

```bash
kubectl apply -f k8s/04-services.yaml

# Verify
kubectl get svc -n ecommerce
```

### Step 4: Deploy PostgreSQL Database

```bash
# Deploy PostgreSQL StatefulSet
kubectl apply -f k8s/06-statefulset-postgres.yaml

# Wait for database to be ready (may take 2-3 minutes)
kubectl wait --for=condition=ready pod -l app=postgres -n ecommerce --timeout=300s

# Verify PostgreSQL is running
kubectl get pods -n ecommerce -l app=postgres
kubectl logs -n ecommerce -l app=postgres

# Initialize database schema (if needed)
# Port forward to database
kubectl port-forward svc/postgres 5432:5432 -n ecommerce &

# Connect and run schema
psql -h localhost -U ecommerce -d ecommerce < data/schema.sql
```

### Step 5: Deploy Application & Presentation Tiers

```bash
# Deploy backend (Flask application)
# Deploy frontend (Nginx presentation)
kubectl apply -f k8s/05-deployments.yaml

# Wait for deployments to be ready
kubectl wait --for=condition=available --timeout=300s deployment/application -n ecommerce
kubectl wait --for=condition=available --timeout=300s deployment/presentation -n ecommerce

# Verify deployments
kubectl get deployments -n ecommerce
kubectl get pods -n ecommerce
```

### Step 6: Configure Ingress (ALB)

```bash
# Update Ingress manifest with your specific values:
# - ACM certificate ARN
# - Domain name
# - Account ID for target group ARN

# Apply ingress
kubectl apply -f k8s/07-ingress-alb.yaml

# Get ALB DNS name (may take 2-3 minutes)
kubectl get ingress -n ecommerce -w

# Extract DNS name
ALB_DNS=$(kubectl get ingress ecommerce-alb-ingress -n ecommerce -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "ALB DNS: $ALB_DNS"

# Add DNS record to Route53 (if using domain)
# Or test via ALB DNS directly
```

### Step 7: Apply Network Policies & Quotas

```bash
kubectl apply -f k8s/08-policies-rbac-quotas.yaml

# Verify
kubectl get networkpolicies -n ecommerce
kubectl get resourcequota -n ecommerce
kubectl get limitrange -n ecommerce
kubectl get hpa -n ecommerce
```

## Verification Steps

### Test Application Connectivity

```bash
# Test backend health
kubectl exec -it deployment/presentation -n ecommerce -- \
  curl -s http://application:8000/health | jq .

# Test database connectivity
kubectl exec -it deployment/application -n ecommerce -- \
  python -c "import pg; conn = pg.connect(os.getenv('DATABASE_URL')); print('DB connected')"

# Test frontend
kubectl exec -it deployment/presentation -n ecommerce -- \
  curl -s http://localhost/
```

### Check Logs

```bash
# Application logs
kubectl logs -n ecommerce -l app=application -f

# Presentation (Nginx) logs
kubectl logs -n ecommerce -l app=presentation -f

# Database logs
kubectl logs -n ecommerce -l app=postgres -f
```

### Monitor Pod Status

```bash
# Watch pod status in real-time
kubectl get pods -n ecommerce -w

# Describe pod for events
kubectl describe pod <pod-name> -n ecommerce

# Check resource usage
kubectl top pods -n ecommerce
kubectl top nodes
```

### Test via ALB

```bash
# Get ALB DNS name
ALB_DNS=$(kubectl get ingress ecommerce-alb-ingress -n ecommerce -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test endpoints
curl -H "Host: ecommerce.example.com" http://$ALB_DNS/
curl -H "Host: ecommerce.example.com" http://$ALB_DNS/api/products
curl -H "Host: ecommerce.example.com" http://$ALB_DNS/health
```

## Port Forwarding (for local testing)

```bash
# Access Presentation frontend
kubectl port-forward svc/presentation 8080:80 -n ecommerce

# Access Application backend
kubectl port-forward svc/application 8000:8000 -n ecommerce

# Access PostgreSQL database
kubectl port-forward svc/postgres 5432:5432 -n ecommerce

# Open in browser: http://localhost:8080
```

## Scaling & High Availability

### Manual Scaling

```bash
# Scale presentation tier
kubectl scale deployment presentation --replicas=5 -n ecommerce

# Scale application tier
kubectl scale deployment application --replicas=5 -n ecommerce

# Verify
kubectl get deployment -n ecommerce
```

### HPA Configuration

HPA is already configured in `08-policies-rbac-quotas.yaml` with:
- Min replicas: 3
- Max replicas: 10
- CPU target: 70%
- Memory target: 80%

Monitor HPA:
```bash
kubectl get hpa -n ecommerce -w
kubectl describe hpa presentation-hpa -n ecommerce
```

## Troubleshooting

### Pod Pending

```bash
# Check pod events
kubectl describe pod <pod-name> -n ecommerce

# Check resource availability
kubectl describe nodes

# Common causes: insufficient CPU/memory, storage not bound
```

### Ingress not getting IP/DNS

```bash
# Check ALB controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Check ingress status
kubectl describe ingress ecommerce-alb-ingress -n ecommerce

# Common causes: ALB controller not running, IAM permissions missing
```

### Database connection failures

```bash
# Test database connectivity from application pod
kubectl exec -it deployment/application -n ecommerce -- bash
psql $DATABASE_URL

# Check PostgreSQL pod logs
kubectl logs -l app=postgres -n ecommerce

# Common causes: database not ready, incorrect credentials, network policy blocking
```

### Image pull errors

```bash
# Verify Docker credentials secret exists
kubectl get secret docker-registry -n ecommerce

# Check pod events for pull errors
kubectl describe pod <pod-name> -n ecommerce

# Common causes: incorrect credentials, image not found in registry
```

## Cleanup

```bash
# Delete all resources in ecommerce namespace
kubectl delete namespace ecommerce

# Delete EKS cluster (if needed)
eksctl delete cluster --name ecommerce --region us-east-1

# Remove ALB controller
helm uninstall aws-load-balancer-controller -n kube-system

# Delete IAM role and policy
aws iam delete-policy --policy-arn arn:aws:iam::ACCOUNT_ID:policy/AWSLoadBalancerControllerIAMPolicy
```

## Production Checklist

- [ ] ACM certificate configured and ARN added to ingress
- [ ] Domain name configured and DNS records created
- [ ] Secrets properly secured (not in version control)
- [ ] Database backups scheduled
- [ ] Monitoring and logging configured (CloudWatch/Prometheus)
- [ ] Autoscaling configured and tested
- [ ] Network policies reviewed and applied
- [ ] Resource quotas reviewed based on workload
- [ ] Container security scanning completed
- [ ] HA testing performed (pod disruption)
- [ ] Disaster recovery plan documented
- [ ] Cost optimization reviewed (instance types, storage)

## Next Steps

1. Configure ArgoCD in `argocd` namespace
2. Point ArgoCD to Git repository with K8s manifests
3. Enable automatic sync for GitOps workflow
4. Setup CI/CD pipeline in Jenkins
5. Configure monitoring with Prometheus/Grafana
6. Setup logging with ELK or CloudWatch
