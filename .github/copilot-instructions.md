---
description: AWS AutoML Lite - AI Agent Development Guidelines
---

# AWS AutoML Lite - Coding Guidelines

## Architecture Overview

**Serverless AutoML platform on AWS** with split architecture:
- **Backend API (Lambda)**: Direct code deployment (5MB ZIP) - FastAPI + Mangum adapter
- **Training Pipeline (AWS Batch)**: Docker container (265MB deps, >15min runtime) - FLAML AutoML
- **Frontend**: Next.js 14 App Router with TypeScript
- **Infrastructure**: Terraform (HCL)

**Why containers ONLY for training?** Lambda limits: 250MB uncompressed, 15min timeout. Training needs 265MB ML libs (FLAML, XGBoost, scikit-learn) and 2-60min runtime. See `infrastructure/terraform/ARCHITECTURE_DECISIONS.md` for detailed analysis.

## Critical Context

**Training Container is Autonomous:** Batch container receives ALL context via environment variables (set in `backend/api/services/batch_service.py`). It runs independently with NO callbacks to the API. All state updates go directly to DynamoDB from the container.

**Environment Variable Cascade:** 
1. Terraform (`lambda.tf`) → Lambda env vars
2. Lambda → Batch job definition (`batch_service.py` containerOverrides)
3. Batch container reads via `os.getenv()` in `backend/training/train.py`

**Missing a variable at any level causes silent failures.**

## Key Data Flows

**Upload Workflow:**
```
Frontend → POST /upload → Lambda generates presigned S3 URL
Frontend → PUT to presigned URL → Direct S3 upload (bypass backend - reduces Lambda costs)
Frontend → POST /datasets/{id}/confirm → Lambda reads CSV from S3, analyzes, saves to DynamoDB
```

**Training Workflow:**
```
Frontend → POST /train → Lambda validates → Creates DynamoDB job record (status='pending')
Lambda → batch_service.submit_training_job() → Sets containerOverrides environment
AWS Batch → Launches Fargate container with all env vars
Container → train.py:
  1. Updates DynamoDB status='running'
  2. Downloads CSV from S3
  3. Generates EDA report → uploads to S3
  4. Trains model with FLAML
  5. Saves model.pkl → uploads to S3
  6. Updates DynamoDB status='completed' + metrics + S3 paths
Frontend polls → GET /jobs/{id} → Returns DynamoDB record + presigned download URLs
```

**Critical:** Container never calls API. All AWS operations are direct (S3, DynamoDB). If DynamoDB permissions are missing from Batch task role, jobs silently fail.

## Code Patterns & Conventions

### Backend (Python)

**Environment Configuration Pattern** (`backend/api/utils/helpers.py`):
```python
class Settings(BaseSettings):
    aws_region: str = os.getenv("REGION", "us-east-1")
    s3_bucket_datasets: str = os.getenv("S3_BUCKET_DATASETS")
    dynamodb_datasets_table: str = os.getenv("DYNAMODB_DATASETS_TABLE")
```
All AWS resource names injected via Lambda environment variables (set in `infrastructure/terraform/lambda.tf`). Never hardcode bucket names or table names.

**FastAPI Router Pattern** (`backend/api/routers/*.py`):
- Use Pydantic schemas from `backend/api/models/schemas.py` for all requests/responses
- Services layer handles AWS SDK calls (`backend/api/services/`)
- Routers stay thin - validation only, delegate to services
- Return typed Pydantic responses (FastAPI auto-serializes to JSON)

**Service Pattern Example** (`backend/api/services/batch_service.py`):
```python
def submit_training_job(self, job_name, dataset_id, target_column, job_id, config):
    response = self.batch_client.submit_job(
        jobName=job_name,
        jobQueue=settings.batch_job_queue,
        jobDefinition=settings.batch_job_definition,
        containerOverrides={
            'environment': [
                {'name': 'DATASET_ID', 'value': dataset_id},
                {'name': 'TARGET_COLUMN', 'value': target_column},
                # ALL context needed by container must be here
            ]
        }
    )
```
**Critical:** If you add a new parameter to `train.py`, you MUST add it to `containerOverrides` environment array.

**Lambda Handler** (`backend/api/main.py`):
```python
from mangum import Mangum
handler = Mangum(app, lifespan="off")  # API Gateway event → FastAPI request
```
Mangum translates API Gateway events to ASGI format. No special Lambda code needed - write normal FastAPI.

### Frontend (TypeScript)

**API Client Pattern** (`frontend/lib/api.ts`):
- Centralized API calls with typed interfaces matching backend Pydantic schemas
- Environment variable: `NEXT_PUBLIC_API_URL` (set at build time)
- All API functions return typed promises: `Promise<JobDetails>`, `Promise<DatasetMetadata>`
- Use `uploadAndConfirm()` helper for complete upload workflow (3 steps: request URL → upload → confirm)

**Next.js App Router Structure:**
- Server Components by default (no `'use client'` unless needed)
- Dynamic routes: `app/configure/[datasetId]/page.tsx`
- **Async params pattern (Next.js 14):**
  ```typescript
  export default async function Page(props: { params: Promise<{ datasetId: string }> }) {
    const params = await props.params;  // Must await in Next.js 14
    const { datasetId } = params;
  }
  ```
- Client components ONLY for: file uploads, polling, form interactions, charts
- Mark with `'use client'` at top of file when needed

**Polling Pattern for Job Status:**
```typescript
useEffect(() => {
  const interval = setInterval(async () => {
    const job = await getJobDetails(jobId);
    if (job.status === 'completed' || job.status === 'failed') {
      clearInterval(interval);
    }
  }, 3000);  // Poll every 3 seconds
  return () => clearInterval(interval);
}, [jobId]);
```

### Infrastructure (Terraform)

**Naming Convention:**
```hcl
locals {
  name_prefix = "${var.project_name}-${var.environment}"  # "automl-lite-dev"
}
resource "aws_s3_bucket" "datasets" {
  bucket = "${local.name_prefix}-datasets-${data.aws_caller_identity.current.account_id}"
}
```
All resources prefixed with environment to avoid collisions.

**Environment Variables Flow:**
1. Terraform variables → `lambda.tf` environment block → Lambda function
2. Lambda function → Batch job definition environment → Container runtime
3. Container reads via `os.getenv()` in `backend/training/train.py`

**Critical Files:**
- `variables.tf`: All configurable parameters (memory, timeout, VPC IDs)
- `data.tf`: Auto-discovers VPC subnets if not specified
- `outputs.tf`: Exposes API URL, ECR URL for deployment scripts

## Development Workflows

### Local Backend Development
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload  # Runs at http://localhost:8000
```
FastAPI auto-generates docs at `/docs` (Swagger UI).

### Local Frontend Development
```powershell
cd frontend
pnpm install
pnpm dev  # Runs at http://localhost:3000
```
Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local` for local backend.

### Infrastructure Changes
```powershell
cd infrastructure/terraform
terraform plan   # Always review before apply
terraform apply
```
**NEVER manually create AWS resources** - always use Terraform to maintain state.

### Testing Training Container Locally
```powershell
cd backend/training
docker build -t automl-training:latest .
docker run --rm `
  -e DATASET_ID=test `
  -e TARGET_COLUMN=price `
  -e JOB_ID=local-test `
  -e TIME_BUDGET=60 `
  -e AWS_ACCESS_KEY_ID=$env:AWS_ACCESS_KEY_ID `
  -e AWS_SECRET_ACCESS_KEY=$env:AWS_SECRET_ACCESS_KEY `
  -e REGION=us-east-1 `
  -e S3_BUCKET_DATASETS=automl-lite-dev-datasets-123456789 `
  -e S3_BUCKET_MODELS=automl-lite-dev-models-123456789 `
  -e S3_BUCKET_REPORTS=automl-lite-dev-reports-123456789 `
  -e DYNAMODB_JOBS_TABLE=automl-lite-dev-training-jobs `
  automl-training:latest
```
Requires dataset already uploaded to S3. Check `infrastructure/terraform/outputs.tf` for bucket names.

### Deploying Changes

**Backend API only (no infra changes):**
```powershell
cd infrastructure/terraform
terraform apply -target=aws_lambda_function.api  # Redeploys Lambda
```

**Training container only:**
```powershell
# Build and push new image (Batch uses :latest automatically)
cd backend/training
$EcrUrl = (cd ..\..\infrastructure\terraform; terraform output -raw ecr_repository_url)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ($EcrUrl -split '/')[0]
docker build -t automl-training:latest .
docker tag automl-training:latest "$EcrUrl:latest"
docker push "$EcrUrl:latest"
```

**Frontend (when CloudFront added in Phase 2):**
```powershell
cd frontend
pnpm build
aws s3 sync out/ s3://automl-lite-frontend-bucket --delete
aws cloudfront create-invalidation --distribution-id E123456 --paths "/*"
```

## Problem Type Detection Logic

Located in `backend/training/preprocessor.py`:
```python
if y.dtype == 'object' or y.nunique() < 10:
    problem_type = 'classification'
else:
    problem_type = 'regression'
```
**Rule:** If target is categorical OR has <10 unique values → classification. Otherwise → regression.

Used in two places:
1. `preprocessor.py` during training
2. Should match detection in `backend/api/routers/upload.py` (confirm endpoint)

## Common Pitfalls & Solutions

### 1. Lambda Package Size Errors
**Symptom:** "Unzipped size must be smaller than 262144000 bytes"
**Cause:** Accidentally included `training/` directory in Lambda ZIP
**Fix:** Check `infrastructure/terraform/lambda.tf` - `excludes` list must include `"training"`

### 2. Batch Job Fails Immediately
**Symptom:** Job status goes to FAILED with "CannotPullContainerError"
**Cause:** Training container not pushed to ECR or wrong tag
**Fix:** Run deployment script in `QUICKSTART.md` Step 3, verify with `aws ecr describe-images`

### 3. Training Job Never Completes
**Symptom:** Job stuck in RUNNING for >1 hour
**Cause:** Batch job can't write to DynamoDB (IAM permissions)
**Fix:** Check `infrastructure/terraform/iam.tf` - Batch task role needs `dynamodb:UpdateItem` permission

### 4. Frontend Can't Connect to API
**Symptom:** CORS errors or 404s
**Cause:** Wrong `NEXT_PUBLIC_API_URL` or API Gateway not deployed
**Fix:** Get URL from `terraform output api_gateway_url`, update `.env.local` and rebuild frontend

### 5. Presigned URL Upload Fails
**Symptom:** 403 Forbidden when uploading to presigned URL
**Cause:** CORS not configured on S3 bucket or URL expired
**Fix:** Check `infrastructure/terraform/s3.tf` - datasets bucket needs CORS rules with PUT method

## Key Files Reference

**When modifying API endpoints:**
- Add route in `backend/api/routers/*.py`
- Add schema in `backend/api/models/schemas.py`
- Add service method in `backend/api/services/*.py`
- Update `frontend/lib/api.ts` with typed function

**When modifying training logic:**
- ML code in `backend/training/model_trainer.py`
- Preprocessing in `backend/training/preprocessor.py`
- EDA in `backend/training/eda.py`
- Orchestration in `backend/training/train.py` (reads env vars, updates DynamoDB)

**When adding AWS resources:**
- Create `infrastructure/terraform/<service>.tf`
- Add variables to `variables.tf` if configurable
- Add outputs to `outputs.tf` if needed by scripts
- Update IAM policies in `iam.tf` for permissions

## Cost Monitoring

Estimated monthly costs (20 training jobs, 100K API calls):
- S3: ~$0.23 (10GB storage)
- DynamoDB: ~$1.00 (on-demand)
- Lambda API: ~$0.80
- API Gateway: ~$1.00
- Batch (Fargate Spot): ~$3.00
- **Total: $6-7/month**

Check actual costs: `aws ce get-cost-and-usage --time-period Start=2025-11-01,End=2025-11-30 --granularity MONTHLY --metrics UnblendedCost`

## Testing Checklist

**Before committing backend changes:**
1. Run `uvicorn api.main:app --reload` - check `/docs` for errors
2. Test endpoint manually with curl or Postman
3. Verify DynamoDB records created correctly
4. Check CloudWatch logs for Lambda errors

**Before committing training changes:**
1. Build Docker image locally
2. Test with sample dataset in S3
3. Verify model.pkl and report.html generated
4. Check DynamoDB job status updated to 'completed'

**Before deploying infrastructure:**
1. Run `terraform plan` and review ALL changes
2. Check estimated costs with `terraform plan -out=plan.out && terraform show -json plan.out`
3. Verify VPC/subnet IDs if using custom VPC
4. Test in dev environment before prod

## Documentation Hierarchy

- **README.md**: Public-facing overview
- **QUICKSTART.md**: Deployment instructions (users)
- **PROJECT_REFERENCE.md**: Complete technical documentation
- **DEPLOYMENT.md**: Detailed production deployment guide
- **This file**: AI agent coding guidelines (you are here)
- **ARCHITECTURE_DECISIONS.md**: Why containers for training

Read in this order for new contributors: README → QUICKSTART → THIS FILE → PROJECT_REFERENCE

---

## Cross-Component Communication

**Backend → Frontend:** 
- REST API with JSON responses (no WebSockets in MVP)
- Frontend polls `/jobs/{id}` every 3s during training
- Presigned S3 URLs for direct downloads (expires in 1 hour)

**Lambda → Batch Container:**
- No direct communication - fire-and-forget pattern
- Lambda sets containerOverrides environment in `batch_service.py`
- Container reads ALL context from environment variables
- Container updates DynamoDB directly (no Lambda callback)

**Container → AWS Services:**
- Direct SDK calls to S3 (download CSV, upload model/report)
- Direct SDK calls to DynamoDB (update job status/metrics)
- Uses Batch task execution role (not Lambda role)

## Debugging Tips

**Backend API issues:**
- Check CloudWatch logs: `/aws/lambda/automl-lite-{env}-api`
- Test locally: `uvicorn api.main:app --reload` then visit `http://localhost:8000/docs`
- Verify env vars in `lambda.tf` match `helpers.py` Settings class

**Training job failures:**
- Check CloudWatch logs: `/aws/batch/automl-lite-{env}-training`
- Common cause: Missing environment variable in `batch_service.py` containerOverrides
- Verify IAM: Batch task role must have S3 read/write + DynamoDB update permissions
- Test container locally (see section below) before pushing to ECR

**Frontend connection issues:**
- Verify `NEXT_PUBLIC_API_URL` matches Terraform output: `terraform output api_gateway_url`
- Check browser console for CORS errors
- Ensure API Gateway stage is deployed: `cd infrastructure/terraform && terraform apply`

---

**Status:** Phase 1 Backend Complete ✅ | Frontend In Progress 🚧  
**Last Updated:** 2025-11-28
