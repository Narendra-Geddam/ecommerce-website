# ArgoCD Setup Guide - GitOps Deployment

This guide covers installing and configuring ArgoCD for pull-based GitOps deployment of the e-commerce application.

---

## 🎯 What is ArgoCD?

**ArgoCD** is a declarative GitOps tool that:
- Watches your Git repository for changes
- Automatically syncs Kubernetes cluster to match Git state
- Provides centralized UI for deployment management
- Enables multi-cluster deployments
- Maintains audit trail of all deployments

**Why use ArgoCD with our pipeline?**
```
Jenkins (Push-based):          ArgoCD (Pull-based):
Code → Build → Registry        Git Repository (desired state)
                                    ↓ (ArgoCD watches)
                              K8s Cluster (actual state)
                                    ↑ (ArgoCD syncs)
```

---

## 📋 Prerequisites

- Kubernetes cluster (1.16+)
- kubectl configured
- Git repository with Helm chart
- Access to Docker Hub

---

## 🚀 Step 1: Install ArgoCD

### Via Helm (Recommended)

```bash
# Add ArgoCD Helm repository
helm repo add argocd https://argoproj.github.io/argo-helm
helm repo update

# Create namespace
kubectl create namespace argocd

# Install ArgoCD
helm install argocd argocd/argo-cd \
  --namespace argocd \
  --set server.service.type=LoadBalancer \
  --wait
```

### Via Kustomize (Alternative)

```bash
# Create namespace
kubectl create namespace argocd

# Apply official ArgoCD manifests
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Patch service to LoadBalancer
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
```

### Verify Installation

```bash
# Check ArgoCD pods are running
kubectl get pods -n argocd

# Check services
kubectl get svc -n argocd

# Get ArgoCD server service IP/hostname
kubectl get svc argocd-server -n argocd
```

---

## 🔐 Step 2: Access ArgoCD UI

### Get Initial Admin Password

```bash
# Retrieve auto-generated password
PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d)

echo "Username: admin"
echo "Password: $PASSWORD"
```

### Port Forward (Local Access)

```bash
# Forward ArgoCD server port to localhost
kubectl port-forward -n argocd svc/argocd-server 8080:443

# Access: https://localhost:8080
# Username: admin
# Password: [from above]
```

### External Access (Production)

```bash
# Get LoadBalancer IP/hostname
kubectl get svc argocd-server -n argocd

# Or configure Ingress
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server
  namespace: argocd
spec:
  rules:
  - host: argocd.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              number: 443
EOF
```

---

## 🔑 Step 3: Configure Git Repository Access

ArgoCD needs access to your GitHub/GitLab repository.

### Option A: HTTPS (Token-based)

```bash
# Get GitHub personal access token (Settings → Developer settings → Personal access tokens)
# Token should have 'repo' and 'admin:repo_hook' scopes

GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
REPO_URL="https://github.com/your-username/your-repo.git"

# Add repository to ArgoCD via UI:
# 1. Settings → Repositories → Connect Repo Using HTTPS
# 2. Repository URL: $REPO_URL
# 3. Username: your-github-username
# 4. Password: $GITHUB_TOKEN
# 5. Click Connect

# Or via CLI:
argocd repo add $REPO_URL \
  --username your-github-username \
  --password $GITHUB_TOKEN \
  --insecure-skip-server-verification
```

### Option B: SSH (Key-based, Recommended)

```bash
# Generate SSH key
ssh-keygen -t ed25519 -f ~/.ssh/argocd -N ""

# Add public key to GitHub
# Settings → Deploy keys → Add deploy key
# Paste contents of ~/.ssh/argocd.pub

# Configure in ArgoCD
argocd repo add git@github.com:your-username/your-repo.git \
  --ssh-private-key-path ~/.ssh/argocd \
  --insecure-ignore-host-key
```

### Verify Repository Connection

```bash
# List connected repositories
argocd repo list

# Output should show your repository with status "Successful"
```

---

## 📦 Step 4: Create ArgoCD Application

### Option A: Via UI

1. **Open ArgoCD UI**
   - Login with admin credentials
   - Click **+ NEW APP**

2. **Application Settings**
   - Application Name: `ecommerce-app`
   - Project: `default`

3. **Source Settings**
   - Repository URL: `https://github.com/your-username/your-repo.git`
   - Revision: `main` (or your branch)
   - Path: `helm-chart`

4. **Deployment Settings**
   - Destination: `https://kubernetes.default.svc`
   - Namespace: `default`

5. **Sync Policy**
   - Check: **Auto-Sync** → **Automatic**
   - Check: **Prune Resources**
   - Check: **Self Heal**

6. **Create Application**
   - Click **CREATE**

### Option B: Via kubectl

```bash
# Apply the Application manifest
kubectl apply -f argocd/application.yaml
```

---

## 🔄 Step 5: Jenkins and ArgoCD Integration

### Jenkins Workflow

1. **Jenkins builds and pushes images to Docker Hub**
   ```
   Build #123
   → ecommerce-presentation:123
   → ecommerce-application:123
   ```

2. **Jenkins updates Helm values.yaml with new image tags**
   ```yaml
   presentation:
     image:
       repository: your-docker-id/ecommerce-presentation
       tag: "123"
   application:
     image:
       repository: your-docker-id/ecommerce-application
       tag: "123"
   ```

3. **Jenkins commits and pushes to Git repository**
   ```
   Commit: "Update image tags to 123 [skip ci]"
   Branch: main
   ```

4. **ArgoCD detects changes (within 3 minutes or on webhook)**
   ```
   Git Repository Updated
   → ArgoCD syncs
   → K8s deployments updated
   → New pods with new images start
   ```

### Git Webhook Setup (Optional - for instant sync)

**GitHub:**
1. Repository → Settings → Webhooks → Add webhook
2. Payload URL: `http://argocd-server/api/webhook`
3. Events: Push events
4. Click Add webhook

**Result:** ArgoCD syncs immediately on Git push

---

## 📊 Step 6: Monitor Deployments

### Via ArgoCD UI

```
Applications → ecommerce-app
├── Sync Status: Synced ✓
├── Health Status: Healthy ✓
├── Sync Policy: Auto-Sync
└── Resource Tree: (shows pods, services, etc.)
```

### Via CLI

```bash
# Get application status
argocd app get ecommerce-app

# Sync application
argocd app sync ecommerce-app

# Refresh from Git
argocd app refresh ecommerce-app

# View application history
argocd app history ecommerce-app

# Rollback to previous sync
argocd app rollback ecommerce-app 1
```

### Via kubectl

```bash
# Watch ArgoCD Application object
kubectl get application -n argocd -w

# Get detailed info
kubectl describe application ecommerce-app -n argocd

# View pod status
kubectl get pods -n default

# Stream logs
kubectl logs -n default -l app=ecommerce-application -f
```

---

## 🔐 Step 7: Security Configuration

### Change Admin Password

```bash
# Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)
echo "New password: $NEW_PASSWORD"

# Update secret
kubectl patch secret argocd-secret -n argocd \
  -p '{"data": {"admin.password": "'$(echo -n $NEW_PASSWORD | base64)'"}}'

# Update password hash
# (Requires ArgoCD password hashing utility - typically done in UI)
```

### Create RBAC Accounts for CI/CD

```bash
# Create policy for Jenkins to trigger syncs
cat > /tmp/argocd-rbac.yaml <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: argocd-jenkins
rules:
- apiGroups: ["argoproj.io"]
  resources: ["applications"]
  verbs: ["get", "list", "patch"]
- apiGroups: ["argoproj.io"]
  resources: ["applications/sync"]
  verbs: ["create"]
EOF

kubectl apply -f /tmp/argocd-rbac.yaml
```

### Network Policy for ArgoCD

```bash
# Restrict ArgoCD communication
kubectl apply -f argocd/argocd-network-policy.yaml
```

---

## 🔄 Syncing Strategies

### Auto-Sync (Recommended for Development)
```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```
**Behavior:** ArgoCD automatically syncs on Git changes

### Manual Sync (Recommended for Production)
```yaml
syncPolicy:
  automated: null  # Remove automated section
```
**Behavior:** Requires manual approval via UI or CLI

### Scheduled Sync
```yaml
syncPolicy:
  syncInterval: 1h
```
**Behavior:** Syncs periodically (recovery from manual drift)

---

## 🚨 Troubleshooting

### Issue: Application shows "OutOfSync"

**Cause:** Git state differs from cluster state

**Solution:**
```bash
# Option 1: Manually sync
argocd app sync ecommerce-app

# Option 2: Force sync (destructive - re-creates resources)
argocd app sync ecommerce-app --force

# Option 3: Check what's different
kubectl diff -f <(helm template ecommerce-app ./helm-chart)
```

### Issue: Sync fails with "permission denied"

**Cause:** ArgoCD can't access Git repository

**Solution:**
```bash
# Verify repository credentials
argocd repo list

# Re-authenticate repository
argocd repo rm https://github.com/your-username/your-repo.git
argocd repo add https://github.com/your-username/your-repo.git \
  --username your-username \
  --password your-token
```

### Issue: Pods not starting after sync

**Cause:** Image pull error or resource issue

**Solution:**
```bash
# Check pod status
kubectl describe pod -n default [pod-name]

# Check logs
kubectl logs -n default [pod-name]

# Check image exists in Docker Hub
docker pull your-docker-id/ecommerce-application:123
```

### Issue: ArgoCD server not accessible

**Cause:** Service not properly exposed

**Solution:**
```bash
# Check service
kubectl get svc -n argocd argocd-server

# If not LoadBalancer, expose it
kubectl patch svc argocd-server -n argocd \
  -p '{"spec": {"type": "LoadBalancer"}}'

# Or use port-forward
kubectl port-forward -n argocd svc/argocd-server 8080:443
```

---

## 📁 Project Structure with ArgoCD

```
your-repo/
├── Jenkinsfile                    # CI/CD pipeline
├── argocd/
│   └── application.yaml          # ArgoCD Application manifest
├── helm-chart/
│   ├── Chart.yaml
│   ├── values.yaml               # ← Jenkins updates this
│   ├── values-dev.yaml
│   ├── values-staging.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── _helpers.tpl
├── application/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
└── presentation/
    ├── Dockerfile
    ├── nginx.conf
    └── index.html
```

---

## 🔄 Full CI/CD + GitOps Workflow

```
1. Developer commits code
   ↓
2. GitHub webhook triggers Jenkins
   ↓
3. Jenkins:
   a) Builds Docker images
   b) Scans with Trivy
   c) Pushes to Docker Hub
   d) Updates Helm values
   e) Commits to Git
   ↓
4. GitHub webhook triggers ArgoCD
   ↓
5. ArgoCD:
   a) Pulls latest values from Git
   b) Compares with cluster state
   c) Syncs Kubernetes cluster
   d) Deploys new images
   ↓
6. Application running with new version
```

---

## 📊 Monitoring & Alerts

### View Application Metrics

```bash
# Get sync count
kubectl get application ecommerce-app -n argocd \
  -o jsonpath='{.status.sync.revision}'

# Get health status
kubectl get application ecommerce-app -n argocd \
  -o jsonpath='{.status.health.status}'

# Get last sync time
kubectl get application ecommerce-app -n argocd \
  -o jsonpath='{.status.operationState.finishedAt}'
```

### Configure Alerts (Optional)

**Slack Integration:**
```bash
# Enable notifications plugin in ArgoCD
helm upgrade argocd argocd/argo-cd \
  --namespace argocd \
  --set notifications.enabled=true
```

---

## ✅ Verification Checklist

Before going live:

- [ ] ArgoCD installed successfully
- [ ] Connected to Git repository
- [ ] Application created and synced
- [ ] Pods are running with correct images
- [ ] Services are accessible
- [ ] Jenkins can push commits to Git
- [ ] ArgoCD auto-sync working
- [ ] Rollback tested
- [ ] Alerts configured (optional)
- [ ] Backup/DR plan documented

---

## 📚 Reference

- [ArgoCD Official Docs](https://argo-cd.readthedocs.io/)
- [ArgoCD Application CRD](https://argo-cd.readthedocs.io/en/stable/user-guide/application-specification/)
- [Helm + ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/helm/)
- [RBAC Authorization](https://argo-cd.readthedocs.io/en/stable/operator-manual/rbac/)

---

**Next:** Configure Jenkins credentials for Git push (see JENKINS_ARGOCD_SETUP.md)
