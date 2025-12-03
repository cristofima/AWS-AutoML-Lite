---
description: AWS AutoML Lite - AI Agent Development Guidelines
applyTo: "**"
---

# AWS AutoML Lite - Coding Guidelines

## Architecture Overview

Serverless AutoML platform with **split architecture**:

| Component | Technology | Deployment | Why |
|-----------|------------|------------|-----|
| Backend API | FastAPI + Mangum | Lambda ZIP (5MB) | Fast cold starts, simple deploys |
| Training | FLAML + scikit-learn | Docker on AWS Batch | 265MB deps, >15min runtime exceed Lambda limits |
| Frontend | Next.js 16 App Router | AWS Amplify | SSR support, auto-deploy on push |
| Infrastructure | Terraform | `infrastructure/terraform/` | State management |

**Key insight:** Containers ONLY for training - ML deps (265MB) exceed Lambda's 250MB limit.

## Critical: Environment Variable Cascade

Training container is **autonomous** - receives ALL context via environment variables, never calls the API:

```
lambda.tf → Lambda env vars → batch_service.py containerOverrides → train.py os.getenv()
```

**⚠️ Adding a param to `train.py`? You MUST also add it to `containerOverrides` in `batch_service.py`.**

Required env vars in training container: `DATASET_ID`, `TARGET_COLUMN`, `JOB_ID`, `TIME_BUDGET`, `S3_BUCKET_DATASETS`, `S3_BUCKET_MODELS`, `S3_BUCKET_REPORTS`, `DYNAMODB_JOBS_TABLE`, `REGION`

## Key Data Flows

**Upload:** Frontend → `POST /upload` → presigned URL → S3 PUT → `POST /datasets/{id}/confirm` → DynamoDB

**Training:** `POST /train` → DynamoDB job → Batch job → container writes directly to DynamoDB → frontend polls `GET /jobs/{id}`

## Code Patterns

### Backend (Python)

**Configuration** (`backend/api/utils/helpers.py`): All AWS resource names via `Settings(BaseSettings)`. Never hardcode bucket/table names - they include AWS account ID suffixes.

**Layered architecture:**
- `routers/*.py` - Thin HTTP layer, delegates to services
- `services/*.py` - AWS SDK calls (boto3), business logic
- `models/schemas.py` - Pydantic schemas for all requests/responses

**Lambda handler**: `handler = Mangum(app)` in `main.py` - write normal FastAPI.

### Training Container (Python)

Located in `backend/training/`, runs as Docker container in AWS Batch:

- **Entry point** (`train.py`): Orchestrates 7-step pipeline (download → EDA → preprocess → train → reports → save → update status)
- **Preprocessing** (`preprocessor.py`): Auto-detects ID columns using regex patterns, uses `feature-engine` for constant/duplicate detection
- **Problem type detection**: `<20 unique values OR <5% unique ratio` = classification
- **Model training** (`model_trainer.py`): FLAML with `['lgbm', 'rf', 'extra_tree']` - xgboost excluded due to `best_iteration` bugs
- **Multiclass**: Explicitly set `metric='accuracy'` (FLAML's auto-detection unreliable)
- **Reports**: Generates both EDA (`sweetviz`) and training reports with feature importance charts

### Frontend (TypeScript)

- **API client** (`frontend/lib/api.ts`): Centralized, typed interfaces matching backend Pydantic schemas
- **Client components**: Use `'use client'` ONLY for file uploads, polling, forms - server components by default
- **Dynamic routes**: Cast `useParams()` results: `const datasetId = params.datasetId as string`

### Infrastructure (Terraform)

- **Naming**: All resources use `${var.project_name}-${var.environment}` prefix
- **Key files**: `lambda.tf` (env vars source of truth), `iam.tf` (permissions), `outputs.tf` (URLs), `amplify.tf` (frontend)
- **IAM**: Batch task role needs DynamoDB write access - both Lambda AND Batch write to DynamoDB

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

# Generate architecture diagrams (requires: pip install diagrams + Graphviz)
python scripts/generate_architecture_diagram.py
```

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Batch job instant FAILED | Container not in ECR | `docker push` + verify with `aws ecr describe-images` |
| Job stuck RUNNING | Missing DynamoDB perms | Add `dynamodb:UpdateItem` to Batch task role in `iam.tf` |
| New train.py param ignored | Not in containerOverrides | Add to `batch_service.py` environment list |
| Frontend CORS errors | Wrong API URL | Get from `terraform output api_gateway_url` |
| Low model accuracy | ID columns in training | Check `preprocessor.py` ID detection patterns |
| DynamoDB Decimal errors | Floats in metrics dict | Convert to `Decimal(str(v))` before saving |

## File Reference by Task

**Adding an API endpoint:** `routers/*.py` → `schemas.py` → `services/*.py` → `frontend/lib/api.ts`

**Modifying training:** `train.py` → `preprocessor.py` → `model_trainer.py` → **ALSO update** `batch_service.py` containerOverrides

**Adding AWS resources:** `<service>.tf` → `variables.tf` → `outputs.tf` → `iam.tf` for permissions

## Schema Sync Pattern

Backend Pydantic and Frontend TypeScript schemas must match. When adding fields:
1. `backend/api/models/schemas.py` - Add to Pydantic model (e.g., `JobResponse`)
2. `frontend/lib/api.ts` - Add to TypeScript interface (e.g., `JobDetails`)
3. Key pairs: `JobResponse` ↔ `JobDetails`, `DatasetMetadata` ↔ `DatasetMetadata`, `TrainResponse` ↔ `TrainResponse`

## Debugging

- Lambda logs: `/aws/lambda/automl-lite-{env}-api`
- Batch logs: `/aws/batch/automl-lite-{env}-training`
- Local API: `http://localhost:8000/docs` (Swagger UI)
- Env var mismatch: Compare `batch_service.py` containerOverrides with `train.py` os.getenv()
- Training issues: Check `dropped_columns` in preprocessing_info for filtered features

## Utility Scripts

| Script | Purpose |
|--------|---------|
| `scripts/run-training-local.py` | Test training in local Docker container |
| `scripts/predict.py` | Make predictions with trained models (Docker) |
| `scripts/generate_architecture_diagram.py` | Generate AWS architecture diagrams |

## CI/CD Workflows (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `deploy-lambda-api.yml` | Push to main/dev | Deploy FastAPI to Lambda |
| `deploy-training-container.yml` | Push to main/dev | Build & push training image to ECR |
| `deploy-infrastructure.yml` | Manual | Terraform apply |
| `ci-terraform.yml` | PR | Terraform validate & plan |

## Key Docs

- `docs/LESSONS_LEARNED.md` - Critical debugging insights (read this first for troubleshooting)
- `docs/QUICKSTART.md` - Deployment guide
- `.github/SETUP_CICD.md` - CI/CD with GitHub Actions
- `infrastructure/terraform/ARCHITECTURE_DECISIONS.md` - Why Lambda + Batch split
- `.github/git-commit-messages-instructions.md` - Commit message conventions
