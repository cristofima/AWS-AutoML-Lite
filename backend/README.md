# Backend - AWS AutoML Lite

FastAPI backend for the AWS AutoML Lite platform.

## Prerequisites

- Python 3.11+
- AWS CLI configured with credentials
- Docker & Docker Compose (for containerized development)

## Quick Start with Docker Compose

The easiest way to run the backend locally, connecting to AWS dev environment:

```bash
# From project root
cd AWS-AutoML-Lite

# 1. Copy environment template and fill in values from terraform output
cp backend/.env.example backend/.env
# Edit backend/.env with your AWS resource names

# 2. Start Backend API
docker-compose up

# 3. Start Frontend (in a separate terminal)
cd frontend
pnpm install
pnpm dev

# 4. Access the application
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:3000
```

### Test Training Container Locally

Before deploying to AWS Batch, you can test the training container locally.

**Prerequisites:**
1. A dataset must already be uploaded via the API/Frontend
2. Get the `dataset_id` from the API response or DynamoDB

**PowerShell:**
```powershell
# Run training with inline environment variables
$env:DATASET_ID = "your-dataset-id"
$env:TARGET_COLUMN = "Customer_Rating"
$env:JOB_ID = "local-test-001"
$env:TIME_BUDGET = "60"
docker-compose --profile training run training
```

**Bash/Linux:**
```bash
DATASET_ID=your-dataset-id \
TARGET_COLUMN=Customer_Rating \
JOB_ID=local-test-001 \
TIME_BUDGET=60 \
docker-compose --profile training run training
```

This runs the **exact same container** that AWS Batch will execute, connecting to AWS dev services (S3, DynamoDB).

**What happens:**
1. Container downloads dataset from S3 (`s3://bucket/datasets/{dataset_id}/`)
2. Generates EDA report → uploads to S3
3. Trains model with FLAML AutoML
4. Saves model.pkl → uploads to S3
5. Updates job status in DynamoDB

## Project Structure

```
backend/
├── .env.example            # Environment template (copy to .env)
├── api/                    # FastAPI application
│   ├── main.py             # Application entry point
│   ├── models/             # Pydantic schemas
│   ├── routers/            # API endpoints
│   ├── services/           # AWS service integrations
│   └── utils/              # Helper functions
├── training/               # Training container code
│   ├── train.py            # Main training script
│   ├── preprocessor.py     # Data preprocessing
│   ├── model_trainer.py    # FLAML AutoML training
│   ├── eda.py              # EDA report generation
│   ├── Dockerfile          # Training container image
│   └── requirements.txt    # Training dependencies
├── Dockerfile.api          # API container image
└── requirements.txt        # API dependencies
```

## Local Development (Without Docker)

### 1. Create Virtual Environment

```bash
# Windows (PowerShell)
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/macOS
cd backend
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the template and fill in your values:

```bash
cp .env.example .env
# Edit .env with values from: terraform output
```

Variables needed:

```env
# AWS Configuration
AWS_REGION=us-east-1

# S3 Buckets
S3_BUCKET_DATASETS=automl-lite-dev-datasets-<account-id>
S3_BUCKET_MODELS=automl-lite-dev-models-<account-id>
S3_BUCKET_REPORTS=automl-lite-dev-reports-<account-id>

# DynamoDB Tables
DYNAMODB_DATASETS_TABLE=automl-lite-dev-datasets
DYNAMODB_JOBS_TABLE=automl-lite-dev-training-jobs

# AWS Batch
BATCH_JOB_QUEUE=automl-lite-dev-training-queue
BATCH_JOB_DEFINITION=automl-lite-dev-training-job
```

> **Note:** Replace `<account-id>` with your AWS account ID. Get values from `terraform output`.

### 4. Run the API Server

```bash
# From project root
cd backend
uvicorn api.main:app --reload
```

The API will be available at:
- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/upload/request-url` | Get presigned URL for upload |
| `POST` | `/datasets/{id}/confirm` | Confirm dataset upload |
| `GET` | `/datasets` | List all datasets |
| `GET` | `/datasets/{id}` | Get dataset details |
| `DELETE` | `/datasets/{id}` | Delete a dataset |
| `POST` | `/train` | Start training job |
| `GET` | `/jobs/{id}` | Get job status |
| `GET` | `/models` | List trained models |
| `GET` | `/models/{id}` | Get model details |

## Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Request upload URL
curl -X POST http://localhost:8000/upload/request-url \
  -H "Content-Type: application/json" \
  -d '{"filename": "data.csv", "content_type": "text/csv"}'

# List datasets
curl http://localhost:8000/datasets

# Start training
curl -X POST http://localhost:8000/train \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "your-dataset-id",
    "target_column": "target",
    "config": {"time_budget": 60}
  }'

# Start training with auto-calculated time budget
curl -X POST http://localhost:8000/train \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "your-dataset-id",
    "target_column": "target"
  }'
```

### Using Python

```python
import requests

base_url = "http://localhost:8000"

# Health check
response = requests.get(f"{base_url}/health")
print(response.json())

# List datasets
response = requests.get(f"{base_url}/datasets")
print(response.json())
```

## Development Tips

### Auto-reload
The `--reload` flag automatically restarts the server when code changes.

### AWS Credentials
Make sure your AWS credentials are configured:

```bash
aws configure
```

Or mount `~/.aws` when using Docker (already configured in docker-compose.yml).

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure you're in the `backend/` directory and virtual environment is activated.

2. **AWS Credentials Error**: Verify AWS credentials are configured correctly.

3. **Port Already in Use**: Change the port with `--port 8001` or kill the existing process.

4. **CORS Errors**: The API includes CORS middleware. Check `api/main.py` if issues persist.

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest --cov=api
```

## Smart Features

### Auto-calculated Time Budget

When `time_budget` is not provided in the training request, the API automatically calculates an optimal value based on dataset size:

| Dataset Rows | Time Budget |
|--------------|-------------|
| < 1,000 | 120s (2 min) |
| 1,000 - 10,000 | 300s (5 min) |
| 10,000 - 50,000 | 600s (10 min) |
| > 50,000 | 1,200s (20 min) |

### Problem Type Detection

The API automatically detects whether a target column is for **Classification** or **Regression** using smart heuristics:

| Condition | Problem Type |
|-----------|-------------|
| Non-numeric column (strings, categories) | Classification |
| Integer-like values with ≤10 unique values | Classification |
| Numeric with <20 unique AND <5% unique ratio | Classification |
| Float values with decimals (continuous) | Regression |
| High unique ratio (≥5%) | Regression |

**Key Improvement (v1.1.0):** The detection logic now correctly identifies continuous float values (like `35.5, 40.2, 38.7`) as regression, even when the unique count is below 20. The previous logic used `OR` instead of `AND`, causing false classification detection.

### Shared Utility Module

The training module uses a centralized `utils.py` for shared functions:

```python
# backend/training/utils.py
from .utils import (
    detect_problem_type,      # Classification vs Regression
    is_id_column,             # Detect identifier columns
    is_constant_column,       # Detect constant features
    is_high_cardinality_categorical,  # Detect high-cardinality categoricals
    ID_PATTERNS,              # Regex patterns for ID detection
)
```

This follows the DRY principle - logic is defined once and reused across `preprocessor.py` and `eda.py`.

This detection is performed both in the API (for UI display) and in the training container (for model training).
