# Jenkins Setup for GitOps CI/CD Pipeline

This guide explains how to configure Jenkins for the new GitOps workflow with ArgoCD.

---

## 🔑 Jenkins Credentials Setup

The new pipeline requires **2 main credentials** (instead of 3):

1. **dockerhub-creds** - Docker Hub (usernamePassword)
2. **github-credentials** - GitHub access (usernamePassword)

---

## Step 1: Create Docker Hub Credentials

### In Jenkins Dashboard:

1. Go to **Manage Jenkins** → **Manage Credentials** → **System** → **Global credentials (unrestricted)**

2. Click **+ Add Credentials**

3. **Create Credential:**
   - **Kind:** Username with password
   - **Username:** `your-docker-hub-username`
   - **Password:** `your-docker-hub-personal-access-token` (not your actual password!)
   - **ID:** `dockerhub-creds`
   - **Description:** Docker Hub Credentials for CI/CD
   - Click **Create**

### Create Docker Hub Personal Access Token

If you don't have a personal access token:

1. Go to https://hub.docker.com/settings/security
2. Click **+ New Access Token**
3. Token name: `Jenkins-CI`
4. Permissions: Select **Read & Write**
5. Generate and copy token
6. Paste into Jenkins credential above

---

## Step 2: Create GitHub Credentials

### In Jenkins Dashboard:

1. Go to **Manage Jenkins** → **Manage Credentials** → **System** → **Global credentials (unrestricted)**

2. Click **+ Add Credentials**

3. **Create Credential:**
   - **Kind:** Username with password
   - **Username:** `your-github-username`
   - **Password:** `your-github-personal-access-token`
   - **ID:** `github-credentials`
   - **Description:** GitHub Repository Access for Helm Values Updates
   - Click **Create**

### Create GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click **Generate new token (classic)**
3. **Token name:** `Jenkins-GitOps`
4. **Scopes:** Select
   - `repo` - Full control of private repositories
   - `workflow` - Update GitHub Actions workflows
5. **Generate token**
6. Copy and paste into Jenkins credential above

⚠️ **Security Note:** GitHub tokens are sensitive! Treat like passwords.

---

## Step 3: Configure Pipeline Job

### Create New Pipeline Job

1. Jenkins Dashboard → **+ New Item**
2. **Name:** `ecommerce-gitops-pipeline`
3. **Type:** Pipeline
4. Click **OK**

### Pipeline Configuration

**Definition:** Pipeline script from SCM

#### SCM Settings:
- **SCM:** Git
- **Repository URL:** `https://github.com/your-username/your-repo.git`
- **Credentials:** Select `github-credentials` (created in Step 2)
- **Branch:** `*/main` (or your default branch)
- **Script Path:** `Jenkinsfile`

#### Build Triggers:
Choose one or more:
- **Poll SCM:** `H/15 * * * *` - Check every 15 minutes
- **GitHub hook trigger:** - Triggered by Git webhook (real-time)
- **Manual - Build Now:** - Manually start builds

#### Advanced Options:
- **Shallow clone:** Check (faster, less data)
- **Clean checkout:** Check (clean workspace before build)

### Save and Test

1. Click **Save**
2. Click **Build Now**
3. Monitor **Console Output**

---

## Step 4: Configure Git in Jenkins

Jenkins needs to be able to commit and push to GitHub.

### Configure Git Username/Email

In the Jenkinsfile, git is configured as:
```groovy
git config user.email "jenkins@example.com"
git config user.name "Jenkins Pipeline"
```

### Enable Git Push

The Jenkinsfile uses:
```groovy
git push origin ${GIT_BRANCH}
```

This requires credentials setup in:
- **Jenkins Credentials:** `github-credentials`
- **Git automatically uses:** ~/.git-credentials or ssh keys

---

## Step 5: Verify Credentials

### Test Docker Hub Credential

```bash
# In Jenkins Script Console:
docker login -u ${DOCKER_HUB_CREDS_USR} -p ${DOCKER_HUB_CREDS_PSW}
docker images
```

### Test Git Credential

```bash
# In pipeline build:
echo "Testing Git access..."
git clone https://${GIT_CREDENTIALS_USR}:${GIT_CREDENTIALS_PSW}@github.com/your-username/your-repo.git test-repo
```

---

## Step 6: Pipeline Environment Variables

The Jenkinsfile automatically extracts credentials:

```groovy
environment {
    // Docker credentials (usernamePassword type)
    DOCKER_HUB_CREDS = credentials('dockerhub-creds')
    DOCKER_HUB_USER = "${DOCKER_HUB_CREDS_USR}"
    DOCKER_HUB_PASSWORD = "${DOCKER_HUB_CREDS_PSW}"
    
    // Git repository
    GIT_REPO_URL = "${GIT_URL}"
    GIT_BRANCH = "${GIT_BRANCH}"
    GIT_CREDENTIALS_ID = 'github-credentials'
}
```

**How it works:**
- Jenkins retrieves credential: `credentials('dockerhub-creds')`
- Automatically sets: `DOCKER_HUB_CREDS` environment variable
- Jenkins provides: `DOCKER_HUB_CREDS_USR` and `DOCKER_HUB_CREDS_PSW`

---

## 🔄 Pipeline Workflow Overview

```
1. Checkout Code
   ├─ Git URL: from Job configuration
   └─ Credentials: github-credentials
   
2. Build Images
   └─ Create presentation:123 and application:123
   
3. Scan with Trivy
   └─ Generate security reports
   
4. Push to Docker Hub
   ├─ Login: using dockerhub-creds
   ├─ Push: presentation:123, application:123
   └─ Push: latest tags
   
5. Update Helm Values
   ├─ Read: helm-chart/values.yaml
   ├─ Update: image tags to 123
   └─ Save: updated values.yaml
   
6. Commit to Git
   ├─ Author: Jenkins Pipeline (credentials)
   ├─ Message: "Update image tags to 123 [skip ci]"
   └─ Push: to origin/main
   
7. ArgoCD Detects (within 3 minutes)
   ├─ Syncs from Git
   ├─ Deploys new images
   └─ Updates cluster
   
8. Verify Deployment
   └─ Check pod status
```

---

## 🐛 Troubleshooting

### Issue: Docker login fails
**Error:** `permission denied` or `unauthorized`

**Solutions:**
1. Verify credentials in Jenkins:
   - Go to Credentials → Find `dockerhub-creds`
   - Click edit and verify username/token
   
2. Test token locally:
   ```bash
   docker login -u your-username -p your-token
   ```
   
3. Regenerate token if expired:
   - Docker Hub → Settings → Security → Personal access tokens
   - Generate new token, update Jenkins credential

### Issue: Git push fails
**Error:** `fatal: Authentication failed` or `permission denied`

**Solutions:**
1. Check GitHub credentials in Jenkins
2. Verify GitHub token has `repo` scope
3. Test locally:
   ```bash
   git clone https://your-username:your-token@github.com/your-username/your-repo.git
   ```

4. Ensure branch protection doesn't block Jenkins
   - Go to GitHub → Settings → Branches
   - Check branch protection rules
   - Add Jenkins bot as allowed user (if needed)

### Issue: Pipeline hangs on Git push
**Cause:** Git credentials not cached

**Solution:**
Use SSH keys instead of HTTPS:
```groovy
// In Jenkinsfile
sh '''
    git config credential.helper store
    git push origin ${GIT_BRANCH}
'''
```

### Issue: [skip ci] commits don't work
**Cause:** Webhook still triggered despite tag

**Solution:**
Configure GitHub webhook to skip:
- Go to Settings → Webhooks
- Uncheck "Pushes" for commits with `[skip ci]` in message
- Or configure in Jenkinsfile to detect the tag

---

## 🔐 Security Best Practices

### 1. Never Commit Credentials
❌ **Bad:**
```groovy
DOCKER_USER = "myuser"
DOCKER_PASSWORD = "mypassword"
```

✅ **Good:**
```groovy
DOCKER_HUB_CREDS = credentials('dockerhub-creds')
DOCKER_HUB_USER = "${DOCKER_HUB_CREDS_USR}"
```

### 2. Rotate Credentials Regularly
```bash
# Every 3 months:
# 1. Generate new tokens in Docker Hub and GitHub
# 2. Update Jenkins credentials
# 3. Delete old tokens
```

### 3. Limit Token Scopes
- Docker Hub token: Only `push` and `pull` permissions
- GitHub token: Only `repo` scope (not admin)

### 4. Monitor Git Commits
```bash
# Audit pipeline commits
git log --author="Jenkins Pipeline" --oneline | head -20
```

### 5. Audit Trail
```bash
# View all credential access
kubectl logs -n jenkins jenkins-0 | grep "credentials"
```

---

## 📊 Jenkins Configuration Checklist

Before first pipeline run:

- [ ] Jenkins installed and running
- [ ] Required plugins installed (Pipeline, Git, Docker Pipeline)
- [ ] Docker Hub credentials created (`dockerhub-creds`)
- [ ] GitHub credentials created (`github-credentials`)
- [ ] Pipeline job created (`ecommerce-gitops-pipeline`)
- [ ] Git repository URL configured correctly
- [ ] Branch name correct (main/master/etc)
- [ ] Build trigger configured (Poll SCM or Webhook)
- [ ] Jenkinsfile in repository root
- [ ] Git can push to repository (branch protection checked)
- [ ] Docker can push to Docker Hub repo

---

## 🧪 Test Pipeline Execution

### First Build

1. **Manually trigger:**
   - Dashboard → `ecommerce-gitops-pipeline` → **Build Now**

2. **Monitor console:**
   - Click build number → **Console Output**
   - Watch for each stage

3. **Expected flow:**
   - ✅ Checkout
   - ✅ Build Docker Images
   - ✅ Scan with Trivy
   - ✅ Push to Docker Hub
   - ✅ Update Helm Values
   - ✅ Commit & Push to Git
   - ✅ Wait for ArgoCD
   - ✅ Verify Deployment

4. **Verify results:**
   ```bash
   # Check Docker Hub
   docker pull your-username/ecommerce-application:1
   
   # Check Git commits
   git log --oneline | head -5
   
   # Check ArgoCD
   kubectl get application -n argocd
   kubectl get pods -n default
   ```

---

## 🔗 Git Integration Types

### Option 1: Poll SCM (Basic)
```
Jenkins polls Git every 15 minutes
Finds changes → Triggers build
✅ Simple
❌ Delayed (wait up to 15 min)
```

### Option 2: GitHub Webhook (Real-time)
```
GitHub webhook → Jenkins webhook endpoint
Instant build trigger
✅ Real-time
❌ More setup
```

**Setup GitHub Webhook:**
1. Your Repo → Settings → Webhooks → Add webhook
2. Payload URL: `http://your-jenkins/github-webhook/`
3. Event: Push events
4. Click Add webhook

---

## 📈 Next Steps

1. ✅ Configure credentials (Docker Hub, GitHub)
2. ✅ Create pipeline job
3. ✅ Trigger first build
4. **Setup ArgoCD** (see ARGOCD_SETUP.md)
5. **Configure Git webhook** (real-time builds)
6. **Monitor deployments** in ArgoCD UI

---

## 🎓 Learning Path

**Beginner:**
1. Create credentials manually
2. Run first pipeline build
3. Verify images in Docker Hub

**Intermediate:**
1. Set up GitHub webhook
2. Monitor Git commits
3. Connect to ArgoCD

**Advanced:**
1. Implement branch-based deployments
2. Set up environment promotion (dev→staging→prod)
3. Add approval gates for production

---

**Reference:** See CI_CD_PIPELINE_README.md for complete pipeline overview
