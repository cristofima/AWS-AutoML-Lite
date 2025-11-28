terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  # S3 backend for remote state with DynamoDB locking
  # Run setup script first: ./scripts/setup-terraform-backend.sh
  backend "s3" {
    bucket         = "automl-lite-terraform-state-835503570883"
    key            = "automl-lite/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "automl-lite-terraform-locks"
    
    # Prevent concurrent state operations
    # DynamoDB table provides state locking and consistency checking
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "AWS-AutoML-Lite"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
