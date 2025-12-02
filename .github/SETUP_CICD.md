# CI/CD Setup Guide

## Overview

This project uses GitHub Actions for automated CI/CD with AWS using OIDC (OpenID Connect) for secure, credential-less authentication.

## Architecture

```
Commit to dev  → Auto Deploy to DEV  → Build Training Container
Commit to main → Plan → Manual Approval → Deploy to PROD → Build Container
```

---

## Prerequisites

### 1. AWS OIDC Provider Setup

Create an OIDC provider in AWS to allow GitHub Actions to assume IAM roles without long-lived credentials.

```bash
# Get your AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO="cristofima/AWS-AutoML-Lite"

# Create OIDC provider (only once per AWS account)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 3. Create IAM Role for GitHub Actions

```bash
# Create trust policy
cat > github-actions-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:${REPO}:*"
        }
      }
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name GitHubActionsDeployRole \
  --assume-role-policy-document file://github-actions-trust-policy.json \
  --description "Role for GitHub Actions to deploy AWS AutoML Lite"
```

### 4. Attach Permissions to Role

```bash
# Create deployment policy
cat > github-actions-permissions.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TerraformStateManagement",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::automl-lite-terraform-state-*",
        "arn:aws:s3:::automl-lite-terraform-state-*/*"
      ]
    },
    {
      "Sid": "TerraformStateLocking",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/automl-lite-terraform-locks"
    },
    {
      "Sid": "S3Management",
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::automl-lite-*",
        "arn:aws:s3:::automl-lite-*/*"
      ]
    },
    {
      "Sid": "DynamoDBManagement",
      "Effect": "Allow",
      "Action": "dynamodb:*",
      "Resource": "arn:aws:dynamodb:*:*:table/automl-lite-*"
    },
    {
      "Sid": "LambdaManagement",
      "Effect": "Allow",
      "Action": "lambda:*",
      "Resource": "arn:aws:lambda:*:*:function:automl-lite-*"
    },
    {
      "Sid": "APIGatewayManagement",
      "Effect": "Allow",
      "Action": "apigateway:*",
      "Resource": "*"
    },
    {
      "Sid": "BatchManagement",
      "Effect": "Allow",
      "Action": "batch:*",
      "Resource": "*"
    },
    {
      "Sid": "ECRManagement",
      "Effect": "Allow",
      "Action": "ecr:*",
      "Resource": "arn:aws:ecr:*:*:repository/automl-lite-*"
    },
    {
      "Sid": "ECRAuth",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "AmplifyManagement",
      "Effect": "Allow",
      "Action": "amplify:*",
      "Resource": "arn:aws:amplify:*:*:apps/*"
    },
    {
      "Sid": "IAMRoleManagement",
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:UpdateRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:PassRole",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:ListInstanceProfilesForRole",
        "iam:TagRole",
        "iam:UntagRole"
      ],
      "Resource": "arn:aws:iam::*:role/automl-lite-*"
    },
    {
      "Sid": "IAMServiceLinkedRoles",
      "Effect": "Allow",
      "Action": [
        "iam:CreateServiceLinkedRole",
        "iam:DeleteServiceLinkedRole",
        "iam:GetServiceLinkedRoleDeletionStatus"
      ],
      "Resource": [
        "arn:aws:iam::*:role/aws-service-role/batch.amazonaws.com/*",
        "arn:aws:iam::*:role/aws-service-role/ecs.amazonaws.com/*",
        "arn:aws:iam::*:role/aws-service-role/spot.amazonaws.com/*",
        "arn:aws:iam::*:role/aws-service-role/spotfleet.amazonaws.com/*"
      ]
    },
    {
      "Sid": "NetworkingForBatch",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeAccountAttributes",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeRouteTables",
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:CreateTags",
        "ec2:DeleteTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:PutRetentionPolicy",
        "logs:DescribeLogGroups",
        "logs:ListTagsLogGroup",
        "logs:TagLogGroup",
        "logs:UntagLogGroup",
        "logs:ListTagsForResource",
        "logs:TagResource",
        "logs:UntagResource"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/lambda/automl-lite-*",
        "arn:aws:logs:*:*:log-group:/aws/batch/automl-lite-*",
        "arn:aws:logs:*:*:log-group:/aws/apigateway/automl-lite-*"
      ]
    },
    {
      "Sid": "CallerIdentity",
      "Effect": "Allow",
      "Action": "sts:GetCallerIdentity",
      "Resource": "*"
    }
  ]
}
EOF

# Create and attach policy
aws iam put-role-policy \
  --role-name GitHubActionsDeployRole \
  --policy-name DeploymentPermissions \
  --policy-document file://github-actions-permissions.json

# Get role ARN
aws iam get-role --role-name GitHubActionsDeployRole --query 'Role.Arn' --output text
```

**Save this ARN - you'll need it for GitHub Secrets!**

---

## GitHub Configuration

### 2. Add Repository Secrets

Go to: **Settings → Secrets and variables → Actions → New repository secret**

#### Required Secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AWS_ROLE_ARN` | IAM Role ARN for OIDC | `arn:aws:iam::123456789:role/GitHubActionsDeployRole` |
| `GH_PAT_AMPLIFY` | GitHub PAT for Amplify | `ghp_xxxxxxxxxxxx` |

#### Creating the GitHub Personal Access Token (PAT) for Amplify:

1. Go to: **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. Click **Generate new token (classic)**
3. Configure:
   - **Note:** `Amplify Deploy Token`
   - **Expiration:** 90 days (or custom)
   - **Scopes:** Select:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `admin:repo_hook` (Full control of repository hooks)
4. Click **Generate token**
5. Copy the token (starts with `ghp_`)
6. Add as repository secret: `GH_PAT_AMPLIFY`

**⚠️ Note:** This token is required for Amplify to:
- Access the repository
- Set up webhooks for auto-deploy on push
- Read the `amplify.yml` build configuration

**That's it!** Two secrets for all environments.

### 3. Create GitHub Environments (Only for Production Protection)

Go to: **Settings → Environments** and create:

#### **prod** Environment
- ✅ Required reviewers: Add yourself
- ✅ Wait timer: 0 minutes (optional: 5-30 min for rollback window)

**Note:** `dev` doesn't need an environment - uses the repository secret directly.

### 4. Enable GitHub Actions

Go to: **Settings → Actions → General**
- Workflow permissions: ✅ Read and write permissions
- Allow GitHub Actions to create and approve pull requests: ✅ Enabled

---

## Workflow Overview

### **ci-validate.yml** - Continuous Integration
**Triggers:** Push/PR to dev or main  
**Actions:**
- Validates Terraform formatting and syntax
- Tests Backend API imports and linting
- Validates Training container builds
- Type-checks Frontend (Next.js)

**Smart triggers:** Only runs jobs for changed components

### **deploy-lambda-api.yml** - Lambda API Deployment
**Triggers:** Changes to `backend/api/` or manual  
**Actions:**
1. Build Lambda package (Docker)
2. Update Lambda function code only
3. Test API health endpoint

**Fast deployment:** ~2-3 minutes (only API, no infrastructure)

### **deploy-training-container.yml** - Training Container Deployment
**Triggers:** Changes to `backend/training/` or manual  
**Actions:**
1. Build training Docker image
2. Push to ECR with environment tag
3. Tag as `:latest` for Batch jobs

**Fast deployment:** ~3-5 minutes (only container, no infrastructure)

### **deploy-frontend.yml** - Frontend Deployment
**Triggers:** Manual only (Amplify auto-deploys on push)  
**Actions:**
1. Get Amplify App ID for environment
2. Trigger Amplify build job
3. Wait for build completion
4. Output deployment URL

**Smart features:**
- Automatically validates infrastructure is deployed first
- Retrieves API URL from Terraform (no manual configuration)
- Separate deployments for dev/prod environments
- Fast deployment: ~3-5 minutes

**Fast deployment:** ~3-5 minutes (frontend only, no infrastructure)

### **deploy-infrastructure.yml** - Full Infrastructure Deployment
**Triggers:** Changes to `infrastructure/terraform/` or manual  
**Actions:**
1. **Plan Job**: Generate Terraform plan
2. **Deploy Job** (requires approval for prod):
   - Apply infrastructure changes
   - Build and deploy Lambda
   - Test API health
3. **Post-Deploy Job**: Build and push training container

**Production requires manual approval** - full safety!

### **destroy-environment.yml** - Teardown Infrastructure
**Triggers:** Manual only  
**Actions:**
- Requires typing "DESTROY" to confirm
- Production destruction requires repository owner
- Runs `terraform destroy` for selected environment

---

## Usage Examples

### Deploy Lambda API Only (Fast - 2 min)
```bash
# Edit API code
git add backend/api/
git commit -m "fix: Update health endpoint response"
git push origin dev

# ✅ Only Lambda function updated
# ✅ Infrastructure untouched
# ✅ Training container untouched
```

### Deploy Training Container Only (Fast - 3 min)
```bash
# Edit training code
git add backend/training/
git commit -m "feat: Add XGBoost hyperparameter tuning"
git push origin dev

# ✅ Only ECR image updated
# ✅ Infrastructure untouched
# ✅ Lambda function untouched
```

### Deploy Frontend Only (Fast - 3 min)
```bash
# Edit frontend code
git add frontend/
git commit -m "feat: Add training progress bar"
git push origin dev

# ✅ Amplify auto-deploys on push (webhook)
# ✅ Infrastructure untouched
# ✅ API untouched
# ✅ Automatically gets API URL from Terraform
```

### Deploy Infrastructure (Full - 10 min)
```bash
# Edit Terraform
git add infrastructure/terraform/
git commit -m "feat: Add CloudWatch alarms"
git push origin dev

# ✅ Infrastructure deployed
# ✅ Lambda rebuilt and deployed
# ✅ Training container rebuilt and pushed
```

### Deploy to Production
```bash
# Merge dev to main
git checkout main
git merge dev
git push origin main

# ⏳ Waits for manual approval if infrastructure changed
# Go to: Actions → Review deployments → Approve
```

### Manual Component Deploy
```bash
# Go to: Actions → Select workflow
# - Deploy Lambda API
# - Deploy Training Container
# - Deploy Frontend
# - Deploy Infrastructure
# Click "Run workflow" → Select environment → Run
```

**Note for Frontend Deployment:**
- Frontend deployment will automatically check if infrastructure exists
- If infrastructure not found, it will fail with clear instructions
- Deploy infrastructure first, then frontend will work automatically

### Destroy Environment
```bash
# Go to: Actions → Destroy Environment
# Select environment (dev/prod)
# Type "DESTROY" to confirm
# Approve if production
```

---

## Deployment Order & Dependencies

### 🎯 Automatic Dependency Resolution

The workflows are smart and **automatically validate dependencies**:

```
Infrastructure (Terraform)
    ↓ (creates API Gateway, Amplify, S3, ECR)
    ├→ Backend API (Lambda)
    ├→ Training Container (ECR/Batch)
    └→ Frontend (Amplify - auto-deploys on push)
         ↓ (gets API URL from Amplify environment variables)
```

### ✅ First-Time Setup Order

When deploying a **new environment** from scratch:

1. **Deploy Infrastructure** (Required first)
```bash
cd infrastructure/terraform
terraform workspace select dev
terraform apply
```
   - Creates all AWS resources
   - Outputs API Gateway URL
   - Creates Amplify app for frontend
   - Takes ~5-10 minutes

2. **Deploy Backend API** (Automatic after infrastructure)
```bash
# Either:
# - Workflow runs automatically if triggered by infrastructure deployment
# - Or manually: Actions → Deploy Lambda API
```
   - Deploys FastAPI code to Lambda
   - Takes ~2-3 minutes

3. **Deploy Training Container** (Automatic after infrastructure)
```bash
# Either:
# - Workflow runs automatically if triggered by infrastructure deployment  
# - Or manually: Actions → Deploy Training Container
```
   - Builds and pushes Docker image to ECR
   - Takes ~3-5 minutes

4. **Deploy Frontend** (Automatic via Amplify)
```bash
# Push to branch triggers Amplify auto-deploy
git push origin dev
```
   - **Amplify auto-deploys on push** (webhook)
   - **API URL set in Amplify environment variables**
   - Builds Next.js SSR app
   - Takes ~3-5 minutes

### 🔄 Subsequent Deployments

After initial setup, you can deploy components **independently**:

| Component | Checks Infrastructure? | Gets API URL? | Independent? |
|-----------|------------------------|---------------|--------------|
| Infrastructure | N/A | N/A | ✅ Yes |
| Lambda API | ✅ Auto-validates | N/A | ✅ Yes (if infra exists) |
| Training Container | ✅ Auto-validates | N/A | ✅ Yes (if infra exists) |
| Frontend | ✅ Auto-validates | ✅ Auto-retrieves | ✅ Yes (if infra exists) |

### ❌ What Happens if You Deploy in Wrong Order?

**Scenario: Deploy frontend before infrastructure**
```
✅ Workflow starts
✅ Checks if infrastructure exists
❌ Infrastructure not found
❌ Workflow fails with clear message:
   "Infrastructure must be deployed first!"
   "Run 'Deploy Infrastructure' workflow for dev environment"
```

**No broken deployments** - the workflow protects you!

### 🎯 How API URL is Passed (Automatic)

**Answer: Automatic via Terraform → Amplify environment variables!**

```hcl
# In amplify.tf:
resource "aws_amplify_app" "frontend" {
  # ...
  environment_variables = {
    NEXT_PUBLIC_API_URL = aws_api_gateway_stage.main.invoke_url  # ← Set by Terraform!
  }
}
```

When Amplify builds, it reads `NEXT_PUBLIC_API_URL` from its environment variables (set by Terraform) and injects it into the Next.js build.

**No manual configuration needed!** The flow is:
1. ✅ Terraform creates API Gateway
2. ✅ Terraform creates Amplify app with `NEXT_PUBLIC_API_URL` = API Gateway URL
3. ✅ Push to branch triggers Amplify webhook
4. ✅ Amplify builds with correct API URL
5. ✅ Amplify deploys to CDN

### 🚦 Validation Flow

```mermaid
graph TD
    A[Push to Branch] --> B{Amplify webhook triggers?}
    B -->|Yes| C[Amplify starts build]
    C --> D[Install dependencies]
    D --> E[Build Next.js SSR]
    E --> F[Deploy to Amplify CDN]
    F --> G[✅ Success]
    B -->|No webhook| H[Manual: Actions → Re-deploy Frontend]
    H --> C
```

### 📝 Manual Override (Optional)

If you need to manually specify API URL (not recommended):

```bash
# Local development
cd frontend
export NEXT_PUBLIC_API_URL=https://your-api.execute-api.us-east-1.amazonaws.com/dev
pnpm build
```

But in CI/CD, **it's always automatic** - no manual steps required!

---

## Monitoring Deployments

### View Deployment Status
1. Go to **Actions** tab
2. Click on running workflow
3. View live logs

### View Terraform Plans
- Plans are added as comments on PRs
- Plan artifacts available for 5-7 days in workflow runs

### Deployment Issues
- Production deployments automatically create GitHub Issues
- Track: **Issues → Label: deployment**

---

## Security Best Practices

### ✅ Implemented
- OIDC authentication (no AWS credentials in secrets)
- Environment-based approvals for production
- Terraform state locking (prevents concurrent runs)
- Least-privilege IAM roles
- Plan before apply (review changes)

### 🔒 Additional Recommendations
1. Enable branch protection rules:
   - Require PR reviews before merge
   - Require status checks to pass
2. Rotate IAM role permissions quarterly
3. Monitor CloudWatch for unusual activity
4. Set up billing alerts for unexpected costs

---

## Troubleshooting

### "Error: No valid credential sources found"
- Check `AWS_ROLE_ARN` secret is set in environment
- Verify OIDC provider exists in AWS
- Ensure IAM role trust policy includes GitHub repo

### "Error: acquiring state lock"
- Another workflow is running
- Check DynamoDB locks table
- If stuck, manually release lock:
  ```bash
  terraform force-unlock <LOCK_ID>
  ```

### "Terraform Plan Failed"
- Check Terraform syntax: `terraform validate`
- Ensure `.tfvars` files exist for environment
- Review CloudWatch logs for API errors

### "Docker build failed"
- Check Dockerfile.lambda syntax
- Ensure backend/requirements.txt is valid
- Verify base image is accessible

---

## Cost Monitoring

### GitHub Actions Usage
- **Free tier**: 2,000 minutes/month
- **Granular deployments save time:**
  - Lambda only: ~2 minutes
  - Training container only: ~3 minutes
  - Full infrastructure: ~10 minutes
- **Estimate:** ~300-500 deployments/month free (with granular approach)
- **Previous approach:** ~100-200 deployments/month (full deploys only)

### AWS Costs
- Infrastructure: ~$7-10/month (as documented)
- No additional CI/CD costs
- Monitor: AWS Cost Explorer with Project tag filter

---

## Advanced: Multi-Region Deployment

To deploy to multiple regions:

1. Create region-specific tfvars:
   - `dev-us-east-1.tfvars`
   - `dev-eu-west-1.tfvars`

2. Modify workflow matrix:
   ```yaml
   strategy:
     matrix:
       region: [us-east-1, eu-west-1]
   ```

3. Update Terraform backend to use region-specific state keys

---

## Support

**Issues?** 
- Check workflow logs in Actions tab
- Review Terraform state: `terraform state list`
- CloudWatch Logs: `/aws/lambda/automl-lite-*`

**Questions?**
- See main README.md
- Review docs/PROJECT_REFERENCE.md
- Check AWS CloudWatch logs

---

**Last Updated:** 2025-11-28  
**Status:** ✅ CI/CD Ready
