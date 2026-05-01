#!/bin/bash

# deploy-observability.sh
# Script to deploy the selected observability stack to the Kubernetes cluster.
# Optimized for iximiuz Labs (NodePort access, no port-forward needed).

set -e

# Default values
STACK="plg"
NAMESPACE="monitoring"

# Resolve KUBE_DIR relative to repo root
cd "$(dirname "$0")/.."
REPO_ROOT=$(pwd)
KUBE_DIR="${REPO_ROOT}/3-kubernetes/observability"

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Deploy observability stack to the cluster."
    echo ""
    echo "Options:"
    echo "  --stack STACK     Specify the stack to deploy: 'plg' (Loki), 'efk' (Elasticsearch), or 'both' (default: $STACK)"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --stack efk"
    echo "  $0 --stack both"
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --stack) STACK="$2"; shift ;;
        --help) usage; exit 0 ;;
        *) echo "Unknown parameter passed: $1"; usage; exit 1 ;;
    esac
    shift
done

# Create namespace if it doesn't exist
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Deploy Base Observability Components (Prometheus, Grafana, Jaeger)
echo "📊 Deploying base observability components (Prometheus, Grafana, Jaeger)..."
kubectl apply -f "${KUBE_DIR}/prometheus-config.yaml"
kubectl apply -f "${KUBE_DIR}/grafana-config.yaml"
kubectl apply -f "${KUBE_DIR}/jaeger-config.yaml"

if [[ "$STACK" == "plg" || "$STACK" == "both" ]]; then
    echo "📋 Deploying PLG Stack (Promtail & Loki)..."
    kubectl apply -f "${KUBE_DIR}/loki-promtail-config.yaml"
fi

if [[ "$STACK" == "efk" || "$STACK" == "both" ]]; then
    echo "📋 Deploying EFK Stack (Elasticsearch, Fluent Bit, Kibana)..."
    kubectl apply -f "${KUBE_DIR}/efk-config.yaml"
fi

echo ""
echo "⏳ Waiting for pods to initialize..."
kubectl wait --for=condition=ready pod -l app=prometheus -n $NAMESPACE --timeout=120s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app=grafana -n $NAMESPACE --timeout=120s 2>/dev/null || true

echo ""
echo "==========================================="
echo "   ✅ Observability Stack Deployed!"
echo "==========================================="
echo ""
echo "   All credentials: admin / admin"
echo ""
echo "   📊 Prometheus:  NodePort 30090"
echo "   📈 Grafana:     NodePort 30030"

if [[ "$STACK" == "efk" || "$STACK" == "both" ]]; then
    echo "   🔍 Kibana:      NodePort 30056"
fi

echo ""
echo "   In iximiuz Labs → Click 'Expose Port' → Enter the port number above."
echo "   In AWS EKS → Change service type to LoadBalancer in the YAML manifests."
echo "==========================================="
echo ""
echo "   Check status: kubectl get all -n $NAMESPACE"
echo ""
