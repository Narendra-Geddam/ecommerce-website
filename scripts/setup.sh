#!/bin/bash

# setup.sh
# Master setup script for the DevOps E-Commerce Learning Lab.
# Deploys the full stack with a single command.
# Optimized for iximiuz Labs (https://labs.iximiuz.com/)
#
# Default Credentials for ALL tools: admin / admin

set -e

cd "$(dirname "$0")/.."
REPO_ROOT=$(pwd)

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       🚀 DevOps E-Commerce Learning Lab Setup          ║"
echo "║       Optimized for iximiuz Labs Playgrounds            ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  All tool credentials:  admin / admin                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Select your environment:"
echo ""
echo "  ── Docker Compose (Local / iximiuz Docker playground) ──"
echo "  1) App Only            (ports: 80, 5000)"
echo "  2) App + ELK Stack     (+ Kibana 5601, Elasticsearch 9200)"
echo "  3) App + Prom/Grafana  (+ Prometheus 9090, Grafana 3000)"
echo "  4) App + Full Stack    (All of the above)"
echo ""
echo "  ── Kubernetes (iximiuz k3s playground) ─────────────────"
echo "  5) K8s App + PLG Stack          (Grafana 30030, Prometheus 30090)"
echo "  6) K8s App + EFK Stack          (Kibana 30056, Grafana 30030)"
echo "  7) K8s App + Full Observability (All K8s tools)"
echo "  8) K8s App + ArgoCD GitOps      (ArgoCD 30081)"
echo "  9) K8s Full Setup (Everything)  (All tools + ArgoCD)"
echo ""
echo "  ── Utilities ───────────────────────────────────────────"
echo "  0) Teardown Everything"
echo ""
read -p "  Select [0-9]: " choice

case $choice in
  1)
    echo ""
    echo "🚀 Starting Base App (Docker Compose)..."
    docker network create ecommerce-network 2>/dev/null || true
    docker compose up -d
    echo ""
    echo "✅ App is running!"
    echo "   Frontend: http://localhost:80"
    echo "   Backend:  http://localhost:5000"
    ;;

  2)
    echo ""
    echo "🚀 Starting App + ELK Stack..."
    docker network create ecommerce-network 2>/dev/null || true
    docker compose -f docker-compose.yml -f 2-labs/1-elk-docker/docker-compose-elk.yml up -d
    echo ""
    echo "✅ App + ELK running!"
    echo "   Frontend:       http://localhost:80"
    echo "   Kibana:         http://localhost:5601"
    echo "   Elasticsearch:  http://localhost:9200"
    ;;

  3)
    echo ""
    echo "🚀 Starting App + Prometheus/Grafana..."
    docker network create ecommerce-network 2>/dev/null || true
    docker compose -f docker-compose.yml -f 2-labs/2-prom-grafana-docker/docker-compose-prom.yml up -d
    echo ""
    echo "✅ App + Monitoring running!"
    echo "   Frontend:    http://localhost:80"
    echo "   Grafana:     http://localhost:3000  (admin / admin)"
    echo "   Prometheus:  http://localhost:9090"
    ;;

  4)
    echo ""
    echo "🚀 Starting App + Full Observability Stack..."
    docker network create ecommerce-network 2>/dev/null || true
    docker compose \
      -f docker-compose.yml \
      -f 2-labs/1-elk-docker/docker-compose-elk.yml \
      -f 2-labs/2-prom-grafana-docker/docker-compose-prom.yml \
      up -d
    echo ""
    echo "✅ Full Docker stack running!"
    echo "   Frontend:       http://localhost:80"
    echo "   Grafana:        http://localhost:3000  (admin / admin)"
    echo "   Prometheus:     http://localhost:9090"
    echo "   Kibana:         http://localhost:5601"
    echo "   Elasticsearch:  http://localhost:9200"
    ;;

  5)
    echo ""
    echo "🚀 Deploying K8s App + PLG Stack..."
    kubectl apply -k 3-kubernetes/base/ 2>/dev/null || kubectl apply -f 3-kubernetes/base/ 2>/dev/null || true
    ./2-labs/deploy-observability.sh --stack plg
    echo ""
    echo "✅ K8s PLG Stack deployed!"
    echo "   Grafana:     NodePort 30030  (admin / admin)"
    echo "   Prometheus:  NodePort 30090"
    echo "   → In iximiuz: Click 'Expose Port' → enter the port number"
    ;;

  6)
    echo ""
    echo "🚀 Deploying K8s App + EFK Stack..."
    kubectl apply -k 3-kubernetes/base/ 2>/dev/null || kubectl apply -f 3-kubernetes/base/ 2>/dev/null || true
    ./2-labs/deploy-observability.sh --stack efk
    echo ""
    echo "✅ K8s EFK Stack deployed!"
    echo "   Kibana:      NodePort 30056"
    echo "   Grafana:     NodePort 30030  (admin / admin)"
    echo "   Prometheus:  NodePort 30090"
    echo "   → In iximiuz: Click 'Expose Port' → enter the port number"
    ;;

  7)
    echo ""
    echo "🚀 Deploying K8s Full Observability..."
    kubectl apply -k 3-kubernetes/base/ 2>/dev/null || kubectl apply -f 3-kubernetes/base/ 2>/dev/null || true
    ./2-labs/deploy-observability.sh --stack both
    echo ""
    echo "✅ Full K8s observability deployed!"
    echo "   Grafana:     NodePort 30030  (admin / admin)"
    echo "   Prometheus:  NodePort 30090"
    echo "   Kibana:      NodePort 30056"
    echo "   → In iximiuz: Click 'Expose Port' → enter the port number"
    ;;

  8)
    echo ""
    echo "🚀 Deploying K8s App + ArgoCD..."
    kubectl apply -k 3-kubernetes/base/ 2>/dev/null || kubectl apply -f 3-kubernetes/base/ 2>/dev/null || true
    chmod +x 4-ci-cd/argocd/install-argocd.sh
    ./4-ci-cd/argocd/install-argocd.sh
    echo ""
    echo "✅ ArgoCD deployed!"
    echo "   ArgoCD UI:  NodePort 30081  (admin / admin)"
    echo "   → In iximiuz: Click 'Expose Port' → enter 30081"
    ;;

  9)
    echo ""
    echo "🚀 Deploying EVERYTHING (Full K8s + Observability + ArgoCD)..."
    kubectl apply -k 3-kubernetes/base/ 2>/dev/null || kubectl apply -f 3-kubernetes/base/ 2>/dev/null || true
    ./2-labs/deploy-observability.sh --stack both
    chmod +x 4-ci-cd/argocd/install-argocd.sh
    ./4-ci-cd/argocd/install-argocd.sh
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║              ✅ FULL STACK DEPLOYED!                    ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  All credentials: admin / admin                         ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  📊 Prometheus:  NodePort 30090                        ║"
    echo "║  📈 Grafana:     NodePort 30030                        ║"
    echo "║  🔍 Kibana:      NodePort 30056                        ║"
    echo "║  🚀 ArgoCD:      NodePort 30081                        ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  In iximiuz → Click 'Expose Port' → Enter port number  ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    ;;

  0)
    echo ""
    echo "🧹 Tearing down everything..."
    docker compose \
      -f docker-compose.yml \
      -f 2-labs/1-elk-docker/docker-compose-elk.yml \
      -f 2-labs/2-prom-grafana-docker/docker-compose-prom.yml \
      down -v 2>/dev/null || true
    kubectl delete namespace monitoring 2>/dev/null || true
    kubectl delete namespace argocd 2>/dev/null || true
    kubectl delete namespace prod-ecommerce 2>/dev/null || true
    echo "✅ All resources cleaned up."
    ;;

  *)
    echo "❌ Invalid choice. Exiting."
    exit 1
    ;;
esac
