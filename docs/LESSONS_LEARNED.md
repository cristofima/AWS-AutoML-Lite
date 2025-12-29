# Lessons Learned

**Last updated:** December 24, 2025 (v1.1.0)

## 📑 Table of Contents

- [Overview](#overview)
- [1. Docker & Container Management](#1-docker--container-management)
- [2. Environment Variables & Configuration](#2-environment-variables--configuration)
- [3. Machine Learning & Feature Engineering](#3-machine-learning--feature-engineering)
- [4. AWS Services Integration](#4-aws-services-integration)
- [5. Frontend Deployment Architecture](#5-frontend-deployment-architecture)
- [6. Frontend & API Integration](#6-frontend--api-integration)
- [7. Caching & State Persistence](#7-caching--state-persistence)
- [8. Local Development & Testing](#8-local-development--testing)
- [9. Unit & Integration Testing](#9-unit--integration-testing)
- [10. Architecture Decisions](#10-architecture-decisions)
- [11. Best Practices Summary](#11-best-practices-summary)
- [12. Common Pitfalls](#12-common-pitfalls)
- [Key Takeaways](#key-takeaways)

---

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
Terraform (lambda.tf) → Lambda env vars → batch_service.py containerOverrides → main.py os.getenv()
```

**Critical Rule:** If you add a parameter to `main.py`, you MUST add it to `containerOverrides` in `batch_service.py`.

### Challenge: Missing Environment Variables
**Problem:** Training jobs silently failed because the container couldn't find required AWS resource names.

**Solution:** Added validation in `main.py`:
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

### Challenge: ReDoc CDN Breaking in FastAPI (v1.1.0)
**Problem:** The `/redoc` endpoint displayed a blank page with console errors. Users couldn't access API documentation through ReDoc.

**Root Cause:** FastAPI versions < 0.115.0 used a CDN URL for ReDoc that was deprecated:
```
# Old broken CDN (used by FastAPI < 0.115.0)
https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js
```

The `@next` tag pointed to unstable builds that eventually broke.

**Solution:** Upgraded FastAPI to >= 0.115.0 in `requirements.txt`:
```txt
fastapi>=0.115.0  # Fixes ReDoc CDN issue (uses stable redoc version)
```

FastAPI 0.115.0+ uses:
```
https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js
```

**Key Insight:** Always use stable tagged versions in CDN URLs. The `@next` tag is inherently unstable. When third-party documentation tools break, check the framework's CDN references first.

### Challenge: Cross-Platform Lock Files in CI/CD (v1.1.0)
**Problem:** CI/CD pipeline failed on Linux after generating `requirements.lock` on Windows.

```
ERROR: Could not find a version that satisfies the requirement pywin32==310
ERROR: Could not find a version that satisfies the requirement pyreadline3==3.5.4
```

**Root Cause:** Lock files generated on Windows included platform-specific packages:
- `pywin32` - Windows-only COM automation
- `pyreadline3` - Windows-only readline replacement

These packages don't exist on Linux PyPI and can't be installed.

**Solution:** Removed lock files entirely and kept only `requirements.txt` with flexible version ranges:
```txt
# Use flexible ranges instead of locked versions
fastapi>=0.115.0
boto3>=1.35.0
pandas>=2.2.0
```

**Alternative Considered:** Using `pip-tools` with `--resolver=backtracking` and platform markers, but this added unnecessary complexity for a simple project.

**Key Insight:** For cross-platform Python projects:
- ❌ Don't commit lock files generated on a specific OS
- ✅ Use version ranges (`>=`, `~=`) in requirements.txt
- ✅ If locks are needed, generate them in CI on the target platform (Linux)
- ✅ Use `pip-compile --generate-hashes` on a Linux runner for production locks

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

### Challenge: XGBoost 'best_iteration' Bug (RESOLVED)
**Problem:** XGBoost models crashed when extracting feature importance with error: `AttributeError: 'Booster' object has no attribute 'best_iteration'`.

**Root Cause:** XGBoost 2.0.0 (Sep 2023) introduced breaking change where `best_iteration` is only available when early stopping is used. FLAML was accessing this attribute unconditionally.

**Timeline:**
- Sep 12, 2023: Bug reported in FLAML issue #1217
- Sep 22, 2023: Fixed in FLAML PR #1219
- Oct 2, 2023: Fix released in FLAML v2.1.1
- Nov 30, 2025: Temporarily excluded XGBoost from production
- Dec 27, 2025: Re-enabled after confirming fix in FLAML >=2.1.0

**Solution:** XGBoost re-enabled in estimator list:
```python
estimator_list = ['lgbm', 'xgboost', 'rf', 'extra_tree']  # XGBoost restored
```

**Key Insight:** Stay updated with library changelogs. Breaking changes in major version bumps (2.0) may affect wrapper libraries like FLAML. Verify compatibility before upgrading dependencies.

### Challenge: Understanding FLAML's Early Stopping Mechanism
**Problem:** Training jobs with large datasets (50k rows, 20 columns) ran for full time budget (20 minutes) even when accuracy plateaued early (e.g., 93.1% at 5 minutes = 20 minutes), wasting compute time and AWS Batch costs.

**Investigation:** Explored FLAML's `early_stop=True` parameter to enable convergence detection. Needed to understand:
1. How does FLAML detect convergence?
2. What parameters control the patience/tolerance?
3. Can we configure when to stop?

**Findings from FLAML Documentation:**

**How `early_stop` works internally:**
- Uses CFO (Cost-Frugal Optimization) or BlendSearch algorithms with built-in convergence detection
- Monitors if the primary metric (accuracy, r2, etc.) has stopped improving
- Each estimator (lgbm, xgb, rf, extra_tree) runs independent local search
- Stops when ALL estimators have converged AND `total_time > 10x time_to_find_best_model`

**What you CAN'T configure:**
- ❌ No `patience` parameter (iterations without improvement)
- ❌ No `min_delta` parameter (minimum improvement threshold)
- ❌ No `eval_frequency` parameter (how often to check convergence)
- ❌ No granular control over convergence criteria

**What you CAN control:**
```python
automl.fit(
    time_budget=1200,        # Maximum total time
    max_iter=None,           # Maximum configurations to try
    early_stop=True,         # Enable convergence detection (boolean only)
    eval_method='holdout',   # 'holdout' or 'cv'
    split_ratio=0.2,         # Train/validation split
)
```

**Solution Implemented:**
```python
automl.fit(
    # ... other params ...
    early_stop=True,   # Enable automatic convergence detection
    retrain_full=True  # Retrain best model on full data after search
)
```

**Expected Behavior:**
- FLAML will automatically detect when hyperparameter search has converged
- Stops early if: (1) all local searches converged + (2) time > 10x time to find best model
- Example: If best model found at 1 minute, stops after ~10 minutes (not full 20 min budget)
- Reduces wasted compute time on datasets that plateau early

**Limitations:**
- Early stopping logic is internal to FLAML (black box)
- Cannot fine-tune sensitivity of convergence detection
- Relies on FLAML's research-backed heuristics from Microsoft Research
- If convergence detection is too aggressive, consider increasing `time_budget` or using `max_iter` instead

**Key Insight:** FLAML's `early_stop` is a smart but opaque feature. It works well for most cases but offers limited configurability. Trust the algorithm unless you have specific domain knowledge suggesting otherwise. Monitor actual training times vs time budget to validate effectiveness.

### Challenge: Problem Type Detection Logic Flaw (v1.1.0)
**Problem:** Training failed with "The least populated class in y has only 1 member" error when training on `Performance Index` column (continuous float values like 35.5, 40.2).

**Root Cause:** The problem type detection logic used `OR` instead of `AND`:
```python
# ❌ WRONG - OR causes regression targets to be classified as classification
if unique_ratio < 0.05 or y.nunique() < 20:
    return 'classification'
```

With 10,000 rows and ~91 unique values, `unique_ratio = 0.91%` (< 5%), triggering classification even though values were continuous floats.

**Solution:** Improved heuristics with multiple conditions:
```python
# ✅ CORRECT - Check if values are integer-like AND have low cardinality
try:
    is_integer_like = (y.dropna() == y.dropna().astype(int)).all()
except (ValueError, TypeError):
    is_integer_like = False

# Classification only if integer-like with few classes
if is_integer_like and n_unique <= 10:
    return 'classification'

# Or if truly low cardinality WITH low ratio (AND not OR)
if n_unique < 20 and unique_ratio < 0.05:
    return 'classification'

return 'regression'  # Default for continuous values
```

**Key Insight:** Problem type detection must consider:
1. **Data type**: Floats with decimals = regression
2. **Value distribution**: Integer-like (0, 1, 2) = classification candidates
3. **Both conditions**: Low unique count AND low ratio = classification

### Challenge: Understanding FLAML's `retrain_full` Parameter

**Problem:** After hyperparameter search with holdout validation, the model was trained on only 90% of the data (if `split_ratio=0.1`). The validation set (10%) was never used for final training, potentially wasting valuable training data and reducing final model accuracy.

**Investigation:** 
- Searched FLAML documentation for `retrain_full` parameter
- Found in **Resampling Strategy** section of Task-Oriented AutoML docs
- Compared with industry best practices for train/validation/test splits

**What `retrain_full` Does:**

By default, FLAML follows this workflow:
1. **Split data** → 90% training + 10% validation (holdout)
2. **Search phase** → Test different hyperparameters on training set, evaluate on validation set
3. **Find best config** → Identifies the hyperparameter combination with lowest validation loss
4. **Final training** → What happens here depends on `retrain_full`:

| `retrain_full` Value | Behavior | Training Data Size |
|----------------------|----------|-------------------|
| `False` (default) | Uses best config, **no retraining** | 90% (original training set) |
| `True` | **Retrains** best config on **full data** (training + validation) | 100% |
| `"budget"` | Retrains within remaining time budget | 100% |

**Benefits of `retrain_full=True`:**

1. **More training data** → Better accuracy (especially for smaller datasets)
   - 10,000 rows: 1,000 more samples for training
   - 100,000 rows: 10,000 more samples
   
2. **Validation set not wasted** → After finding best hyperparameters, validation data contributes to final model

3. **Industry standard practice** → Common pattern in AutoML frameworks:
   - Azure ML AutoML uses this approach
   - Google Cloud AutoML retrains on full data
   - AWS SageMaker Autopilot does the same

4. **No overfitting risk** → Hyperparameters were chosen on validation set before retraining, so no information leakage

**Tradeoff:**
- **Cost**: Additional training time at the end (typically 1-2 more training runs)
- **Benefit**: Improved accuracy on test/production data

**Our Configuration:**
```python
automl.fit(
    X_train=X_train,
    y_train=y_train,
    task=task,
    metric=metric,
    time_budget=time_budget,
    early_stop=True,     # Stop hyperparameter search early if converged
    retrain_full=True    # Retrain best model on full data (training + validation)
)
```

**Expected Behavior:**
- If `time_budget=300` seconds and best config found at 180s:
  - Remaining budget: 120s
  - Uses remaining time to retrain on 100% of data
  - If retraining takes 30s, saves 90s (doesn't waste budget)
  - If `retrain_full="budget"`, caps retraining at remaining 120s

**Key Insights:**
- `retrain_full=True` is recommended for production models
- Small computational cost (<5% extra time typically)
- Significant accuracy improvements on small-medium datasets (5-15% improvement reported in literature)
- No accuracy improvement on very large datasets (>1M rows) where 10% holdout is still massive
- Combines well with `early_stop=True` to optimize both search time and final model quality

**References:**
- FLAML Docs: [Resampling Strategy](https://microsoft.github.io/FLAML/docs/Use-Cases/Task-Oriented-AutoML/#resampling-strategy)
- Microsoft Fabric: [Hyperparameter Tuning Guide](https://learn.microsoft.com/fabric/data-science/how-to-tune-lightgbm-flaml#compare-the-results)

---

### Challenge: Duplicated Code Across Training Modules (v1.1.0)
**Problem:** The `detect_problem_type()` function was duplicated in both `preprocessor.py` and `eda.py`, violating DRY principle. When fixing one, the other was forgotten, causing inconsistent behavior.

**Evidence:** EDA report showed "CLASSIFICATION" while training correctly detected "REGRESSION" after partial fix.

**Solution:** Created centralized `utils.py` module:
```python
# backend/training/utils.py
def detect_problem_type(y: pd.Series) -> str:
    """Single source of truth for problem type detection."""
    ...

def is_id_column(col_name: str, series: pd.Series) -> bool:
    """Detect identifier columns."""
    ...

# Usage in both files:
from .utils import detect_problem_type, is_id_column
```

**Key Insight:** 
- **DRY principle is critical for ML pipelines** - detection logic must be consistent
- Create utility modules early, not after bugs surface
- Shared logic should live in one place with imports

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
  platform = "WEB_COMPUTE"  # Required for Next.js 16+ SSR

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

**Key Insight:** For Next.js 16+ applications:
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

### Challenge: CORS with Externally-Created Amplify Apps (v1.1.0)
**Problem:** S3 CORS blocked uploads from Amplify frontend with error:
```
Access to XMLHttpRequest blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header
```

**Root Cause:** Amplify app was created manually in AWS Console, not by Terraform. The Terraform CORS logic depends on `amplify_enabled = true`, which requires `github_repository` AND `github_token` variables. Without these, CORS only included `localhost:3000`.

**Solution:** Two options:
1. Add `github_repository` to tfvars (token comes from CI/CD via `TF_VAR_github_token`)
2. Add explicit `cors_allowed_origins` to tfvars with Amplify domain

```hcl
# Option 1: Let Terraform manage Amplify (recommended)
github_repository = "https://github.com/owner/repo"

# Option 2: Manual CORS for external Amplify
cors_allowed_origins = [
  "https://branch.xxx.amplifyapp.com",
  "http://localhost:3000"
]
```

**Key Insight:** When Amplify is created outside Terraform, you must manually configure CORS. The `cors_origins` local should **combine** sources (not override) to allow both manual and automatic origins.

### Challenge: Terraform Destroyed Amplify App Unexpectedly (v1.1.0)
**Problem:** Running `terraform apply` locally destroyed the existing Amplify app, breaking the production frontend.

**Root Cause:** 
- Amplify resources use `count = local.amplify_enabled ? 1 : 0`
- `amplify_enabled` requires both `github_repository` AND `github_token`
- Local execution didn't have `TF_VAR_github_token` set
- Terraform saw count change from 1 to 0 → destroyed the resource

**Solution:** 
1. Always set `github_repository` in tfvars files
2. CI/CD pipeline passes `TF_VAR_github_token` from secrets
3. For local Terraform, either set the env var or use `-target` to avoid Amplify resources

**Key Insight:** Resources with conditional `count` are dangerous when variables are missing. Consider using `lifecycle { prevent_destroy = true }` for critical resources.

### Challenge: SSE Doesn't Work on AWS Amplify (v1.1.0)
**Problem:** Server-Sent Events endpoint returned 500 error when accessed from Amplify:
```
GET https://xxx.amplifyapp.com/api/jobs/xxx/stream/ 500 (Internal Server Error)
SSE failed, falling back to polling
```

**Root Cause:** AWS Amplify uses Lambda@Edge for Next.js SSR, which has:
- 30 second timeout (configurable up to 30s max)
- Stateless invocations - can't maintain long-lived connections
- Each request = new Lambda invocation

SSE requires the server to keep the connection open indefinitely, which is fundamentally incompatible with Lambda's execution model.

**Solution:** Removed SSE implementation entirely and use polling directly. For training jobs that take 5-15 minutes, a 5-second polling delay is imperceptible to users. Polling is:
- Simple and reliable
- Works on all serverless platforms
- No complex connection management

**Key Insight:** This is the fundamental **trade-off of serverless**: you sacrifice long-lived connections for scalability and cost efficiency. Don't over-engineer with SSE/WebSocket when polling works perfectly for long-running operations.

### Challenge: Python Relative Imports in Container (v1.1.0)
**Problem:** Training container failed immediately with:
```
ImportError: attempted relative import with no known parent package
```

**Root Cause:** Files used relative imports (`from .utils import ...`) but were executed directly, not as part of a package.

**Solution (v1.1.1):** Restructured training module into proper Python package with absolute imports:
```python
# Package structure:
# training/
# ├── __init__.py
# ├── main.py
# ├── core/preprocessor.py
# ├── reports/eda.py
# └── utils/detection.py

# Absolute imports work with `python -m training.main`
from training.utils.detection import detect_problem_type, is_id_column
from training.core.preprocessor import AutoPreprocessor
```

Dockerfile updated:
```dockerfile
COPY . ./training/
ENV PYTHONPATH=/app
CMD ["python", "-m", "training.main"]
```

**Key Insight:** For modular Python packages in Docker, use `python -m package.module` syntax with proper `__init__.py` files and absolute imports.

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
**Problem:** TypeScript errors accessing route parameters in Next.js 16 App Router.

**Solution:** Cast params to string:
```typescript
const params = useParams();
const datasetId = params.datasetId as string;
```

**Key Insight:** Next.js App Router `useParams()` returns `string | string[]`. Always cast for single-param routes.

---


### Challenge: Background Threads in Lambda
**Problem:** The `S3Service` initially used a background daemon thread to clean up expired presigned URLs from the in-memory cache.
**Root Cause:** In AWS Lambda, the execution environment (and all threads) is frozen immediately after the handler returns. Background threads do not run typically, and when the environment unfreezes, behavior can be unpredictable.
**Solution:** Switched to **lazy cleanup**. The service now scans for and removes expired items during cache access (read/write operations) instead of relying on a background process.
**Key Insight:** Avoid background threads in Serverless functions. Use lazy evaluation, TTLs (like DynamoDB TTL), or scheduled events (EventBridge) for cleanup tasks.

---

## 7. Caching & State Persistence (v1.1.1)

### Challenge: Stale Data After Deletion
**Problem:** Users could still view job details after deleting a job because the browser served the previous `200 OK` response from its disk cache.

**Solution:**
1. **Backend:** `DELETE` endpoint must return `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` headers.
2. **Frontend:** `fetch` requests for details must use `cache: 'no-cache'` to force ETag validation.

**Key Insight:** Deleting a resource on the server doesn't automatically clear the browser's cache of that resource's *URL*. You must explicitly tell the browser to stop using the cached version using headers AND client-side fetch options.

### Challenge: DynamoDB Empty Strings
**Problem:** Clearing "notes" field failed because DynamoDB does not allow empty strings `""`. attempting to set `notes = ""` resulted in a validation error.

**Solution:**
1. **Frontend:** Send explicit `""` (empty string) instead of `null` or `undefined` to signal clearing.
2. **Backend:** Check for empty string and use DynamoDB `REMOVE` operation instead of `SET`.

**Key Insight:** DynamoDB treats `""` as invalid. Always map empty text inputs to attribute removal or a sentinel value (like "EMPTY") if the attribute must exist.

---

## 8. Local Development & Testing

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

**Key Insight:** Docker Compose with mounted AWS credentials enables fast iteration. Changes to `main.py` can be tested in seconds instead of minutes.

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

## 8. Unit & Integration Testing

### Challenge: FastAPI TestClient HTTP Version Incompatibility
**Problem:** Tests failed with `TypeError: Client.__init__() got an unexpected keyword argument 'app'` when using Starlette TestClient with httpx 0.28.0.

**Root Cause:** Starlette 0.35.1 (bundled with FastAPI 0.109.0) is incompatible with httpx 0.28.0. The internal transport API changed between versions.

**Solution:** Pinned httpx to compatible version in `requirements-dev.txt`:
```txt
httpx==0.27.2  # Last version compatible with Starlette 0.35.1
```

**Key Insight:** When adding testing libraries, check compatibility with existing framework versions. FastAPI version dictates Starlette version, which constrains httpx version.

### Challenge: Low Initial Test Coverage
**Problem:** Initial API coverage was 39% with routers at 18% and services at 25%. Tests mocked AWS services but didn't execute router/service code paths.

**Root Cause:** Unit tests mocked service methods at a high level, bypassing actual router logic. For example:
```python
# ❌ This mocks too high - router code isn't executed
@patch('api.services.dynamo_service.DynamoDBService.get_job')
def test_get_job(self, mock_get):
    mock_get.return_value = {...}
    response = client.get("/jobs/123")
```

**Solution:** Added comprehensive endpoint tests that exercise full router logic, and integration tests using `moto` for AWS service mocking:
```python
# ✅ Endpoint tests - exercise router logic with targeted mocks
from api.routers import models
@patch.object(models.dynamodb_service, 'get_job')
def test_get_job(self, mock_get):
    mock_get.return_value = {...}
    response = client.get("/jobs/123")  # Router code executes

# ✅ Integration tests - real service code with moto
from moto import mock_aws
@mock_aws
def test_s3_presigned_url_generation(self):
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    
    service = S3Service()
    url = service.generate_presigned_upload_url('test-bucket', 'file.csv')
    assert 'X-Amz-Signature' in url
```

**Result:** Coverage improved from 39% to 69%.

**Key Insight:** For FastAPI testing:
- **Endpoint tests** → Mock at the service instance level (`patch.object(router.service, 'method')`)
- **Integration tests** → Use `moto` to mock AWS services, execute real service code
- **Unit tests** → Pure logic with no external dependencies

### Challenge: Mocking Service Dependencies in Routers
**Problem:** Routers import services at module level. Patching the wrong module path causes mocks to not apply.

**Evidence:**
```python
# ❌ WRONG - patches the service module, not the router's reference
@patch('api.services.dynamo_service.DynamoDBService.get_job')

# Router imports like this:
# from api.services.dynamo_service import dynamodb_service
# dynamodb_service = DynamoDBService()  # Instance created at import time
```

**Solution:** Import the router module and patch the service instance:
```python
from api.routers import models  # Router that uses dynamodb_service

@patch.object(models.dynamodb_service, 'get_job')
def test_get_job_success(self, mock_get):
    mock_get.return_value = {...}
    response = client.get("/jobs/123")
```

**Key Insight:** In Python, you must patch where the object is **used**, not where it's **defined**. For singleton services instantiated at import time, use `patch.object()` on the router's imported instance.

### Challenge: Pydantic Validation vs Endpoint Validation
**Problem:** Test expected HTTP 400 for invalid tags (>10 items), but received HTTP 422.

**Root Cause:** Pydantic validates request schemas **before** the endpoint code runs. Schema violations return 422 (Unprocessable Entity), not 400 (Bad Request).

```python
class UpdateJobRequest(BaseModel):
    tags: Optional[List[str]] = Field(None, max_length=10)  # Pydantic validates this
```

**Solution:** Updated tests to expect correct status codes:
```python
def test_update_job_too_many_tags(self):
    response = client.patch(
        "/jobs/123",
        json={"tags": ["tag1"]*11}  # 11 tags exceeds max_length=10
    )
    assert response.status_code == 422  # Pydantic validation, not 400
```

**Key Insight:** 
- **422** = Pydantic schema validation errors (type mismatch, constraints)
- **400** = Endpoint-level business logic errors (raised manually)
- **404** = Resource not found (raised in router after lookup)

### Challenge: DynamoDB Decimal Conversion in Tests
**Problem:** Moto creates real DynamoDB tables that store floats as `Decimal`. Tests failed when comparing returned values.

**Solution:** Added decimal conversion utility and used it in service code:
```python
def convert_decimals(obj: Any) -> Any:
    """Recursively convert Decimal to int/float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    return obj
```

**Key Insight:** DynamoDB returns `Decimal` types for numbers. Always convert before JSON serialization or comparison in tests.

### Challenge: Test Organization for CI/CD
**Problem:** Needed separate test runs for API and Training modules with independent coverage reports.

**Solution:** Organized tests into separate directories with component-specific pipelines:
```
backend/tests/
├── api/                    # API endpoint & service tests
│   ├── test_endpoints.py   # 39 endpoint tests
│   ├── test_schemas.py     # 23 schema tests
│   ├── test_services_integration.py  # 21 integration tests
│   └── ...
└── training/               # Training module tests
    ├── unit/               # 93 unit tests
    │   ├── test_preprocessor.py
    │   ├── test_utils.py
    │   └── ...
    └── integration/        # Training integration tests
```

**CI/CD Integration:**
```yaml
# deploy-lambda-api.yml - runs API tests only
pytest tests/api --cov=api --cov-report=xml

# deploy-training-container.yml - runs training tests only
pytest tests/training --cov=training --cov-report=xml
```

**Key Insight:** Separate test directories enable:
- **Faster CI** - only run relevant tests per component
- **Independent coverage** - track coverage per module
- **Clear ownership** - developers know which tests to update

### Final Test Coverage Summary

| Component | Tests | Coverage | CI Pipeline |
|-----------|-------|----------|-------------|
| API | 104 | 69% | `deploy-lambda-api.yml` |
| Training | 159 | 53%+ | `deploy-training-container.yml` |
| **Total** | **263** | - | - |

---

## 9. Architecture Decisions

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

### Why Polling Instead of WebSocket for Job Updates? (v1.1.0)
**Decision:** Use polling (5-second interval) instead of WebSocket API Gateway for real-time training updates.

**Context:**
- SSE (Server-Sent Events) failed on Amplify due to Lambda@Edge 30s timeout
- Considered implementing WebSocket API Gateway as alternative
- Training jobs run 5-15 minutes typically

**Analysis:**
| Factor | Polling | WebSocket |
|--------|---------|-----------|
| Implementation time | 0 hours (done) | 5-6 hours |
| Latency | 5 seconds max | Real-time |
| Infrastructure | None additional | API Gateway, Lambda, DynamoDB |
| Maintenance | Simple | Connection management |
| Cost | Low (periodic requests) | Low but more complex |

**Decision Rationale (KISS & YAGNI):**
- For 10-minute training jobs, 5-second delay is **imperceptible** to users
- WebSocket adds **significant complexity** (connection management, reconnection logic, Lambda handlers)
- No user-facing benefit for multi-minute jobs
- Polling is **battle-tested** and works everywhere (including Amplify)

**Key Insight:** Don't over-engineer for perceived technical elegance. The right solution is the simplest one that solves the user's problem. Real-time is overkill when the underlying operation takes minutes.

---

## 10. Best Practices Summary

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

## 11. Common Pitfalls to Avoid

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
| Use relative imports in container | Use absolute imports (`from utils import`) |
| Run `terraform apply` without all vars | Ensure `github_token` env var for Amplify |
| Expect SSE to work on Amplify | Use polling for serverless real-time |
| Build WebSocket for multi-minute ops | Use polling (KISS principle) |

---

## 12. Future Improvements

### Short Term
- [ ] Implement feature engineering (polynomial features, interactions)
- [ ] Add hyperparameter tuning UI for FLAML settings
- [ ] Support for time series datasets
- [ ] Batch predictions on validation datasets (v1.2.0 planned)

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

### ✅ Completed (v1.1.0)
- [x] ONNX model export for cross-platform deployment
- [x] Serverless model inference (Lambda + ONNX Runtime)
- [x] Model comparison dashboard
- [x] Dark mode support
- [x] Improved problem type detection (regression vs classification)

---

## 13. Conclusion

The most critical lessons learned:

1. **Environment Variable Cascade:** Understand the flow from Terraform → Lambda → Batch container
2. **Container Autonomy:** Treat containers as isolated units that never call the API
3. **Feature Engineering:** Always filter useless columns automatically
4. **IAM Permissions:** Both Lambda and Batch need DynamoDB access
5. **Local Testing:** Docker Compose with mounted credentials enables fast iteration
6. **Frontend Deployment Architecture:** Research industry best practices before committing - App Runner is NOT suitable for Next.js SSR, use AWS Amplify instead
7. **Health Check Configuration:** Configure 60s grace periods for frameworks with non-trivial startup times
8. **Problem Type Detection (v1.1.0):** Use AND not OR for classification heuristics - float values with decimals should be regression
9. **DRY Principle (v1.1.0):** Shared ML logic must live in a single utility module to prevent inconsistencies
10. **SSE Limitations (v1.1.0):** Amplify uses Lambda@Edge with 30s timeout - SSE won't work; use polling
11. **Terraform State Management (v1.1.0):** Resources with conditional `count` can be destroyed when variables are missing
12. **KISS over Over-Engineering (v1.1.0):** For multi-minute operations, polling is simpler and equally effective as WebSocket
13. **Testing Strategy (v1.1.0):** Use `patch.object()` for router service mocks, `moto` for AWS integration tests, and separate test directories per component for CI/CD efficiency

These lessons transformed the development process from trial-and-error to predictable, efficient workflows. The frontend deployment challenges alone saved future iterations from 80+ minutes of debugging by identifying architectural mismatches early.

---

**Last Updated:** December 24, 2025 (v1.1.0)  
