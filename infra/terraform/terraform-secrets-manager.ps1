# PowerShell script for Terraform Secrets Management
# Usage: .\terraform-secrets-manager.ps1

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("init", "plan", "apply", "destroy", "output", "verify", "rotate", "sync", "help")]
    [string]$Action = "help",
    
    [Parameter(Mandatory=$false)]
    [string]$SecretName,
    
    [Parameter(Mandatory=$false)]
    [string]$SecretValue,
    
    [Parameter(Mandatory=$false)]
    [string]$AwsRegion = "eu-north-1"
)

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Function to initialize Terraform
function Initialize-Terraform {
    Write-Info "Initializing Terraform..."
    terraform init
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Terraform initialized"
    } else {
        Write-Error-Custom "Terraform initialization failed"
        exit 1
    }
}

# Function to validate configuration
function Validate-Terraform {
    Write-Info "Validating Terraform configuration..."
    terraform validate
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Terraform configuration is valid"
    } else {
        Write-Error-Custom "Terraform validation failed"
        exit 1
    }
}

# Function to plan changes
function Plan-Terraform {
    Write-Info "Planning Terraform changes..."
    terraform plan -out=tfplan
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Terraform plan completed"
        Write-Info "Review the plan above, then run 'terraform apply tfplan'"
    } else {
        Write-Error-Custom "Terraform plan failed"
        exit 1
    }
}

# Function to apply changes
function Apply-Terraform {
    Write-Warning-Custom "This will create/update AWS resources"
    $confirm = Read-Host "Continue? (yes/no)"
    if ($confirm -eq "yes") {
        Write-Info "Applying Terraform configuration..."
        terraform apply tfplan
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Terraform apply completed"
        } else {
            Write-Error-Custom "Terraform apply failed"
            exit 1
        }
    } else {
        Write-Info "Operation cancelled"
    }
}

# Function to destroy resources
function Destroy-Terraform {
    Write-Warning-Custom "This will DELETE all AWS resources"
    $confirm = Read-Host "Are you sure? (type: destroy)"
    if ($confirm -eq "destroy") {
        Write-Info "Destroying Terraform resources..."
        terraform destroy -auto-approve
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Terraform destroy completed"
        }
    } else {
        Write-Info "Operation cancelled"
    }
}

# Function to display outputs
function Display-Outputs {
    Write-Info "Terraform Outputs:"
    terraform output -json | ConvertFrom-Json | ForEach-Object {
        $_.PSObject.Properties | ForEach-Object {
            Write-Host "$($_.Name): $($_.Value.value)" -ForegroundColor Cyan
        }
    }
}

# Function to verify resources in AWS
function Verify-Resources {
    Write-Info "Verifying AWS resources..."
    
    Write-Host "`n--- Secrets Manager ---" -ForegroundColor Cyan
    aws secretsmanager list-secrets `
        --region $AwsRegion `
        --query 'SecretList[?contains(Name, `ecommerce`)].{Name:Name, ARN:ARN, LastRotated:LastRotatedDate}' `
        --output table
    
    Write-Host "`n--- Parameter Store ---" -ForegroundColor Cyan
    aws ssm describe-parameters `
        --region $AwsRegion `
        --filters "Key=Name,Values=/ecommerce" `
        --query 'Parameters[].{Name:Name, Type:Type, Version:Version}' `
        --output table
    
    Write-Success "Verification completed"
}

# Function to get secret value
function Get-SecretValue {
    param([string]$SecretId)
    
    Write-Info "Retrieving secret: $SecretId"
    aws secretsmanager get-secret-value `
        --secret-id $SecretId `
        --region $AwsRegion `
        --query 'SecretString' `
        --output text
}

# Function to update secret
function Update-SecretValue {
    param(
        [string]$SecretId,
        [string]$NewValue
    )
    
    Write-Warning-Custom "Updating secret: $SecretId"
    $confirm = Read-Host "Continue? (yes/no)"
    if ($confirm -eq "yes") {
        aws secretsmanager update-secret `
            --secret-id $SecretId `
            --secret-string $NewValue `
            --region $AwsRegion
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Secret updated successfully"
        } else {
            Write-Error-Custom "Failed to update secret"
        }
    }
}

# Function to rotate secrets
function Rotate-Secrets {
    Write-Info "Initiating secret rotation..."
    
    @("ecommerce/database-url", "ecommerce/secret-key") | ForEach-Object {
        Write-Info "Rotating $_..."
        aws secretsmanager rotate-secret `
            --secret-id $_ `
            --region $AwsRegion
    }
    
    Write-Success "Rotation initiated"
}

# Function to sync with External Secrets Operator
function Sync-ExternalSecrets {
    Write-Info "Syncing External Secrets Operator..."
    
    kubectl rollout restart deployment/external-secrets -n external-secrets
    Write-Success "External Secrets Operator restarted"
    
    Write-Info "External Secrets status:"
    kubectl get externalsecrets -n prod-ecommerce -o wide
}

# Function to display help
function Show-Help {
    Write-Host @"
╔════════════════════════════════════════════════════════════════════════╗
║         Terraform Secrets & Parameters Management Script                ║
╚════════════════════════════════════════════════════════════════════════╝

USAGE:
  ./terraform-secrets-manager.ps1 -Action <action> [options]

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
  .\terraform-secrets-manager.ps1 -Action init
  
  # Plan and review changes
  .\terraform-secrets-manager.ps1 -Action plan
  
  # Apply configuration
  .\terraform-secrets-manager.ps1 -Action apply
  
  # Display all outputs
  .\terraform-secrets-manager.ps1 -Action output
  
  # Verify resources in AWS
  .\terraform-secrets-manager.ps1 -Action verify
  
  # Rotate secrets
  .\terraform-secrets-manager.ps1 -Action rotate
  
  # Sync with Kubernetes
  .\terraform-secrets-manager.ps1 -Action sync

WORKFLOW:
  1. Setup:       .\terraform-secrets-manager.ps1 -Action init
  2. Review:      .\terraform-secrets-manager.ps1 -Action plan
  3. Deploy:      .\terraform-secrets-manager.ps1 -Action apply
  4. Verify:      .\terraform-secrets-manager.ps1 -Action verify
  5. Connect K8S: .\terraform-secrets-manager.ps1 -Action sync

ENVIRONMENT VARIABLES:
  AWS_REGION     Default region (default: eu-north-1)
  AWS_PROFILE    AWS profile to use
  TF_LOG         Enable debug logging (set to DEBUG)

PREREQUISITES:
  - Terraform >= 1.0
  - AWS CLI configured
  - kubectl (for sync action)
  - Sufficient IAM permissions

FOR MORE HELP:
  - See terraform/README.md
  - Run: terraform -help
  - Run: aws secretsmanager help

"@
}

# Main execution
switch ($Action.ToLower()) {
    "init" {
        Initialize-Terraform
        Validate-Terraform
    }
    "plan" {
        Initialize-Terraform
        Validate-Terraform
        Plan-Terraform
    }
    "apply" {
        Apply-Terraform
    }
    "destroy" {
        Destroy-Terraform
    }
    "output" {
        Display-Outputs
    }
    "verify" {
        Verify-Resources
    }
    "rotate" {
        Rotate-Secrets
    }
    "sync" {
        Sync-ExternalSecrets
    }
    default {
        Show-Help
    }
}
