environment  = "prod"
aws_region   = "us-east-1"
project_name = "automl-lite"

# GitHub repository for Amplify (token is passed via TF_VAR_github_token in CI/CD)
github_repository = "https://github.com/cristofima/AWS-AutoML-Lite"

# Lambda configuration
lambda_memory_size = 2048
lambda_timeout     = 60

# Batch configuration
batch_vcpu      = "4"
batch_memory    = "8192"
batch_max_vcpus = 8

# Lifecycle
s3_lifecycle_days         = 365
cloudwatch_retention_days = 30

# VPC configuration (configure for production)
vpc_id             = "" # Add your VPC ID
subnet_ids         = [] # Add your subnet IDs
security_group_ids = [] # Add your security group IDs
