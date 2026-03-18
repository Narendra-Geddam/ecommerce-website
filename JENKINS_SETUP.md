# Jenkins CI/CD Pipeline Setup Guide

This guide explains how to set up and configure the Jenkins pipeline for building, scanning, and deploying the e-commerce application to Kubernetes.

---

## 📋 Prerequisites

### Required Tools
- Jenkins (2.387+ recommended)
- Docker and Docker CLI
- Kubernetes cluster (with kubectl configured)
- Helm 3.x
- Git
- Trivy CLI for vulnerability scanning

### Required Jenkins Plugins
Install these plugins in Jenkins (Manage Jenkins → Manage Plugins):

```
- Pipeline: Stage View
- Git Pipeline for Blue Ocean
- Docker Pipeline
- Kubernetes CLI
- Helm
- Email Extension Plugin (optional, for notifications)
- Slack Notification Plugin (optional, for alerts)
```

---

## 🔧 Step 1: Install Required Tools on Jenkins Agents

### On Jenkins Controller/Agents, ensure installed:

```bash
# Update system
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins

# Install kubectl
curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install Trivy
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install -y trivy

# Verify installations
docker --version
kubectl version --client
helm version
trivy --version
```

---

## 🔐 Step 2: Configure Jenkins Credentials

### 2.1 Docker Hub Credentials

1. Go to **Jenkins Dashboard → Manage Credentials → System → Global credentials**
2. Click **Add Credentials** and create entries for:

   **Credential 1: Docker Hub User**
   - Kind: Secret text
   - Secret: `your-docker-hub-username`
   - ID: `docker-hub-user`
   - Description: Docker Hub Username

   **Credential 2: Docker Hub Password**
   - Kind: Secret text
   - Secret: `your-docker-hub-password` (or personal access token)
   - ID: `docker-hub-password`
   - Description: Docker Hub Password/Token

   **Credential 3: Docker Hub Repo**
   - Kind: Secret text
   - Secret: `your-docker-hub-username` (repo owner)
   - ID: `docker-hub-repo`
   - Description: Docker Hub Repository Owner

### 2.2 Kubernetes Configuration

1. Get your kubeconfig file from your Kubernetes cluster
2. Add it as a Jenkins credential:
   - Kind: Secret file
   - File: `~/.kube/config` (your kubeconfig file)
   - ID: `kubeconfig`
   - Description: Kubernetes Config File

3. Configure the kubeconfig in Jenkins system:
   - **Jenkins → Manage Jenkins → Configure System**
   - Find **Kubernetes** section
   - Set **Kubernetes URL**: `https://your-k8s-api-server:6443`
   - Set **Kubernetes Namespace**: `default`
   - Upload your kubeconfig under **Kubernetes Credentials**

---

## 📦 Step 3: Create the Jenkins Pipeline Job

### 3.1 Create a New Pipeline Job

1. Click **New Item** on Jenkins Dashboard
2. Enter name: `ecommerce-build-and-deploy`
3. Select **Pipeline**
4. Click **OK**

### 3.2 Pipeline Configuration

In the job configuration page:

**Definition:** Pipeline script from SCM
- **SCM:** Git
- **Repository URL:** `https://github.com/your-username/your-repo.git`
- **Credentials:** Add your Git credentials if private
- **Branch:** `*/main` (or your default branch)
- **Script Path:** `Jenkinsfile`

**Build Trigger Options (choose one):**
- **Poll SCM:** `H/15 * * * *` (every 15 minutes)
- **GitHub hook trigger:** Add webhook in GitHub settings
- **Manual trigger:** Manually start builds

### 3.3 Save and Run

Click **Save**, then **Build Now** to test the pipeline.

---

## 🚀 Step 4: Configure Kubernetes Cluster

### 4.1 Create Kubernetes Namespace (optional)

```bash
kubectl create namespace ecommerce
```

### 4.2 Create Docker Registry Secret (if using private registry)

```bash
kubectl create secret docker-registry docker-hub-secret \
  --docker-server=docker.io \
  --docker-username=your-username \
  --docker-password=your-password \
  --docker-email=your-email@example.com \
  -n default
```

### 4.3 Create Kubernetes Secrets for Application

```bash
kubectl create secret generic ecommerce-secrets \
  --from-literal=database-url=postgresql://ecommerce:password@postgres:5432/ecommerce \
  --from-literal=secret-key=your-flask-secret-key \
  -n default
```

---

## 📊 Step 5: Understanding the Pipeline Stages

The pipeline executes the following stages:

### Stage 1: **Checkout**
- Clones the Git repository

### Stage 2: **Build Docker Images** (Parallel)
- Builds Presentation (Nginx) image
- Builds Application (Flask) image

### Stage 3: **Scan for Vulnerabilities** (Parallel)
- Scans both images with Trivy
- Checks for HIGH and CRITICAL vulnerabilities
- Generates JSON reports

### Stage 4: **Publish Test Reports**
- Archives Trivy scan reports as artifacts
- Optionally fails if critical vulnerabilities found

### Stage 5: **Push to Docker Hub**
- Authenticates to Docker Hub
- Pushes images with version tag
- Pushes images with `latest` tag

### Stage 6: **Deploy to Kubernetes with Helm**
- Creates namespace if needed
- Upgrades/installs Helm release
- Applies image tags from pipeline
- Waits for successful rollout

### Stage 7: **Verify Deployment**
- Checks deployment status
- Outputs pod logs
- Displays services

---

## 🔍 Troubleshooting

### Issue: Docker login fails
```bash
# Verify credentials are correct in Jenkins
# Test locally:
docker login
# If using personal token, use token as password instead
```

### Issue: Kubectl commands not found
```bash
# Ensure kubeconfig is properly mounted
# Check Jenkins agent has kubectl installed:
which kubectl
```

### Issue: Helm chart not found
```bash
# Verify chart path is correct:
ls -la ./helm-chart/Chart.yaml

# Validate Helm chart:
helm lint ./helm-chart
```

### Issue: Pod fails to start
```bash
# Check pod logs:
kubectl logs -n default deployment/ecommerce-application

# Check events:
kubectl describe pod -n default [pod-name]

# Check image pull:
kubectl get events -n default --sort-by='.lastTimestamp'
```

---

## 📝 Pipeline Environment Variables

The following variables are set in the Jenkinsfile:

| Variable | Value |
|----------|-------|
| `DOCKER_HUB_USER` | Credentials: docker-hub-user |
| `DOCKER_HUB_PASSWORD` | Credentials: docker-hub-password |
| `KUBECONFIG` | Credentials: kubeconfig |
| `HELM_RELEASE_NAME` | ecommerce-app |
| `HELM_NAMESPACE` | default |
| `APP_VERSION` | BUILD_NUMBER (incremental) |
| `TRIVY_SEVERITY` | HIGH,CRITICAL |

---

## ⚙️ Customization

### Change Deployment Namespace

In the Jenkinsfile, modify:
```groovy
HELM_NAMESPACE = 'ecommerce'  // Change from 'default'
```

### Change Trivy Severity Level

```groovy
TRIVY_SEVERITY = 'MEDIUM,HIGH,CRITICAL'  // Include medium vulnerabilities
```

### Add Slack Notifications

Uncomment in post section and configure:
```groovy
slackSend(
    color: 'good',
    message: "Deployment of ${HELM_RELEASE_NAME} succeeded",
    webhookUrl: 'your-slack-webhook-url'
)
```

### Add Email Notifications

Install Email Extension Plugin, then add:
```groovy
emailext(
    subject: "Build ${BUILD_NUMBER}: ${BUILD_STATUS}",
    body: "${BUILD_LOG}",
    to: "your-email@example.com"
)
```

---

## 🔄 Pipeline Execution Flow

```
┌─────────────────┐
│   Git Trigger   │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Checkout │
    └────┬────┘
         │
    ┌────▼─────────────────────────┐
    │  Build Docker Images (Parallel)│
    │  ├─ Presentation             │
    │  └─ Application              │
    └────┬──────────────────────────┘
         │
    ┌────▼──────────────────────────┐
    │ Scan Vulnerabilities (Parallel)│
    │ ├─ Trivy Presentation         │
    │ └─ Trivy Application          │
    └────┬───────────────────────────┘
         │
    ┌────▼─────────────────┐
    │ Publish Test Reports │
    └────┬─────────────────┘
         │
    ┌────▼──────────────┐
    │ Push to Docker Hub│
    └────┬──────────────┘
         │
    ┌────▼───────────────────────────────┐
    │ Deploy to Kubernetes with Helm    │
    └────┬───────────────────────────────┘
         │
    ┌────▼─────────────────┐
    │ Verify Deployment    │
    └────┬─────────────────┘
         │
    ┌────▼─────────────┐
    │ Success / Failure│
    └──────────────────┘
```

---

## 📚 Additional Resources

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Jenkinsfile Syntax](https://www.jenkins.io/doc/book/pipeline/jenkinsfile/)
- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)

---

## ✅ Verification Checklist

- [ ] Jenkins is installed and running
- [ ] Required plugins are installed
- [ ] Docker credentials are configured
- [ ] Kubernetes credentials are configured
- [ ] Trivy is installed on Jenkins agent
- [ ] Helm is installed on Jenkins agent
- [ ] kubectl is installed and configured
- [ ] Docker Hub account is accessible
- [ ] Kubernetes cluster is accessible
- [ ] Git repository is accessible to Jenkins
- [ ] Jenkinsfile is in repository root
- [ ] Helm chart exists in ./helm-chart directory
- [ ] First pipeline run succeeds

---

## 🎯 Next Steps

1. Set up Jenkins infrastructure (use Docker/Kubernetes)
2. Configure all credentials
3. Create the pipeline job
4. Set up Git webhooks for automatic triggers
5. Monitor build logs and deployment
6. Customize for your environment
7. Set up alerting/notifications
8. Document any custom modifications
