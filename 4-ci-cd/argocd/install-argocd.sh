#!/bin/bash
# install-argocd.sh
# Installs ArgoCD into the Kubernetes cluster with NodePort access.
# Optimized for iximiuz Labs (https://labs.iximiuz.com/)
# Default Credentials: admin / admin

set -e

echo "==========================================="
echo "   🚀 ArgoCD Installation (NodePort Mode)"
echo "   Optimized for iximiuz Labs"
echo "==========================================="

# Step 1: Create namespace
echo ""
echo "📦 Step 1: Creating argocd namespace..."
kubectl create namespace argocd 2>/dev/null || echo "  ↳ Namespace already exists, skipping."

# Step 2: Install ArgoCD
echo ""
echo "📥 Step 2: Installing ArgoCD manifests..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Step 3: Wait for pods
echo ""
echo "⏳ Step 3: Waiting for ArgoCD pods to be ready (this may take 1-2 minutes)..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# Step 4: Patch ArgoCD server to use NodePort
echo ""
echo "🔧 Step 4: Patching ArgoCD server service to NodePort 30080..."
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort", "ports": [{"port": 443, "targetPort": 8080, "nodePort": 30080, "name": "https"}, {"port": 80, "targetPort": 8080, "nodePort": 30081, "name": "http"}]}}'

# Step 5: Disable HTTPS redirect (needed for iximiuz proxy)
echo ""
echo "🔧 Step 5: Disabling HTTPS redirect for lab environment..."
kubectl -n argocd patch configmap argocd-cmd-params-cm --type merge -p '{"data": {"server.insecure": "true"}}'

# Restart ArgoCD server to pick up the config change
kubectl rollout restart deployment argocd-server -n argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s

# Step 6: Set admin password to 'admin'
echo ""
echo "🔐 Step 6: Setting admin password to 'admin'..."
# Install argocd CLI if not present
if ! command -v argocd &> /dev/null; then
    echo "  ↳ Installing ArgoCD CLI..."
    curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
    chmod +x /usr/local/bin/argocd
fi

# Get the initial auto-generated password
INIT_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

# Login and change password to 'admin'
argocd login localhost:30080 --insecure --username admin --password "$INIT_PASSWORD" || \
argocd login 127.0.0.1:30080 --insecure --username admin --password "$INIT_PASSWORD"

argocd account update-password --current-password "$INIT_PASSWORD" --new-password "admin" --insecure

echo ""
echo "==========================================="
echo "   ✅ ArgoCD Installation Complete!"
echo "==========================================="
echo ""
echo "   🌐 Access UI:  http://<NODE_IP>:30081"
echo "   👤 Username:   admin"
echo "   🔑 Password:   admin"
echo ""
echo "   In iximiuz Labs:"
echo "   → Click 'Expose Port' → Enter 30081"
echo "   → Open the generated URL"
echo "==========================================="
