# 🚀 MoreCraze E-Commerce Application on AWS EKS

> **Production-Ready Infrastructure as Code | AWS RDS & EKS Deployment | Enterprise-Level Architecture**

<!-- Badges -->
<div align="center">

![Kubernetes](https://img.shields.io/badge/Kubernetes-1.19%2B-326CE5?style=for-the-badge&logo=kubernetes)
![Terraform](https://img.shields.io/badge/Terraform-1.0%2B-7B42BC?style=for-the-badge&logo=terraform)
![Helm](https://img.shields.io/badge/Helm-3.0%2B-0F1689?style=for-the-badge&logo=helm)
![AWS](https://img.shields.io/badge/AWS-EKS-FF9900?style=for-the-badge&logo=amazon-aws)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker)

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql)
![Flask](https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask)
![Nginx](https://img.shields.io/badge/Nginx-Frontend-009639?style=for-the-badge&logo=nginx)
![SSL/TLS](https://img.shields.io/badge/SSL%2FTLS-HTTPS-00AA00?style=for-the-badge&logo=letsencrypt)

![Status](https://img.shields.io/badge/Status-Production--Ready-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [🗺️ The Learning Curriculum (Start Here!)](#️-the-learning-curriculum-start-here)
2. [Quick Start](#quick-start)
3. [Helm Deployment (Recommended)](#helm-deployment-recommended)
4. [Architecture Diagrams (SVG)](#architecture-diagrams-svg)
5. [Architecture Overview](#architecture-overview)
6. [Prerequisites](#prerequisites)
7. [Project Structure](#project-structure)
8. [Observability Learning Labs (iximiuz)](#observability-learning-labs-iximiuz)
9. [Terraform - Secrets & Parameters](#terraform---secrets--parameters)
10. [External Secrets Integration](#external-secrets-integration)
11. [IRSA Setup](#irsa-setup)
12. [Deployment Methods](#deployment-methods)
13. [Troubleshooting](#troubleshooting)
14. [AWS CLI Commands Reference](#aws-cli-commands-reference)
15. [Cleanup & Destruction](#cleanup--destruction)

---

## 🗺️ The Learning Curriculum (Start Here!)

Welcome to the ultimate DevOps learning repository! This isn't just a dummy application—it's a full **"Production Simulator"** designed to take you from running a basic application locally to deploying an enterprise-grade, observable Kubernetes cluster on AWS.

This repository is designed to be learned in phases. Follow this roadmap to build your skills step-by-step:

### Phase 1: Application & Containerization Basics
- **Goal:** Understand the 3-tier architecture.
- **Where to look:** The root `docker-compose.yml` and the `1-apps/` directory.
- **Action:** Run the app locally to see how Nginx, Flask, and Postgres interact.
  ```bash
  docker compose up -d
  curl http://localhost/health
  ```

### Phase 2: Observability Fundamentals (The Labs)
- **Goal:** Learn how to capture logs and metrics before introducing Kubernetes complexity.
- **Where to look:** The `2-labs/` directory.
- **Action:** Use [iximiuz Labs](https://labs.iximiuz.com/) to complete the observability modules.
  - `2-labs/1-elk-docker/`: Learn basic log scraping with Fluent Bit & ELK.
  - `2-labs/2-prom-grafana-docker/`: Learn metrics scraping with Prometheus.
  - `2-labs/3-plg-k8s/`: Introduction to K8s logging with Promtail/Loki.
  - `2-labs/4-efk-k8s/`: Enterprise K8s logging with Fluent Bit/Elasticsearch.

### Phase 3: Kubernetes Fundamentals
- **Goal:** Graduate from Docker Compose to enterprise container orchestration.
- **Where to look:** `3-kubernetes/`
- **Action:** Deploy the app using standard Kubernetes manifests (`base/`) and then learn how to package it for production using Helm charts (`helm/`).

### Phase 4: CI/CD Pipeline Automation
- **Goal:** Automate testing and deployment.
- **Where to look:** The `4-ci-cd/jenkins/` folder and the root `Jenkinsfile`.
- **Action:** Read the `Jenkinsfile` to understand how the code is tested, built, and pushed automatically.

### Phase 5: Infrastructure as Code (AWS & Terraform)
- **Goal:** Provision real-world cloud resources.
- **Where to look:** `5-terraform/`
- **Action:** Learn how to provision AWS Secrets Manager, Parameter Store, and RDS using Terraform.

*(For detailed technical documentation on how to deploy these phases, see the sections below).*

---

## Architecture Diagrams (SVG)

These diagrams are stored as SVG files for long-term reuse and easy updates.

### 1) Complete Workflow and Architecture

![Complete Workflow and Architecture](docs/diagrams/01-complete-workflow-architecture.svg)

### 2) Folder Structure and Component Hierarchy

![Folder Structure and Component Hierarchy](docs/diagrams/02-folder-structure-hierarchy.svg)

### 3) Observability and Canary Deployment Architecture

![Observability and Canary Deployment Architecture](docs/diagrams/03-observability-canary-architecture.svg)

### 4) Complete Testing and Deployment Pipeline

![Complete Testing and Deployment Pipeline](docs/diagrams/04-testing-deployment-pipeline.svg)

### 5) New Components and Capabilities Added

![New Components and Capabilities Added](docs/diagrams/05-new-components-capabilities.svg)

---

## Quick Start

### 3-Minute Helm Deployment

```powershell
# 1. Deploy Terraform secrets (AWS credentials & parameters)
cd 5-terraform
terraform init
terraform apply

# 2. Deploy entire application using Helm
cd ../..
helm install ecommerce ./3-kubernetes/helm -n prod-ecommerce --create-namespace

# 3. Verify deployment
kubectl get all -n prod-ecommerce
kubectl get externalsecrets -n prod-ecommerce -o wide
```

**Expected Result:** All pods running, External Secrets syncing, app accessible

### Destroy When Done

```powershell
# Helm uninstall
helm uninstall ecommerce -n prod-ecommerce

# Terraform destroy
cd terraform
terraform destroy
```

---

## Helm Deployment (Recommended)

### Why Helm?

- **Package Management**: All K8s resources in one chart
- **Version Control**: Easy to version and rollback
- **Templating**: Dynamic values for different environments
- **GitOps Ready**: ArgoCD can read and deploy Helm charts
- **Easy Updates**: Single command to update all components

### Setup

```powershell
# Install Helm (if not already installed)
# Windows: choco install kubernetes-helm
# Linux/Mac: brew install helm

# Verify
helm version
```

### Deploy with Helm

```powershell
# Add repository or use local chart
cd c:\Users\don81\OneDrive\Desktop\demo

# Dry-run to preview
helm install ecommerce ./3-kubernetes/helm -n prod-ecommerce --create-namespace --dry-run

# Install
helm install ecommerce ./3-kubernetes/helm -n prod-ecommerce --create-namespace

# Verify
helm list -n prod-ecommerce
helm status ecommerce -n prod-ecommerce
```

### Update Configuration

```powershell
# Edit values
notepad 3-kubernetes/helm/values.yaml

# Upgrade
helm upgrade ecommerce ./3-kubernetes/helm -n prod-ecommerce

# Rollback if needed
helm rollback ecommerce 1 -n prod-ecommerce
```

### Helm Values Override

```powershell
# Override specific values on command line
helm install ecommerce ./3-kubernetes/helm -n prod-ecommerce \
  --set application.flask.replicas=5 \
  --set application.nginx.replicas=3 \
  --set database.storage=50Gi

# Or use custom values file
helm install ecommerce ./3-kubernetes/helm -n prod-ecommerce \
  -f custom-values.yaml
```

### View Helm Chart Content

```powershell
# Template rendering (see what will be deployed)
helm template ecommerce ./3-kubernetes/helm -n prod-ecommerce

# Get values
helm get values ecommerce -n prod-ecommerce

# Get manifest after deployment
helm get manifest ecommerce -n prod-ecommerce
```

### Uninstall

```powershell
# Uninstall (keeps PVCs)
helm uninstall ecommerce -n prod-ecommerce

# Delete namespace
kubectl delete namespace prod-ecommerce
```

---

## Quick Start (Legacy - kubectl apply)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Account (593067253640)           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  AWS Secrets Manager (3 secrets)                │   │
│  │  ├─ ecommerce/database-url (Auto-generated)     │   │
│  │  ├─ ecommerce/secret-key                        │   │
│  │  └─ ecommerce/docker-config                     │   │
│  └────────────────────┬─────────────────────────────┘   │
│  ┌────────────────────v─────────────────────────────┐   │
│  │  Parameter Store (3 parameters)                 │   │
│  │  ├─ /ecommerce/flask-env                        │   │
│  │  ├─ /ecommerce/debug                            │   │
│  │  └─ /ecommerce/log-level                        │   │
│  └────────────────────┬─────────────────────────────┘   │
│  ┌────────────────────v─────────────────────────────┐   │
│  │  Amazon RDS (PostgreSQL 15)                     │   │
│  │  └─ db.t3.micro (ecommerce_db)                  │   │
│  └────────────────────┬─────────────────────────────┘   │
│  ┌────────────────────v─────────────────────────────┐   │
│  │  IAM Role (ecommerce-external-secrets-role)     │   │
│  │  └─ Trust: OIDC Provider                        │   │
│  └────────────────────┬─────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                       │
              ┌────────v────────┐
              │  EKS Cluster    │
              │  (eu-north-1)   │
              └────────┬────────┘
        ┌─────────────v──────────────┐
        │ External Secrets Operator  │
        │ └─ SecretStore (AWS)       │
        └─────────────┬──────────────┘
                      │
        ┌─────────────v──────────────┐
        │ Kubernetes Secrets         │
        │ ├─ ecommerce-secrets       │
        │ └─ ecommerce-params        │
        └─────────────┬──────────────┘
                      │
        ┌─────────────v──────────────┐
        │ Application Pods           │
        │ ├─ Flask API (3x)          │
        │ ├─ Nginx Frontend (3x)     │
        │ └─ DB Init Job (Hook)      │
        └────────────────────────────┘
```

---

## Prerequisites

### Required Tools
- ✓ AWS CLI (configured with credentials): `aws sts get-caller-identity`
- ✓ Terraform (v1.0+): `terraform version`
- ✓ kubectl (configured for EKS): `kubectl cluster-info`
- ✓ EKS Cluster already created
- ✓ External Secrets Operator installed

### AWS Account Details
- **Account ID:** 593067253640
- **Region:** eu-north-1
- **OIDC ID:** D9F3585A3CEB7F58435405A9E7833268

---

## Project Structure

```
e-commerce/
├── 1-apps/                               # Application source code
│   ├── backend/                         # Flask backend API
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/                        # Nginx frontend
│       ├── index.html
│       ├── nginx.conf
│       ├── /static
│       ├── /images
│       └── Dockerfile
│
├── infra/                              # Infrastructure as Code
│   ├── kubernetes/
│   │   ├── helm/                        # ⭐ PRIMARY - Helm Chart (use this!)
│   │   │   ├── Chart.yaml
│   │   │   ├── README.md
│   │   │   ├── values.yaml
│   │   │   ├── values-dev.yaml
│   │   │   ├── values-prod.yaml
│   │   │   └── templates/
│   │   └── base/                        # 📚 REFERENCE - K8s learning manifests
│   │       ├── 01-namespace.yaml
│   │       ├── 02-configmaps.yaml
│   │       └── kustomization.yaml
│   └── terraform/                       # 🏗️ AWS Infrastructure as Code
│       ├── provider.tf
│       ├── variables.tf
│       ├── secrets.tf
│       ├── parameters.tf
│       └── outputs.tf
│
├── 4-ci-cd/                              # CI/CD Pipeline
│   └── jenkins/
│       ├── Jenkinsfile
│       └── docker-compose.yml
│
├── scripts/                            # Automation scripts
│
├── docs/                               # Documentation
│
├── data/                               # Database schema
│   └── schema.sql
│
├── tests/                              # Test suites
│
└── README.md                           # This file
```

**Legend:**
- ⭐ **3-kubernetes/helm/** - Use for deployment (Kubernetes package management)
- ⭐ **3-kubernetes/helm/ - Use for deployment (Kubernetes package management)
- 📚 **3-kubernetes/base/ - Reference learning (individual K8s manifests)
- 🏗️ **5-terraform/ - AWS infrastructure (secrets & parameters)

---

## Observability Learning Labs (iximiuz)

This repository functions as a "production simulator" specifically optimized for the [iximiuz Labs](https://labs.iximiuz.com/) platform. It contains a suite of modular environments so you can learn log aggregation and metrics without a heavy local setup.

### Available Labs
You can easily switch between different learning environments using the master setup script:

```powershell
chmod +x 2-labs/learning-lab.sh
./2-labs/learning-lab.sh
```

**The script provides 5 learning paths:**
1. **Base App:** Just the application via Docker Compose.
2. **Local ELK:** Docker Compose setup with Elasticsearch, Kibana, and Fluent Bit (mounting `/var/lib/docker/containers`).
3. **Local Prometheus:** Docker Compose setup with Prometheus and Grafana.
4. **K8s PLG Stack:** Kubernetes setup with Promtail, Loki, and Grafana.
5. **K8s EFK Stack:** Kubernetes setup with Elasticsearch, Fluent Bit, and Kibana.

For complete details on exposing ports inside the iximiuz playground and architectural instructions, see the dedicated [LEARNING_LABS.md](docs/LEARNING_LABS.md) and [IXIMIUZ_PLAN.md](2-labs/IXIMIUZ_PLAN.md) documents.

---

## Quick Start (Legacy - kubectl apply)

### Overview

Terraform manages all AWS secrets and parameters in **Infrastructure as Code**.

Use **Helm instead** (see section above), but if you prefer manual kubectl:

```powershell
# Deploy all K8s resources from manifests
kubectl apply -k k8s/

# Verify
kubectl get all -n prod-ecommerce
```

---

## Project Structure

---

## Terraform - Secrets & Parameters

### Overview

Terraform manages all AWS secrets and parameters in **Infrastructure as Code**.

**Resources Created:**
- 3 Secrets Manager secrets (database-url, secret-key, docker-config)
- 3 Parameter Store parameters (flask-env, debug, log-level)
- IAM policy for External Secrets access
- Secret access policy

### Setup

#### 1. Initialize

```powershell
cd terraform
terraform init
```

#### 2. Configure Variables

```powershell
# Copy example
Copy-Item terraform.tfvars.example terraform.tfvars

# Edit with your values
notepad terraform.tfvars
```

**Required values:**
```hcl
secret_key = "your-production-secret-key-here"
docker_config = '{"auths":{"docker.io":{"username":"privatergistry","password":"YOUR_PASSWORD"}}}'
flask_env = "production"
debug_mode = "false"
log_level = "INFO"
```
*(Note: `database_url` is automatically generated by Terraform upon creating the RDS instance and placed directly into Secrets Manager.)*

#### 3. Plan & Apply

```powershell
# Review changes
terraform plan

# Apply
terraform apply

# View outputs
terraform output
```

#### 4. Verify Resources

```powershell
# List Secrets Manager
aws secretsmanager list-secrets --region eu-north-1 --query 'SecretList[?contains(Name, `ecommerce`)].Name' --output table

# List Parameter Store
aws ssm describe-parameters --region eu-north-1 --filters "Key=Name,Values=/ecommerce" --query 'Parameters[].Name' --output table

# Get secret value
aws secretsmanager get-secret-value --secret-id ecommerce/database-url --region eu-north-1 --query 'SecretString'
```

### Management Commands

```powershell
# View all resources
terraform state list

# Show specific resource
terraform state show aws_secretsmanager_secret.database_url

# Update secret
# Edit terraform.tfvars then:
terraform plan
terraform apply

# Destroy all resources
terraform destroy
```

---

## External Secrets Integration

### How It Works

1. **IRSA (IAM Roles for Service Accounts)** annotations on `ecommerce-sa` service account
2. **External Secrets Operator** pod assumes the IAM role using OIDC
3. **SecretStores** authenticate to AWS (Secrets Manager + Parameter Store)
4. **ExternalSecrets** fetch values and create/update K8s Secrets
5. **Application pods** mount K8s Secrets as volumes or environment variables

### Verify Sync

```powershell
# Watch External Secrets sync
kubectl get externalsecrets -n prod-ecommerce -o wide --watch

# Expected output:
# NAME                STORETYPE     STORE                STATUS         READY
# ecommerce-secrets   SecretStore   aws-secrets-store    SecretSynced   True
# ecommerce-params    SecretStore   aws-parameter-store  SecretSynced   True

# Check synced K8s secrets
kubectl describe secret ecommerce-secrets -n prod-ecommerce
kubectl describe secret ecommerce-params -n prod-ecommerce
```

### Troubleshooting Sync Issues

```powershell
# Check External Secrets Operator logs
kubectl logs -n external-secrets deployment/external-secrets -f

# Check ExternalSecret resource status
kubectl describe externalsecret ecommerce-secrets -n prod-ecommerce

# Verify IRSA annotation
kubectl get serviceaccount ecommerce-sa -n prod-ecommerce -o yaml | grep eks.amazonaws.com

# Verify IAM role can access secrets
aws iam get-role --role-name ecommerce-external-secrets-role --query 'Role.AssumeRolePolicyDocument'

# Manual test: assume role from pod
kubectl run -it debug --image=amazonlinux --serviceaccount=ecommerce-sa -n prod-ecommerce -- sh
# Inside pod:
# aws secretsmanager list-secrets --region eu-north-1
# aws ssm describe-parameters --region eu-north-1
```

---

## IRSA Setup

### Automatic Setup (via Terraform)

Terraform handles IRSA automatically through:
1. Trust policy with OIDC provider
2. IAM role creation
3. Secret access policy
4. Service account annotation

### Manual Verification

```powershell
# Verify OIDC Provider
aws iam list-open-id-connect-providers --query 'OpenIDConnectProviderList[?contains(Arn, `eks`)]'

# Verify IAM Role
aws iam get-role --role-name ecommerce-external-secrets-role

# Verify Trust Policy
aws iam get-role --role-name ecommerce-external-secrets-role --query 'Role.AssumeRolePolicyDocument'

# Verify Service Account Annotation
kubectl get serviceaccount ecommerce-sa -n prod-ecommerce -o yaml
```

---

## Deployment Methods

### Method 1: Helm (Recommended - Production Ready) ⭐

```powershell
# Deploy
helm install ecommerce ./3-kubernetes/helm -n prod-ecommerce --create-namespace

# Deploy Terraform secrets first
cd terraform
terraform apply
cd ..

# Verify
helm list -n prod-ecommerce
kubectl get all -n prod-ecommerce
```

**Pros:** 
- Package management, version control
- Environment-specific values (dev/prod)
- Easy upgrades and rollbacks
- Single command deployment

**Cons:** Requires Helm knowledge

---

### Method 2: kubectl + Kustomize (Reference - Learning Only)

For understanding K8s resources manually:

```powershell
# Deploy all K8s resources
kubectl apply -k k8s/

# Deploy Terraform secrets
cd terraform
terraform apply
```

**Pros:** Direct control, see individual resources  
**Cons:** Manual updates, harder to maintain

---

### Method 3: Terraform Only (Infrastructure as Code)

Manages AWS infrastructure only (not K8s):

```powershell
cd terraform
terraform apply
```

**Pros:** Infrastructure version controlled, reproducible  
**Cons:** Doesn't deploy K8s resources (use Helm after)

---

## Troubleshooting

### Problem: Pods not starting

```powershell
# Check pod status
kubectl describe pod <pod-name> -n prod-ecommerce

# Check logs
kubectl logs <pod-name> -n prod-ecommerce

# Common causes:
# - ImagePullBackOff: Docker credentials issue
# - CrashLoopBackOff: Application error, check logs
# - Pending: Resource constraints or node issues
```

### Problem: External Secrets not syncing

```powershell
# Check ExternalSecret status
kubectl describe externalsecret ecommerce-secrets -n prod-ecommerce

# Check for errors
kubectl get externalsecrets -n prod-ecommerce -o wide

# Common causes:
# - IRSA role not found: Verify IAM role ARN annotation
# - Secret not found in AWS: Re-run terraform apply
# - Secret Store invalid: Check AWS credentials from pod
```

### Problem: Database connection failing

```powershell
# Check RDS connectivity from within cluster
kubectl run -it test-db --image=postgres:15-alpine --rm -- sh
# Inside pod, try connecting with the DATABASE_URL secret
# psql $DATABASE_URL

# Check Flask API logs for connection errors
kubectl logs -n prod-ecommerce deployment/flask-api

# Verify secret value is correct
kubectl get secret ecommerce-secrets -n prod-ecommerce -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

### Problem: Terraform apply failing

```powershell
# Enable debug logging
$env:TF_LOG = "DEBUG"

# Validate configuration
terraform validate

# Check credentials
aws sts get-caller-identity

# Try again
terraform apply
```

### Problem: Resource already exists

```powershell
# List current state
terraform state list

# Show imported resource
terraform state show <resource-name>

# Manual cleanup if needed
terraform state rm <resource-name>
terraform apply
```

---

## AWS CLI Commands Reference

### Secrets Manager

```powershell
# List all ecommerce secrets
aws secretsmanager list-secrets --region eu-north-1 --query 'SecretList[?contains(Name, `ecommerce`)]'

# Get secret value
aws secretsmanager get-secret-value --secret-id ecommerce/database-url --region eu-north-1 --query 'SecretString'

# Update secret
aws secretsmanager update-secret --secret-id ecommerce/database-url --secret-string "new-value" --region eu-north-1

# Delete secret
aws secretsmanager delete-secret --secret-id ecommerce/database-url --force-delete-without-recovery --region eu-north-1
```

### Parameter Store

```powershell
# List all ecommerce parameters
aws ssm describe-parameters --region eu-north-1 --filters "Key=Name,Values=/ecommerce"

# Get parameter value
aws ssm get-parameter --name /ecommerce/flask-env --region eu-north-1 --query 'Parameter.Value'

# Update parameter
aws ssm put-parameter --name /ecommerce/flask-env --value "production" --type String --overwrite --region eu-north-1

# Delete parameter
aws ssm delete-parameter --name /ecommerce/flask-env --region eu-north-1
```

### IAM

```powershell
# List IRSA roles
aws iam list-roles --query 'Roles[?contains(RoleName, `external-secrets`)]'

# Check role trust policy
aws iam get-role --role-name ecommerce-external-secrets-role

# Attach policy to role
aws iam attach-role-policy --role-name ecommerce-external-secrets-role --policy-arn arn:aws:iam::593067253640:policy/ecommerce-external-secrets-policy
```

### Kubernetes Resources

```powershell
# List EKS clusters
aws eks list-clusters --region eu-north-1

# Describe cluster
aws eks describe-cluster --name my-eks-cluster --region eu-north-1

# Update kubeconfig
aws eks update-kubeconfig --name my-eks-cluster --region eu-north-1
```

---

## Cleanup & Destruction

### Destroy Terraform Resources (Saves AWS costs!)

```powershell
cd terraform

# Plan destruction
terraform plan -destroy

# Destroy all
terraform destroy

# Verify
aws secretsmanager list-secrets --region eu-north-1 --query 'SecretList[?contains(Name, `ecommerce`)]'
aws ssm describe-parameters --region eu-north-1 --filters "Key=Name,Values=/ecommerce"
```

### Delete Kubernetes Resources

```powershell
# Delete namespace (everything in it)
kubectl delete namespace prod-ecommerce

# Verify
kubectl get namespace prod-ecommerce
```

### Reapply When Needed

```powershell
# Kubernetes
kubectl apply -k k8s/

# Terraform
cd terraform
terraform apply
```

---

## Complete Workflow

### Initial Deployment

```powershell
# Step 1: Deploy K8s base
cd c:\Users\don81\OneDrive\Desktop\demo
kubectl apply -k k8s/

# Step 2: Deploy Terraform secrets
cd terraform
terraform init
terraform plan
terraform apply

# Step 3: Verify
kubectl get all -n prod-ecommerce
kubectl get externalsecrets -n prod-ecommerce -o wide
```

### Development/Testing

```powershell
# Make changes
# Edit terraform.tfvars if needed

# Update
terraform plan
terraform apply

# Verify
kubectl get secrets -n prod-ecommerce
kubectl logs -n prod-ecommerce deployment/flask-api
```

### Done Testing - Save Costs

```powershell
cd terraform
terraform destroy
```

### Resume Work

```powershell
cd terraform
terraform apply
```

---

## Key Information

| Item | Value |
|------|-------|
| AWS Account | 593067253640 |
| AWS Region | eu-north-1 |
| OIDC ID | D9F3585A3CEB7F58435405A9E7833268 |
| Namespace | prod-ecommerce |
| Service Account | ecommerce-sa |
| IAM Role | ecommerce-external-secrets-role |
| External Secrets Version | v2.1.0 |
| Terraform Version | 1.0+ |

---

## Support & Documentation

**Terraform:**
- See `terraform/README.md` for detailed Terraform setup
- See `terraform/QUICKSTART.md` for 5-minute quickstart
- See `terraform/INTEGRATION_GUIDE.md` for External Secrets integration

**Kubernetes:**
- See `k8s/README.md` for K8s structure and deployment options

**External Secrets:**
- [External Secrets Documentation](https://external-secrets.io/)
- [AWS Provider Docs](https://external-secrets.io/provider-aws-secrets-manager/)

**Terraform Docs:**
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Command Reference](https://www.terraform.io/cli)

---

## Quick Commands Cheat Sheet

```powershell
# Deploy everything
kubectl apply -k k8s/ && cd terraform && terraform apply

# Check status
kubectl get all -n prod-ecommerce
kubectl get externalsecrets -n prod-ecommerce -o wide

# View logs
kubectl logs -n prod-ecommerce deployment/flask-api -f

# View secrets
kubectl get secret ecommerce-secrets -n prod-ecommerce -o jsonpath='{.data}' | jq

# Update secrets (via Terraform)
cd terraform
terraform plan
terraform apply

# Destroy (save costs)
terraform destroy

# Cleanup namespace
kubectl delete namespace prod-ecommerce
```

---

**Last Updated:** March 19, 2026  
**Status:** ✅ Production Ready  
**Maintained By:** Platform Team
