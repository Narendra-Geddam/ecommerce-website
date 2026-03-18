# CI/CD + GitOps Integration Guide

Complete workflow guide for building, scanning, and deploying with Jenkins and ArgoCD.

---

## 🎯 Big Picture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Push-Based (Jenkins)                              │
│                                                                      │
│  Code Commit                                                         │
│      ↓                                                               │
│  1. Build Docker Images                                             │
│  2. Scan with Trivy                                                 │
│  3. Push to Docker Hub                                              │
│  4. Update Helm values (image tags)                                 │
│  5. Commit & Push to Git                                            │
│                                                                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    Git Repository Updated
                        (values.yaml)
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│                   Pull-Based (ArgoCD)                               │
│                                                                      │
│  1. Detect Git changes                                              │
│  2. Compare Git state with K8s state                                │
│  3. Sync Kubernetes cluster                                         │
│  4. Deploy new images                                               │
│  5. Monitor and report                                              │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                             ↓
                    Application Running
                    with Latest Images
```

---

## 📋 Prerequisites Checklist

### Infrastructure
- [ ] Kubernetes cluster running
- [ ] Docker Hub account with repository
- [ ] GitHub/GitLab repository

### Jenkins Setup
- [ ] Jenkins installed and running
- [ ] Required plugins: Pipeline, Git, Docker Pipeline
- [ ] Credentials configured:
  - [ ] `dockerhub-creds` (usernamePassword)
  - [ ] `github-credentials` (usernamePassword)
- [ ] Pipeline job created

### ArgoCD Setup
- [ ] ArgoCD installed in K8s
- [ ] GitHub repository connected
- [ ] Application manifest created
- [ ] ArgoCD accessible (UI)

### Git Repository
- [ ] Jenkinsfile in root
- [ ] helm-chart/ directory with Chart.yaml
- [ ] helm-chart/values.yaml with image configuration

---

## 🚀 Complete Workflow

### Step 1: Developer Commits Code

```bash
# Developer makes changes
git add .
git commit -m "Add new feature"
git push origin main
```

### Step 2: Jenkins Pipeline Triggered

**Option A: Polling (every 15 minutes)**
```
Git poll → Changes detected → Pipeline starts
```

**Option B: Webhook (instant)**
```
GitHub webhook → Jenkins webhook endpoint → Pipeline starts
```

**Triggered Stage:**
```groovy
// Jenkinsfile automatically triggered via SCM
```

### Step 3: Jenkins Build Process

#### 3a. Checkout Code
```
Repository cloned to Jenkins workspace
Branch: main
```

#### 3b. Build Docker Images (Parallel)
```bash
# Presentation service
docker build -t your-docker-id/ecommerce-presentation:123 presentation/

# Application service
docker build -t your-docker-id/ecommerce-application:123 application/
```

#### 3c. Security Scanning
```bash
# Scan both images with Trivy
trivy image --severity HIGH,CRITICAL your-docker-id/ecommerce-presentation:123
trivy image --severity HIGH,CRITICAL your-docker-id/ecommerce-application:123

# Generate JSON reports
# Archive reports in Jenkins artifacts
```

#### 3d. Push to Docker Hub
```bash
# Login to Docker Hub (using dockerhub-creds)
docker login -u your-username -p your-token

# Push versioned images
docker push your-docker-id/ecommerce-presentation:123
docker push your-docker-id/ecommerce-application:123

# Push latest tags
docker push your-docker-id/ecommerce-presentation:latest
docker push your-docker-id/ecommerce-application:latest
```

#### 3e. Update Helm Values
```bash
# Read current values.yaml
# Update image repositories and tags
nano helm-chart/values.yaml

# Updated file:
presentation:
  image:
    repository: your-docker-id/ecommerce-presentation
    tag: "123"
application:
  image:
    repository: your-docker-id/ecommerce-application
    tag: "123"
```

#### 3f. Commit and Push to Git
```bash
# Configure Git in Jenkins
git config user.email "jenkins@example.com"
git config user.name "Jenkins Pipeline"

# Commit changes
git add helm-chart/values.yaml
git commit -m "Update image tags to 123 [skip ci]"

# Push to repository
git push origin main

# Note: [skip ci] prevents webhook from triggering Jenkins again
```

### Step 4: ArgoCD Detects Changes

#### Detection Methods:

**A) Periodic Refresh (default: every 3 minutes)**
```
ArgoCD polls Git repository every 3 minutes
Detects: helm-chart/values.yaml changed
Status: Application marked as OutOfSync
```

**B) Git Webhook (instant)**
```
GitHub webhook → ArgoCD webhook endpoint
Instant detection of changes
Status: Immediately marked as OutOfSync
```

#### Sync Decision:
```
Check sync policy in Application manifest:
syncPolicy:
  automated:
    prune: true
    selfHeal: true

Decision: Auto-sync enabled → Sync immediately
```

### Step 5: ArgoCD Syncs Deployment

#### 5a. Get Latest Helm Chart from Git
```bash
git clone https://github.com/your-username/your-repo.git
cd helm-chart
```

#### 5b. Template Helm Chart
```bash
helm template ecommerce-app . \
  --values values.yaml \
  --namespace default
```

**Generated Kubernetes manifest includes:**
```yaml
spec:
  containers:
  - image: your-docker-id/ecommerce-presentation:123
  - image: your-docker-id/ecommerce-application:123
```

#### 5c. Compare with Cluster State
```
Git State (desired):
  Pod with image:123

Cluster State (actual):
  Pod with image:120

Difference detected: Restart pods with new image
```

#### 5d. Apply Changes to Cluster
```bash
# ArgoCD runs kubectl apply internally
kubectl apply -f helm-chart/manifests/

# Old pods:120 → Terminated
# New pods:123 → Created and started
```

### Step 6: Kubernetes Cluster Updates

```
1. Old pods (image:120)
   ├─ Marked for termination
   └─ Graceful shutdown (30 sec)

2. New pods (image:123)
   ├─ Image pulled from Docker Hub
   ├─ Container started
   ├─ Health checks run
   └─ Ready to serve traffic

3. Services updated
   ├─ Endpoint updated to new pod IPs
   └─ Traffic flows to new pods

4. Old pods terminated
   └─ Cleanup complete
```

### Step 7: Monitoring and Verification

#### Check ArgoCD Status
```bash
# Via CLI
argocd app get ecommerce-app

# Output:
# Status: Synced
# Health: Healthy

# Via UI
# Applications → ecommerce-app
# Shows green checkmarks for Sync and Health
```

#### Check Kubernetes Pods
```bash
# View pods
kubectl get pods -n default

# Check logs
kubectl logs -n default -l app=ecommerce-application

# Port forward to test
kubectl port-forward -n default svc/ecommerce-presentation 8080:80
# Access: http://localhost:8080
```

#### Monitor Deployment
```bash
# Watch pod status
kubectl get pods -n default -w

# Check deployment events
kubectl describe deployment ecommerce-application -n default

# View resource usage
kubectl top pods -n default
```

---

## 📊 Real Example Flow

### Timeline:

```
10:00:00 → Developer pushes code
           git push origin main

10:00:05 → GitHub webhook triggers Jenkins
           "Build #123 started"

10:00:10 → Jenkins Stage 1: Checkout
           "Cloned repository"

10:05:00 → Jenkins Stages 2-4: Build & Scan
           "Built images, scanned for vulnerabilities"

10:08:30 → Jenkins Stage 5: Push
           "Pushed presentation:123 and application:123 to Docker Hub"

10:10:00 → Jenkins Stage 6: Update & Commit
           "Updated values.yaml with tag 123"
           "Committed and pushed to Git"

10:10:05 → GitHub webhook detected values.yaml change
           But [skip ci] prevents Jenkins re-trigger

10:10:10 → ArgoCD webhook notified of Git change (instant)
           Application marked as OutOfSync

10:10:15 → ArgoCD starts sync
           "Pulling Helm chart from Git"
           "Comparing with cluster state"

10:10:30 → ArgoCD deployment starts
           "Terminating pods with image:120"
           "Creating pods with image:123"

10:11:00 → New pods healthy
           "Deployment completed successfully"

10:11:05 → Rollout complete
           "ecommerce-app running with image:123"
           "All endpoints healthy"
```

**Total time:** ~11 minutes (build: 8-10 min, ArgoCD sync: 1-2 min)

---

## 🔄 GitOps Benefits

### 1. **Declarative Infrastructure**
- Git is source of truth
- Diff shows exact changes
- Easy to audit and review

### 2. **Automatic Sync**
- No manual deployments needed
- ArgoCD ensures cluster matches Git
- Automatic recovery from drift

### 3. **Easy Rollback**
```bash
# Rollback to previous Git commit
git revert [commit-hash]
git push origin main

# ArgoCD syncs automatically
# Application rolls back in 1-2 minutes
```

### 4. **Multi-Cluster Deployment**
- Single Git repo
- Multiple ArgoCD instances
- Consistent deployments across clusters

### 5. **Audit Trail**
- All changes in Git history
- Who changed what and when
- Why (commit message)

### 6. **PR-based Deployments**
```
Feature branch (dev)
    ↓ (PR review)
Main branch (production-ready)
    ↓ (auto-deploy via ArgoCD)
Running in production
```

---

## 🛡️ When to Use Manual Sync

Some scenarios require manual approval:

```yaml
# Production sync policy
syncPolicy:
  automated: null  # Disable auto-sync

# Manual promotions required:
# 1. Merge to main
# 2. Review changes in ArgoCD UI
# 3. Manually approve sync
# 4. ArgoCD deploys
```

**Manual Sync Command:**
```bash
# Review what will change
kubectl diff -f helm-chart/

# Manually sync
argocd app sync ecommerce-app

# Rollback if needed
argocd app rollback ecommerce-app 1
```

---

## 🔐 Security Considerations

### 1. Credentials
- [x] Docker Hub token (read/write scope)
- [x] GitHub token (repo scope)
- [x] K8s credentials not in Git

### 2. Git Repository Protection
```
Settings → Branches → Branch Protection
├─ Require pull request reviews
├─ Require status checks to pass
├─ Require branches to be up to date
└─ Allow force pushes: OFF
```

### 3. ArgoCD Security
```
RBAC:
├─ Admin only for sync approvals
├─ Developers read-only for monitoring
└─ CI/CD service account limited permissions
```

### 4. Image Signing (Optional)
```bash
# Sign images before push
docker trust sign your-docker-id/ecommerce-application:123

# Verify signature in ArgoCD
# Reject unsigned images
```

---

## 📈 Monitoring Dashboard

### Jenkins Metrics
```
Build Success Rate:  95%
Average Build Time:  9 minutes
Failed Stage:        Push (network)
```

### ArgoCD Metrics
```
Application Status:      Synced
Health Status:           Healthy
Last Sync:               2 minutes ago
Sync Success Rate:       99%
```

### Application Metrics
```
Pods Ready:              3/3
Memory Usage:            512Mi/1Gi
CPU Usage:               250m/500m
Requests/sec:            120
Error Rate:              0.1%
```

---

## 🐛 Troubleshooting Matrix

| Issue | Cause | Solution |
|-------|-------|----------|
| Build fails | Docker image error | Check Dockerfile, build locally |
| Push fails | Registry auth error | Verify dockerhub-creds credential |
| Git push fails | Git auth error | Verify github-credentials credential |
| OutOfSync | Git not synced | Run `argocd app sync` or wait 3 min |
| Pods not running | Image pull error | Check image exists in Docker Hub |
| ArgoCD can't access Git | Auth failed | Verify GitHub token has repo scope |

---

## ✅ Success Criteria

Pipeline working when:
- ✅ Jenkins builds succeed
- ✅ Images appear in Docker Hub
- ✅ Git commits are created
- ✅ ArgoCD detects changes
- ✅ Pods are updated with new images
- ✅ Application serves traffic
- ✅ No manual intervention needed

---

## 🎓 Next Steps

1. **Setup Phase** (2 hours)
   - [ ] Configure Jenkins credentials
   - [ ] Configure ArgoCD
   - [ ] Create ArgoCD Application

2. **Testing Phase** (1 hour)
   - [ ] Run first pipeline build
   - [ ] Verify Docker Hub push
   - [ ] Monitor ArgoCD sync
   - [ ] Check pod updates

3. **Optimization Phase** (ongoing)
   - [ ] Setup Git webhook (real-time)
   - [ ] Add email/Slack notifications
   - [ ] Implement approval gates
   - [ ] Add performance monitoring

4. **Production Phase**
   - [ ] Backup and DR plan
   - [ ] Security audit
   - [ ] Team training
   - [ ] Documentation

---

## 📚 Quick Reference

```bash
# Jenkins pipeline run
jenkins-cli build ecommerce-gitops-pipeline -s

# Check Docker Hub
docker pull your-docker-id/ecommerce-application:123

# Check Git commits
git log --oneline | head -5

# Check ArgoCD
argocd app get ecommerce-app
kubectl get application -n argocd

# Check K8s deployment
kubectl get pods,svc -n default

# Monitor in real-time
kubectl get pods -n default -w
```

---

**Read:** JENKINS_GITOPS_SETUP.md for detailed Jenkins configuration
**Read:** ARGOCD_SETUP.md for detailed ArgoCD configuration
