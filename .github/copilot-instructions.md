---
description: AWS AutoML Lite - AI Agent Development Guidelines
applyTo: "**"
---

# AWS AutoML Lite - Coding Guidelines

## Important Note

**DO NOT create `.md` documentation files with every prompt unless explicitly requested.**

## Architecture Overview

Serverless AutoML platform with **split architecture**:

| Component | Technology | Deployment | Why |
|-----------|------------|------------|-----|
| Backend API | FastAPI + Mangum | Lambda ZIP (5MB) | Fast cold starts, simple deploys |
| Training | FLAML + scikit-learn | Docker on AWS Batch | 265MB deps, >15min runtime exceed Lambda limits |
| Frontend | Next.js 16 App Router | AWS Amplify | SSR support, auto-deploy on push |
| Infrastructure | Terraform | `infrastructure/terraform/` | State management |

**Key insight:** Containers ONLY for training - ML deps (265MB) exceed Lambda's 250MB limit.

**Critical architectural principle:** The training container is **fully autonomous** and stateless. It:
- Never calls the backend API
- Receives ALL context via environment variables only
- Writes results directly to DynamoDB and S3
- Outputs both `.pkl` (scikit-learn) and `.onnx` (cross-platform) model formats
- Can be tested locally with `docker-compose --profile training run training`

## Critical: Environment Variable Cascade

Training container is **autonomous** - receives ALL context via environment variables, never calls the API:

```
lambda.tf → Lambda env vars → batch_service.py containerOverrides → train.py os.getenv()
```

**⚠️ Adding a param to `train.py`? You MUST also add it to `containerOverrides` in `batch_service.py`.**

Required env vars in training container: `DATASET_ID`, `TARGET_COLUMN`, `JOB_ID`, `TIME_BUDGET`, `S3_BUCKET_DATASETS`, `S3_BUCKET_MODELS`, `S3_BUCKET_REPORTS`, `DYNAMODB_JOBS_TABLE`, `REGION`

## Key Data Flows

**Upload:** Frontend → `POST /upload` → presigned URL → S3 PUT → `POST /datasets/{id}/confirm` → DynamoDB

**Training:** `POST /train` → DynamoDB job → Batch job → container writes directly to DynamoDB → frontend polls `GET /jobs/{id}` every 5 seconds until complete/failed

**Prediction (v1.1.0):** `POST /predict/{job_id}` → Lambda loads ONNX from S3 → returns prediction + probability + inference time

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

- **Entry point** (`train.py`): Orchestrates 7-step pipeline (download → EDA → preprocess → train → ONNX export → reports → save → update status)
- **Shared utilities** (`utils.py`): Centralized `detect_problem_type()`, `is_id_column()`, `is_constant_column()` - imported by both `preprocessor.py` and `eda.py`
- **Preprocessing** (`preprocessor.py`): Auto-detects ID columns using regex patterns in `utils.py`, uses `feature-engine` for constant/duplicate detection
- **Problem type detection**: Uses BOTH conditions: integer-like values AND (<20 unique values OR <5% unique ratio) = classification. Floats with decimal values = regression.
- **Model training** (`model_trainer.py`): FLAML with `['lgbm', 'rf', 'extra_tree']` - xgboost excluded due to `best_iteration` bugs
- **Multiclass**: Explicitly set `metric='accuracy'` (FLAML's auto-detection unreliable)
- **ONNX export** (`onnx_exporter.py`): Exports `.onnx` alongside `.pkl` for cross-platform deployment
- **Reports**: Generates both EDA (`sweetviz`) and training reports with feature importance charts

### Frontend (TypeScript)

- **API client** (`frontend/lib/api.ts`): Centralized, typed interfaces matching backend Pydantic schemas
- **Polling hook** (`frontend/lib/useJobPolling.ts`): Job status polling with 5-second interval. Stops when job completes/fails. SSE won't work on Amplify (Lambda@Edge 30s timeout).
- **Client components**: Use `'use client'` ONLY for file uploads, polling, forms, theme toggle - server components by default
- **Dynamic routes**: Cast `useParams()` results: `const datasetId = params.datasetId as string`
- **Theming**: Uses `next-themes` with `ThemeToggle` component. Dark mode via Tailwind `dark:` variants.
- **Compare page** (`/compare`): Side-by-side comparison of up to 4 training jobs
- **Prediction playground** (`/results/[jobId]`): Interactive form to test deployed models

### Infrastructure (Terraform)

- **Naming**: All resources use `${var.project_name}-${var.environment}` prefix
- **Key files**: `lambda.tf` (env vars source of truth), `iam.tf` (permissions), `outputs.tf` (URLs), `amplify.tf` (frontend)
- **IAM**: Batch task role needs DynamoDB write access - both Lambda AND Batch write to DynamoDB

## Development Commands

### Local Development (Docker Compose)

```powershell
# 1. Configure backend environment
cp backend/.env.example backend/.env
# Edit backend/.env with values from: terraform output

# 2. Start API (connects to dev AWS services)
docker-compose up

# 3. Frontend (separate terminal)
cd frontend
cp .env.local.example .env.local
# Edit .env.local with NEXT_PUBLIC_API_URL
pnpm install && pnpm dev
```

### Backend Development

```powershell
# Run API locally without Docker
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload  # API at http://localhost:8000/docs
```

### Training Container Testing

```powershell
# Test training locally with uploaded dataset
DATASET_ID=xxx TARGET_COLUMN=price docker-compose --profile training run training

# Or use helper script (requires dataset uploaded to dev)
python scripts/run-training-local.py --dataset-id xxx --target-column price --time-budget 120
```

### Deployment

```powershell
# Full infrastructure
cd infrastructure/terraform
terraform apply

# Deploy Lambda API only (fast iteration)
terraform apply -target=aws_lambda_function.api

# Build and deploy training container
$EcrUrl = terraform output -raw ecr_repository_url
$Region = terraform output -raw aws_region
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $($EcrUrl.Split('/')[0])
docker build -t automl-training:latest backend/training
docker tag automl-training:latest "$EcrUrl:latest"
docker push "$EcrUrl:latest"

# Verify image in ECR
aws ecr describe-images --repository-name automl-lite-dev-training --image-ids imageTag=latest
```

### Utilities

```powershell
# Generate architecture diagrams (requires: pip install diagrams + Graphviz)
python scripts/generate_architecture_diagram.py

# Make predictions with trained model
docker build -f scripts/Dockerfile.predict -t automl-predict .
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl --info
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
| "least populated class has 1 member" | Regression misdetected as classification | Problem type detection in `utils.py` - check if float values have decimals |

## File Reference by Task

**Adding an API endpoint:** `routers/*.py` → `schemas.py` → `services/*.py` → `frontend/lib/api.ts`

**Modifying training:** `train.py` → `preprocessor.py` → `model_trainer.py` → **ALSO update** `batch_service.py` containerOverrides

**Modifying detection logic:** `backend/training/utils.py` is single source of truth for `detect_problem_type()`, `is_id_column()`, etc.

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
| `scripts/test_onnx_export.py` | Verify ONNX model export functionality |

## Testing & Validation

### API Testing

```powershell
# Health check
curl $API_URL/health

# Test upload endpoint
curl -X POST $API_URL/upload -H "Content-Type: application/json" -d '{"filename": "test.csv"}'

# View API docs (Swagger UI)
# http://localhost:8000/docs (local) or $API_URL/docs (deployed)
```

### Container Testing

```powershell
# Build training container locally
docker build -t automl-training:latest backend/training

# Test with environment variables
docker run --rm \
  -e DATASET_ID=xxx \
  -e TARGET_COLUMN=price \
  -e JOB_ID=test-123 \
  -e TIME_BUDGET=60 \
  -e S3_BUCKET_DATASETS=automl-lite-dev-datasets-XXX \
  -e DYNAMODB_JOBS_TABLE=automl-lite-dev-training-jobs \
  -e REGION=us-east-1 \
  -v ~/.aws:/root/.aws:ro \
  automl-training:latest
```

### Frontend Testing

```powershell
cd frontend
pnpm dev  # Development server at http://localhost:3000
pnpm build  # Test production build
pnpm lint  # ESLint check
```

### Terraform Validation

```powershell
cd infrastructure/terraform
terraform fmt  # Format files
terraform validate  # Syntax check
terraform plan  # Preview changes
```

## Testing (v1.1.0)

**197 total tests** (104 API + 93 Training) with coverage reports in CI.

### Test Commands

```powershell
cd backend

# API tests (before Lambda deploy)
pytest tests/api --cov=api --cov-report=xml

# Training tests (before container deploy)
pytest tests/training --cov=training --cov-report=xml
```

### Key Testing Patterns

- **Mocking services in routers**: Use `patch.object(router.service_instance, 'method')` not `patch('path.to.module')`
- **AWS mocking**: Use `moto` library for S3/DynamoDB integration tests
- **Pydantic validation**: Returns 422 (not 400) for schema violations
- **DynamoDB Decimals**: Convert to int/float before JSON serialization

## CI/CD Workflows (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `deploy-lambda-api.yml` | Push to main/dev | Deploy FastAPI to Lambda |
| `deploy-training-container.yml` | Push to main/dev | Build & push training image to ECR |
| `deploy-infrastructure.yml` | Manual | Terraform apply |
| `deploy-frontend.yml` | Push to main/dev (via Amplify) | Auto-deploy Next.js frontend |
| `ci-terraform.yml` | PR | Terraform validate & plan |
| `destroy-environment.yml` | Manual | Destroy all infrastructure (requires confirmation) |

**Branch Strategy:**
- `dev` → Deploy to dev environment (automl-lite-dev-*)
- `main` → Deploy to prod environment (automl-lite-prod-*)
- Feature branches → CI validation only (no deployment)

## Key Docs

- `docs/LESSONS_LEARNED.md` - Critical debugging insights (read this first for troubleshooting)
- `docs/QUICKSTART.md` - Deployment guide
- `.github/SETUP_CICD.md` - CI/CD with GitHub Actions
- `infrastructure/terraform/ARCHITECTURE_DECISIONS.md` - Why Lambda + Batch split
- `.github/git-commit-messages-instructions.md` - Commit message conventions