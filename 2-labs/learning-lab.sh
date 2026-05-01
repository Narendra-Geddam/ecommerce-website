#!/bin/bash

# learning-lab.sh
# Quick-start script for individual lab scenarios.
# For the full setup menu, use: ./scripts/setup.sh (from repo root)
#
# All tool credentials: admin / admin

set -e

cd "$(dirname "$0")/.."

echo "==========================================="
echo "   Observability Learning Lab Manager"
echo "   (Optimized for iximiuz Playgrounds)"
echo "   All credentials: admin / admin"
echo "==========================================="
echo "1. Start Base App Only (Docker Compose)"
echo "2. Start App + ELK Stack (Docker Compose)"
echo "3. Start App + Prometheus/Grafana (Docker Compose)"
echo "4. Start K8s PLG Stack (Promtail/Loki/Grafana)"
echo "5. Start K8s EFK Stack (Elasticsearch/Fluent Bit/Kibana)"
echo "6. Teardown All Docker Compose Labs"
echo "==========================================="
read -p "Select a lab scenario [1-6]: " choice

case $choice in
  1)
    echo "Starting Base App..."
    docker network create ecommerce-network 2>/dev/null || true
    docker compose up -d
    echo ""
    echo "✅ App running → Frontend: port 80, Backend: port 5000"
    ;;
  2)
    echo "Starting App + ELK Stack..."
    docker network create ecommerce-network 2>/dev/null || true
    docker compose -f docker-compose.yml -f 2-labs/1-elk-docker/docker-compose-elk.yml up -d
    echo ""
    echo "✅ Kibana → port 5601 | Elasticsearch → port 9200"
    echo "   In iximiuz: Click 'Expose Port' → enter the port number"
    ;;
  3)
    echo "Starting App + Prometheus/Grafana..."
    docker network create ecommerce-network 2>/dev/null || true
    docker compose -f docker-compose.yml -f 2-labs/2-prom-grafana-docker/docker-compose-prom.yml up -d
    echo ""
    echo "✅ Grafana → port 3000 (admin/admin) | Prometheus → port 9090"
    echo "   In iximiuz: Click 'Expose Port' → enter the port number"
    ;;
  4)
    echo "Starting K8s PLG Stack..."
    ./2-labs/deploy-observability.sh --stack plg
    echo ""
    echo "✅ Grafana → NodePort 30030 (admin/admin) | Prometheus → NodePort 30090"
    echo "   In iximiuz: Click 'Expose Port' → enter the NodePort number"
    ;;
  5)
    echo "Starting K8s EFK Stack..."
    ./2-labs/deploy-observability.sh --stack efk
    echo ""
    echo "✅ Kibana → NodePort 30056 | Grafana → NodePort 30030 (admin/admin)"
    echo "   In iximiuz: Click 'Expose Port' → enter the NodePort number"
    ;;
  6)
    echo "Tearing down Docker Compose labs..."
    docker compose -f docker-compose.yml -f 2-labs/1-elk-docker/docker-compose-elk.yml -f 2-labs/2-prom-grafana-docker/docker-compose-prom.yml down -v
    echo "✅ All Docker labs torn down."
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac
