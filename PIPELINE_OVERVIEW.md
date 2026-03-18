# CI/CD Pipeline: Complete Overview & Workflow

This document provides a comprehensive overview of the build, scan, and deploy pipeline for the e-commerce application.

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline Flow                        │
└──────────────────────────────────────────────────────────────────┘

1. CODE COMMIT
   │
   └─→ Git Repository (GitHub/GitLab)
        │
        ├─→ Webhook triggers Jenkins
        │
        └─→ Pipeline starts

2. BUILD PHASE
   │
   ├─→ Presentation Service (Nginx)
   │   └─→ Docker build → ecommerce-presentation:1234
   │
   └─→ Application Service (Flask)
       └─→ Docker build → ecommerce-application:1234

3. SECURITY SCAN PHASE
   │
   ├─→ Trivy Scan (Presentation)
   │   └─→ Check for vulnerabilities
   │
   └─→ Trivy Scan (Application)
       └─→ Check for vulnerabilities
       └─→ Generate reports

4. REGISTRY PUSH
   │
   ├─→ Docker Login to Docker Hub
   │
   ├─→ Push presentation:1234 → Docker Hub
   ├─→ Push presentation:latest → Docker Hub
   │
   ├─→ Push application:1234 → Docker Hub
   └─→ Push application:latest → Docker Hub

5. KUBERNETES DEPLOYMENT
   │
   ├─→ Connect to K8s cluster
   ├─→ Create namespace (if needed)
   │
   ├─→ Helm Upgrade/Install
   │   └─→ Read helm-chart/values.yaml
   │   └─→ Override image tags with build #1234
   │   └─→ Deploy presentation pods
   │   └─→ Deploy application pods
   │   └─→ Deploy services
   │
   └─→ Verify Deployment
       ├─→ Check pod status
       ├─→ Check service endpoints
       └─→ Output logs

6. RESULT
   │
   ├─→ SUCCESS: Application running in K8s ✓
   └─→ FAILURE: Send alert to team
```

---

## 📁 Project Structure

```
.
├── Jenkinsfile                      # Main pipeline definition
├── docker-compose.jenkins.yml       # Local Jenkins setup
├── setup-k8s-prerequisites.sh       # K8s resource setup script
├── JENKINS_SETUP.md                 # Detailed Jenkins configuration
├── JENKINS_QUICKSTART.md            # Quick start guide
├── HELM_VALUES_EXAMPLES.md          # Environment-specific values
│
├── application/                     # Flask Backend
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ...
│
├── presentation/                    # Nginx Frontend
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── index.html
│   └── ...
│
├── helm-chart/                      # Kubernetes Helm Chart
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml (create)
│   ├── values-staging.yaml (create)
│   ├── values-prod.yaml (create)
│   ├── templates/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── _helpers.tpl
│
├── k8s/                             # Direct K8s manifests (optional)
│   ├── deployment.yaml
│   └── ...
│
└── data/                            # Database schema
    └── schema.sql
```

---

## 🔄 Pipeline Stages Explained

### Stage 1: Checkout (1-2 minutes)
**Purpose:** Clone the Git repository
```groovy
stage('Checkout') {
    steps {
        checkout scm  // Pulls code from Git
    }
}
```
- Clones entire repository
- Checks out the triggered branch
- No code compilation yet

### Stage 2: Build Docker Images (Parallel, 5-10 minutes)
**Purpose:** Build container images for both services
```groovy
stage('Build Docker Images') {
    parallel {
        stage('Build Presentation Image') {
            docker build -t ${PRESENTATION_IMAGE} presentation/
        }
        stage('Build Application Image') {
            docker build -t ${APPLICATION_IMAGE} application/
        }
    }
}
```
**Runs in parallel:** Both images built simultaneously
**Output:** 
- `your-docker-id/ecommerce-presentation:1234`
- `your-docker-id/ecommerce-application:1234`

### Stage 3: Scan for Vulnerabilities (Parallel, 3-5 minutes)
**Purpose:** Security scanning using Trivy
```groovy
stage('Scan for Vulnerabilities') {
    parallel {
        trivy image --severity HIGH,CRITICAL ${PRESENTATION_IMAGE}
        trivy image --severity HIGH,CRITICAL ${APPLICATION_IMAGE}
    }
}
```
**Checks for:**
- HIGH severity vulnerabilities
- CRITICAL severity vulnerabilities
- OS package vulnerabilities
- Application dependency vulnerabilities

**Output:** JSON reports in Jenkins artifacts

### Stage 4: Publish Test Reports (1 minute)
**Purpose:** Archive vulnerability reports
```groovy
stage('Publish Test Reports') {
    archiveArtifacts artifacts: '**/trivy-*.json'
}
```
**Allows:**
- Review vulnerability reports
- Long-term audit trail
- Trend analysis

### Stage 5: Push to Docker Hub (3-5 minutes)
**Purpose:** Publish images to registry
```groovy
stage('Push to Docker Hub') {
    sh '''
        docker login -u ${DOCKER_HUB_USER} --password-stdin ${DOCKER_HUB_PASSWORD}
        docker push ${PRESENTATION_IMAGE}
        docker push ${APPLICATION_IMAGE}
        docker push ${DOCKER_HUB_USER}/ecommerce-presentation:latest
        docker push ${DOCKER_HUB_USER}/ecommerce-application:latest
    '''
}
```
**Pushes:**
- Versioned image (e.g., `ecommerce-presentation:1234`)
- Latest tag for quick reference

### Stage 6: Deploy to Kubernetes with Helm (3-5 minutes)
**Purpose:** Deploy application to K8s
```groovy
stage('Deploy to Kubernetes with Helm') {
    helm upgrade --install ecommerce-app ./helm-chart \
        --set image.presentation.tag=${APP_VERSION} \
        --set image.application.tag=${APP_VERSION} \
        --wait --timeout 5m
}
```
**Does:**
- Connects to K8s cluster
- Creates namespace if needed
- Installs/updates Helm release
- Pulls latest image tags
- Creates deployments, services, configmaps
- Waits for rollout completion

### Stage 7: Verify Deployment (2-3 minutes)
**Purpose:** Confirm deployment success
```groovy
stage('Verify Deployment') {
    kubectl rollout status deployment/ecommerce-presentation
    kubectl rollout status deployment/ecommerce-application
    kubectl logs -n default deployment/ecommerce-application --tail=20
}
```
**Verifies:**
- Pods are running
- Services are accessible
- No startup errors in logs

---

## ⏱️ Total Pipeline Execution Time

| Stage | Duration | Notes |
|-------|----------|-------|
| Checkout | 1-2 min | Depends on repo size |
| Build Docker | 5-10 min | Parallel builds (main time) |
| Scan (Trivy) | 3-5 min | Parallel scans |
| Publish Reports | 1 min | Archive artifacts |
| Push to Registry | 3-5 min | Network upload speed |
| Deploy (Helm) | 3-5 min | K8s scheduling + image pull |
| Verify | 2-3 min | Wait for rollout |
| **Total** | **18-30 min** | Typical full pipeline |

**With caching & optimization:** Can reduce to 12-15 minutes

---

## 🔐 Security Scanning Details

### Trivy Configuration

```groovy
TRIVY_SEVERITY = 'HIGH,CRITICAL'  // What gets reported
EXIT_CODE = 0                      // Don't fail on findings
```

**Scanned For:**
- OS Package Vulnerabilities
  - Alpine, Ubuntu, Debian packages
  - Known CVEs in base images
- Application Dependencies
  - Python pip packages
  - Node.js npm packages
  - Java Maven packages
- Misconfigurations
  - Docker best practices
  - Secret detection

**Example Finding:**
```json
{
  "vulnerability_id": "CVE-2021-12345",
  "severity": "HIGH",
  "package": "openssl",
  "installed_version": "1.1.1",
  "fixed_version": "1.1.1.1k",
  "title": "Buffer overflow in OpenSSL"
}
```

---

## 🧩 Helm Deployment Details

### What Helm Does

**Template rendering:**
```bash
helm template ecommerce-app ./helm-chart \
  --set image.presentation.tag=1234 \
  --set image.application.tag=1234
```

**Generates K8s manifests:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-presentation
spec:
  template:
    spec:
      containers:
      - image: your-docker-id/ecommerce-presentation:1234
        ...
```

**Applies to cluster:**
```bash
kubectl apply -f [generated-manifests]
```

### Environment-Specific Values

```
Pipeline → Build #1234 → Helm Install 
                           ├─ Presentation replica count?
                           ├─ Application replica count?
                           ├─ Resources limits/requests?
                           ├─ Service type?
                           └─ Configuration env vars?

Answers from: helm-chart/values.yaml (or -dev, -staging, -prod)
```

**Examples:**
- **Dev:** 1 replica, LoadBalancer service
- **Staging:** 2 replicas, ClusterIP service
- **Prod:** 3+ replicas, Pod anti-affinity

---

## 📊 Monitoring & Troubleshooting

### Check Pipeline Status

```bash
# View all builds
Jenkins Dashboard → ecommerce-build-and-deploy → Build History

# View specific build
Click build number → Console Output
```

### Check Deployment Status

```bash
# Pods
kubectl get pods -n default
kubectl describe pod -n default [pod-name]
kubectl logs -n default [pod-name]

# Services
kubectl get svc -n default
kubectl get endpoints -n default [service-name]

# Helm
helm status ecommerce-app -n default
helm get values ecommerce-app -n default
```

### Common Issues & Solutions

**Issue:** Pod stuck in ImagePullBackOff
```bash
# Solution: Check Docker Hub image availability
docker pull your-docker-id/ecommerce-application:1234
```

**Issue:** Pod crashloop in CrashLoopBackOff
```bash
# Solution: Check application logs
kubectl logs -n default [pod-name] --previous
kubectl logs -n default [pod-name] --tail=100
```

**Issue:** Service unreachable
```bash
# Solution: Verify service endpoints
kubectl get endpoints -n default [service-name]
kubectl port-forward -n default svc/[service-name] 8080:80
```

---

## 🎯 Key Metrics to Track

### Pipeline Metrics
- Build success rate
- Average build duration
- Failed stage distribution
- Vulnerability trends

### Deployment Metrics
- Pod creation time
- Image pull time
- First request latency
- Pod restart count

### Security Metrics
- Vulnerabilities per scan
- CRITICAL/HIGH ratio
- Vulnerability resolution time
- Build failure rate due to security

---

## 🔄 CI/CD Best Practices

### 1. Version Everything
- Use immutable tags: `v1.2.3`, `2024-03-18`
- Never reuse `latest` across environments
- Tag builds consistently

### 2. Track Artifacts
- Archive scan reports
- Keep build logs
- Document deployment versions
- Maintain audit trail

### 3. Secure Credentials
- Don't commit secrets
- Use Jenkins credential store
- Rotate credentials regularly
- Use short-lived tokens

### 4. Test Thoroughly
- Unit tests before build
- Integration tests in staging
- Manual testing before prod
- Automated smoke tests

### 5. Progressive Deployment
- Deploy to dev first
- Promote to staging
- Final approval for production
- Automated rollback on failure

### 6. Monitor Continuously
- Check pod health
- Monitor application logs
- Alert on failures
- Track deployment frequency

---

## 📝 Maintenance Tasks

### Weekly
```bash
# Remove old Docker images
docker image prune -a

# Check Trivy for new CVE definitions
trivy image --severity CRITICAL your/image:latest
```

### Monthly
```bash
# Update base images
docker pull alpine:latest
docker pull ubuntu:latest

# Rebuild all images with latest base
```

### Quarterly
```bash
# Review and update dependencies
# Upgrade vulnerable packages
# Rebuild images for security updates
```

---

## 🚀 Next Steps

1. ✅ Setup Jenkins infrastructure
2. ✅ Configure credentials
3. ✅ Create pipeline job
4. ✅ Run first successful build
5. **Set up Git webhooks** (auto-trigger)
6. **Configure notifications** (Slack/Email)
7. **Add environment promotion** (dev→staging→prod)
8. **Implement rollback procedure**
9. **Set up monitoring/alerting**
10. **Document runbooks** for ops team

---

## 📚 Reference Documents

In this workspace:
- `JENKINS_SETUP.md` - Detailed Jenkins configuration
- `JENKINS_QUICKSTART.md` - Quick start (15 minutes)
- `HELM_VALUES_EXAMPLES.md` - Environment-specific configs
- `setup-k8s-prerequisites.sh` - Automated K8s setup
- `docker-compose.jenkins.yml` - Local Jenkins setup

External resources:
- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)

---

## ✅ Readiness Checklist

Before going to production:

- [ ] Jenkins cluster is highly available
- [ ] All credentials are securely stored
- [ ] Pipeline runs consistently and reliably
- [ ] Vulnerability scanning identifies issues
- [ ] Docker images have small size footprint
- [ ] K8s resources are properly configured
- [ ] Pod resource limits are set
- [ ] Health checks are functioning
- [ ] Logs are centralized and searchable
- [ ] Deployments can be rolled back
- [ ] Team understands the pipeline
- [ ] Runbooks are documented
- [ ] On-call procedures are defined

---

**Last Updated:** March 18, 2026
**Pipeline Version:** 1.0.0
**Read Time:** 10-15 minutes
