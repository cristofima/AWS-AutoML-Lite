# AWS AutoML Lite - Terraform Infrastructure

Infrastructure as Code for AWS AutoML Lite platform.

## Prerequisites

- Terraform >= 1.5
- AWS CLI configured
- Docker (for training container)

## Quick Start

```bash
# Initialize
terraform init

# Deploy
terraform plan
terraform apply

# Get outputs
terraform output
```

See [QUICKSTART.md](../../docs/QUICKSTART.md) for complete deployment guide.

## Configuration Files

Core Terraform modules:
- `main.tf` - Provider & backend configuration
- `variables.tf` - Input variables
- `*.tf` - Resource definitions (S3, Lambda, Batch, etc.)
- `terraform.tfvars` - Development environment values

## Key Outputs

- `api_gateway_url` - API endpoint
- `ecr_repository_url` - Container registry
- `*_bucket_name` - S3 buckets for datasets/models/reports

## Cleanup

```bash
# Empty S3 buckets first
aws s3 rm s3://$(terraform output -raw datasets_bucket_name) --recursive
aws s3 rm s3://$(terraform output -raw models_bucket_name) --recursive
aws s3 rm s3://$(terraform output -raw reports_bucket_name) --recursive

# Destroy infrastructure
terraform destroy
```

## Additional Resources

- [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md) - Why containers for training
- [PROJECT_REFERENCE.md](../../docs/PROJECT_REFERENCE.md) - Complete technical docs
- [SETUP_CICD.md](../../.github/SETUP_CICD.md) - CI/CD with GitHub Actions
