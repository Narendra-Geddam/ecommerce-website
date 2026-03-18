# Quick Start Guide: Jenkins CI/CD Pipeline

Get the CI/CD pipeline up and running in minutes!

---

## 🚀 Quick Start (Local Testing)

### Prerequisites
- Docker and Docker Compose installed
- Docker Hub account
- Kubernetes cluster (or minikube for local testing)
- kubectl configured

### Step 1: Start Jenkins Locally

```bash
# Start Jenkins and PostgreSQL using Docker Compose
docker-compose -f docker-compose.jenkins.yml up -d

# Wait for Jenkins to be ready (1-2 minutes)
# Check status:
docker-compose -f docker-compose.jenkins.yml logs -f jenkins

# Jenkins will be available at: http://localhost:8080/jenkins/
```

### Step 2: Get Initial Jenkins Admin Password

```bash
# Get the initial admin password
docker exec jenkins-pipeline cat /var/jenkins_home/secrets/initialAdminPassword

# Note this password for the first login
```

### Step 3: Configure Jenkins

1. Open **http://localhost:8080/jenkins/** in browser
2. Paste the admin password
3. Click **Install suggested plugins** (takes 2-5 minutes)
4. Create first admin user
5. Complete Jenkins initialization

### Step 4: Install Required Plugins

From Jenkins Dashboard:
1. Go to **Manage Jenkins** → **Manage Plugins**
2. Go to **Available** tab
3. Search and install:
   - Pipeline: Stage View
   - Docker Pipeline
   - Kubernetes CLI
   - Helm
   - Git (usually pre-installed)

4. Restart Jenkins after plugins install

### Step 5: Configure Credentials

#### 5.1 Add Docker Hub Credentials

1. **Manage Jenkins** → **Manage Credentials** → **System** → **Global credentials**
2. Click **Add Credentials**

**Create 3 credentials:**

**#1 - Docker Username:**
- Kind: Secret text
- Secret: `your-docker-hub-username`
- ID: `docker-hub-user`
- OK

**#2 - Docker Token:**
- Kind: Secret text
- Secret: `your-docker-hub-token` (create personal access token on Docker Hub)
- ID: `docker-hub-password`
- OK

**#3 - Docker Repo:**
- Kind: Secret text
- Secret: `your-docker-hub-username`
- ID: `docker-hub-repo`
- OK

#### 5.2 Add Kubernetes Config

1. **Manage Jenkins** → **Manage Credentials** → **System** → **Global credentials**
2. Click **Add Credentials**
3. Create credential:
   - Kind: Secret file
   - File: Select your `~/.kube/config`
   - ID: `kubeconfig`
   - OK

### Step 6: Create Pipeline Job

1. Click **New Item** on Jenkins homepage
2. Job name: `ecommerce-build-and-deploy`
3. Select **Pipeline**
4. Click **OK**

**Configuration:**
- **Definition:** Pipeline script from SCM
- **SCM:** Git
- **Repository URL:** Your git repo URL
- **Credentials:** Add if private repo
- **Branch:** `*/main`
- **Script Path:** `Jenkinsfile`

5. Click **Save**

### Step 7: Test the Pipeline

1. Go back to job page
2. Click **Build Now**
3. Watch the build progress in real-time
4. Check **Console Output** for logs

---

## 📊 Monitoring the Pipeline

### View Build Logs

```bash
# Stream logs from running build
docker exec jenkins-pipeline tail -f /var/jenkins_home/logs/jenkins.log
```

### View Kubernetes Deployments

```bash
# Check deployment status
kubectl get deployments -n default
kubectl get pods -n default
kubectl get services -n default

# Check Helm releases
helm list

# View pod logs
kubectl logs -n default deployment/ecommerce-application
kubectl logs -n default deployment/ecommerce-presentation
```

### Check Trivy Scan Reports

Scan reports are archived in Jenkins job artifacts:
- Job page → **#N Artifacts**
- Download `trivy-*.json` files

---

## 🔧 Useful Commands

### Stop Jenkins

```bash
docker-compose -f docker-compose.jenkins.yml down
```

### View Jenkins Logs

```bash
docker-compose -f docker-compose.jenkins.yml logs -f jenkins
```

### Access Jenkins Container Shell

```bash
docker exec -it jenkins-pipeline bash
```

### Check Docker Image Sizes

```bash
docker images | grep ecommerce
```

### Clean Up Docker Resources

```bash
# Remove old images
docker image prune

# Remove unused volumes
docker volume prune

# Remove all stopped containers
docker container prune
```

---

## 🐛 Troubleshooting

### Pipeline Won't Start

**Error:** `docker: command not found`

**Solution:** Jenkins container needs Docker access:
```bash
# Recreate with proper Docker socket mount
docker-compose -f docker-compose.jenkins.yml down
docker-compose -f docker-compose.jenkins.yml up -d
```

### Docker Login Fails

**Error:** `denied: requested access to the resource is denied`

**Solution:**
1. Verify Docker Hub credentials in Jenkins
2. Create personal access token on Docker Hub instead of password
3. Verify token has read/write permissions

```bash
# Test Docker login locally
docker login
# Use: username, token (not password)
```

### Kubernetes Connection Error

**Error:** `Unable to connect to the server`

**Solution:**
1. Verify kubeconfig is correctly mounted to Jenkins
2. Check cluster is running:
   ```bash
   kubectl cluster-info
   ```
3. Update kubeconfig path in Jenkins configuration

### Helm Release Fails

**Error:** `Error: release: not found`

**Solution:**
1. Verify helm chart exists:
   ```bash
   helm lint ./helm-chart
   ```
2. Check Helm release namespace:
   ```bash
   helm list -n default
   ```
3. View Helm history:
   ```bash
   helm history ecommerce-app -n default
   ```

### Trivy Scan Fails

**Error:** `trivy: command not found`

**Solution:** Ensure Trivy is installed on Jenkins agent:
```bash
docker exec jenkins-pipeline bash -c "
  wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | apt-key add -
  echo 'deb https://aquasecurity.github.io/trivy-repo deb $(lsb_release -sc) main' | tee -a /etc/apt/sources.list.d/trivy.list
  apt-get update
  apt-get install -y trivy
"
```

---

## 📈 Pipeline Metrics

Once pipeline runs successfully, check these metrics:

```bash
# Build count
ls /var/jenkins_home/jobs/ecommerce-build-and-deploy/builds/ | wc -l

# Check build times
cat /var/jenkins_home/jobs/ecommerce-build-and-deploy/builds/lastBuiltRevision.xml

# View artifacts generated
ls /var/jenkins_home/jobs/ecommerce-build-and-deploy/builds/*/archive/
```

---

## 🎯 Next Steps

1. ✅ Jenkins running and configured
2. ✅ Pipeline job created
3. ✅ First build completed
4. **Set up Git webhook for automatic triggers**
   - GitHub: Settings → Webhooks → Add webhook
   - GitLab: Settings → Integrations → Jenkins CI
   - URL: `http://your-jenkins/github-webhook/`
5. **Configure notifications** (Slack, Email)
6. **Set up monitoring** (Prometheus, Grafana)
7. **Production deployment** (move to permanent Jenkins instance)

---

## 📚 References

- [Jenkins Official Documentation](https://www.jenkins.io/doc/)
- [Jenkinsfile Documentation](https://www.jenkins.io/doc/book/pipeline/jenkinsfile/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Trivy Scanner](https://aquasecurity.github.io/trivy/)

---

## ⚡ Tips & Tricks

### Run Pipeline with Custom Parameters

```groovy
// Add this to Jenkinsfile for parameterized builds
properties([
    parameters([
        string(name: 'ENVIRONMENT', defaultValue: 'dev', description: 'Deployment environment'),
        booleanParam(name: 'SKIP_TESTS', defaultValue: false, description: 'Skip test stages')
    ])
])
```

### Parallel Stages for Faster Builds

The current pipeline already uses parallel stages for:
- Building multiple images simultaneously
- Scanning multiple images simultaneously

This reduces total pipeline time ~40-50%

### Cache Docker Layers

Add to Jenkinsfile:
```groovy
docker.build("${PRESENTATION_IMAGE}", "--cache-from ${PRESENTATION_IMAGE}:latest presentation/")
```

### Archive Logs for Debugging

```groovy
post {
    always {
        archiveArtifacts artifacts: '**/logs/**', allowEmptyArchive: true
    }
}
```

---

## ✅ Success Checklist

After completing quick start, verify:

- [ ] Jenkins is running on http://localhost:8080/jenkins/
- [ ] All plugins are installed
- [ ] Docker Hub credentials configured
- [ ] Kubernetes config uploaded
- [ ] Pipeline job created
- [ ] First build completed successfully
- [ ] Docker images built and pushed
- [ ] Trivy scan completed without blocking failures
- [ ] Helm deployment successful
- [ ] Pods running in Kubernetes
- [ ] Services accessible

You're ready to go! 🚀
