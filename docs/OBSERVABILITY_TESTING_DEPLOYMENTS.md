# Observability & Testing Guide

## Overview

This document covers the complete observability, testing, and deployment strategy for the e-commerce system.

---

## Part 1: Observability Stack

### Components

| Component | Purpose | Port | Interface |
|-----------|---------|------|-----------|
| **Prometheus** | Metrics collection & storage | 9090 | http://prometheus:9090 |
| **Grafana** | Dashboards & visualization | 3000 | http://grafana:3000 |
| **Loki** | Log aggregation | 3100 | http://loki:3100 |
| **Promtail** | Log shipper | - | DaemonSet |
| **Jaeger** | Distributed tracing | 16686 | http://jaeger:16686 |

### Installation

#### 1. Deploy Observability Stack

```bash
# Deploy to Kubernetes
kubectl apply -f infra/kubernetes/observability/prometheus-config.yaml
kubectl apply -f infra/kubernetes/observability/grafana-config.yaml
kubectl apply -f infra/kubernetes/observability/loki-promtail-config.yaml
kubectl apply -f infra/kubernetes/observability/jaeger-config.yaml

# Verify deployment
kubectl get all -n monitoring

# Port forward to access dashboards
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
kubectl port-forward -n monitoring svc/grafana 3000:80 &
kubectl port-forward -n monitoring svc/jaeger 16686:16686 &
```

#### 2. Configure Prometheus

Prometheus automatically discovers Kubernetes pods with these annotations:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

#### 3. Access Grafana

- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: GrafanaAdminPassword123!
- **Dashboard**: "E-Commerce System"

### Metrics Available

#### Application Metrics

```
# HTTP Requests
flask_http_request_total{method, endpoint, status}
flask_http_request_duration_seconds_bucket{method, endpoint}

# Business Metrics
ecommerce_shopping_cart_items_total{product_id}
ecommerce_orders_total{status}
ecommerce_order_value_total{currency}
ecommerce_users_registered_total

# Database Metrics
ecommerce_db_query_duration_seconds{query_type}
ecommerce_db_connection_pool_size
```

#### Querying Examples

```promql
# Request rate (requests/sec)
rate(flask_http_request_total[5m])

# Error rate
rate(flask_http_request_total{status=~"5.."}[5m])

# 95th percentile response time
histogram_quantile(0.95, flask_http_request_duration_seconds_bucket)

# Orders per minute
rate(ecommerce_orders_total[1m])

# Average order value
increase(ecommerce_order_value_total[1h]) / increase(ecommerce_orders_total[1h])
```

### Logs

Logs are collected by Promtail and stored in Loki. Access via Grafana's Loki datasource.

```
# Filter by pod
{pod="ecommerce-backend-xyz"}

# Filter by level
{pod=~"ecommerce-.*"} | json | level="ERROR"

# Show backend errors
{pod=~"ecommerce-backend.*"} | json level="ERROR" | pattern "<_> <_>"
```

### Distributed Tracing

Jaeger collects distributed traces from instrumented services.

```bash
# Frontend
curl http://localhost:16686  # Jaeger UI

# Services are automatically traced:
# - Flask API calls
# - Database queries
# - External requests
```

---

## Part 2: Testing Strategy

### Setup

#### 1. Install Test Dependencies

```bash
cd apps/backend
pip install -r requirements-test.txt
```

#### 2. Test Structure

```
tests/
├── conftest.py              # Shared fixtures & config
├── test_api.py              # API endpoint tests
├── test_auth.py             # Authentication tests
├── test_observability.py    # Observability tests
└── pytest.ini               # Pytest configuration
```

### Running Tests

#### Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::TestProductAPI::test_get_products

# Run with coverage
pytest --cov=apps/backend --cov-report=html

# Run with verbosity
pytest -vv --tb=long
```

#### Test Markers

```bash
# Run only API tests
pytest -m api

# Run integration tests (requires DB)
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run observability tests
pytest -m observability
```

### CI/CD Integration

The Jenkins pipeline runs tests automatically:

```groovy
stage('Run Tests') {
    when {
        expression { params.SKIP_TESTS == false }
    }
    steps {
        sh '''
            pytest tests/ -v --junit-xml=test-results.xml
        '''
    }
}
```

Test results are archived and displayed in Jenkins dashboard.

### Test Coverage

Target: **>80% code coverage**

```bash
# Generate coverage report
pytest --cov=apps/backend --cov-report=html

# View report
open htmlcov/index.html
```

---

## Part 3: Deployment Strategies

### Three Supported Strategies

#### 1. Canary Deployment (Recommended for Production)

**Progressive rollout with traffic shifting**

```
Timeline:
Minute 0   ▓░░░░░░░░░ 5% canary
Minute 5   ▓▓░░░░░░░░ 10% canary
Minute 10  ▓▓▓▓░░░░░░ 20% canary
Minute 15  ▓▓▓▓▓▓░░░░ 40% canary
Minute 20  ▓▓▓▓▓▓▓▓▓░ 95% canary
Minute 25  ▓▓▓▓▓▓▓▓▓▓ 100% canary (complete)
```

**Features**:
- Automatic rollback on errors
- Real-time metrics monitoring
- Zero downtime
- Safe for critical systems

**Configuration**:

```bash
# Jenkins parameters
DEPLOYMENT_STRATEGY = "canary"
CANARY_WEIGHT = "5"        # Start with 5% traffic

# Istio VirtualService automatically routes traffic
```

**How it works**:

1. New pods deployed with `version=canary` label
2. Istio VirtualService routes 5% traffic to canary
3. Prometheus collects metrics from canary pods
4. If error rate > threshold: rollback
5. If healthy: gradually increase traffic
6. After 25 minutes: canary becomes stable

#### 2. Blue-Green Deployment

**Complete version swap**

```
Timeline:
T=0    🔵 Blue (stable)  ← users
       🟢 Green (new)

T=+1m  🔵 Blue (old)
       🟢 Green (stable) ← users (instant switch)
```

**Features**:
- Instant rollback
- Full testing before switch
- High resource usage

**Configuration**:

```bash
DEPLOYMENT_STRATEGY = "blue-green"
```

#### 3. Rolling Deployment (Default)

**One-by-one pod replacement**

```
Timeline:
T=0   🟦🟦🟦  (3 blue pods, 0 green)
T=+50s 🟦🟦🟩  (2 blue, 1 green)
T=+100s 🟦🟩🟩  (1 blue, 2 green)
T=+150s 🟩🟩🟩  (3 green, 0 blue) ✅
```

**Features**:
- Gradual rollout
- Low resource usage
- Slower deployment time

**Configuration**:

```bash
DEPLOYMENT_STRATEGY = "rolling"
```

### Deployment Process

#### 1. Trigger Deployment

```bash
# Via Jenkins UI:
# 1. Click "Build with Parameters"
# 2. Select DEPLOYMENT_STRATEGY
# 3. Set CANARY_WEIGHT (for canary)
# 4. Click "Build"

# Or via CLI:
curl -X POST http://jenkins:8080/job/ecommerce/buildWithParameters \
  -u admin:password \
  -F DEPLOYMENT_STRATEGY=canary \
  -F CANARY_WEIGHT=5
```

#### 2. Pipeline Steps

```
✅ Checkout Code
  ↓
🧪 Run Tests (if enabled)
  ↓
🔨 Build Images (parallelized)
  ├─ Build Frontend
  └─ Build Backend
  ↓
🔍 Security Scan (Trivy)
  ↓
📤 Push to Docker Hub
  ↓
📝 Update Helm Chart
  ↓
🚀 Deploy with Selected Strategy
  ├─ Canary: Progressive rollout
  ├─ Blue-Green: Instant switch
  └─ Rolling: One-by-one
  ↓
🏥 Health Checks
  ↓
🔥 Smoke Tests
  ↓
📊 Monitor (if canary)
  ↓
🔗 Commit & Push
  ↓
✅ Complete
```

### Monitoring During Deployment

#### Canary Monitoring

```bash
# Watch canary rollout
kubectl get pods -n prod-ecommerce -l app=ecommerce-backend -w

# Check traffic distribution
kubectl exec -n monitoring prometheus-0 -- \
  promtool query instant 'rate(flask_http_request_total[1m]) by (version)'

# View canary metrics
# In Grafana: E-Commerce Dashboard → Canary Metrics

# Check Jaeger traces
# Visit http://localhost:16686 → Search → Service: ecommerce-backend
```

#### Alert During Deployment

Prometheus alerts configured for:

- Error rate > 1%
- Response time > 500ms
- Pod crash loops
- Database connection limit
- Memory usage > 80%

If any alert triggers during canary: **automatic rollback**

### Rollback Procedure

#### Automatic (Canary)

```
❌ Error detected
  → Error rate spike
  → Alert triggered
  → Canary pods terminated
  → Traffic reverted to stable
  → Original version active
  → Pipeline marked as FAILED
```

#### Manual

```bash
# For any strategy:

# Option 1: Revert Helm values
git revert HEAD
git push origin main
# Pipeline auto-triggers

# Option 2: Manual kubectl
kubectl rollout undo deployment/ecommerce-backend -n prod-ecommerce

# Option 3: Restore from backup
helm upgrade ecommerce ./infra/kubernetes/helm \
  --values helm-values-backup.yaml \
  -n prod-ecommerce
```

---

## Part 4: Best Practices

### Observability

✅ **DO**:
- Add custom business metrics (orders, revenue, user signups)
- Set meaningful alert thresholds
- Regularly review dashboards
- Document metric runbooks

❌ **DON'T**:
- Alert on every metric
- Leave default thresholds unchanged
- Ignore logs and traces
- Skip health check endpoints

### Testing

✅ **DO**:
- Write tests for new endpoints
- Run full test suite before deployment
- Target 80%+ coverage
- Test error scenarios

❌ **DON'T**:
- Skip tests for "small changes"
- Assume manual testing is enough
- Test only happy path
- Ignore flaky tests

### Deployment

✅ **DO**:
- Use canary for production
- Monitor first 30 minutes closely
- Have rollback plan ready
- Test in staging first

❌ **DON'T**:
- Deploy directly to production
- Ignore alerts during deployment
- Deploy during peak hours (if possible)
- Skip smoke tests

---

## Troubleshooting

### Prometheus Not Scraping

```bash
# Check targets
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Visit http://localhost:9090/targets

# Check pod annotations
kubectl get pod -n prod-ecommerce -o yaml | grep prometheus

# Solution: Add annotations
prometheus.io/scrape: "true"
prometheus.io/port: "5000"
prometheus.io/path: "/metrics"
```

### Grafana Dashboards Empty

```bash
# Check datasource
Grafana → Configuration → Data sources → Prometheus → Test

# Check query
Grafana → Explore → Query Editor → Verify PromQL

# Solution: Wait for metrics
# Metrics only appear after requests are made
```

### Traces Not Appearing

```bash
# Check Jaeger connectivity
kubectl exec -n prod-ecommerce deployment/ecommerce-backend -- \
  curl -v http://jaeger:14268/api/traces

# Check instrumentation
# Verify observability.py is imported in app.py
```

### Canary Stuck in Progress

```bash
# Check status
kubectl get canary -n prod-ecommerce

# Check metrics
kubectl logs deployment/flagger-loadtester -n prod-ecommerce

# Manual trigger: Skip analysis
kubectl patch canary ecommerce-canary -n prod-ecommerce \
  --type merge -p '{"spec":{"skipAnalysis":true}}'
```

---

## Next Steps

1. **Deploy observability stack** to EKS cluster
2. **Instrument the application** with observability.py
3. **Run test suite** to ensure coverage
4. **Configure alerting** for business metrics
5. **Plan canary migration** from rolling deployments
6. **Update documentation** with runbooks for each alert
