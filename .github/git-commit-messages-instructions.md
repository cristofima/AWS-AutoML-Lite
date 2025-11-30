# GitHub Copilot Git Commit Message Guidelines

Generate [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for AWS AutoML Lite project.

**Tech Stack:** Next.js 14 + FastAPI + AWS Lambda + Terraform + AWS Batch + DynamoDB + S3

## Commit Structure

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Header rules:** Max 50 chars, imperative tense ("add" not "added"), lowercase type, capitalize description
**Body rules:** Past tense, wrap at 72 chars, explain WHY not what
**Footer rules:** Breaking changes (`BREAKING CHANGE:`)

---

## Commit Types

### `feat` - New Functionality

New API endpoints, frontend pages, AutoML features, training capabilities, AWS services.

```
feat(api): add model download endpoint
feat(training): implement FLAML AutoML integration
feat(upload): add presigned URL generation
feat(frontend): add training history page
```

### `fix` - Bug Resolution

API errors, training failures, frontend bugs, AWS resource issues, data preprocessing errors.

```
fix(batch): resolve container memory overflow
fix(api): correct DynamoDB query pagination
fix(training): fix target column detection logic
fix(frontend): resolve file upload state management
```

### `refactor` - Code Improvement (Same Behavior)

Extracting services, reorganizing FastAPI routers, simplifying preprocessing logic, removing duplicates.

```
refactor(api): extract S3 operations to service layer
refactor(training): consolidate preprocessing functions
refactor(services): simplify DynamoDB query patterns
refactor(frontend): extract API client utilities
```

### `perf` - Performance Optimization

Lambda cold start reduction, S3 transfer optimization, training algorithm tuning, batch job efficiency.

```
perf(lambda): reduce package size from 8MB to 5MB
perf(training): optimize FLAML time budget allocation
perf(api): add DynamoDB query result caching
perf(batch): use Fargate Spot for cost reduction
```

### `docs` - Documentation ONLY

**CRITICAL:** ANY `.md` file change = `docs` type (even new files). Also docstrings, comments.

```
docs: update README with deployment steps
docs(api): document FastAPI endpoint schemas
docs: add ARCHITECTURE_DECISIONS rationale
docs(terraform): document IAM permissions
```

**Common mistakes:**

- ❌ `feat: add deployment guide` → ✅ `docs: add deployment guide`
- ❌ `chore: update PROJECT_REFERENCE` → ✅ `docs: update PROJECT_REFERENCE`

### `test` - Test Code

Unit tests, integration tests, E2E tests, container testing, load testing.

```
test(api): add upload endpoint tests
test(training): add preprocessor unit tests
test(batch): test container locally with Docker
test(frontend): add FileUpload component tests
```

### `build` - Build System & Infrastructure

**Terraform resources, Lambda configs, Docker images, AWS Batch, dependencies.**

```
build(terraform): add DynamoDB training-jobs table
build(lambda): update Python runtime to 3.11
build(batch): increase vCPU to 2 for training jobs
build(docker): optimize training image size
build: upgrade FastAPI to version 0.115
```

Use specific scopes: `build(terraform):`, `build(lambda):`, `build(batch):`, `build(docker):`

### `ci` - CI/CD Pipelines

GitHub Actions, deployment scripts, automated testing, ECR pushes.

```
ci(github-actions): add Lambda deployment workflow
ci: add automated ECR image push script
ci: add Terraform validation on PR
ci(scripts): add verify-resources health check
```

### `style` - Formatting Only

Black formatting, prettier, whitespace (rare, usually auto-formatted).

```
style: format Python files with Black
style: fix indentation in FastAPI routers
```

### `chore` - Miscellaneous

IDE configs, .gitignore, environment files, .env.local.example.

```
chore: update .gitignore for Python cache
chore(.vscode): configure Python interpreter
chore: add .env.local.example template
chore(.github): add issue templates
```

**Common mistakes:**

- ❌ `chore(terraform): add S3 bucket` → ✅ `build(terraform): add S3 bucket`
- ❌ `chore: upgrade dependencies` → ✅ `build: upgrade dependencies`

### `revert` - Revert Commit

```
revert: revert "feat(training): add GPU support"

This reverts commit abc123.
Reason: Fargate doesn't support GPU, reverting to CPU.
```

---

## Scopes (Project-Specific)

**Backend layers:**
- `api`: FastAPI routers and main application
- `services`: S3, DynamoDB, Batch service layers
- `models`: Pydantic schemas
- `training`: ML training container code
- `utils`: Helper functions

**Frontend:**
- `upload`: File upload flow
- `configure`: Training configuration page
- `history`: Training jobs history
- `results`: Model results display
- `components`: Reusable UI components
- `lib`: API client and utilities

**Infrastructure:**
- `terraform`: Infrastructure as code
- `lambda`: Lambda function configuration
- `batch`: AWS Batch job definitions
- `dynamodb`: DynamoDB table schemas
- `s3`: S3 bucket configurations
- `iam`: IAM roles and policies
- `ecr`: Container registry

**Cross-cutting:**
- `api/upload`: Upload router specifically
- `api/training`: Training router
- `training/eda`: EDA generation logic
- `training/preprocessor`: Data preprocessing

Examples:

```
feat(api/upload): add CSV validation before S3 upload
fix(training/eda): resolve matplotlib memory leak
refactor(services/dynamo): consolidate query builders
build(terraform/batch): increase job timeout to 60min
```

Omit scope for project-wide changes:

```
refactor: standardize error responses
style: format all Python files
docs: update architecture documentation
```

---

## Body Guidelines

### When to Include Body

**REQUIRED:**

- Multiple files modified (list if 2-8, group if >8)
- Complex AWS infrastructure changes
- Breaking API contract changes
- Performance/cost optimizations (include metrics)
- Training algorithm modifications

**Format for 2-8 files:**

```
Modified files (5):
- backend/api/routers/upload.py: Added CSV validation
- backend/api/services/s3_service.py: Presigned URL logic
- backend/api/models/schemas.py: UploadResponse schema
- frontend/lib/api.ts: Upload API client
- frontend/components/FileUpload.tsx: Error handling
```

**Format for >8 files:**

```
This change spans 12 files across multiple layers:

Backend API: Updated upload flow with validation
Backend services: Refactored S3 and DynamoDB clients
Frontend: New upload UI with progress tracking
Infrastructure: Added CloudWatch logs for debugging
```

### When to Omit Body

- Single file, simple change
- Self-explanatory (e.g., `docs: fix typo`)
- Trivial dependency updates

---

## Breaking Changes

Mark changes requiring consumers to modify their usage.

**Format:**

```
feat(api)!: change training job response format

BREAKING CHANGE: Job status endpoint now includes EDA URL.

Old: { job_id, status, model_url }
New: { job_id, status, model_url, eda_url, report_url }

Migration:
- Update TypeScript interfaces in frontend/lib/api.ts
- Add optional chaining: job.eda_url?.includes('s3')
- Update JobResult component to display new fields

All jobs created after this commit include new fields.
```

**What IS breaking:**

- Changing API request/response schemas
- Removing Pydantic model fields
- Modifying DynamoDB primary/sort keys
- Changing S3 bucket naming conventions
- Updating Lambda environment variable names
- Altering Batch container environment variables

**What is NOT breaking:**

- Adding optional API parameters (with defaults)
- Internal refactoring (same external behavior)
- Performance improvements (same output)
- Bug fixes restoring documented behavior

---

## Quick Decision Tree

1. **Only .md files?** → `docs`
2. **IDE config (.vscode/, .editorconfig)?** → `chore`
3. **Terraform files (.tf)?** → `build`
4. **Docker files (Dockerfile, .dockerignore)?** → `build`
5. **requirements.txt, package.json dependencies?** → `build`
6. **CI scripts (.github/workflows/)?** → `ci`
7. **New API endpoint or ML feature?** → `feat`
8. **Fix broken functionality?** → `fix`
9. **Performance/cost optimization?** → `perf`
10. **Code restructuring (same behavior)?** → `refactor`
11. **Tests only?** → `test`
12. **Formatting only?** → `style`
13. **Everything else?** → `chore`

---

## File Type Reference

| File Pattern                           | Type    | Example                                |
| -------------------------------------- | ------- | -------------------------------------- |
| `*.md`                                 | `docs`  | `docs: update QUICKSTART`              |
| `.vscode/*`, `.editorconfig`           | `chore` | `chore: configure Python linting`      |
| `.github/workflows/*.yml`              | `ci`    | `ci: add Lambda deployment workflow`   |
| `infrastructure/terraform/*.tf`        | `build` | `build(terraform): add S3 bucket`      |
| `backend/training/Dockerfile`          | `build` | `build(docker): optimize image layers` |
| `backend/requirements.txt`             | `build` | `build: upgrade FastAPI to 0.115`      |
| `frontend/package.json` (deps)         | `build` | `build: add chart.js for metrics`      |
| `backend/api/routers/*.py` (new)       | `feat`  | `feat(api): add model download route`  |
| `backend/training/*.py` (new logic)    | `feat`  | `feat(training): add FLAML estimator`  |
| `frontend/app/**/page.tsx` (new)       | `feat`  | `feat(history): add jobs list page`    |
| `frontend/components/*.tsx` (new)      | `feat`  | `feat(components): add FileUpload`     |
| `backend/api/services/*.py` (bugfix)   | `fix`   | `fix(services): handle S3 exceptions`  |
| `infrastructure/terraform/scripts/*.ps1` | `ci`    | `ci: add automated deployment script`  |

---

## Examples

### Simple Commits

```
feat(upload): add presigned S3 URL generation
feat(training): integrate FLAML AutoML
fix(batch): resolve container OOM errors
fix(api): correct DynamoDB pagination
refactor(services): extract S3 client logic
perf(lambda): reduce cold start time
test(training): add preprocessor tests
docs: update deployment guide
build(terraform): add ECR repository
build: upgrade FastAPI dependencies
ci: add ECR push automation
chore: update .gitignore for Python
```

### With Body (Upload Feature)

```
feat(upload): implement CSV upload with validation

Complete upload workflow with presigned URLs, validation,
and metadata extraction for AutoML training.

Modified files (7):
- backend/api/routers/upload.py: Upload and confirm endpoints
- backend/api/services/s3_service.py: Presigned URL generation
- backend/api/services/dynamo_service.py: Dataset metadata storage
- backend/api/models/schemas.py: Upload request/response schemas
- frontend/components/FileUpload.tsx: Drag-and-drop UI
- frontend/lib/api.ts: Upload API client functions
- frontend/app/page.tsx: Integrated upload component

Features:
- CSV validation (columns, size, format)
- Problem type detection (regression/classification)
- Direct S3 upload via presigned URL (no backend bottleneck)
- DynamoDB metadata indexing
```

### Bug Fix (Training Container)

```
fix(batch): resolve training container memory errors

Fixed OOM kills during FLAML training on large datasets.
Increased Fargate memory from 2GB to 4GB and optimized
pandas DataFrame chunking.

Root cause: Loading entire 500MB CSV into memory
Solution: Chunk-based processing + increased memory limit

Modified files (3):
- infrastructure/terraform/batch.tf: Memory 2048 → 4096
- backend/training/preprocessor.py: Add chunked reading
- backend/training/train.py: Optimize data flow

Cost impact: +$0.50/month for memory increase
Performance: Can now handle CSVs up to 1GB

Fixes #78
```

### Performance (Lambda Optimization)

```
perf(lambda): reduce package size by 40%

Optimized Lambda deployment package by excluding training
dependencies, reducing cold start from 3.5s to 2.1s.

Changes:
- Excluded backend/training/ from Lambda ZIP
- Removed unnecessary test files and __pycache__
- Used slim boto3 imports instead of full SDK

Performance metrics (100 cold starts):
- Before: 5MB package, 3.5s avg cold start
- After: 3MB package, 2.1s avg cold start
- Cost reduction: Faster execution = lower Lambda costs

Modified files (2):
- infrastructure/terraform/lambda.tf: Updated excludes list
- infrastructure/terraform/scripts/build-lambda.ps1: Build script

Refs: #45
```

### Infrastructure (Batch Job)

```
build(batch): configure Fargate Spot for training jobs

Implemented AWS Batch with Fargate Spot compute for
cost-effective AutoML training. 70% cost savings vs on-demand.

Modified files (6):
- infrastructure/terraform/batch.tf: Compute environment
- infrastructure/terraform/iam.tf: Batch execution roles
- infrastructure/terraform/ecr.tf: Container registry
- backend/api/services/batch_service.py: Job submission
- backend/training/train.py: Environment variable handling
- backend/training/Dockerfile: Multi-stage build

Configuration:
- vCPU: 2, Memory: 4GB
- Max runtime: 60 minutes
- Spot pricing: ~$0.05/job vs $0.17/job on-demand

Cost estimate: $3/month for 20 training jobs
```

---

## Common Mistakes

### Documentation

```
❌ feat: add deployment guide → ✅ docs: add deployment guide
❌ chore: update README → ✅ docs: update README
❌ refactor(docs): reorganize → ✅ docs: reorganize structure
```

### Infrastructure

```
❌ feat(terraform): add S3 bucket → ✅ build(terraform): add S3 bucket
❌ chore(batch): increase memory → ✅ build(batch): increase memory
❌ fix(terraform): correct IAM policy → ✅ build(iam): fix Batch permissions
```

### CI/CD

```
❌ build(github-actions): add workflow → ✅ ci(github-actions): add workflow
❌ feat(scripts): deployment script → ✅ ci(scripts): add deployment automation
```

### Backend API

```
❌ refactor(api): add new endpoint → ✅ feat(api): add model download endpoint
❌ feat: fix upload bug → ✅ fix(upload): resolve presigned URL expiry
```

### Training Code

```
❌ chore(training): add FLAML → ✅ feat(training): integrate FLAML AutoML
❌ refactor: fix preprocessing → ✅ fix(training): correct target detection
```

---

## Checklist Before Committing

- [ ] Type correct (used decision tree)
- [ ] Scope matches project structure
- [ ] Description < 50 chars, imperative tense
- [ ] Body included if 2+ files modified
- [ ] Breaking change marked with `!`
- [ ] Cost/performance impacts noted
- [ ] AWS resource changes documented
- [ ] Files listed (2-8) or grouped (>8)
- [ ] Explained WHY, not just WHAT
- [ ] No sensitive data (keys, URLs)
- [ ] Terraform state not committed

---

## Key Principles

1. **Atomic commits:** One logical change per commit
2. **Type hierarchy:** When mixed: feat > fix > perf > refactor
3. **Documentation = `docs`:** ANY .md file = `docs`, no exceptions
4. **Infrastructure = `build`:** Terraform, Docker, configs = `build`
5. **CI/CD = `ci`:** GitHub Actions, deployment scripts = `ci`
6. **IDE = `chore`:** .vscode, .editorconfig = `chore`
7. **Use scopes:** Helps team understand impact (api, training, terraform)
8. **Document AWS costs:** Include cost impact for infrastructure changes
9. **Test containers:** Docker changes should mention local testing
10. **Breaking changes need migration:** Always explain API contract changes

---

## AWS AutoML Lite Specific Notes

### Lambda vs Batch Container

- **Lambda changes** (API, services, routers): Usually `feat` or `fix`
- **Training container** (Dockerfile, training/*.py): Usually `feat(training)` or `build(docker)`
- **Remember:** Lambda = direct code, Batch = Docker container

### Common Workflows

**Upload flow:**
```
feat(upload): add CSV upload workflow

Modified files (4):
- backend/api/routers/upload.py
- backend/api/services/s3_service.py
- frontend/components/FileUpload.tsx
- frontend/lib/api.ts
```

**Training flow:**
```
feat(training): implement AutoML training pipeline

Modified files (5):
- backend/training/train.py
- backend/training/preprocessor.py
- backend/training/model_trainer.py
- backend/api/services/batch_service.py
- infrastructure/terraform/batch.tf
```

**Frontend page:**
```
feat(history): add training jobs history page

Modified files (3):
- frontend/app/history/page.tsx
- frontend/lib/api.ts
- backend/api/routers/training.py (pagination)
```

### Cost-Related Changes

Always mention cost impact for:
- Fargate memory/vCPU changes
- S3 storage class changes
- DynamoDB capacity mode changes
- Lambda memory configuration

Example:
```
build(batch): increase training job timeout to 60min

Cost impact: ~$0.10/job → ~$0.15/job (longer runtime)
Allows FLAML to explore more models for better accuracy.
```

### Environment-Specific Changes

When modifying environment variables:

```
build(lambda): add S3_BUCKET_MODELS environment variable

Modified files (2):
- infrastructure/terraform/lambda.tf: Added env var
- backend/api/utils/helpers.py: Added to Settings class

Required for model download feature. Backward compatible
with default value fallback.
```

### Docker Image Updates

When updating training container:

```
build(docker): optimize training image size

Reduced image from 1.2GB to 850MB using multi-stage build
and Alpine base image where possible.

Modified files (2):
- backend/training/Dockerfile: Multi-stage build
- backend/training/requirements.txt: Removed dev deps

Build time: 8min → 5min
ECR storage cost: -$0.15/month

Deploy with:
cd backend/training
docker build -t automl-training:latest .
docker push $(terraform output -raw ecr_repository_url):latest
```

### Pydantic Schema Changes

When modifying API contracts:

```
feat(api)!: add optional metadata to dataset schema

BREAKING CHANGE: DatasetResponse now includes metadata field.

Modified files (3):
- backend/api/models/schemas.py: Added metadata field
- backend/api/routers/upload.py: Populate metadata
- frontend/lib/api.ts: Updated TypeScript interface

Old response: { dataset_id, filename, status }
New response: { dataset_id, filename, status, metadata: {...} }

Migration for frontend:
- Update DatasetResponse interface
- Access with optional chaining: dataset.metadata?.rows

Backward compatible: metadata defaults to null for old datasets.
```

### FastAPI Router Organization

When adding new endpoints:

```
feat(api): add model metrics endpoint

Added /models/{model_id}/metrics for retrieving training
performance metrics from DynamoDB.

Modified files (4):
- backend/api/routers/models.py: New metrics endpoint
- backend/api/services/dynamo_service.py: Query method
- backend/api/models/schemas.py: MetricsResponse schema
- frontend/lib/api.ts: API client function

Returns: accuracy, precision, recall, f1_score, training_time
```

### DynamoDB Schema Changes

When modifying table structures:

```
build(terraform): add GSI for dataset queries by user

Added Global Secondary Index to support multi-tenant features
for filtering datasets by user_id.

Modified files (2):
- infrastructure/terraform/dynamodb.tf: Added GSI definition
- backend/api/services/dynamo_service.py: Updated queries

GSI: user-id-index on user_id attribute
Projection: ALL attributes

Cost impact: +$0.50/month for GSI storage and queries

Requires: terraform apply (creates GSI without downtime)
```

---

**Remember:** Clear commits enable automated changelogs and maintain this serverless AutoML platform!