variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "eu-north-1"
}

variable "environment" {
  description = "Environment name (prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "ecommerce"
}

variable "secret_project_prefix" {
  description = "Prefix for secret names in Secrets Manager"
  type        = string
  default     = "ecommerce"
}

variable "parameter_project_prefix" {
  description = "Prefix for parameter names in Parameter Store"
  type        = string
  default     = "/ecommerce"
}

# Secrets Manager Variables


variable "secret_key" {
  description = "Flask application secret key"
  type        = string
  sensitive   = true
}

variable "docker_config" {
  description = "Docker Hub configuration (base64 encoded or JSON)"
  type        = string
  sensitive   = true
}

variable "secrets_recovery_window" {
  description = "Recovery window for secret deletion in days"
  type        = number
  default     = 7
}

# Parameter Store Variables
variable "flask_env" {
  description = "Flask environment (development, production)"
  type        = string
  default     = "production"
}

variable "debug_mode" {
  description = "Flask debug mode (true/false)"
  type        = string
  default     = "false"
}

variable "log_level" {
  description = "Application log level (DEBUG, INFO, WARNING, ERROR)"
  type        = string
  default     = "INFO"
}

variable "parameters_tier" {
  description = "Parameter Store tier (Standard or Advanced)"
  type        = string
  default     = "Standard"

  validation {
    condition     = contains(["Standard", "Advanced"], var.parameters_tier)
    error_message = "Parameter tier must be either 'Standard' or 'Advanced'."
  }
}

variable "enable_parameter_encryption" {
  description = "Enable encryption for sensitive parameters"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "KMS key ID for parameter encryption (optional, uses default AWS managed key if not provided)"
  type        = string
  default     = null
}

variable "domain_name" {
  description = "Domain name for the application (e.g., morecraze.in)"
  type        = string
  default     = "morecraze.in"
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone ID for DNS validation (optional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default = {
    Owner      = "Platform Team"
    CostCenter = "Engineering"
  }
}

