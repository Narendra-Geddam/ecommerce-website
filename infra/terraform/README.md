# Infrastructure as Code - Terraform

This directory contains **Terraform** configuration for deploying AWS infrastructure to support the e-commerce application on Kubernetes.

## Overview

The Terraform configuration manages:
- **AWS Secrets Manager** - Sensitive data (database URL, API keys)
- **AWS Systems Manager Parameter Store** - Configuration parameters
- **IAM Policies** - Access control for Kubernetes pods
- **Security Groups** - Network access controls (optional)

## Architecture

```
terraform/
├── provider.tf           # AWS provider configuration
├── variables.tf          # Input variable definitions
├── secrets.tf            # Secrets Manager resources
├── parameters.tf         # Parameter Store resources
├── outputs.tf            # Output values
├── terraform.tfvars      # Production configuration (gitignored)
├── terraform.tfvars.example  # Example configuration template
├── terraform.tfstate     # Current infrastructure state
├── .terraform/           # Provider plugins cache
├── policies/             # IAM policy documents
│   └── ecommerce-irsa-policy.json
├── secrets/              # Sensitive defaults (gitignored)
│   └── docker-config.json
└── README.md            # This file
```

## Key Technologies

- **Terraform** v1.0+ - Infrastructure as Code
- **AWS Provider** ~5.0 - AWS resource management
- **AWS Secrets Manager** - Encrypted secret storage
- **AWS Systems Manager Parameter Store** - Configuration storage
- **IAM** - Identity and Access Management

## Quick Start

### Prerequisites

```bash
# Install Terraform
# macOS
brew install terraform

# Windows
choco install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.0.0/terraform_1.0.0_linux_amd64.zip
unzip terraform_1.0.0_linux_amd64.zip
```

### Initialize Terraform

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform (download providers)
terraform init

# Validate configuration syntax
terraform validate

# Format code (idiomatic style)
terraform fmt -recursive
```

### Plan & Apply

```bash
# Preview changes without making them
terraform plan

# Save plan to file (recommended)
terraform plan -out=tfplan

# Apply the plan
terraform apply tfplan

# Or apply directly (requires confirmation)
terraform apply
```

## Configuration

### Variables (terraform.tfvars)

Copy `terraform.tfvars.example` to `terraform.tfvars` and customize:

```hcl
# AWS Configuration
aws_region     = "eu-north-1"
environment    = "prod"
project_name   = "ecommerce"

# Secrets Manager
secret_project_prefix = "ecommerce"
database_url = "postgresql://ecommerce:password@postgres-service.prod-ecommerce:5432/ecommerce"
secret_key   = "your-flask-secret-key-change-this"
docker_config = "{...}"  # Docker registry credentials

# Parameter Store
parameter_project_prefix = "/ecommerce"
flask_env   = "production"
debug_mode  = "false"
log_level   = "INFO"

# Tagging
tags = {
  Owner      = "Platform Team"
  CostCenter = "Engineering"
  ManagedBy  = "Terraform"
}
```

### Important Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `aws_region` | string | AWS region | `eu-north-1` |
| `environment` | string | Environment name | `prod`, `staging`, `dev` |
| `database_url` | string | PostgreSQL connection | `postgresql://user:pass@host:5432/db` |
| `secret_key` | string | Flask encryption key | Min 32 characters |
| `docker_config` | string | Docker credentials JSON | `{"auths":{...}}` |

## Resources

### Secrets Manager Resources (3)

```hcl
aws_secretsmanager_secret.database_url
aws_secretsmanager_secret.secret_key
aws_secretsmanager_secret.docker_config
```

Stores sensitive data encrypted:
- Database connection string
- Flask session signing key
- Docker registry credentials

### Parameter Store Resources (3)

```hcl
aws_ssm_parameter.flask_env
aws_ssm_parameter.debug_mode
aws_ssm_parameter.log_level
```

Stores non-sensitive configuration:
- Flask environment (production/development)
- Debug mode toggle
- Logging verbosity level

### IAM Policy Resource (1)

```hcl
aws_secretsmanager_secret_policy.ecommerce_access
```

Grants Kubernetes pod RBAC to access secrets via IRSA (IAM Roles for Service Accounts).

## State Management

### Local State (Current)

State file stored locally: `terraform.tfstate`

```bash
# View current state
terraform state list

# Inspect specific resource
terraform state show aws_secretsmanager_secret.database_url

# Backup state
cp terraform.tfstate terraform.tfstate.backup
```

### Remote State (S3 - Production Recommended)

```hcl
# Uncomment in provider.tf
backend "s3" {
  bucket         = "ecommerce-terraform-state"
  key            = "ecommerce/secrets/terraform.tfstate"
  region         = "eu-north-1"
  encrypt        = true
  dynamodb_table = "terraform-locks"
}
```

**Setup:**

```bash
# Create S3 bucket
aws s3 mb s3://ecommerce-terraform-state --region eu-north-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ecommerce-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB lock table
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

Then migrate:
```bash
terraform init
# Select yes to migrate state to S3
```

## Outputs

```hcl
# Retrieve output values
terraform output

# Specific output
terraform output database_url_arn

# JSON format
terraform output -json
```

**Available Outputs:**

```bash
database_url_arn
database_url_version_id
secret_key_arn
secret_key_version_id
docker_config_arn
docker_config_version_id
flask_env_arn
debug_mode_arn
log_level_arn
ecommerce_access_policy_arn
aws_account_id
aws_region
```

## Workflow

### Development

```bash
# 1. Make changes to configuration
# (Edit *.tf files)

# 2. Plan changes
terraform plan

# 3. Review output carefully

# 4. Apply changes
terraform apply

# 5. Verify in AWS Console or CLI
aws secretsmanager list-secrets --region eu-north-1
```

### Adding New Secret

```hcl
# In secrets.tf
resource "aws_secretsmanager_secret" "new_secret" {
  name                    = "${var.secret_project_prefix}/new-secret"
  recovery_window_in_days = var.secrets_recovery_window

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "new_secret" {
  secret_id      = aws_secretsmanager_secret.new_secret.id
  secret_string  = "your-secret-value"
}
```

Then:
```bash
terraform plan
terraform apply
```

### Updating Secret Values

```bash
# Option 1: Edit terraform.tfvars and apply
# (Recommended: use AWS Secrets Manager console for sensitive updates)

# Option 2: Use AWS CLI directly
aws secretsmanager put-secret-value \
  --secret-id ecommerce/database-url \
  --secret-string "postgresql://new-url" \
  --region eu-north-1

# Refresh Terraform state
terraform refresh
```

## Policy Documents

### IRSA Policy (policies/ecommerce-irsa-policy.json)

Grants Kubernetes pod access to AWS Secrets Manager and Parameter Store:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:eu-north-1:*:secret:ecommerce/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:eu-north-1:*:parameter/ecommerce/*"
    }
  ]
}
```

Used by External Secrets Operator to sync AWS → Kubernetes.

## Common Commands

```bash
# Plan specific resource
terraform plan -target=aws_secretsmanager_secret.database_url

# Apply specific resource
terraform apply -target=aws_secretsmanager_secret.database_url

# Destroy all resources
terraform destroy

# Destroy specific resource
terraform destroy -target=aws_secretsmanager_secret.docker_config

# Format all files
terraform fmt -recursive

# Validate syntax
terraform validate

# Show resource details
terraform state show aws_secretsmanager_secret.database_url

# Taint resource (force update on next apply)
terraform taint aws_secretsmanager_secret_version.database_url

# Remove from state (but keeps AWS resource)
terraform state rm aws_secretsmanager_secret.database_url
```

## Troubleshooting

### "Error: Invalid or missing provider"

**Solution:**
```bash
terraform init
```

### "Error: resource created but not managed by module"

**Cause:** Resource already exists in AWS

**Solution:**
```bash
# Import existing resource
terraform import aws_secretsmanager_secret.database_url \
  arn:aws:secretsmanager:eu-north-1:123456789:secret:ecommerce/database-url

# Or remove and recreate
terraform destroy -target=aws_secretsmanager_secret.database_url
terraform apply
```

### "Error: AccessDenied: User is not authorized to perform: secretsmanager:CreateSecret"

**Cause:** AWS credentials lack permissions

**Solution:**
```bash
# Check IAM role/user policy
aws iam get-user-policy --user-name <username> --policy-name <policy-name>

# Add required permissions (attach policy with secretsmanager:*, ssm:*, iam:*)
```

### State Lock Issues

**Problem:** "Error acquiring the state lock"

**Solution:**
```bash
# Break lock (use with caution)
terraform force-unlock <LOCK-ID>

# Migrating to remote state
terraform init  # Select 'yes' to migrate
```

## Best Practices

1. **Version Control** - Commit `.tf` files, never commit `terraform.tfvars`
2. **State Files** - Use S3 + DynamoDB for remote state in production
3. **Review** - Always run `plan` before `apply`
4. **Backends** - Initialize once, avoid switching backends
5. **Workspace** - Use workspaces for multiple environments:
   ```bash
   terraform workspace new prod
   terraform workspace new staging
   terraform workspace select prod
   ```

6. **Variables** - Sensitive values via environment:
   ```bash
   export TF_VAR_database_url="postgresql://..."
   terraform plan
   ```

7. **Comments** - Document non-obvious configurations
8. **Modules** - Extract reusable components into modules

## Integration with Kubernetes

## Jenkins Infrastructure (Controller + Ephemeral Agents)

This Terraform stack now provisions:

1. One Jenkins controller EC2 instance
2. One Launch Template for Jenkins agents
3. One Auto Scaling Group (min=0) for ephemeral agents
4. IAM roles/policies for EC2 Fleet style scaling
5. Security groups for controller/agent SSH separation

### Files Added

- `jenkins.tf`
- `templates/jenkins-controller-user-data.sh.tftpl`
- `templates/jenkins-agent-user-data.sh.tftpl`

### Key Variables

- `jenkins_controller_instance_type`
- `jenkins_admin_username`
- `jenkins_admin_password`
- `jenkins_agent_instance_type`
- `jenkins_agent_max_size`
- `jenkins_controller_allowed_cidrs`

### Apply

```bash
terraform plan
terraform apply
```

### Configure Jenkins for Ephemeral Agents

After first login to Jenkins:

1. Verify plugin `ec2-fleet` is installed.
2. Go to `Manage Jenkins` -> `Clouds` -> `New Cloud`.
3. Select EC2 Fleet cloud type.
4. Use ASG name from Terraform output `jenkins_agent_asg_name`.
5. Set SSH credentials/key for agent connection.
6. Keep ASG min size at 0 and let Jenkins scale on queue demand.

This gives one persistent controller and short-lived build agents created from Launch Template instances.

### External Secrets Operator

The Terraform-created secrets are synced to Kubernetes via External Secrets Operator:

```yaml
# In infra/kubernetes/helm/templates/external-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: ecommerce-secrets
spec:
  secretStoreRef:
    name: aws-secrets-store
    kind: SecretStore
  target:
    name: ecommerce-secrets
    creationPolicy: Owner
  data:
  - secretKey: DATABASE_URL
    remoteRef:
      key: ecommerce/database-url
  - secretKey: SECRET_KEY
    remoteRef:
      key: ecommerce/secret-key
```

**Workflow:**
1. Terraform creates secrets in AWS
2. External Secrets Operator watches AWS Secrets Manager
3. Updates automatically sync to Kubernetes
4. Flask application reads from K8s secrets

## Disaster Recovery

### Backup

```bash
# Export all resources
terraform state pull > backup.tfstate

# S3 versioning (if using S3 backend)
aws s3api list-object-versions \
  --bucket ecommerce-terraform-state \
  --prefix ecommerce/secrets/
```

### Recovery

```bash
# Restore from backup
terraform state push backup.tfstate

# Re-apply configuration
terraform apply
```

## Cost Management

```bash
# Estimate costs (requires Terraform Cloud)
terraform plan -out=tfplan
# -> Outputs estimated monthly cost

# Cleanup unused resources
terraform destroy -target=aws_secretsmanager_secret.unused_secret
```

**Cost breakdown (approx):**
- Secrets Manager: $0.40/secret/month
- Parameter Store (Standard): Free
- Parameter Store (Advanced): $0.05/parameter/month

## Maintenance

### Weekly
- Review `terraform plan` output
- Monitor secret rotation schedules
- Check CloudTrail for unauthorized access

### Monthly
- Update AWS provider version
- Review and update documentation
- Run `terraform fmt -recursive`

### Quarterly
- Audit IAM policies
- Review and update security configurations
- Test disaster recovery procedure

## Security

### Secrets Protection

- **Encryption**: KMS encryption by default
- **Rotation**: Configure secret rotation policies
- **Access**: Restricted to IRSA-authenticated pods
- **Audit**: CloudTrail logs all API calls

### Best Practices

1. Never commit `terraform.tfvars` with real secrets
2. Use AWS Secrets Manager for sensitive data
3. Enable CloudTrail for audit logging
4. Rotate secrets regularly
5. Use least-privilege IAM policies

## Links

- **Main Guide**: [README.md](../../README.md)
- **Helm Deployment**: [infra/kubernetes/helm/README.md](../kubernetes/helm/README.md)
- **Backend**: [apps/backend/README.md](../../apps/backend/README.md)
- **Database**: [data/README.md](../../data/README.md)
- **Terraform Docs**: https://www.terraform.io/docs/
- **AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
