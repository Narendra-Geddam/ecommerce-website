terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment below to use S3 remote state (recommended for production)
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "ecommerce/secrets/terraform.tfstate"
  #   region         = "eu-north-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region
}
