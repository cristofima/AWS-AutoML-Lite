variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
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
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "batch_vcpu" {
  description = "Batch job vCPU"
  type        = string
  default     = "2"
}

variable "batch_memory" {
  description = "Batch job memory in MB"
  type        = string
  default     = "4096"
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
