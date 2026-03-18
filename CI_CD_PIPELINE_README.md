# CI/CD Pipeline - Complete Package

This directory now contains a complete, production-ready CI/CD pipeline for building, scanning, and deploying your e-commerce application to Kubernetes using Helm and Jenkins.

---

## 📦 What Was Created

### 1. **Jenkinsfile** ⭐
Main pipeline definition with all stages:
- ✅ Build Docker images (parallel)
- ✅ Scan with Trivy (parallel)
- ✅ Push to Docker Hub
- ✅ Deploy with Helm
- ✅ Verify deployment

**Key Features:**
- Parallel stage execution for speed
- Comprehensive error handling
- Intermediate artifact collection
- Pod status verification

**Total Runtime:** 18-30 minutes

---

### 2. **Configuration Files**

#### `helm-chart/values.yaml` (Updated)
Enhanced values file with:
- Separate presentation and application tiers
- Image repository configuration
- Resource limits aligned with environment
- Health checks configuration
- Database and secret management

#### `docker-compose.jenkins.yml`
Local Jenkins setup for testing:
- Jenkins container with LTS image
- PostgreSQL database
- Volume persistence
- Health checks

---

### 3. **Documentation**

#### `JENKINS_SETUP.md` (Comprehensive Setup Guide)
**Contents:**
- Prerequisites and tool installation
- Required Jenkins plugins
- Complete credential configuration
- Step-by-step job creation
- Troubleshooting guide
- Customization options

**Read Time:** 20-30 minutes
**Covers:** Everything needed to set up Jenkins from scratch

#### `JENKINS_QUICKSTART.md` (Fast Track)
**Contents:**
- Local Jenkins setup (Docker)
- Credential configuration
- First pipeline execution
- Monitoring and verification
- Common troubleshooting

**Read Time:** 10-15 minutes
**Use When:** You want to test pipeline locally quickly

#### `PIPELINE_OVERVIEW.md` (Architecture & Flow)
**Contents:**
- Complete architecture diagram
- Stage-by-stage explanation
- Execution time breakdown
- Security scanning details
- Troubleshooting guide
- Best practices

**Read Time:** 15-20 minutes
**Use When:** Understanding how everything works together

#### `HELM_VALUES_EXAMPLES.md` (Environment Configs)
**Contents:**
- Development values
- Staging values
- Production values
- High-availability production
- Deployment scripts
- Value override examples

**Read Time:** 10 minutes
**Use When:** Deploying to specific environments

---

### 4. **Scripts**

#### `setup-k8s-prerequisites.sh` (Kubernetes Setup)
Automated Kubernetes resource creation:
```bash
./setup-k8s-prerequisites.sh [namespace] [registry] [username] [password]
```

**Creates:**
- Kubernetes namespace
- Docker registry secrets
- Application secrets (DB URL, secret key)
- ConfigMaps
- RBAC roles and bindings

**Run Before:** First Helm deployment

---

## 🚀 Quick Start (3 Steps)

### Step 1: Setup Jenkins Locally (5 minutes)
```bash
# Start Jenkins and PostgreSQL
docker-compose -f docker-compose.jenkins.yml up -d

# Wait for startup
docker-compose -f docker-compose.jenkins.yml logs -f jenkins

# Access: http://localhost:8080/jenkins/
```

### Step 2: Configure Jenkins (10 minutes)
Follow `JENKINS_QUICKSTART.md`:
1. Get initial admin password
2. Install suggested plugins
3. Add Docker Hub credentials
4. Add Kubernetes config
5. Create pipeline job

### Step 3: Run First Build (varies)
```bash
# In Jenkins UI:
1. Go to ecommerce-build-and-deploy job
2. Click "Build Now"
3. Monitor build progress
```

**Total Time:** ~40 minutes for first working pipeline

---

## 📊 Which Document to Read?

| Goal | Document | Time |
|------|----------|------|
| Get running fast | JENKINS_QUICKSTART.md | 10-15 min |
| Set up production | JENKINS_SETUP.md | 20-30 min |
| Understand how it works | PIPELINE_OVERVIEW.md | 15-20 min |
| Deploy to environments | HELM_VALUES_EXAMPLES.md | 10 min |
| Fix K8s errors | JENKINS_SETUP.md (troubleshooting) | 5-10 min |

---

## 🔑 Key Capabilities

### Build Automation
```
Git Commit → Automatic Build Start
             ├─ Build images
             ├─ Scan for vulnerabilities
             └─ Push to registry
```

### Security Scanning
```
Built Images → Trivy Scanner
                ├─ OS package vulnerabilities
                ├─ App dependency vulnerabilities
                ├─ Generate JSON reports
                └─ Archive artifacts
```

### Kubernetes Deployment
```
Images in Registry → Helm Chart
                    ├─ Template rendering
                    ├─ Image tag injection
                    ├─ Config management
                    └─ Auto rollout verification
```

### Multi-Environment Support
```
Single Pipeline → Dev (1 replica)
                ├─ Staging (2 replicas)
                └─ Production (3+ replicas)
        via helm-chart/values-*.yaml
```

---

## 📋 Pre-Deployment Checklist

Before first pipeline run:

**Jenkins Setup:**
- [ ] Jenkins installed and running
- [ ] Plugins installed: Pipeline, Docker, Kubernetes CLI, Helm
- [ ] Docker Hub credentials configured
- [ ] Kubernetes config uploaded
- [ ] Git repository accessible

**Project Setup:**
- [ ] Jenkinsfile in repository root
- [ ] Dockerfile in presentation/ directory
- [ ] Dockerfile in application/ directory
- [ ] helm-chart/ directory exists with templates

**Kubernetes Setup:**
- [ ] Cluster accessible
- [ ] kubectl configured
- [ ] Helm installed
- [ ] Docker registry secret created (if private)
- [ ] K8s secrets created for app (DB URL, secret key)

**Docker Registry:**
- [ ] Docker Hub account exists
- [ ] Repository created
- [ ] Personal access token generated
- [ ] Credentials tested locally

---

## 🎯 Next Steps After First Run

### 1. Verify Deployment (5 minutes)
```bash
# Check deployments
kubectl get deployments -n default

# Check pods
kubectl get pods -n default

# Check services
kubectl get services -n default

# View logs
kubectl logs -n default -l app=ecommerce-application
```

### 2. Set Up Git Webhooks (5 minutes)
- **GitHub:** Settings → Webhooks → Add webhook
- **GitLab:** Settings → Integrations → Jenkins CI
- URL: `http://your-jenkins-url/jenkins/github-webhook/`

Now builds trigger automatically on commits!

### 3. Configure Notifications (10 minutes)
- **Slack:** Install Slack plugin, add webhook
- **Email:** Configure SMTP server
- Add to Jenkinsfile post section

### 4. Set Up Monitoring (15 minutes)
- Monitor Jenkins job performance
- Track build success rate
- Set up alerts for failures
- Export metrics to monitoring system

### 5. Production Preparation (30 minutes)
- Set up permanent Jenkins infrastructure
- Configure backup/disaster recovery
- Implement audit logging
- Create runbooks for operations team

---

## 📚 File Reference

```
demo/
├── Jenkinsfile                          [MAIN PIPELINE]
├── docker-compose.jenkins.yml          [LOCAL JENKINS SETUP]
├── setup-k8s-prerequisites.sh           [K8S AUTOMATION]
│
├── JENKINS_SETUP.md                     [REFERENCE: Complete setup]
├── JENKINS_QUICKSTART.md                [REFERENCE: Fast track]
├── PIPELINE_OVERVIEW.md                 [REFERENCE: How it works]
├── HELM_VALUES_EXAMPLES.md              [REFERENCE: Environments]
└── CI_CD_PIPELINE_README.md             [THIS FILE]
```

---

## 🔧 Customization Guide

### Change Build Trigger
Edit pipeline section in Jenkins:
```
Poll SCM:        H/15 * * * *  (every 15 min)
GitHub webhook:  Automatic on push
Manual:          Click "Build Now"
```

### Add More Stages
Example: Add unit tests before build
```groovy
stage('Unit Tests') {
    steps {
        sh 'python -m pytest application/tests/'
    }
}
```

### Change Kubernetes Namespace
In Jenkinsfile:
```groovy
HELM_NAMESPACE = 'my-namespace'  // Change from 'default'
```

### Add Email Notifications
In Jenkinsfile post section:
```groovy
emailext(
    subject: "Build ${BUILD_NUMBER}: ${BUILD_STATUS}",
    to: "team@company.com"
)
```

---

## ⚠️ Common Pitfalls

❌ **Don't:**
- Hardcode secrets in Jenkinsfile
- Use `latest` tag in production
- Deploy without testing first
- Ignore vulnerability scan results
- Skip health checks

✅ **Do:**
- Use Jenkins credentials store
- Use immutable version tags
- Deploy to dev/staging first
- Review and fix vulnerabilities
- Configure comprehensive health checks

---

## 🆘 Getting Help

### Pipeline fails to start
→ Check: JENKINS_SETUP.md → Troubleshooting section

### Deployment errors
→ Check: JENKINS_QUICKSTART.md → Troubleshooting section

### Kubernetes issues
→ Check: PIPELINE_OVERVIEW.md → Monitoring & Troubleshooting

### Understanding the pipeline
→ Read: PIPELINE_OVERVIEW.md → Architecture section

---

## 📞 Support Resources

**Official Documentation:**
- [Jenkins Docs](https://www.jenkins.io/doc/)
- [Helm Docs](https://helm.sh/docs/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Trivy Docs](https://aquasecurity.github.io/trivy/)
- [Docker Docs](https://docs.docker.com/)

**Commands Cheat Sheet:**

```bash
# Jenkins
docker-compose -f docker-compose.jenkins.yml up -d
docker-compose -f docker-compose.jenkins.yml logs -f jenkins

# Kubernetes
kubectl get pods -n default
kubectl logs -n default [pod-name]
kubectl describe pod -n default [pod-name]

# Helm
helm install ecommerce-app ./helm-chart -n default
helm upgrade ecommerce-app ./helm-chart -n default
helm rollback ecommerce-app 1 -n default

# Docker
docker build -t myimage:tag .
docker push myimage:tag
docker run -it myimage:tag bash
```

---

## ✅ Success Indicators

Your pipeline is working when:
- ✅ Jenkinsfile syntax is valid (no errors in UI)
- ✅ Build completes all 7 stages without failure
- ✅ Docker images appear in Docker Hub
- ✅ Trivy scan reports are generated
- ✅ Pods are running in Kubernetes
- ✅ Services are accessible
- ✅ Application logs show no errors

---

## 📈 Next Evolution

After mastering this pipeline, consider:
1. **Automated testing** - Add unit/integration tests
2. **Code quality gates** - SonarQube integration
3. **Progressive deployment** - Blue-green or canary
4. **Advanced monitoring** - Prometheus + Grafana
5. **Policy enforcement** - Open Policy Agent (OPA)
6. **GitOps integration** - ArgoCD for pull-based deployments
7. **Observability** - Elasticsearch, Kibana, Jaeger
8. **Multi-cluster** - Deploy to multiple K8s clusters

---

## 📝 Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-03-18 | 1.0.0 | Initial release |

---

## 🎓 Learning Path

**Beginner (Day 1):**
1. Read JENKINS_QUICKSTART.md
2. Follow Steps 1-3 to get running locally
3. Understand basic pipeline flow

**Intermediate (Day 2-3):**
1. Read PIPELINE_OVERVIEW.md
2. Study each stage in detail
3. Understand Helm templating
4. Learn Kubernetes concepts

**Advanced (Day 4+):**
1. Read JENKINS_SETUP.md fully
2. Set up production infrastructure
3. Customize for your needs
4. Add monitoring and alerting

---

**Start with:** [JENKINS_QUICKSTART.md](JENKINS_QUICKSTART.md)

**Total estimated time to production:** 2-4 hours

Happy deploying! 🚀
