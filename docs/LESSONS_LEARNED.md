# Lessons Learned

## Overview

This document captures key challenges, solutions, and architectural insights discovered during the development and enhancement of AWS AutoML Lite. These lessons are organized by category to help future developers avoid common pitfalls and understand critical design decisions.

---

## 1. Docker & Container Management

### Challenge: Lambda Package Size Limits
**Problem:** Initial attempts to deploy ML training code directly in Lambda failed due to the 250MB deployment package limit. ML dependencies (FLAML, scikit-learn, xgboost, lightgbm) totaled ~265MB.

**Solution:** Split architecture - Lambda handles API requests (5MB), AWS Batch runs training in Docker containers (no size limit).

**Key Insight:** Always check Lambda limits early. For ML workloads with heavy dependencies or long runtimes (>15min), use containers from the start.

### Challenge: Docker Build Timeouts
**Problem:** Building the training container timed out when downloading xgboost (297MB package).

```
ERROR: TimeoutError: The read operation timed out
Downloading xgboost-2.0.3-py3-none-manylinux2014_x86_64.whl (297.1 MB)
   36.9/297.1 MB when timeout occurred
```

**Solution:** Retry the build. Network issues are transient. Second attempt succeeded after ~11 minutes.

**Key Insight:** Large ML packages (xgboost, torch, tensorflow) require patience. Consider multi-stage builds or pre-built base images for faster iterations.

### Challenge: Lambda ZIP Excludes
**Problem:** Initially included the `training/` folder in Lambda deployment, causing package bloat.

**Solution:** Updated `lambda.tf` with explicit excludes:
```hcl
source {
  content_filename = "main.py"
  content = file("${path.module}/../../backend/api/main.py")
}

excludes = [
  "training",
  "**/__pycache__",
  "**/*.pyc",
  ".pytest_cache",
  "tests"
]
```

**Key Insight:** Always use `excludes` in Terraform `archive_file` resources to prevent accidental inclusion of unnecessary files.

---

## 2. Environment Variables & Configuration

### Challenge: Container Isolation
**Problem:** Training container tried to call the API for configuration, causing circular dependencies and network issues.

**Solution:** Pass ALL required configuration via environment variables in `batch_service.py`:
```python
container_overrides = {
    "environment": [
        {"name": "JOB_ID", "value": job_id},
        {"name": "DATASET_ID", "value": dataset_id},
        {"name": "TARGET_COLUMN", "value": target_column},
        {"name": "S3_BUCKET_DATASETS", "value": settings.s3_bucket_datasets},
        {"name": "DYNAMODB_JOBS_TABLE", "value": settings.dynamodb_jobs_table},
        # ... all other required vars
    ]
}
```

**Key Insight:** Treat containers as autonomous units. The cascade is:
```
Terraform (lambda.tf) → Lambda env vars → batch_service.py containerOverrides → train.py os.getenv()
```

**Critical Rule:** If you add a parameter to `train.py`, you MUST add it to `containerOverrides` in `batch_service.py`.

### Challenge: Missing Environment Variables
**Problem:** Training jobs silently failed because the container couldn't find required AWS resource names.

**Solution:** Added validation in `train.py`:
```python
required_vars = ["JOB_ID", "DATASET_ID", "TARGET_COLUMN", "S3_BUCKET_DATASETS"]
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    raise ValueError(f"Missing required environment variables: {missing}")
```

**Key Insight:** Fail fast with clear error messages. Silent failures waste debugging time.

---

## 3. Machine Learning & Feature Engineering

### Challenge: Low Model Accuracy
**Problem:** Initial training run showed 35.98% accuracy. Investigation revealed irrelevant columns (Order_ID, Customer_ID) were included in training.

**Root Cause:** No automatic detection of useless columns. The model tried to learn from random identifiers.

**Solution:** Integrated `feature-engine` library with custom ID pattern detection:
```python
ID_PATTERNS = [
    r'.*_?id$',           # order_id, user_id, customer_id
    r'^id_?.*',           # id_order, id_user
    r'.*_?key$',          # order_key, user_key
    r'.*_?uuid$',         # session_uuid
    r'.*_?code$',         # transaction_code
]

def detect_useless_columns_with_feature_engine(self, df):
    useless_cols = []
    reasons = {}
    
    # Step 1: feature-engine for constant columns
    drop_constant = DropConstantFeatures(tol=0.98)
    drop_constant.fit(df.drop(columns=[self.target_column], errors='ignore'))
    
    # Step 2: feature-engine for duplicate columns
    drop_duplicates = DropDuplicateFeatures()
    drop_duplicates.fit(df.drop(columns=[self.target_column], errors='ignore'))
    
    # Step 3: Custom ID detection (name patterns + sequential numbers)
    for col in df.columns:
        if self._is_id_column(col, df[col]):
            useless_cols.append(col)
            reasons[col] = "identifier/ID column"
    
    return useless_cols, reasons
```

**Result:** Successfully detected and excluded Order_ID and Customer_ID.

**Key Insight:** Always implement automatic feature filtering for:
- Identifier columns (IDs, UUIDs, codes)
- Constant/quasi-constant features (>98% same value)
- Duplicate features (perfect correlation)
- High cardinality categoricals (>50% unique values)

### Challenge: Dependency Version Conflicts
**Problem:** Adding `feature-engine==1.8.1` failed because it requires `pandas>=2.2.0`, but we had `pandas==2.1.4`.

**Solution:** Updated to `pandas==2.2.3` in `requirements.txt`.

**Key Insight:** When adding new ML libraries, check their dependency requirements. Use `pip install --dry-run` to preview conflicts before committing.

### Challenge: FLAML Multiclass Classification
**Problem:** FLAML crashed with multiclass classification using default settings.

**Solution:** Explicitly set metric to 'accuracy' for multiclass:
```python
if self.num_classes > 2:
    print(f"Detected multiclass classification ({self.num_classes} classes)")
    print("Using metric: accuracy")
    metric = 'accuracy'
```

**Key Insight:** FLAML's auto-detection isn't perfect. For multiclass problems, explicitly specify `metric='accuracy'`.

### Challenge: XGBoost 'best_iteration' Bug
**Problem:** XGBoost models crashed when extracting feature importance with error: `AttributeError: 'Booster' object has no attribute 'best_iteration'`.

**Solution:** Removed xgboost from estimator list:
```python
estimator_list = ['lgbm', 'rf', 'extra_tree']  # Removed 'xgb'
```

**Key Insight:** Test each estimator individually. Some FLAML-wrapped models have compatibility issues. Keep only stable estimators in production.

---

## 4. AWS Services & IAM

### Challenge: Batch Job Instant Failures
**Problem:** Batch jobs immediately transitioned to FAILED status without logs.

**Root Cause:** Container image wasn't pushed to ECR. Batch couldn't pull the image.

**Solution:** Always push after building:
```powershell
$EcrUrl = terraform output -raw ecr_repository_url
docker build -t automl-training:latest backend/training
docker tag automl-training:latest "$EcrUrl:latest"
docker push "$EcrUrl:latest"
```

**Key Insight:** Verify image exists before submitting jobs:
```powershell
aws ecr describe-images --repository-name automl-lite-dev-training --image-ids imageTag=latest
```

### Challenge: Jobs Stuck in RUNNING State
**Problem:** Batch jobs ran successfully but never updated their status in DynamoDB.

**Root Cause:** Batch task role lacked `dynamodb:UpdateItem` permission.

**Solution:** Added permissions in `iam.tf`:
```hcl
resource "aws_iam_role_policy" "batch_task_dynamodb" {
  name = "${var.project_name}-${var.environment}-batch-task-dynamodb"
  role = aws_iam_role.batch_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:PutItem"
        ]
        Resource = aws_dynamodb_table.training_jobs.arn
      }
    ]
  })
}
```

**Key Insight:** Always grant both Lambda AND Batch task roles the same DynamoDB permissions. The container writes directly to DynamoDB.

### Challenge: Dataset Visibility Issues
**Problem:** Locally created training jobs weren't visible in the frontend.

**Root Cause:** Frontend filtered by `user_id` from auth context. Local script used random UUIDs.

**Solution:** Changed local script to use `user_id="default"`:
```powershell
$jobItem = @{
    job_id = @{S = $jobId}
    user_id = @{S = "default"}  # Changed from random UUID
    dataset_id = @{S = $DatasetId}
    # ...
}
```

**Key Insight:** Understand authentication context. For local testing, use a known sentinel value like "default" that bypasses auth filters.

---

## 5. Frontend Deployment Architecture

### Challenge: App Runner Incompatibility with Next.js Standalone
**Problem:** Four consecutive App Runner deployments failed with CREATE_FAILED status after 20-minute timeouts each (~80 minutes wasted). Health checks consistently failed despite Next.js starting successfully in 120-170ms.

**Investigation:**
- CloudWatch logs showed: "✓ Next.js 16.0.4 Ready in 150ms" - app was healthy
- Service logs showed: "Health check failed on protocol `HTTP`[Path: '/'], [Port: '3000']"
- Created dedicated `/api/health` endpoint - no improvement
- Increased health check tolerances - no improvement
- Modified Dockerfile HOSTNAME binding - no improvement

**Root Cause:** App Runner's health check system is fundamentally incompatible with Next.js standalone initialization timing.

### Challenge: ECS Fargate Complexity
**Problem:** After App Runner failure, considered ECS Fargate + ALB but found it overly complex for this use case:
- Required ALB, Target Groups, Security Groups, ECS Cluster, Service, Task Definition
- Cost: ~$27/month (ALB alone is $16/month)
- 6+ Terraform files to manage
- Overkill for a simple frontend

### Solution: AWS Amplify Hosting
**Final Decision:** Migrated to AWS Amplify, which is purpose-built for Next.js applications.

**Why Amplify Works:**
1. **Native Next.js Support:** Amplify detects Next.js automatically and configures SSR correctly
2. **Monorepo Support:** Works with `AMPLIFY_MONOREPO_APP_ROOT=frontend`
3. **pnpm Support:** Requires `.npmrc` with `node-linker=hoisted` and pnpm install in preBuild
4. **Auto-Deploy:** Webhooks trigger builds on push to connected branches
5. **Terraform Integration:** Can be created via `aws_amplify_app` resource
6. **Cost-Effective:** ~$5-15/month depending on usage

**Implementation:**

1. **Terraform Configuration** (`amplify.tf`):
```hcl
resource "aws_amplify_app" "frontend" {
  count = local.amplify_enabled ? 1 : 0

  name       = "${var.project_name}-${var.environment}"
  repository = var.github_repository
  access_token = var.github_token
  platform = "WEB_COMPUTE"  # Required for Next.js 14+ SSR

  environment_variables = {
    NEXT_PUBLIC_API_URL       = aws_api_gateway_stage.main.invoke_url
    AMPLIFY_MONOREPO_APP_ROOT = "frontend"
  }

  build_spec = <<-EOT
    version: 1
    applications:
      - appRoot: frontend
        frontend:
          phases:
            preBuild:
              commands:
                - npm install -g pnpm
                - pnpm install --frozen-lockfile
            build:
              commands:
                - echo "NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL" >> .env.production
                - pnpm run build
          artifacts:
            baseDirectory: .next
            files:
              - '**/*'
          cache:
            paths:
              - node_modules/**/*
              - .next/cache/**/*
  EOT
}

resource "aws_amplify_branch" "main" {
  count       = local.amplify_enabled ? 1 : 0
  app_id      = aws_amplify_app.frontend[0].id
  branch_name = var.environment == "prod" ? "main" : "dev"
  framework   = "Next.js - SSR"
  stage       = var.environment == "prod" ? "PRODUCTION" : "DEVELOPMENT"
}
```

2. **Required Files:**
   - `frontend/.npmrc`: `node-linker=hoisted` (required for pnpm in Amplify)
   - `amplify.yml` (repo root): Build configuration for monorepo

3. **GitHub Token Secret:**
   - Create PAT with `repo` and `admin:repo_hook` scopes
   - Add as `GH_PAT_AMPLIFY` secret in GitHub repository
   - Pass to Terraform via `TF_VAR_github_token`

4. **IAM Permissions:**
   - Add `amplify:*` to GitHub Actions deploy role
   - Required actions: `amplify:CreateApp`, `amplify:CreateBranch`, `amplify:TagResource`

**Key Insight:** For Next.js 14+ applications:
- **WEB_COMPUTE platform** is required (not WEB)
- **baseDirectory must be `.next`** regardless of SSR or SSG
- **Don't use `output: 'export'`** if you need dynamic routes with SSR

### Architecture Evolution Summary

| Attempt | Solution | Result | Time Wasted |
|---------|----------|--------|-------------|
| 1 | App Runner | ❌ Health check failures | 80 minutes |
| 2 | ECS Fargate + ALB | ⚠️ Too complex, $27/month | Planning only |
| 3 | AWS Amplify | ✅ Works perfectly | Final solution |

**Cost Comparison:**

| Solution | Monthly Cost | Complexity |
|----------|-------------|------------|
| App Runner | $12-15 | Low (but doesn't work) |
| ECS Fargate + ALB | $27-40 | High |
| AWS Amplify | $5-15 | Low ✅ |

**Key Insight:** Always research the right tool for the framework. Amplify is AWS's answer to Vercel - purpose-built for Next.js. Don't fight against a service that wasn't designed for your use case.

---

## 6. Frontend & API Integration

### Challenge: CORS and API URL Configuration
**Problem:** Frontend couldn't connect to local API due to wrong endpoint.

**Solution:** Always get URL from Terraform:
```powershell
terraform output api_gateway_url
```

Set in `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=https://abc123.execute-api.us-east-1.amazonaws.com/dev
```

**Key Insight:** Never hardcode URLs. Use environment variables and Terraform outputs for all endpoints.

### Challenge: Dynamic Routes with useParams
**Problem:** TypeScript errors accessing route parameters in Next.js 14 App Router.

**Solution:** Cast params to string:
```typescript
const params = useParams();
const datasetId = params.datasetId as string;
```

**Key Insight:** Next.js App Router `useParams()` returns `string | string[]`. Always cast for single-param routes.

---

## 7. Local Development & Testing

### Challenge: Testing Without Full AWS Deployment
**Problem:** Needed to test training logic without deploying to AWS Batch (slow feedback loop).

**Solution:** Created `docker-compose.yml` for local testing against real AWS services:
```yaml
services:
  training:
    build:
      context: ./backend/training
    environment:
      - AWS_REGION=us-east-1
      - S3_BUCKET_DATASETS=automl-lite-dev-datasets-835503570883
      - DYNAMODB_JOBS_TABLE=automl-lite-dev-training-jobs
      # ... all required vars
    volumes:
      - ~/.aws:/root/.aws:ro  # Mount AWS credentials
```

**Key Insight:** Docker Compose with mounted AWS credentials enables fast iteration. Changes to `train.py` can be tested in seconds instead of minutes.

### Challenge: PowerShell Script Parameter Validation
**Problem:** Script didn't validate required parameters, leading to cryptic errors.

**Solution:** Added parameter validation:
```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$DatasetId,
    
    [Parameter(Mandatory=$true)]
    [string]$TargetColumn,
    
    [Parameter(Mandatory=$false)]
    [int]$TimeBudget = 120
)
```

**Key Insight:** Always use `[Parameter(Mandatory=$true)]` for required params in PowerShell scripts.

---

## 8. Architecture Decisions

### Why Split Backend and Training?
**Decision:** API in Lambda (FastAPI + Mangum), training in Batch containers.

**Rationale:**
- Lambda has 250MB package limit, 15min timeout
- Training needs 265MB+ dependencies, can run 2-60min
- API needs fast cold starts (<1s), training doesn't
- Containers allow GPU support in the future

**Trade-off:** More complex than monolithic, but necessary for ML workloads.

### Why Terraform Over CDK/CloudFormation?
**Decision:** Use Terraform HCL for infrastructure.

**Rationale:**
- State management out of the box
- Better readability than JSON/YAML
- Multi-cloud capability (future-proofing)
- Strong community and modules

**Trade-off:** Learning curve for AWS-native developers.

### Why FLAML Over AutoGluon?
**Decision:** Use FLAML for AutoML instead of AutoGluon.

**Rationale:**
- Lightweight (~20MB vs ~1GB+)
- Faster training on small datasets
- Better for serverless constraints
- Sufficient for MVP use cases

**Trade-off:** Less accurate than AutoGluon on complex problems.

---

## 9. Best Practices Summary

### Container Development
1. ✅ Always pass configuration via environment variables, never API calls
2. ✅ Build images with `--no-cache-dir` to reduce size
3. ✅ Use multi-stage builds for production (not yet implemented)
4. ✅ Validate required env vars at container startup
5. ✅ Push to ECR immediately after successful builds

### Machine Learning
1. ✅ Implement automatic feature filtering (IDs, constants, duplicates)
2. ✅ Use lightweight libraries when possible (feature-engine over AutoGluon)
3. ✅ Test each FLAML estimator individually before production
4. ✅ Explicitly set metrics for multiclass classification
5. ✅ Log detected useless columns for user transparency

### AWS & IAM
1. ✅ Grant DynamoDB write permissions to BOTH Lambda and Batch task roles
2. ✅ Use resource name prefixes (`${project}-${env}-${resource}`)
3. ✅ Verify ECR images before submitting Batch jobs
4. ✅ Use CloudWatch log groups for debugging
5. ✅ Output resource ARNs and URLs from Terraform

### Frontend Deployment
1. ✅ Research industry best practices BEFORE committing to a deployment service
2. ✅ Use AWS Amplify for Next.js SSR applications (purpose-built for Next.js)
3. ✅ Use S3 + CloudFront only for static exports (SSG)
4. ✅ Configure health check grace periods (60s+) for framework initialization
5. ✅ Set health check intervals to 30s, not aggressive 5-10s defaults
6. ✅ Use `/api/health` endpoint for lightweight health checks
7. ✅ Test deployments with staging environments before production
8. ✅ Keep old infrastructure running until new infrastructure is proven

### Development Workflow
1. ✅ Use docker-compose for local testing with real AWS services
2. ✅ Create helper scripts (run-training-local.ps1) for common tasks
3. ✅ Validate all parameters in scripts (PowerShell `[Parameter(Mandatory)]`)
4. ✅ Use sentinel values ("default") for local testing without auth
5. ✅ Test Lambda changes with `terraform apply -target=aws_lambda_function.api`

### Frontend
1. ✅ Centralize API calls in `lib/api.ts`
2. ✅ Use TypeScript interfaces matching backend Pydantic schemas
3. ✅ Cast `useParams()` results for type safety
4. ✅ Use `'use client'` only when necessary (forms, polling, uploads)
5. ✅ Get API URLs from environment variables, never hardcode

---

## 10. Common Pitfalls to Avoid

| ❌ Don't | ✅ Do |
|---------|------|
| Include `training/` in Lambda ZIP | Exclude in `lambda.tf` |
| Make API calls from training container | Pass all config via env vars |
| Forget to push ECR image | Push immediately after build |
| Use random UUIDs for local `user_id` | Use "default" for visibility |
| Hardcode bucket/table names | Use Terraform outputs |
| Skip parameter validation | Use `[Parameter(Mandatory)]` |
| Train on ID columns | Implement automatic detection |
| Use default FLAML metrics | Explicitly set for multiclass |
| Add training params without env vars | Update `containerOverrides` |
| Test only in AWS | Use docker-compose locally |
| Use App Runner for Next.js SSR | Use AWS Amplify for Next.js SSR |
| Start health checks immediately | Configure 60s grace period |
| Hardcode deployment architecture | Research industry best practices first |

---

## 11. Future Improvements

### Short Term
- [ ] Add support for regression problems (currently classification-only)
- [ ] Implement feature engineering (polynomial features, interactions)
- [ ] Add hyperparameter tuning for top models
- [ ] Support for time series datasets

### Medium Term
- [ ] GPU support for deep learning models
- [ ] Multi-stage Docker builds for faster iterations
- [ ] Automated feature selection with SHAP values
- [ ] Model monitoring and drift detection

### Long Term
- [ ] AutoGluon integration for complex problems
- [ ] Distributed training with Ray
- [ ] Feature store integration
- [ ] MLOps pipeline with CI/CD
- [ ] Multi-region deployment with failover

---

## 12. Conclusion

The most critical lessons learned:

1. **Environment Variable Cascade:** Understand the flow from Terraform → Lambda → Batch container
2. **Container Autonomy:** Treat containers as isolated units that never call the API
3. **Feature Engineering:** Always filter useless columns automatically
4. **IAM Permissions:** Both Lambda and Batch need DynamoDB access
5. **Local Testing:** Docker Compose with mounted credentials enables fast iteration
6. **Frontend Deployment Architecture:** Research industry best practices before committing - App Runner is NOT suitable for Next.js SSR, use AWS Amplify instead
7. **Health Check Configuration:** Configure 60s grace periods for frameworks with non-trivial startup times

These lessons transformed the development process from trial-and-error to predictable, efficient workflows. The frontend deployment challenges alone saved future iterations from 80+ minutes of debugging by identifying architectural mismatches early.

---

**Last Updated:** December 1, 2025  
**Contributors:** Development team working on AWS AutoML Lite  
**Related Docs:** [PROJECT_REFERENCE.md](./PROJECT_REFERENCE.md), [QUICKSTART.md](./QUICKSTART.md)
