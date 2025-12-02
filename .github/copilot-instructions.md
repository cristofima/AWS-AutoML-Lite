---
description: AWS AutoML Lite - AI Agent Development Guidelines
applyTo: "**"
---

# AWS AutoML Lite - Coding Guidelines

## Architecture Overview

Serverless AutoML platform with **split architecture** - understanding this is critical:

| Component | Technology | Deployment | Why |
|-----------|------------|------------|-----|
| Backend API | FastAPI + Mangum | Lambda ZIP (5MB) | Fast cold starts, simple deploys |
| Training | FLAML + scikit-learn | Docker on AWS Batch | 265MB deps, >15min runtime exceed Lambda limits |
| Frontend | Next.js 14 App Router | AWS Amplify | Native SSR support, monorepo-friendly |
| Infrastructure | Terraform | HCL in `infrastructure/terraform/` | State management, reproducibility |

**Key insight:** Containers are used ONLY for training because ML dependencies (265MB) exceed Lambda's 250MB limit and jobs can run 2-60min (Lambda max: 15min).

## Critical: Environment Variable Cascade

Training container is **autonomous** - receives ALL context via environment variables, never calls the API:

```
Terraform (lambda.tf) → Lambda env vars
    ↓
batch_service.py containerOverrides → Batch container
    ↓  
train.py reads via os.getenv() → Direct DynamoDB/S3 operations
```

**⚠️ If you add a parameter to `train.py`, you MUST add it to `containerOverrides` in `batch_service.py` or the job will silently fail.**

Required env vars in training container: `DATASET_ID`, `TARGET_COLUMN`, `JOB_ID`, `TIME_BUDGET`, `S3_BUCKET_DATASETS`, `S3_BUCKET_MODELS`, `S3_BUCKET_REPORTS`, `DYNAMODB_JOBS_TABLE`, `REGION`

## Key Data Flows

**Upload:** Frontend → `POST /upload` → presigned URL → direct S3 PUT → `POST /datasets/{id}/confirm` → analyze CSV → save to DynamoDB

**Training:** `POST /train` → create DynamoDB job → submit Batch job → container runs autonomously → updates DynamoDB directly → frontend polls `GET /jobs/{id}`

## Code Patterns

### Backend (Python)

**Configuration** - All AWS resource names via environment variables (`backend/api/utils/helpers.py`):
```python
class Settings(BaseSettings):
    s3_bucket_datasets: str = "automl-lite-dev-datasets-123"  # From lambda.tf
    dynamodb_jobs_table: str = "automl-lite-dev-training-jobs"
```
Never hardcode bucket/table names - they include AWS account ID suffixes.

**Layered architecture:**
- `routers/*.py` - Thin HTTP layer, validation only, delegates to services
- `services/*.py` - AWS SDK calls (boto3), business logic
- `models/schemas.py` - Pydantic schemas for all requests/responses

**Lambda handler** (`backend/api/main.py`): Just `handler = Mangum(app)` - write normal FastAPI.

### Training Container (Python)

**Feature preprocessing** (`backend/training/preprocessor.py`):
- Auto-detects ID columns via regex patterns and data characteristics
- Uses `feature-engine` for constant/duplicate column detection  
- Problem type: `<20 unique values or <5% unique ratio` = classification

**Model training** (`backend/training/model_trainer.py`):
- Uses FLAML with estimators: `['lgbm', 'rf', 'extra_tree']` (xgboost excluded due to bugs)
- For multiclass, explicitly use `metric='accuracy'`

### Frontend (TypeScript)

**API client** (`frontend/lib/api.ts`) - Centralized, typed interfaces matching backend Pydantic schemas. All API calls go through here.

**Client components** - Use `'use client'` ONLY for: file uploads, polling, form interactions. Server components by default.

**Dynamic routes** - Cast `useParams()` results: `const datasetId = params.datasetId as string;`

### Infrastructure (Terraform)

**Naming:** All resources use `${var.project_name}-${var.environment}` prefix (e.g., `automl-lite-dev-datasets`).

**Key files:**
- `lambda.tf` - Lambda env vars (source of truth for resource names)
- `iam.tf` - Permissions (Batch task role needs DynamoDB write access!)
- `outputs.tf` - API URL, ECR URL for deployment scripts
- `amplify.tf` - Frontend deployment with `WEB_COMPUTE` platform for SSR

## Development Commands

```powershell
# Backend (local) - http://localhost:8000/docs
cd backend; uvicorn api.main:app --reload

# Frontend (local) - Set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local
cd frontend; pnpm dev

# Test training container locally (requires uploaded dataset)
docker-compose --profile training run training

# Deploy Lambda only
cd infrastructure/terraform; terraform apply -target=aws_lambda_function.api

# Deploy training container
$EcrUrl = terraform output -raw ecr_repository_url
docker build -t automl-training:latest backend/training
docker tag automl-training:latest "$EcrUrl:latest"; docker push "$EcrUrl:latest"
```

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Lambda ZIP too large | Included `training/` folder | Check exclude patterns in CI build |
| Batch job instant FAILED | Container not in ECR | Push image, verify with `aws ecr describe-images` |
| Job stuck RUNNING | Missing DynamoDB permissions | Add `dynamodb:UpdateItem` to Batch task role in `iam.tf` |
| Frontend 404/CORS errors | Wrong API URL | Get URL from `terraform output api_gateway_url` |
| Training wrong problem type | Threshold mismatch | Check `<20 unique values = classification` in `preprocessor.py` |
| New train.py param ignored | Not in containerOverrides | Add to `batch_service.py` environment list |

## File Reference by Task

**Adding an API endpoint:** `routers/*.py` → `schemas.py` → `services/*.py` → `frontend/lib/api.ts`

**Modifying training:** `train.py` (orchestration) → `preprocessor.py` → `model_trainer.py` → `eda.py`

**Adding AWS resources:** Create `<service>.tf` → `variables.tf` → `outputs.tf` → `iam.tf` for permissions

## Debugging

- Lambda logs: `/aws/lambda/automl-lite-{env}-api`
- Batch logs: `/aws/batch/automl-lite-{env}-training`
- Local API test: Visit `http://localhost:8000/docs` (Swagger UI)
- Check training env vars: Compare `batch_service.py` containerOverrides with `train.py` os.getenv() calls

## Key Documentation

- `docs/LESSONS_LEARNED.md` - Critical debugging insights and architectural decisions
- `docs/QUICKSTART.md` - Complete deployment guide
- `infrastructure/terraform/ARCHITECTURE_DECISIONS.md` - Why Lambda + Batch split
