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
  secret_id      = aws_secretsmanager_secret.database_url.id
  secret_string  = "postgresql://${aws_db_instance.ecommerce_db.username}:${random_password.db_password.result}@${aws_db_instance.ecommerce_db.endpoint}/${aws_db_instance.ecommerce_db.db_name}"
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
  secret_id      = aws_secretsmanager_secret.secret_key.id
  secret_string  = var.secret_key
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
  secret_id      = aws_secretsmanager_secret.docker_config.id
  secret_string  = var.docker_config
  version_stages = ["AWSCURRENT"]
}

