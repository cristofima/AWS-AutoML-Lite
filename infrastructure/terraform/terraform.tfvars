environment  = "dev"
aws_region   = "us-east-1"
project_name = "automl-lite"

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
