# GitOps with ArgoCD

ArgoCD is a declarative, GitOps continuous delivery tool for Kubernetes. It continuously monitors this Git repository and ensures that the live state of your Kubernetes cluster matches the desired state defined in your Helm charts.

## Credentials

| Field    | Value   |
|----------|---------|
| Username | `admin` |
| Password | `admin` |

## Quick Start (One Command)

```bash
chmod +x 4-ci-cd/argocd/install-argocd.sh
./4-ci-cd/argocd/install-argocd.sh
```

This script will:
1. Create the `argocd` namespace
2. Install the official ArgoCD manifests
3. Patch the server service to **NodePort 30081** (HTTP) / **30080** (HTTPS)
4. Disable HTTPS redirect (required for iximiuz proxy)
5. Set the admin password to `admin`

## Accessing the UI

### In iximiuz Labs
1. Click **Expose Port** in the iximiuz UI
2. Enter port **30081**
3. Open the generated URL
4. Login with `admin` / `admin`

### In AWS EKS (Production)
Change the ArgoCD server service type to `LoadBalancer`:
```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
```
Then access via the provisioned NLB hostname.

## Deploy the Application

Once ArgoCD is running, register your e-commerce app by applying the Application manifest:

```bash
# Edit application.yaml first — update the repoURL to your GitHub fork
kubectl apply -f 4-ci-cd/argocd/application.yaml
```

### What application.yaml does:
- Points ArgoCD at the `3-kubernetes/helm` directory in this repo
- Deploys to the `prod-ecommerce` namespace
- Enables **automated sync** with self-heal and prune
- Creates the namespace automatically if it doesn't exist

## The Complete GitOps Workflow

```
Developer pushes code
        ↓
GitHub Actions runs CI pipeline (.github/workflows/ci-cd.yml)
        ↓
Tests → Build Docker Images → Trivy Security Scan → Push to Docker Hub
        ↓
GitHub Actions commits new image tag to 3-kubernetes/helm/values.yaml
        ↓
ArgoCD detects the Git change (polling every 3 minutes)
        ↓
ArgoCD syncs the new Helm chart to the live Kubernetes cluster
        ↓
Application is live with zero manual intervention!
```

## Files in this Directory

| File                  | Purpose                                    |
|-----------------------|--------------------------------------------|
| `install-argocd.sh`   | Automated install script (NodePort + creds) |
| `application.yaml`    | ArgoCD Application manifest for GitOps      |
| `README.md`           | This documentation                          |
