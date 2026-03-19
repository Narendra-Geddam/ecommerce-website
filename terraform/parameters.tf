# AWS Systems Manager Parameter Store - Non-sensitive Configuration
# Stores non-sensitive application configuration parameters

# Parameter: Flask Environment
resource "aws_ssm_parameter" "flask_env" {
  name            = "${var.parameter_project_prefix}/flask-env"
  description     = "Flask environment setting (development, production)"
  type            = "String"
  value           = var.flask_env
  tier            = var.parameters_tier
  overwrite       = true
  
  tags = merge(
    var.tags,
    {
      Name                = "ecommerce-flask-env"
      Parameter_Type      = "configuration"
      Sensitivity         = "non-sensitive"
    }
  )
}

# Parameter: Debug Mode
resource "aws_ssm_parameter" "debug_mode" {
  name            = "${var.parameter_project_prefix}/debug"
  description     = "Flask debug mode (true/false)"
  type            = "String"
  value           = var.debug_mode
  tier            = var.parameters_tier
  overwrite       = true
  
  tags = merge(
    var.tags,
    {
      Name                = "ecommerce-debug-mode"
      Parameter_Type      = "configuration"
      Sensitivity         = "non-sensitive"
    }
  )
}

# Parameter: Log Level
resource "aws_ssm_parameter" "log_level" {
  name            = "${var.parameter_project_prefix}/log-level"
  description     = "Application log level (DEBUG, INFO, WARNING, ERROR)"
  type            = "String"
  value           = var.log_level
  tier            = var.parameters_tier
  overwrite       = true
  
  tags = merge(
    var.tags,
    {
      Name                = "ecommerce-log-level"
      Parameter_Type      = "configuration"
      Sensitivity         = "non-sensitive"
    }
  )
}

# KMS Key for encrypted parameters (optional, only if enable_parameter_encryption is true and kms_key_id is provided)
# If not provided, AWS managed key (alias/aws/ssm) is used by default

# Outputs for reference
output "parameter_store_parameters" {
  description = "Created Parameter Store parameter details"
  value = {
    flask_env_arn       = aws_ssm_parameter.flask_env.arn
    flask_env_name      = aws_ssm_parameter.flask_env.name
    flask_env_version   = aws_ssm_parameter.flask_env.version
    
    debug_mode_arn      = aws_ssm_parameter.debug_mode.arn
    debug_mode_name     = aws_ssm_parameter.debug_mode.name
    debug_mode_version  = aws_ssm_parameter.debug_mode.version
    
    log_level_arn       = aws_ssm_parameter.log_level.arn
    log_level_name      = aws_ssm_parameter.log_level.name
    log_level_version   = aws_ssm_parameter.log_level.version
  }
}
