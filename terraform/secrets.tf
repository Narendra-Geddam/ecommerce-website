# AWS Secrets Manager - Ecommerce Application Secrets
# Stores sensitive credentials that should not be in version control

# Secret: Database Connection URL
resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${var.secret_project_prefix}/database-url"
  description             = "PostgreSQL database connection URL for ecommerce application"
  recovery_window_in_days = var.secrets_recovery_window
  
  tags = merge(
    var.tags,
    {
      Name        = "ecommerce-database-url"
      Secret_Type = "database"
    }
  )
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id       = aws_secretsmanager_secret.database_url.id
  secret_string   = var.database_url
  version_stages = ["AWSCURRENT"]
}

# Secret: Flask Application Secret Key
resource "aws_secretsmanager_secret" "secret_key" {
  name                    = "${var.secret_project_prefix}/secret-key"
  description             = "Flask application secret key for session management and security"
  recovery_window_in_days = var.secrets_recovery_window
  
  tags = merge(
    var.tags,
    {
      Name        = "ecommerce-secret-key"
      Secret_Type = "application"
    }
  )
}

resource "aws_secretsmanager_secret_version" "secret_key" {
  secret_id       = aws_secretsmanager_secret.secret_key.id
  secret_string   = var.secret_key
  version_stages = ["AWSCURRENT"]
}

# Secret: Docker Hub Configuration
resource "aws_secretsmanager_secret" "docker_config" {
  name                    = "${var.secret_project_prefix}/docker-config"
  description             = "Docker Hub authentication credentials for pulling private images"
  recovery_window_in_days = var.secrets_recovery_window
  
  tags = merge(
    var.tags,
    {
      Name        = "ecommerce-docker-config"
      Secret_Type = "registry"
    }
  )
}

resource "aws_secretsmanager_secret_version" "docker_config" {
  secret_id       = aws_secretsmanager_secret.docker_config.id
  secret_string   = var.docker_config
  version_stages = ["AWSCURRENT"]
}

# Data source to get current AWS account ID for resource policies
data "aws_caller_identity" "current" {}

# Example: Grant read access to EKS service account (if needed)
# Uncomment and update principal_type and principal_id to grant IRSA access
resource "aws_secretsmanager_secret_policy" "ecommerce_access" {
  secret_arn = aws_secretsmanager_secret.database_url.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEKSServiceAccountAccess"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/ecommerce-external-secrets-role"
        }
        Action   = "secretsmanager:GetSecretValue"
        Resource = "*"
        Condition = {
          StringEquals = {
            "secretsmanager:VersionStage" = "AWSCURRENT"
          }
        }
      }
    ]
  })
}

# Outputs for reference
output "secrets_manager_secrets" {
  description = "Created Secrets Manager secret details"
  value = {
    database_url_arn  = aws_secretsmanager_secret.database_url.arn
    database_url_name = aws_secretsmanager_secret.database_url.name
    secret_key_arn    = aws_secretsmanager_secret.secret_key.arn
    secret_key_name   = aws_secretsmanager_secret.secret_key.name
    docker_config_arn = aws_secretsmanager_secret.docker_config.arn
    docker_config_name = aws_secretsmanager_secret.docker_config.name
  }
  sensitive = true
}
