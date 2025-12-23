environment  = "dev"
aws_region   = "us-east-1"
project_name = "automl-lite"

# GitHub repository for Amplify (token is passed via TF_VAR_github_token in CI/CD)
github_repository = "https://github.com/cristofima/AWS-AutoML-Lite"

# CORS - additional origins for dev (localhost added automatically in Terraform for dev)
cors_allowed_origins = []

# Lambda configuration
lambda_memory_size = 1024
lambda_timeout     = 60

# Batch configuration
batch_vcpu      = "2"
batch_memory    = "4096"
batch_max_vcpus = 4

# Lifecycle
s3_lifecycle_days         = 90
cloudwatch_retention_days = 7

# VPC configuration (leave empty to use default VPC)
vpc_id             = ""
subnet_ids         = []
security_group_ids = []
