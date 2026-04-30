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

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default = {
    Owner      = "Platform Team"
    CostCenter = "Engineering"
  }
}
# Jenkins Infrastructure Variables
variable "jenkins_vpc_id" {
  description = "VPC ID for Jenkins resources (leave empty to use default VPC)"
  type        = string
  default     = ""
}

variable "jenkins_subnet_ids" {
  description = "Subnet IDs for Jenkins controller and agents (leave empty to auto-discover subnets in selected VPC)"
  type        = list(string)
  default     = []
}

variable "jenkins_ami_id" {
  description = "AMI ID to use for Jenkins controller and agents (leave empty to use latest Amazon Linux 2)"
  type        = string
  default     = ""
}

variable "jenkins_controller_instance_type" {
  description = "Instance type for Jenkins controller"
  type        = string
  default     = "t3.medium"
}

variable "jenkins_controller_root_volume_size" {
  description = "Root volume size (GB) for Jenkins controller"
  type        = number
  default     = 50
}

variable "jenkins_controller_public_ip" {
  description = "Whether Jenkins controller should have a public IP"
  type        = bool
  default     = true
}

variable "jenkins_controller_allowed_cidrs" {
  description = "CIDR blocks allowed to access Jenkins UI (8080) and SSH (22)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "jenkins_controller_key_name" {
  description = "Optional EC2 key pair name for Jenkins controller"
  type        = string
  default     = ""
}

variable "jenkins_admin_username" {
  description = "Initial Jenkins admin username"
  type        = string
  default     = "admin"
}

variable "jenkins_admin_password" {
  description = "Initial Jenkins admin password"
  type        = string
  sensitive   = true
}

variable "jenkins_agent_instance_type" {
  description = "Instance type for ephemeral Jenkins agents"
  type        = string
  default     = "t3.small"
}

variable "jenkins_agent_max_size" {
  description = "Maximum number of ephemeral Jenkins agents"
  type        = number
  default     = 10
}

variable "jenkins_agent_key_name" {
  description = "Optional EC2 key pair name for Jenkins agents (needed for SSH-based plugin mode)"
  type        = string
  default     = ""
}
