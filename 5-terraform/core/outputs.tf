# Primary Outputs for Secrets and Parameters

output "aws_account_id" {
  description = "AWS Account ID where resources are deployed"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

# Secrets Manager Outputs
output "database_url_secret_arn" {
  description = "ARN of the database URL secret"
  value       = aws_secretsmanager_secret.database_url.arn
}

output "database_url_secret_name" {
  description = "Name of the database URL secret"
  value       = aws_secretsmanager_secret.database_url.name
}

output "secret_key_secret_arn" {
  description = "ARN of the Flask secret key"
  value       = aws_secretsmanager_secret.secret_key.arn
}

output "secret_key_secret_name" {
  description = "Name of the Flask secret key"
  value       = aws_secretsmanager_secret.secret_key.name
}

output "docker_config_secret_arn" {
  description = "ARN of the Docker config secret"
  value       = aws_secretsmanager_secret.docker_config.arn
}

output "docker_config_secret_name" {
  description = "Name of the Docker config secret"
  value       = aws_secretsmanager_secret.docker_config.name
}

# Parameter Store Outputs
output "flask_env_parameter_arn" {
  description = "ARN of the Flask environment parameter"
  value       = aws_ssm_parameter.flask_env.arn
}

output "flask_env_parameter_name" {
  description = "Name of the Flask environment parameter"
  value       = aws_ssm_parameter.flask_env.name
}

output "debug_mode_parameter_arn" {
  description = "ARN of the debug mode parameter"
  value       = aws_ssm_parameter.debug_mode.arn
}

output "debug_mode_parameter_name" {
  description = "Name of the debug mode parameter"
  value       = aws_ssm_parameter.debug_mode.name
}

output "log_level_parameter_arn" {
  description = "ARN of the log level parameter"
  value       = aws_ssm_parameter.log_level.arn
}

output "log_level_parameter_name" {
  description = "Name of the log level parameter"
  value       = aws_ssm_parameter.log_level.name
}

# ACM Certificate Outputs
output "acm_certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS"
  value       = aws_acm_certificate.ecommerce_domain.arn
}

output "acm_certificate_domain" {
  description = "Domain name of the ACM certificate"
  value       = aws_acm_certificate.ecommerce_domain.domain_name
}

output "acm_certificate_status" {
  description = "Status of the ACM certificate (pending_validation, issued, etc.)"
  value       = aws_acm_certificate.ecommerce_domain.status
}

output "acm_certificate_validation_options" {
  description = "DNS validation options for ACM certificate (use in Route 53)"
  value       = aws_acm_certificate.ecommerce_domain.domain_validation_options
  sensitive   = true
}

# RDS Outputs
output "rds_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = aws_db_instance.ecommerce_db.endpoint
}

output "rds_port" {
  description = "The port the RDS instance is listening on"
  value       = aws_db_instance.ecommerce_db.port
}

output "rds_security_group_id" {
  description = "The ID of the security group attached to the RDS instance"
  value       = aws_security_group.rds_sg.id
}

# Summary Outputs
output "summary" {
  description = "Summary of created resources"
  value = {
    secrets_created = {
      database_url  = aws_secretsmanager_secret.database_url.name
      secret_key    = aws_secretsmanager_secret.secret_key.name
      docker_config = aws_secretsmanager_secret.docker_config.name
    }
    parameters_created = {
      flask_env  = aws_ssm_parameter.flask_env.name
      debug_mode = aws_ssm_parameter.debug_mode.name
      log_level  = aws_ssm_parameter.log_level.name
    }
    total_resources = 6
    region          = var.aws_region
    environment     = var.environment
  }
}

