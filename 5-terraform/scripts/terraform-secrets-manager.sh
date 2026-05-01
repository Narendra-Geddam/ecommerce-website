#!/bin/bash
# Bash script for Terraform Secrets Management
# Usage: ./terraform-secrets-manager.sh [action]

set -e

# Default values
ACTION="${1:-help}"
AWS_REGION="${AWS_REGION:-eu-north-1}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Utility functions
write_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

write_error() {
    echo -e "${RED}✗ $1${NC}"
}

write_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

write_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Initialize Terraform
initialize_terraform() {
    write_info "Initializing Terraform..."
    terraform init
    write_success "Terraform initialized"
}

# Validate configuration
validate_terraform() {
    write_info "Validating Terraform configuration..."
    terraform validate
    write_success "Terraform configuration is valid"
}

# Plan changes
plan_terraform() {
    write_info "Planning Terraform changes..."
    terraform plan -out=tfplan
    write_success "Terraform plan completed"
    write_info "Review the plan above, then run 'terraform apply tfplan'"
}

# Apply changes
apply_terraform() {
    write_warning "This will create/update AWS resources"
    read -p "Continue? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        write_info "Applying Terraform configuration..."
        terraform apply tfplan
        write_success "Terraform apply completed"
    else
        write_info "Operation cancelled"
    fi
}

# Destroy resources
destroy_terraform() {
    write_warning "This will DELETE all AWS resources"
    read -p "Are you sure? (type: destroy): " confirm
    if [ "$confirm" = "destroy" ]; then
        write_info "Destroying Terraform resources..."
        terraform destroy -auto-approve
        write_success "Terraform destroy completed"
    else
        write_info "Operation cancelled"
    fi
}

# Display outputs
display_outputs() {
    write_info "Terraform Outputs:"
    terraform output -json | jq '.' || terraform output
}

# Verify resources in AWS
verify_resources() {
    write_info "Verifying AWS resources..."
    
    echo ""
    echo -e "${CYAN}--- Secrets Manager ---${NC}"
    aws secretsmanager list-secrets \
        --region "$AWS_REGION" \
        --query 'SecretList[?contains(Name, `ecommerce`)].{Name:Name, ARN:ARN, LastRotated:LastRotatedDate}' \
        --output table
    
    echo ""
    echo -e "${CYAN}--- Parameter Store ---${NC}"
    aws ssm describe-parameters \
        --region "$AWS_REGION" \
        --filters "Key=Name,Values=/ecommerce" \
        --query 'Parameters[].{Name:Name, Type:Type, Version:Version}' \
        --output table
    
    write_success "Verification completed"
}

# Get secret value
get_secret_value() {
    local secret_id=$1
    write_info "Retrieving secret: $secret_id"
    aws secretsmanager get-secret-value \
        --secret-id "$secret_id" \
        --region "$AWS_REGION" \
        --query 'SecretString' \
        --output text
}

# Update secret
update_secret_value() {
    local secret_id=$1
    local new_value=$2
    
    write_warning "Updating secret: $secret_id"
    read -p "Continue? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        aws secretsmanager update-secret \
            --secret-id "$secret_id" \
            --secret-string "$new_value" \
            --region "$AWS_REGION"
        
        write_success "Secret updated successfully"
    fi
}

# Rotate secrets
rotate_secrets() {
    write_info "Initiating secret rotation..."
    
    for secret in "ecommerce/database-url" "ecommerce/secret-key"; do
        write_info "Rotating $secret..."
        aws secretsmanager rotate-secret \
            --secret-id "$secret" \
            --region "$AWS_REGION"
    done
    
    write_success "Rotation initiated"
}

# Sync with External Secrets Operator
sync_external_secrets() {
    write_info "Syncing External Secrets Operator..."
    
    kubectl rollout restart deployment/external-secrets -n external-secrets
    write_success "External Secrets Operator restarted"
    
    write_info "External Secrets status:"
    kubectl get externalsecrets -n prod-ecommerce -o wide
}

# Show help
show_help() {
    cat << 'EOF'
╔════════════════════════════════════════════════════════════════════════╗
║         Terraform Secrets & Parameters Management Script                ║
╚════════════════════════════════════════════════════════════════════════╝

USAGE:
  ./terraform-secrets-manager.sh <action>

ACTIONS:
  init          Initialize Terraform working directory
  plan          Plan Terraform changes
  apply         Apply Terraform configuration
  destroy       Destroy all resources (use with caution!)
  output        Display all Terraform outputs
  verify        Verify AWS resources were created
  rotate        Initiate secret rotation
  sync          Sync External Secrets Operator
  help          Display this help message

EXAMPLES:
  
  # Initialize Terraform
  ./terraform-secrets-manager.sh init
  
  # Plan and review changes
  ./terraform-secrets-manager.sh plan
  
  # Apply configuration
  ./terraform-secrets-manager.sh apply
  
  # Display all outputs
  ./terraform-secrets-manager.sh output
  
  # Verify resources in AWS
  ./terraform-secrets-manager.sh verify
  
  # Rotate secrets
  ./terraform-secrets-manager.sh rotate
  
  # Sync with Kubernetes
  ./terraform-secrets-manager.sh sync

WORKFLOW:
  1. Setup:       ./terraform-secrets-manager.sh init
  2. Review:      ./terraform-secrets-manager.sh plan
  3. Deploy:      ./terraform-secrets-manager.sh apply
  4. Verify:      ./terraform-secrets-manager.sh verify
  5. Connect K8S: ./terraform-secrets-manager.sh sync

ENVIRONMENT VARIABLES:
  AWS_REGION     AWS region (default: eu-north-1)
  AWS_PROFILE    AWS profile to use
  TF_LOG         Enable debug logging (set to DEBUG)

PREREQUISITES:
  - Terraform >= 1.0
  - AWS CLI configured
  - kubectl (for sync action)
  - jq (optional, for output formatting)
  - Sufficient IAM permissions

FOR MORE HELP:
  - See terraform/README.md
  - Run: terraform -help
  - Run: aws secretsmanager help

EOF
}

# Main execution
case "$ACTION" in
    init)
        initialize_terraform
        validate_terraform
        ;;
    plan)
        initialize_terraform
        validate_terraform
        plan_terraform
        ;;
    apply)
        apply_terraform
        ;;
    destroy)
        destroy_terraform
        ;;
    output)
        display_outputs
        ;;
    verify)
        verify_resources
        ;;
    rotate)
        rotate_secrets
        ;;
    sync)
        sync_external_secrets
        ;;
    *)
        show_help
        ;;
esac
