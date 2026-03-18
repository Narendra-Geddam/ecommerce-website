# GitOps CI/CD Pipeline - Complete Implementation

Universal pipeline combining **push-based Jenkins CI** with **pull-based ArgoCD CD** for automated deployment to Kubernetes.

---

## 🎯 What You Get

### ✅ Fully Automated Workflow

```
Code → Build → Scan → Push → Git Update → ArgoCD Sync → Deploy
  ↓      ↓      ↓      ↓         ↓           ↓          ↓
Code  Images Security Docker   Source of  GitOps   Running
Push  Built  Checked  Hub      Truth    Deployment  App
```

### ✅ Two-Tier Architecture

| Component | Role | Technology |
|-----------|------|------------|
| **CI (Build)** | Build & push images | Jenkins + Docker |
| **Security** | Vulnerability scanning | Trivy |
| **Registry** | Image storage | Docker Hub |
| **Source of Truth** | Configuration | Git Repository |
| **CD (Deploy)** | Sync cluster to Git | ArgoCD |
| **Orchestration** | Container management | Kubernetes + Helm |

### ✅ GitOps Best Practices

- **Declarative:** Everything defined in Git
- **Automated:** No manual deployments
- **Auditable:** Full history in Git commits
- **Recoverable:** Easy rollback via Git
- **Safe:** Approval gates available

---

## 📁 Files Included

### Core Files
1. **[Jenkinsfile](Jenkinsfile)** - CI/CD pipeline definition
2. **[argocd/application.yaml](argocd/application.yaml)** - ArgoCD Application manifest
3. **[helm-chart/values.yaml](helm-chart/values.yaml)** - Kubernetes configuration
4. **[docker-compose.jenkins.yml](docker-compose.jenkins.yml)** - Local Jenkins setup

### Setup Guides
5. **[JENKINS_GITOPS_SETUP.md](JENKINS_GITOPS_SETUP.md)** - Jenkins credential configuration
6. **[ARGOCD_SETUP.md](ARGOCD_SETUP.md)** - ArgoCD installation and setup
7. **[GITOPS_INTEGRATION.md](GITOPS_INTEGRATION.md)** - Complete workflow guide
8. **[HELM_VALUES_EXAMPLES.md](HELM_VALUES_EXAMPLES.md)** - Environment-specific configs

### Automation Scripts
9. **[setup-k8s-prerequisites.sh](setup-k8s-prerequisites.sh)** - K8s resource automation

---

## 🚀 Quick Start (30 minutes)

### 1. Prerequisites (5 min)
```bash
# Verify requirements installed
docker --version
kubectl version --client
helm version
git --version
```

### 2. Jenkins Setup (10 min)
```bash
# Start Jenkins locally
docker-compose -f docker-compose.jenkins.yml up -d
# Access: http://localhost:8080/jenkins/

# Configure credentials (in Jenkins UI):
# 1. Manage Jenkins → Manage Credentials
# 2. Add dockerhub-creds (usernamePassword)
# 3. Add github-credentials (usernamePassword)
# 4. Create Pipeline Job pointing to Jenkinsfile
```

### 3. ArgoCD Setup (10 min)
```bash
# Install ArgoCD
kubectl create namespace argocd
helm repo add argocd https://argoproj.github.io/argo-helm
helm install argocd argocd/argo-cd -n argocd --wait

# Get password
kubectl get secret -n argocd argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# Access ArgoCD UI
kubectl port-forward -n argocd svc/argocd-server 8080:443
# Access: https://localhost:8080
```

### 4. Test Pipeline (5 min)
```bash
# Trigger first build
# Jenkins UI → ecommerce-gitops-pipeline → Build Now

# Monitor progress:
# Jenkins Console Output → Check all stages

# Verify results:
docker pull your-docker-id/ecommerce-application:1
git log --oneline | head -1  # See Git commit
argocd app get ecommerce-app  # Check ArgoCD sync
kubectl get pods -n default   # Check pods
```

---

## 🔄 How It Works

### The Flow

```
Developer commits code
         ↓
    GitHub webhook
         ↓
Jenkins Pipeline Starts (Build #123)
    ├─ Checkout code
    ├─ Build Docker images
    │  ├─ presentation:123
    │  └─ application:123
    ├─ Scan with Trivy
    ├─ Push to Docker Hub
    ├─ Update helm-chart/values.yaml
    │  └─ image tags = 123
    ├─ Commit to Git
    │  └─ "Update image tags to 123"
    └─ Push to GitHub
         ↓
    Git Repository Updated
         ↓
ArgoCD Detects Change
    ├─ Polls Git every 3 min (or via webhook)
    ├─ Pulls updated values.yaml
    ├─ Renders Helm templates
    ├─ Compares with cluster state
    └─ Starts sync
         ↓
Kubernetes Cluster Updated
    ├─ Old pods terminated
    ├─ New pods created (image:123)
    ├─ Health checks verify
    ├─ Traffic routed to new pods
    └─ Old pods cleaned up
         ↓
    Application Live!
```

---

## 🔑 Key Credentials

### Jenkins Requires
1. **dockerhub-creds** (usernamePassword)
   - User: Docker Hub username
   - Pass: Docker Hub personal access token
   - Used for: Pushing images

2. **github-credentials** (usernamePassword)
   - User: GitHub username
   - Pass: GitHub personal access token
   - Used for: Pushing Helm value updates

### How to Create

**Docker Hub Personal Access Token:**
1. hub.docker.com → Account Settings → Security
2. New Access Token → Copy token
3. Jenkins → Add credential → usernamePassword

**GitHub Personal Access Token:**
1. github.com → Settings → Developer settings → Tokens
2. New token (classic) → Scopes: `repo`
3. Jenkins → Add credential → usernamePassword

---

## 📊 Pipeline Stages Explained

| Stage | Duration | Purpose |
|-------|----------|---------|
| **1. Checkout** | 1-2 min | Clone Git repository |
| **2. Build** | 5-10 min | Build Docker images (parallel) |
| **3. Scan** | 3-5 min | Trivy vulnerability scanning |
| **4. Push** | 2-5 min | Push images to Docker Hub |
| **5. Update** | 1 min | Update Helm values.yaml |
| **6. Commit** | 1 min | Commit and push to Git |
| **7. ArgoCD Sync** | 2-5 min | ArgoCD deploys to cluster |
| **8. Verify** | 2-3 min | Check deployment health |
| **Total** | **15-25 min** | End to end |

---

## 🔄 What Gets Updated

### In Docker Hub
```
Before:
  your-docker-id/ecommerce-application:120

After (Build #123):
  your-docker-id/ecommerce-application:123
  your-docker-id/ecommerce-application:latest
```

### In Git Repository
```yaml
# helm-chart/values.yaml

Before:
  image:
    tag: "120"

After:
  image:
    tag: "123"
```

### In Kubernetes Cluster
```
Before:
  Pod: ecommerce-app-xyz123 (image:120)

After:
  Pod: ecommerce-app-abc456 (image:123)
```

---

## 📚 Documentation Map

```
START HERE
    ↓
├─ [Quick Start] - 30 minutes to first deployment
│  └─ GITOPS_INTEGRATION.md (complete workflow)
│
├─ [Setup Phase]
│  ├─ JENKINS_GITOPS_SETUP.md (credential configuration)
│  └─ ARGOCD_SETUP.md (install and configure ArgoCD)
│
├─ [Configuration]
│  └─ HELM_VALUES_EXAMPLES.md (dev/staging/prod configs)
│
├─ [Troubleshooting]
│  ├─ JENKINS_GITOPS_SETUP.md § Troubleshooting
│  ├─ ARGOCD_SETUP.md § Troubleshooting
│  └─ GITOPS_INTEGRATION.md § Troubleshooting Matrix
│
└─ [Automation]
   └─ setup-k8s-prerequisites.sh (automated K8s setup)
```

---

## 🎓 Reading Guide

### "I want to understand the overall architecture"
→ Read: [GITOPS_INTEGRATION.md](GITOPS_INTEGRATION.md)
(20 minutes, includes diagrams and timeline)

### "I want to set up Jenkins"
→ Read: [JENKINS_GITOPS_SETUP.md](JENKINS_GITOPS_SETUP.md)
(15 minutes, step-by-step credential setup)

### "I want to set up ArgoCD"
→ Read: [ARGOCD_SETUP.md](ARGOCD_SETUP.md)
(20 minutes, installation and configuration)

### "I want to deploy to multiple environments"
→ Read: [HELM_VALUES_EXAMPLES.md](HELM_VALUES_EXAMPLES.md)
(10 minutes, dev/staging/prod configurations)

### "Something is broken, help!"
→ Read: [GITOPS_INTEGRATION.md](GITOPS_INTEGRATION.md) § Troubleshooting Matrix
(5 minutes, common issues and solutions)

---

## ✅ Success Checklist

### Before You Start
- [ ] Kubernetes cluster accessible (kubectl working)
- [ ] Docker Hub account with repository
- [ ] GitHub account with repository
- [ ] Git configured locally
- [ ] Docker installed locally

### After Setup
- [ ] Jenkins running and accessible
- [ ] Docker Hub credentials configured
- [ ] GitHub credentials configured
- [ ] Pipeline job created
- [ ] First build succeeded

### After First Build
- [ ] Images pushed to Docker Hub
- [ ] Git commits created
- [ ] ArgoCD synced the deployment
- [ ] Pods are running
- [ ] Application is accessible

### Production Ready
- [ ] Pipeline runs reliably (85%+ success rate)
- [ ] Deployment time under 20 minutes
- [ ] Rollback tested and documented
- [ ] Team trained on the workflow
- [ ] Monitoring/alerts configured
- [ ] Backup procedures documented

---

## 🔐 Security Checklist

Before production:
- [ ] Credentials stored in Jenkins secure store (not in files)
- [ ] GitHub tokens limited to `repo` scope
- [ ] Docker Hub tokens limited to image push/pull
- [ ] Git branch protection enabled
- [ ] Commit signatures verified (optional)
- [ ] Container scanning (Trivy) blocking critical CVEs
- [ ] Pod security policies configured
- [ ] Network policies restricting pod communication
- [ ] RBAC limiting access to deployments
- [ ] Audit logging enabled for all deployments

---

## 📊 Monitoring & Observability

### What to Monitor

**Build Metrics:**
```bash
# Jenkins
Build success rate (target: >95%)
Average build time (target: <20 min)
Failed stages (remediate immediately)
```

**Deployment Metrics:**
```bash
# ArgoCD
Application sync status (should be: Synced)
Health status (should be: Healthy)
Last sync time (should be: <5 min ago)
Sync frequency (typically: 1 per hour)
```

**Application Metrics:**
```bash
# Kubernetes
Pod ready status (should be: 3/3)
Container restarts (should be: <1 per week)
Memory/CPU usage (should be: consistent)
Request latency (should be: <100ms)
Error rate (should be: <0.1%)
```

---

## 🚀 Advanced Features

### Multi-Cluster Deployment
```
Single Git repo + Multiple ArgoCD instances
= Consistent deployment across clusters
```

### Environment Promotion
```
Dev branch →[manual] Staging →[manual] Prod
(auto-deploy)        (auto-deploy)
```

### Approval Gates
```
# Production sync policy
syncPolicy:
  automated: null  # Disable auto-sync

# Manual approval required:
argocd app sync [--approval] ecommerce-app
```

### Notifications
```
Slack → #deployments
"✅ ecommerce-app synced to image:123"

Email → devops@company.com
"Deployment report: 3 pods updated"
```

---

## 🔄 Comparing with Traditional Deployment

### Traditional (Push-based)
```
Jenkins → Manual kubectl apply
       → Manual Helm install
       → No automatic rollback
       → Hard to track changes
```

### Modern (GitOps Pull-based)
```
Jenkins → Git → ArgoCD → Automatic sync
       → Full history in Git
       → One-command rollback
       → Everything traceable
```

---

## 📈 Roadmap

### Phase 1: Basic GitOps (This Setup)
- ✅ CI/CD pipeline with Jenkins
- ✅ SecurityScanning with Trivy
- ✅ ArgoCD GitOps deployment
- ✅ Auto-sync from Git

### Phase 2: Enhanced Workflow (Next)
- [ ] Multi-environment promotion (dev→staging→prod)
- [ ] Approval gate for production
- [ ] Blue-green deployments
- [ ] Automated rollback on health check failure

### Phase 3: Advanced Features
- [ ] Canary deployments (with Flagger)
- [ ] Cost optimization (Kubecost)
- [ ] Multi-cluster management (ArgoCD ApplicationSet)
- [ ] Policy enforcement (OPA/Kyverno)

### Phase 4: Observability
- [ ] Distributed tracing (Jaeger)
- [ ] Metrics collection (Prometheus)
- [ ] Log aggregation (ELK Stack)
- [ ] Dashboards (Grafana)

---

## 💡 Pro Tips

### 1. Use Immutable Tags
```
❌ Don't: image:latest
✅ Do: image:build-123 or image:v1.2.3
```

### 2. Git Commits Must Be Atomic
```
Each commit = one logical change
makes it easy to revert if needed
```

### 3. Monitor the Sync
```
# Watch ArgoCD in real-time
kubectl get application -n argocd ecommerce-app -w
```

### 4. Practice Rollbacks
```
# You should be able to rollback in <5 minutes
git revert [commit-hash]
git push origin main
# ArgoCD syncs automatically
```

### 5. Keep Values Files Simple
```
Don't hardcode complex logic in values.yaml
Keep YAML simple and readable
```

---

## 🎯 Next Steps

1. **Read** → [GITOPS_INTEGRATION.md](GITOPS_INTEGRATION.md) (understand workflow)
2. **Setup** → [JENKINS_GITOPS_SETUP.md](JENKINS_GITOPS_SETUP.md) (configure Jenkins)
3. **Setup** → [ARGOCD_SETUP.md](ARGOCD_SETUP.md) (configure ArgoCD)
4. **Deploy** → Run first pipeline build
5. **Verify** → Check images, commits, pods
6. **Monitor** → Setup alerts and dashboards
7. **Optimize** → Add webhooks and approval gates

---

## 📞 Support

### Documentation
- [Jenkins Official](https://www.jenkins.io/doc/)
- [ArgoCD Official](https://argo-cd.readthedocs.io/)
- [Kubernetes Official](https://kubernetes.io/docs/)
- [Helm Official](https://helm.sh/docs/)

### Common Issues
1. **Build fails** → Check console output in Jenkins
2. **Images don't push** → Verify Docker Hub credentials
3. **Git push fails** → Verify GitHub credentials and branch protection
4. **ArgoCD can't detect changes** → Check Git repository connection
5. **Pods won't start** → Check image exists in Docker Hub, check logs

---

## 📝 Version Info

| Component | Version | Notes |
|-----------|---------|-------|
| Jenkinsfile | 2.0 | GitOps integrated |
| ArgoCD Application | 1.0 | With auto-sync enabled |
| Helm Chart | v0.1.0 | Updated with image tags |
| K8s | 1.20+ | Any recent version |

---

## 🎉 Ready?

1. Start with: **[GITOPS_INTEGRATION.md](GITOPS_INTEGRATION.md)**
2. Skip to setup if you're impatient: **[JENKINS_GITOPS_SETUP.md](JENKINS_GITOPS_SETUP.md)**
3. Questions? Check: **[GITOPS_INTEGRATION.md](GITOPS_INTEGRATION.md) § Troubleshooting**

**Total setup time:** 30-60 minutes to first working deployment

**Let's go! 🚀**
