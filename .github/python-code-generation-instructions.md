# GitHub Copilot Custom Instructions - Python Backend Code Generation

These instructions guide GitHub Copilot in generating clean, maintainable, and type-safe Python code following industry best practices, PEP standards, and SOLID principles.

---

## I. Core Design Principles

### 1. DRY (Don't Repeat Yourself)

- **Extract repeated logic** into reusable functions, classes, or modules
- **Centralize configuration** in a single location (e.g., `Settings` class with Pydantic)
- **Use inheritance/composition** for shared behavior across classes
- **Create utility modules** for common operations

**Examples:**

```python
# ❌ BAD - Repeated S3 client creation
def upload_file(bucket, key, data):
    client = boto3.client('s3')
    client.put_object(Bucket=bucket, Key=key, Body=data)

def download_file(bucket, key):
    client = boto3.client('s3')
    return client.get_object(Bucket=bucket, Key=key)

# ✅ GOOD - Centralized client in service class
class S3Service:
    def __init__(self):
        self._client = boto3.client('s3')
    
    def upload(self, bucket: str, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=bucket, Key=key, Body=data)
    
    def download(self, bucket: str, key: str) -> bytes:
        response = self._client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
```

### 2. KISS (Keep It Simple, Stupid)

- **Prefer simple solutions** over clever or abstract ones
- **Avoid premature optimization** - optimize only when measured
- **Use built-in functions** when they solve the problem
- **Limit nesting depth** - extract complex conditions into functions

**Examples:**

```python
# ❌ BAD - Over-engineered
class DataProcessorFactory:
    @staticmethod
    def create_processor(data_type: str) -> IDataProcessor:
        processors = {
            'csv': CSVProcessor(),
            'json': JSONProcessor(),
        }
        return processors.get(data_type, DefaultProcessor())

# ✅ GOOD - Simple function is sufficient
def process_data(data: pd.DataFrame, data_type: str) -> pd.DataFrame:
    if data_type == 'csv':
        return data.dropna()
    return data
```

### 3. YAGNI (You Aren't Gonna Need It)

- **Build only what's needed now** - avoid speculative features
- **Remove unused imports and code** before committing
- **Don't create abstractions** for single implementations
- **Avoid generic parameters** when only one type is used

**Examples:**

```python
# ❌ BAD - Hypothetical features
@dataclass
class TrainingJob:
    job_id: str
    status: str
    # Hypothetical future features:
    scheduled_time: Optional[datetime] = None
    retry_count: int = 0
    webhook_url: Optional[str] = None
    notification_email: Optional[str] = None

# ✅ GOOD - Only current requirements
@dataclass
class TrainingJob:
    job_id: str
    status: str
    created_at: datetime
    target_column: str
```

### 4. Single Responsibility Principle (SRP)

- **One class/function = one purpose** - should have only one reason to change
- **Separate concerns**: data access, business logic, presentation
- **Keep functions under 50 lines** when possible
- **Split large modules** into focused submodules

**Examples:**

```python
# ❌ BAD - Multiple responsibilities
class TrainingService:
    def train_model(self, dataset_id: str, target: str):
        # 1. Download data from S3
        data = self._download_from_s3(dataset_id)
        # 2. Preprocess
        processed = self._preprocess(data)
        # 3. Train
        model = self._train(processed, target)
        # 4. Save to S3
        self._save_model(model)
        # 5. Update DynamoDB
        self._update_job_status()
        # 6. Generate report
        self._generate_report()

# ✅ GOOD - Separated concerns
# services/s3_service.py
class S3Service:
    def download_dataset(self, dataset_id: str) -> pd.DataFrame: ...
    def upload_model(self, model: Any, key: str) -> str: ...

# services/dynamo_service.py
class DynamoService:
    def update_job_status(self, job_id: str, status: str) -> None: ...

# training/preprocessor.py
class Preprocessor:
    def preprocess(self, data: pd.DataFrame) -> pd.DataFrame: ...

# training/model_trainer.py
class ModelTrainer:
    def train(self, data: pd.DataFrame, target: str) -> Any: ...
```

### 5. Dependency Inversion Principle (DIP)

- **Depend on abstractions** (protocols/interfaces), not concrete implementations
- **Inject dependencies** via constructor or function parameters
- **Use protocols** for external services (AWS, APIs)
- **Facilitate testing** by making dependencies swappable

**Examples:**

```python
# ❌ BAD - Direct dependency on AWS
class JobService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')  # Tight coupling
    
    def get_job(self, job_id: str) -> dict:
        table = self.dynamodb.Table('jobs')
        return table.get_item(Key={'id': job_id})

# ✅ GOOD - Dependency injection
from typing import Protocol

class JobRepository(Protocol):
    def get(self, job_id: str) -> dict: ...
    def save(self, job: dict) -> None: ...

class DynamoJobRepository:
    def __init__(self, table_name: str):
        self._table = boto3.resource('dynamodb').Table(table_name)
    
    def get(self, job_id: str) -> dict:
        return self._table.get_item(Key={'id': job_id}).get('Item', {})

class JobService:
    def __init__(self, repository: JobRepository):
        self._repository = repository  # Abstraction injected
    
    def get_job(self, job_id: str) -> dict:
        return self._repository.get(job_id)
```

---

## II. Python Best Practices

### 1. Type Hints (PEP 484, 604)

- **Always annotate** function parameters and return types
- **Use `|` syntax** for unions (Python 3.10+): `str | None` instead of `Optional[str]`
- **Import from `typing`** for complex types: `Callable`, `TypeVar`, `Generic`
- **Use `TypedDict`** for dictionary shapes with known keys

**Examples:**

```python
# ❌ BAD - No type hints
def process_data(data, columns):
    result = []
    for col in columns:
        result.append(data[col].mean())
    return result

# ✅ GOOD - Fully typed
from typing import TypedDict

class ProcessingResult(TypedDict):
    column: str
    mean: float
    std: float

def process_data(
    data: pd.DataFrame,
    columns: list[str]
) -> list[ProcessingResult]:
    return [
        ProcessingResult(
            column=col,
            mean=float(data[col].mean()),
            std=float(data[col].std())
        )
        for col in columns
    ]
```

### 2. Error Handling

- **Catch specific exceptions** - never bare `except:`
- **Use custom exceptions** for domain-specific errors
- **Log errors with context** - include relevant IDs and state
- **Fail fast** - validate inputs early and raise clear errors

**Examples:**

```python
# ❌ BAD - Bare except, silent failure
def load_model(path):
    try:
        return joblib.load(path)
    except:  # Catches everything, hides bugs
        return None

# ✅ GOOD - Specific exceptions with context
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelLoadError(Exception):
    """Raised when model loading fails."""
    def __init__(self, path: str, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to load model from {path}: {reason}")

def load_model(path: str | Path) -> Any:
    path = Path(path)
    
    if not path.exists():
        raise ModelLoadError(str(path), "File not found")
    
    try:
        return joblib.load(path)
    except (pickle.UnpicklingError, EOFError) as e:
        logger.error(f"Corrupted model file: {path}", exc_info=True)
        raise ModelLoadError(str(path), f"Corrupted file: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error loading model: {path}", exc_info=True)
        raise ModelLoadError(str(path), str(e)) from e
```

### 3. Naming Conventions (PEP 8)

| Element | Convention | Example |
|---------|------------|---------|
| Modules | `lower_with_under` | `batch_service.py` |
| Classes | `CapWords` | `TrainingJob` |
| Functions | `lower_with_under` | `process_dataset()` |
| Constants | `CAPS_WITH_UNDER` | `MAX_RETRIES = 3` |
| Variables | `lower_with_under` | `job_status` |
| Private | `_leading_under` | `_internal_cache` |

### 4. Docstrings (PEP 257)

- **Use triple quotes** for all public modules, classes, and functions
- **First line**: brief summary ending with period
- **Args section**: describe each parameter with type
- **Returns section**: describe return value
- **Raises section**: list exceptions that may be raised

**Examples:**

```python
def train_model(
    data: pd.DataFrame,
    target_column: str,
    time_budget: int = 300
) -> tuple[Any, dict[str, float]]:
    """Train an AutoML model on the provided dataset.
    
    Uses FLAML to automatically select the best model and hyperparameters
    within the given time budget.
    
    Args:
        data: Input DataFrame with features and target.
        target_column: Name of the column to predict.
        time_budget: Maximum training time in seconds. Defaults to 300.
    
    Returns:
        A tuple of (trained_model, metrics_dict) where metrics_dict contains
        'accuracy', 'f1_score', and 'training_time' keys.
    
    Raises:
        ValueError: If target_column is not in data.
        TrainingError: If model training fails.
    """
```

### 5. Configuration Management

- **Use Pydantic Settings** for environment-based configuration
- **Never hardcode** secrets, URLs, or resource names
- **Validate at startup** - fail fast if config is invalid
- **Use `.env` files** for local development only

**Examples:**

```python
# ❌ BAD - Hardcoded values
def get_s3_client():
    return boto3.client(
        's3',
        region_name='us-east-1'  # Hardcoded
    )

bucket = 'my-datasets-bucket'  # Hardcoded

# ✅ GOOD - Configuration from environment
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    s3_bucket_datasets: str
    s3_bucket_models: str
    dynamodb_jobs_table: str
    
    model_config = {"env_file": ".env"}

@lru_cache
def get_settings() -> Settings:
    return Settings()

# Usage
settings = get_settings()
client = boto3.client('s3', region_name=settings.aws_region)
```

---

## III. FastAPI Patterns

### 1. Router Organization

- **One router per domain** (datasets, training, models)
- **Thin routers** - delegate logic to services
- **Use dependency injection** for services and settings
- **Define response models** for all endpoints

**Examples:**

```python
# routers/training.py
from fastapi import APIRouter, Depends, HTTPException, status
from ..models.schemas import TrainRequest, TrainResponse, JobResponse
from ..services.batch_service import BatchService

router = APIRouter(prefix="/train", tags=["training"])

@router.post("", response_model=TrainResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_training(
    request: TrainRequest,
    batch_service: BatchService = Depends()
) -> TrainResponse:
    """Start a new model training job."""
    job_id = await batch_service.submit_training_job(
        dataset_id=request.dataset_id,
        target_column=request.target_column,
        time_budget=request.time_budget
    )
    return TrainResponse(job_id=job_id, status="SUBMITTED")
```

### 2. Pydantic Schemas

- **Separate schemas** for request, response, and internal models
- **Use Field()** for validation and documentation
- **Define examples** in `model_config`
- **Use enums** for finite value sets

**Examples:**

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class JobStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

class TrainRequest(BaseModel):
    dataset_id: str = Field(..., min_length=1, description="ID of uploaded dataset")
    target_column: str = Field(..., min_length=1, description="Column to predict")
    time_budget: int = Field(default=300, ge=60, le=3600, description="Training time in seconds")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "dataset_id": "abc123",
                "target_column": "price",
                "time_budget": 300
            }]
        }
    }

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    metrics: dict[str, float] | None = None
```

### 3. Error Responses

- **Use HTTPException** with appropriate status codes
- **Create custom exception handlers** for domain errors
- **Include error details** in response body
- **Log errors** before raising

**Examples:**

```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class DatasetNotFoundError(Exception):
    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id

# Exception handler (in main.py)
@app.exception_handler(DatasetNotFoundError)
async def dataset_not_found_handler(request: Request, exc: DatasetNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"Dataset not found: {exc.dataset_id}"}
    )

# In router
@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str, dynamo: DynamoService = Depends()):
    dataset = await dynamo.get_dataset(dataset_id)
    if not dataset:
        logger.warning(f"Dataset not found: {dataset_id}")
        raise DatasetNotFoundError(dataset_id)
    return dataset
```

---

## IV. AWS Integration Patterns

### 1. Boto3 Best Practices

- **Reuse clients** - create once, use throughout request lifecycle
- **Handle pagination** for list operations
- **Use waiters** for async operations
- **Convert Decimals** when reading from DynamoDB

**Examples:**

```python
from decimal import Decimal
from typing import Any

def convert_decimals(obj: Any) -> Any:
    """Recursively convert Decimal to int/float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    return obj

def decimal_safe(value: float | int) -> Decimal:
    """Convert float/int to Decimal for DynamoDB storage."""
    return Decimal(str(value))
```

### 2. S3 Operations

- **Use presigned URLs** for client uploads/downloads
- **Set appropriate expiration** for presigned URLs
- **Use multipart upload** for files > 100MB
- **Include content type** for browser compatibility

**Examples:**

```python
def generate_upload_url(
    bucket: str,
    key: str,
    content_type: str = "text/csv",
    expiration: int = 3600
) -> str:
    """Generate presigned URL for file upload."""
    return self._client.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': bucket,
            'Key': key,
            'ContentType': content_type
        },
        ExpiresIn=expiration
    )
```

### 3. DynamoDB Operations

- **Use conditions** to prevent overwrites
- **Handle ConditionalCheckFailedException**
- **Use UpdateExpression** for partial updates
- **Create composite keys** for query efficiency

---

## V. Data Science Patterns

### 1. Pandas Best Practices

- **Use vectorized operations** over loops
- **Handle missing values** explicitly
- **Copy DataFrames** before modification when needed
- **Use categorical dtype** for low-cardinality columns

**Examples:**

```python
# ❌ BAD - Row-by-row iteration
for idx, row in df.iterrows():
    df.at[idx, 'normalized'] = row['value'] / row['value'].max()

# ✅ GOOD - Vectorized operation
df['normalized'] = df['value'] / df['value'].max()

# ❌ BAD - Modifying original
def preprocess(df):
    df.drop(columns=['id'], inplace=True)  # Mutates input!
    return df

# ✅ GOOD - Return new DataFrame
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=['id'])
```

### 2. Safe Numerical Operations

- **Guard against division by zero**
- **Handle NaN values** before calculations
- **Use appropriate defaults** for missing statistics

**Examples:**

```python
# ❌ BAD - Division by zero risk
def calculate_ratio(a: float, b: float) -> float:
    return a / b

# ✅ GOOD - Safe division
def calculate_ratio(a: float, b: float, default: float = 0.0) -> float:
    if b == 0:
        return default
    return a / b

# ❌ BAD - NaN propagation
median_value = df['column'].median()

# ✅ GOOD - Handle NaN
median_value = df['column'].median()
if pd.isna(median_value):
    median_value = 0.0  # or appropriate default
```

### 3. Model Persistence

- **Use joblib** for scikit-learn models
- **Include metadata** with saved models
- **Version model artifacts**
- **Test loading after saving**

---

## VI. Code Organization

### 1. Project Structure

```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── datasets.py
│   │   ├── training.py
│   │   └── models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── s3_service.py
│   │   ├── dynamo_service.py
│   │   └── batch_service.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py       # Settings, common utilities
├── training/
│   ├── train.py             # Entry point
│   ├── preprocessor.py
│   ├── model_trainer.py
│   └── training_report.py
├── requirements.txt
└── Dockerfile
```

### 2. Import Order (PEP 8)

```python
# 1. Standard library
import logging
import os
from datetime import datetime
from pathlib import Path

# 2. Third-party packages
import boto3
import pandas as pd
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# 3. Local imports
from ..models.schemas import JobResponse
from ..services.dynamo_service import DynamoService
```

---

## VII. Testing Patterns

### 1. Test Structure

- **Use pytest** as the test framework
- **Name tests descriptively**: `test_<function>_<scenario>_<expected>`
- **Use fixtures** for common setup
- **Mock external dependencies** (AWS, APIs)

**Examples:**

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_s3_client():
    with patch('boto3.client') as mock:
        yield mock.return_value

def test_upload_dataset_success(mock_s3_client):
    """Test successful dataset upload returns presigned URL."""
    mock_s3_client.generate_presigned_url.return_value = "https://..."
    
    service = S3Service()
    result = service.generate_upload_url("bucket", "key.csv")
    
    assert result.startswith("https://")
    mock_s3_client.generate_presigned_url.assert_called_once()

def test_upload_dataset_invalid_bucket_raises_error(mock_s3_client):
    """Test upload with invalid bucket raises ValueError."""
    mock_s3_client.generate_presigned_url.side_effect = ClientError(...)
    
    service = S3Service()
    with pytest.raises(ValueError, match="Invalid bucket"):
        service.generate_upload_url("", "key.csv")
```

---

## VIII. Remember

- **Type everything** - IDE support and bug prevention
- **Fail fast** - validate inputs, raise clear errors
- **Keep it simple** - avoid unnecessary abstraction
- **Test behavior** - not implementation details
- **Log with context** - include IDs and relevant state
- **Don't repeat** - extract common patterns
- **Document why** - code shows what, comments explain why
