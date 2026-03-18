# Helm Values Examples for Different Environments

## Development Environment
Create `helm-chart/values-dev.yaml`:

```yaml
replicaCount: 1

# Presentation Tier (Nginx Frontend)
presentation:
  replicaCount: 1
  image:
    repository: your-docker-id/ecommerce-presentation
    pullPolicy: IfNotPresent
    tag: "latest"
  service:
    type: LoadBalancer
    port: 80
    targetPort: 80
  resources:
    limits:
      cpu: 100m
      memory: 128Mi
    requests:
      cpu: 50m
      memory: 64Mi

# Application Tier (Flask Backend)
application:
  replicaCount: 1
  image:
    repository: your-docker-id/ecommerce-application
    pullPolicy: IfNotPresent
    tag: "latest"
  service:
    type: ClusterIP
    port: 5000
    targetPort: 5000
  resources:
    limits:
      cpu: 200m
      memory: 256Mi
    requests:
      cpu: 100m
      memory: 128Mi
  env:
    - name: FLASK_ENV
      value: "development"
    - name: DEBUG
      value: "true"

environment: development
```

**Usage:**
```bash
helm install ecommerce-app ./helm-chart -f helm-chart/values-dev.yaml -n dev
```

---

## Staging Environment
Create `helm-chart/values-staging.yaml`:

```yaml
replicaCount: 2

# Presentation Tier (Nginx Frontend)
presentation:
  replicaCount: 2
  image:
    repository: your-docker-id/ecommerce-presentation
    pullPolicy: IfNotPresent
    tag: "v1.0.0"  # Use specific version in staging
  service:
    type: ClusterIP
    port: 80
    targetPort: 80
  resources:
    limits:
      cpu: 200m
      memory: 256Mi
    requests:
      cpu: 100m
      memory: 128Mi
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values:
              - ecommerce-presentation
          topologyKey: kubernetes.io/hostname

# Application Tier (Flask Backend)
application:
  replicaCount: 2
  image:
    repository: your-docker-id/ecommerce-application
    pullPolicy: IfNotPresent
    tag: "v1.0.0"  # Use specific version in staging
  service:
    type: ClusterIP
    port: 5000
    targetPort: 5000
  resources:
    limits:
      cpu: 300m
      memory: 512Mi
    requests:
      cpu: 150m
      memory: 256Mi
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values:
              - ecommerce-application
          topologyKey: kubernetes.io/hostname

environment: staging
```

**Usage:**
```bash
helm install ecommerce-app ./helm-chart -f helm-chart/values-staging.yaml -n staging
```

---

## Production Environment
Create `helm-chart/values-prod.yaml`:

```yaml
replicaCount: 3

# Presentation Tier (Nginx Frontend)
presentation:
  replicaCount: 3
  image:
    repository: your-docker-id/ecommerce-presentation
    pullPolicy: IfNotPresent
    tag: "v1.0.0"  # Use specific version in production
  service:
    type: LoadBalancer
    port: 80
    targetPort: 80
    # Optional: Configure ingress instead of LoadBalancer
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - ecommerce-presentation
        topologyKey: kubernetes.io/hostname

# Application Tier (Flask Backend)
application:
  replicaCount: 3
  image:
    repository: your-docker-id/ecommerce-application
    pullPolicy: IfNotPresent
    tag: "v1.0.0"  # Use specific version in production
  service:
    type: ClusterIP
    port: 5000
    targetPort: 5000
  resources:
    limits:
      cpu: 500m
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 512Mi
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - ecommerce-application
        topologyKey: kubernetes.io/hostname

environment: production
```

**Usage:**
```bash
helm install ecommerce-app ./helm-chart -f helm-chart/values-prod.yaml -n prod
```

---

## High-Availability Production Setup
Create `helm-chart/values-prod-ha.yaml`:

```yaml
replicaCount: 5

# Presentation Tier
presentation:
  replicaCount: 5
  image:
    repository: your-docker-id/ecommerce-presentation
    pullPolicy: Always
    tag: "v1.0.0"
  service:
    type: LoadBalancer
    port: 80
    targetPort: 80
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - ecommerce-presentation
        topologyKey: kubernetes.io/hostname
  nodeSelector:
    tier: frontend
  tolerations:
    - key: tier
      operator: Equal
      value: frontend
      effect: NoSchedule

# Application Tier
application:
  replicaCount: 5
  image:
    repository: your-docker-id/ecommerce-application
    pullPolicy: Always
    tag: "v1.0.0"
  service:
    type: ClusterIP
    port: 5000
    targetPort: 5000
  resources:
    limits:
      cpu: 1000m
      memory: 2Gi
    requests:
      cpu: 500m
      memory: 1Gi
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - ecommerce-application
        topologyKey: kubernetes.io/hostname
  nodeSelector:
    tier: backend
  tolerations:
    - key: tier
      operator: Equal
      value: backend
      effect: NoSchedule

environment: production-ha
```

**Usage:**
```bash
helm install ecommerce-app ./helm-chart -f helm-chart/values-prod-ha.yaml -n prod
```

---

## Deploying with Different Values Files

### Development:
```bash
helm upgrade --install ecommerce-app ./helm-chart \
  -f helm-chart/values-dev.yaml \
  -n dev --create-namespace \
  --wait
```

### Staging:
```bash
helm upgrade --install ecommerce-app ./helm-chart \
  -f helm-chart/values-staging.yaml \
  -n staging --create-namespace \
  --wait --timeout 10m
```

### Production:
```bash
helm upgrade --install ecommerce-app ./helm-chart \
  -f helm-chart/values-prod.yaml \
  -n prod --create-namespace \
  --wait --timeout 15m
```

### High-Availability Production:
```bash
helm upgrade --install ecommerce-app ./helm-chart \
  -f helm-chart/values-prod-ha.yaml \
  -n prod-ha --create-namespace \
  --wait --timeout 20m
```

---

## Override Specific Values via CLI

You can override values without separate files:

```bash
helm install ecommerce-app ./helm-chart \
  --set image.presentation.repository=myregistry/ecommerce-presentation \
  --set image.presentation.tag=v2.0.0 \
  --set image.application.repository=myregistry/ecommerce-application \
  --set image.application.tag=v2.0.0 \
  --set presentation.replicaCount=3 \
  --set application.replicaCount=3 \
  -n prod
```

---

## Environment-Specific Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash

ENVIRONMENT=${1:-dev}
NAMESPACE=${2:-$ENVIRONMENT}

case $ENVIRONMENT in
  dev)
    echo "Deploying to Development..."
    helm upgrade --install ecommerce-app ./helm-chart \
      -f helm-chart/values-dev.yaml \
      -n $NAMESPACE --create-namespace
    ;;
  staging)
    echo "Deploying to Staging..."
    helm upgrade --install ecommerce-app ./helm-chart \
      -f helm-chart/values-staging.yaml \
      -n $NAMESPACE --create-namespace \
      --wait --timeout 10m
    ;;
  prod)
    echo "Deploying to Production..."
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
      echo "Cancelled."
      exit 1
    fi
    helm upgrade --install ecommerce-app ./helm-chart \
      -f helm-chart/values-prod.yaml \
      -n $NAMESPACE --create-namespace \
      --wait --timeout 15m
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    echo "Usage: ./deploy.sh [dev|staging|prod]"
    exit 1
    ;;
esac

echo "Deployment complete!"
kubectl get deployments -n $NAMESPACE
```

**Usage:**
```bash
chmod +x deploy.sh
./deploy.sh dev
./deploy.sh staging
./deploy.sh prod
```

---

## Checking Deployed Configuration

```bash
# See your deployed values
helm get values ecommerce-app -n dev

# See the actual manifest being deployed
helm get manifest ecommerce-app -n dev

# View deployment history
helm history ecommerce-app -n dev

# Rollback to previous version
helm rollback ecommerce-app 1 -n dev
```
