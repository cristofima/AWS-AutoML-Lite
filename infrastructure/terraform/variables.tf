variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be either 'dev' or 'prod'."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "AWS region must be in valid format (e.g., us-east-1, eu-west-2)."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "automl-lite"
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 1024

  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory must be between 128 MB and 10240 MB (AWS limits)."
  }
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60

  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds (AWS limits)."
  }
}

variable "batch_vcpu" {
  description = "Batch job vCPU"
  type        = number
  default     = 2
}

variable "batch_memory" {
  description = "Batch job memory in MB"
  type        = number
  default     = 4096
}

variable "batch_max_vcpus" {
  description = "Max vCPUs for Batch compute environment"
  type        = number
  default     = 4
}

variable "s3_lifecycle_days" {
  description = "Days before S3 objects are deleted"
  type        = number
  default     = 90
}

variable "cloudwatch_retention_days" {
  description = "CloudWatch logs retention in days"
  type        = number
  default     = 7
}

variable "vpc_id" {
  description = "VPC ID for Batch compute environment (leave empty to use default VPC)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "Subnet IDs for Batch compute environment (leave empty to auto-detect)"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security group IDs for Batch compute environment (leave empty to create default)"
  type        = list(string)
  default     = []
}

variable "terraform_state_bucket" {
  description = "S3 bucket name for Terraform state (override in backend config)"
  type        = string
  default     = "automl-lite-terraform-state"
}

variable "terraform_locks_table" {
  description = "DynamoDB table for Terraform state locking"
  type        = string
  default     = "automl-lite-terraform-locks"
}

# =============================================================================
# Frontend (Amplify) Variables
# =============================================================================

variable "github_repository" {
  description = "GitHub repository URL for Amplify (e.g., https://github.com/owner/repo)"
  type        = string
  default     = ""
}

variable "github_token" {
  description = "GitHub personal access token for Amplify to access the repository"
  type        = string
  sensitive   = true
  default     = ""
}
