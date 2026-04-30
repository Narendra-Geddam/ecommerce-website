#!/bin/bash

# Kubernetes Deployment Prerequisites Script
# This script sets up the necessary Kubernetes resources before pipeline deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${1:-default}"
DOCKER_REGISTRY="${2:-docker.io}"
DOCKER_USERNAME="${3:-}"
DOCKER_PASSWORD="${4:-}"
DATABASE_URL="${5:-postgresql://ecommerce:password@postgres:5432/ecommerce}"
SECRET_KEY="${6:-your-flask-secret-key-here}"

echo -e "${YELLOW}=== Kubernetes Deployment Prerequisites Setup ===${NC}"
echo "Namespace: $NAMESPACE"
echo "Registry: $DOCKER_REGISTRY"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if namespace exists, create if not
echo -e "${YELLOW}[1/5] Checking namespace...${NC}"
if kubectl get namespace "$NAMESPACE" 2>/dev/null; then
    print_status "Namespace '$NAMESPACE' already exists"
else
    echo "Creating namespace '$NAMESPACE'..."
    kubectl create namespace "$NAMESPACE"
    print_status "Namespace created"
fi

# Create Docker registry secret (if credentials provided)
echo -e "${YELLOW}[2/5] Configuring Docker registry secret...${NC}"
if [ -n "$DOCKER_USERNAME" ] && [ -n "$DOCKER_PASSWORD" ]; then
    echo "Creating Docker registry secret..."
    kubectl create secret docker-registry docker-hub-secret \
        --docker-server="$DOCKER_REGISTRY" \
        --docker-username="$DOCKER_USERNAME" \
        --docker-password="$DOCKER_PASSWORD" \
        --docker-email="noreply@example.com" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    print_status "Docker registry secret created/updated"
else
    echo "Skipping Docker registry secret (no credentials provided)"
fi

# Create application secrets
echo -e "${YELLOW}[3/5] Creating application secrets...${NC}"
echo "Creating ecommerce-secrets..."
kubectl create secret generic ecommerce-secrets \
    --from-literal=database-url="$DATABASE_URL" \
    --from-literal=secret-key="$SECRET_KEY" \
    -n "$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -
print_status "Application secrets created/updated"

# Create ConfigMap for application configuration
echo -e "${YELLOW}[4/5] Creating application ConfigMap...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: ecommerce-config
  namespace: $NAMESPACE
data:
  FLASK_ENV: "production"
  SERVICE_NAME: "flask"
  SERVICE_TIER: "backend"
EOF
print_status "ConfigMap created"

# Create RBAC resources for pipeline
echo -e "${YELLOW}[5/5] Setting up RBAC for pipeline...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jenkins-deployer
  namespace: $NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: jenkins-deployer
rules:
- apiGroups: [""]
  resources: ["pods", "pods/logs", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale", "replicasets"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["get", "list"]
- apiGroups: ["extensions"]
  resources: ["ingresses"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: jenkins-deployer
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: jenkins-deployer
subjects:
- kind: ServiceAccount
  name: jenkins-deployer
  namespace: $NAMESPACE
EOF
print_status "RBAC resources created"

# Display summary
echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Namespace: $NAMESPACE"
echo "Resources created:"
echo "  - Namespace"
echo "  - Docker Registry Secret (docker-hub-secret)"
echo "  - Application Secrets (ecommerce-secrets)"
echo "  - ConfigMap (ecommerce-config)"
echo "  - ServiceAccount (jenkins-deployer)"
echo "  - ClusterRole (jenkins-deployer)"
echo "  - ClusterRoleBinding (jenkins-deployer)"
echo ""

# Verify resources
echo -e "${YELLOW}Verifying resources...${NC}"
echo ""
echo "Secrets:"
kubectl get secrets -n "$NAMESPACE" --no-headers
echo ""
echo "ConfigMaps:"
kubectl get configmaps -n "$NAMESPACE" --no-headers
echo ""
echo "ServiceAccounts:"
kubectl get serviceaccounts -n "$NAMESPACE" --no-headers
echo ""

print_status "All prerequisites configured successfully!"
echo ""
echo "Next steps:"
echo "1. Update Docker image references in Helm values"
echo "2. Verify Helm chart syntax: helm lint ./infra/kubernetes/helm"
echo "3. Do a dry-run deployment: helm install --dry-run --debug ecommerce-app ./infra/kubernetes/helm -n $NAMESPACE"
echo "4. Deploy using Helm: helm install ecommerce-app ./infra/kubernetes/helm -n $NAMESPACE"
echo ""
