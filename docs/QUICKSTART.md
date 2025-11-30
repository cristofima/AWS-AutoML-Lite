# 🚀 AWS AutoML Lite - Quick Start Guide

Complete deployment guide for AWS AutoML Lite using Terraform.

---

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ **AWS Account** with administrative access
- ✅ **AWS CLI** installed and configured ([Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- ✅ **Terraform** >= 1.5 installed ([Download](https://www.terraform.io/downloads))
- ✅ **Docker** installed and running ([Get Docker](https://www.docker.com/get-started)) - *Only for training container*
- ✅ **Git** installed

**Note:** Docker is ONLY needed for building the training container (AWS Batch). The API Lambda function uses direct code deployment (no containers).

---

## 🏁 Quick Start (3 Steps)

### Step 1: Configure AWS CLI

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format: `json`

Verify configuration:
```bash
aws sts get-caller-identity
```

---

### Step 2: Deploy Infrastructure

```bash
# Navigate to Terraform directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Deploy (type 'yes' when prompted)
terraform apply
```

**⏱️ Deployment time:** ~5-10 minutes

---

### Step 3: Build & Push Training Container

After infrastructure is deployed:

```bash
# Get ECR repository URL
ECR_URL=$(terraform output -raw ecr_repository_url)
REGION=$(terraform output -raw aws_region)

# Authenticate Docker to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $(echo $ECR_URL | cut -d'/' -f1)

# Build and push training container
cd ../../backend/training
docker build -t automl-training:latest .
docker tag automl-training:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

**Windows PowerShell:**
```powershell
# Get ECR repository URL
$EcrUrl = terraform output -raw ecr_repository_url
$Region = terraform output -raw aws_region

# Authenticate Docker to ECR
$Password = aws ecr get-login-password --region $Region
$Password | docker login --username AWS --password-stdin $($EcrUrl.Split('/')[0])

# Build and push training container
cd ../../backend/training
docker build -t automl-training:latest .
docker tag automl-training:latest "$EcrUrl:latest"
docker push "$EcrUrl:latest"
```

---

## 🎯 Get Your API URL

```bash
cd infrastructure/terraform
terraform output api_gateway_url
```

Copy this URL - you'll need it for the frontend and testing.

Example output: `https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev`

---

## 🧪 Test Your Deployment

### 1. Test API Health

```bash
API_URL=$(terraform output -raw api_gateway_url)
curl $API_URL/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "automl-api",
  "region": "us-east-1"
}
```

### 2. Request Upload URL

```bash
curl -X POST $API_URL/upload \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.csv"}'
```

### 3. View All Outputs

```bash
terraform output
```

---

## 📊 What Gets Created

| Resource | Purpose | Cost Impact |
|----------|---------|-------------|
| **3 S3 Buckets** | Store datasets, models, reports | $0.23/month (10GB) |
| **2 DynamoDB Tables** | Training history & metadata | $1.00/month (on-demand) |
| **Lambda Function** | API endpoints | $0.80/month (100K requests) |
| **API Gateway** | REST API | $1.00/month (100K requests) |
| **AWS Batch** | Training jobs (Fargate Spot) | $3.00/month (20 jobs) |
| **ECR Repository** | Container images | Included |
| **CloudWatch Logs** | Monitoring | $0.50/month |
| **IAM Roles** | Permissions | Free |

**💰 Total Estimated Cost:** ~$7-10/month for moderate usage

---

## ⚙️ Configuration Options

Edit `infrastructure/terraform/terraform.tfvars` before deploying:

```hcl
# Environment
environment = "dev"  # or "prod"
aws_region  = "us-east-1"

# Lambda Configuration
lambda_memory_size = 1024  # MB
lambda_timeout     = 60    # seconds

# Batch Configuration
batch_vcpu      = "2"      # vCPUs
batch_memory    = "4096"   # MB
batch_max_vcpus = 4

# Lifecycle
s3_lifecycle_days         = 90  # Days before auto-delete
cloudwatch_retention_days = 7

# VPC (leave empty to use default VPC)
vpc_id             = ""
subnet_ids         = []
security_group_ids = []
```

---

## 📈 Monitoring Your Services

### View Lambda Logs
```bash
aws logs tail /aws/lambda/automl-lite-dev-api --follow
```

### View Batch Training Logs
```bash
aws logs tail /aws/batch/automl-lite-dev-training --follow
```

### Check Resource Status
```bash
terraform show
terraform state list
```

---

## 🔄 Updating Your Deployment

### Update Lambda Code
```bash
cd infrastructure/terraform
terraform apply -target=aws_lambda_function.api
```

### Update Training Container
```bash
# Rebuild and push new image
cd backend/training
docker build -t automl-training:latest .
docker tag automl-training:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Batch will use the new image on next training job
```

### Update All Infrastructure
```bash
cd infrastructure/terraform
terraform apply
```

---

## 🗑️ Cleanup (Destroy Resources)

**⚠️ Warning:** This will delete ALL resources and data!

```bash
cd infrastructure/terraform

# Empty S3 buckets first (required)
aws s3 rm s3://$(terraform output -raw datasets_bucket_name) --recursive
aws s3 rm s3://$(terraform output -raw models_bucket_name) --recursive
aws s3 rm s3://$(terraform output -raw reports_bucket_name) --recursive

# Destroy all infrastructure
terraform destroy
```

Type `yes` when prompted.

---

## 🐛 Troubleshooting

### Issue: "Error: Error acquiring the state lock"

**Solution:**
```bash
# Force unlock (use the Lock ID from error message)
terraform force-unlock <LOCK_ID>
```

### Issue: Lambda function deployment failed

**Solution:**
```bash
# Check if package is too large
cd infrastructure/terraform
ls -lh lambda_function.zip

# If > 50MB, optimize dependencies or use Lambda layers
```

### Issue: Batch jobs not starting

**Solution:**
1. Verify ECR image exists:
   ```bash
   aws ecr describe-images --repository-name automl-training
   ```

2. Check compute environment status:
   ```bash
   aws batch describe-compute-environments
   ```

3. Verify VPC/subnet configuration in `terraform.tfvars`

### Issue: API returns 502 Bad Gateway

**Solution:**
1. Check Lambda logs for errors
2. Verify Lambda has correct environment variables
3. Test Lambda directly:
   ```bash
   aws lambda invoke --function-name automl-lite-dev-api --payload '{}' response.json
   ```

---

## 🔐 Security Best Practices

✅ **Implemented by default:**
- S3 buckets are private (block public access)
- IAM roles use least privilege
- CloudWatch logging enabled
- X-Ray tracing enabled
- Encryption at rest (S3, DynamoDB)

🔒 **Additional recommendations:**
- Enable MFA for AWS account
- Use AWS Secrets Manager for sensitive data
- Enable CloudTrail for audit logs
- Use VPC endpoints for S3/DynamoDB (optional)
- Rotate AWS access keys regularly

---

## 📚 Next Steps

1. **Run Locally**
   ```bash
   # Configure backend
   cp backend/.env.example backend/.env
   # Edit with values from: terraform output
   
   # Start API
   docker-compose up
   
   # Configure and start frontend
   cd frontend
   cp .env.local.example .env.local
   # Edit with API URL from terraform output
   pnpm install && pnpm dev
   ```

2. **Test Complete Workflow**
   - Upload sample CSV
   - Train model
   - Download results

3. **Write Article**
   - Document architecture
   - Share cost analysis
   - Publish as AWS Community Builder

---

## 🆘 Need Help?

- 📖 **Full Documentation:** See `PROJECT_REFERENCE.md`
- 🔧 **Terraform Docs:** See `infrastructure/terraform/README.md`
- 🐛 **Issues:** Create a GitHub issue
- 💬 **AWS Support:** Use AWS Support Center

---

## 📝 Useful Commands Cheat Sheet

```bash
# Terraform
terraform init                    # Initialize
terraform plan                    # Preview changes
terraform apply                   # Deploy
terraform destroy                 # Delete everything
terraform output                  # Show outputs
terraform state list              # List resources
terraform show                    # Show current state

# AWS CLI
aws sts get-caller-identity      # Check credentials
aws s3 ls                         # List S3 buckets
aws lambda list-functions         # List Lambda functions
aws batch list-jobs --job-queue <name> --job-status RUNNING  # Check Batch jobs

# Docker
docker build -t name:tag .        # Build image
docker push repo:tag              # Push to registry
docker images                     # List local images
docker ps                         # List running containers

# Logs
aws logs tail <log-group> --follow          # Stream logs
aws logs describe-log-groups                # List log groups
```

---

**🎉 You're all set!** Your AutoML platform is now running on AWS.
