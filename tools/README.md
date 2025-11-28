# Development & Deployment Tools

This directory contains manual tools for developers and operators.

## Available Tools

### `verify-resources.ps1`
**Purpose:** Validate all deployed AWS resources  
**Usage:**
```powershell
cd tools
.\verify-resources.ps1
```

**Checks:**
- API Gateway endpoints
- Lambda function health
- S3 buckets accessibility
- DynamoDB tables status
- Batch compute environment
- ECR repository and images
- CloudWatch log groups
- IAM roles and permissions
- Resource tagging compliance

**When to use:**
- After infrastructure deployment
- Before production releases
- Troubleshooting deployment issues
- Auditing resource state

---

### `setup-backend.ps1`
**Purpose:** Initialize Terraform S3 remote backend (one-time setup)  
**Usage:**
```powershell
cd tools
.\setup-backend.ps1
```

**What it does:**
- Creates S3 bucket for Terraform state
- Enables versioning and encryption
- Creates DynamoDB table for state locking
- Configures lifecycle policies
- Sets up point-in-time recovery

**When to use:**
- First time setting up the project
- Creating new AWS account setup
- Disaster recovery (recreate backend)

**Prerequisites:**
- AWS CLI configured
- Admin permissions in AWS account

---

## Best Practices

1. **Run from project root or tools directory**
   ```powershell
   # From project root
   .\tools\verify-resources.ps1
   
   # Or from tools/
   cd tools
   .\verify-resources.ps1
   ```

2. **Check AWS credentials before running**
   ```powershell
   aws sts get-caller-identity
   ```

3. **Review output carefully**
   - All scripts provide detailed status
   - ❌ Red errors require immediate attention
   - ⚠️ Yellow warnings are informational

4. **Version control**
   - These scripts are committed to Git
   - Changes should be code-reviewed
   - Test in dev before using in prod

---

## CI/CD vs Manual Tools

| Location | Purpose | Usage |
|----------|---------|-------|
| `.github/workflows/` | Automated CI/CD pipelines | Runs on git push |
| `infrastructure/terraform/scripts/` | Build artifacts for CI/CD | Used by workflows |
| `tools/` (this directory) | Manual operations | Run by developers |

---

**Last Updated:** 2025-11-28
