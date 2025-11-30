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
| Frontend | Next.js 14 App Router | Static (S3/CloudFront) | SSG for cost efficiency |
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
Never hardcode bucket/table names.

**Layered architecture:**
- `routers/*.py` - Thin, validation only, delegates to services
- `services/*.py` - AWS SDK calls (boto3)
- `models/schemas.py` - Pydantic schemas for all requests/responses

**Lambda handler** (`backend/api/main.py`): Just `handler = Mangum(app)` - write normal FastAPI.

### Frontend (TypeScript)

**API client** (`frontend/lib/api.ts`) - Centralized, typed interfaces matching backend Pydantic schemas:
```typescript
export async function uploadAndConfirm(file: File): Promise<DatasetMetadata> {
  const { dataset_id, upload_url } = await requestUploadUrl(file.name);
  await uploadFile(upload_url, file);
  return await confirmUpload(dataset_id);
}
```

**Client components** - Use `'use client'` ONLY for: file uploads, polling, form interactions. Server components by default.

**Dynamic routes with useParams** (`app/configure/[datasetId]/page.tsx`):
```typescript
const params = useParams();
const datasetId = params.datasetId as string;
```

### Infrastructure (Terraform)

**Naming:** All resources use `${var.project_name}-${var.environment}` prefix (e.g., `automl-lite-dev-datasets`).

**Key files:**
- `lambda.tf` - Lambda env vars (source of truth for resource names)
- `iam.tf` - Permissions (Batch task role needs DynamoDB write access!)
- `outputs.tf` - API URL, ECR URL for deployment scripts

## Development Commands

```powershell
# Backend (local)
cd backend; uvicorn api.main:app --reload  # http://localhost:8000/docs

# Frontend (local) 
cd frontend; pnpm dev  # Set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local

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
| Lambda ZIP too large | Included `training/` folder | Check `lambda.tf` excludes list |
| Batch job instant FAILED | Container not in ECR | Push image, verify with `aws ecr describe-images` |
| Job stuck RUNNING | Missing DynamoDB permissions | Add `dynamodb:UpdateItem` to Batch task role in `iam.tf` |
| Frontend 404/CORS errors | Wrong API URL | Get URL from `terraform output api_gateway_url` |
| Training wrong problem type | Threshold mismatch | Check `<10 unique values = classification` rule in `preprocessor.py` |

## File Reference by Task

**Adding an API endpoint:** `routers/*.py` → `schemas.py` → `services/*.py` → `frontend/lib/api.ts`

**Modifying training:** `train.py` (orchestration) → `preprocessor.py` → `model_trainer.py` → `eda.py`

**Adding AWS resources:** Create `<service>.tf` → `variables.tf` → `outputs.tf` → `iam.tf` for permissions

## Debugging

- Lambda logs: `/aws/lambda/automl-lite-{env}-api`
- Batch logs: `/aws/batch/automl-lite-{env}-training`
- Local API test: Visit `http://localhost:8000/docs` (Swagger UI)
- Check training env vars: Compare `batch_service.py` containerOverrides with `train.py` os.getenv() calls
