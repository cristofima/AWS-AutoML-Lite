# Unit Testing Analysis for AWS AutoML Lite

This document outlines the unit testing strategy for the AWS AutoML Lite project and documents the **implemented** test suite.

**Status:** ✅ **IMPLEMENTED** (December 2025)

---

## Table of Contents

1. [Implementation Summary](#implementation-summary)
2. [Testing Philosophy](#testing-philosophy)
3. [Testing Stack](#testing-stack)
4. [Folder Structure](#folder-structure)
5. [Test Categories](#test-categories)
6. [Coverage Summary](#coverage-summary)
7. [GitHub Actions Integration](#github-actions-integration)
8. [Running Tests Locally](#running-tests-locally)
9. [Lessons Learned](#lessons-learned)

---

## Implementation Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 263 |
| **API Tests** | 104 |
| **Training Tests** | 159 |
| **API Coverage** | 69% |
| **Training Coverage** | 53%+ |
| **CI/CD Integration** | ✅ Both pipelines |

All tests run automatically before deployment in the respective CI/CD pipelines.

---

## Testing Philosophy

Following CI/CD best practices from Microsoft Learn:

> "Implement unit tests for business logic using libraries, such as pytest for Python. Validate functionality with automated tests that run on every PR."

### Core Principles

1. **Automate Testing** - Run tests on every pull request before merge ✅
2. **Test Business Logic** - Focus on logic that can break silently ✅
3. **Isolate from AWS** - Mock boto3 clients for fast, reliable tests ✅
4. **Fail Fast** - Tests should run quickly and fail clearly ✅
5. **Version Control Everything** - Tests are part of the codebase ✅

---

## Testing Stack

Implemented stack in `requirements-dev.txt`:

| Package | Version | Purpose |
|---------|---------|---------|
| **pytest** | 8.3.4 | Test framework with fixtures |
| **pytest-cov** | 6.0.0 | Coverage reports |
| **httpx** | 0.27.2 | FastAPI TestClient (pinned for Starlette compatibility) |
| **moto** | 5.0.26 | AWS service mocking (S3, DynamoDB) |

> ⚠️ **Important:** Use `httpx==0.27.2`, not 0.28.0. Version 0.28.0 has breaking changes incompatible with Starlette 0.35.1 (bundled with FastAPI 0.109.0).

---

## Folder Structure

Implemented test organization:

```
backend/
├── api/
│   ├── main.py
│   ├── models/
│   ├── routers/
│   ├── services/
│   └── utils/
├── training/                   # Modular ML package
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── core/                   # Core ML components
│   │   ├── preprocessor.py
│   │   ├── trainer.py
│   │   └── exporter.py
│   ├── reports/                # Report generation
│   │   ├── eda.py
│   │   └── training.py
│   └── utils/                  # Shared utilities
│       └── detection.py
├── tests/                      # ✅ Implemented
│   ├── __init__.py
│   ├── pytest.ini              # Pytest configuration
│   │
│   ├── api/                    # API tests (104 tests)
│   │   ├── __init__.py
│   │   ├── conftest.py                      # API test fixtures
│   │   ├── test_endpoints.py                # 39 endpoint tests
│   │   ├── test_schemas.py                  # 23 schema validation tests
│   │   ├── test_dynamo_service.py           # 9 DynamoDB tests
│   │   ├── test_s3_service.py               # 12 S3 tests
│   │   └── test_services_integration.py     # 21 moto integration tests
│   │
│   └── training/               # Training tests (159 tests)
│       ├── __init__.py
│       ├── conftest.py                      # Training test fixtures
│       ├── unit/                            # Pure unit tests
│       │   ├── test_preprocessor.py         # Preprocessing tests
│       │   ├── test_column_detection.py     # Column detection tests
│       │   ├── test_detect_problem_type.py  # Problem type detection
│       │   ├── test_eda.py                  # EDA report tests
│       │   └── test_training_report.py      # Training report tests
│       └── integration/                     # Training integration tests
│
├── requirements.txt
└── requirements-dev.txt        # ✅ Testing dependencies
```

### Configuration Files

**`backend/tests/pytest.ini`**:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: marks tests as unit tests (fast, no external deps)
    api: marks tests as API tests (use TestClient)
    integration: marks tests requiring mocked AWS services
asyncio_mode = auto
```

**`backend/tests/conftest.py`**:
```python
"""
Shared pytest fixtures for all tests.
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Add backend modules to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "api"))
sys.path.insert(0, str(backend_path / "training"))


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing preprocessing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'customer_id': ['C001', 'C002', 'C003', 'C004', 'C005'],
        'age': [25, 30, 35, 40, 45],
        'income': [50000.0, 60000.0, 70000.0, 80000.0, 90000.0],
        'category': ['A', 'B', 'A', 'C', 'B'],
        'target': [0, 1, 0, 1, 1]
    })


@pytest.fixture
def classification_target():
    """Binary classification target."""
    return pd.Series([0, 1, 0, 1, 1, 0, 1, 0, 0, 1])


@pytest.fixture
def regression_target():
    """Continuous regression target."""
    return pd.Series([35.5, 42.1, 38.7, 41.2, 50.8, 33.4, 45.6, 39.2, 44.1, 37.8])
```

---

## Test Categories

### 1. Unit Tests (Highest Value)

Pure logic tests that run fast without external dependencies.

| Module | Functions to Test | Why High Value |
|--------|-------------------|----------------|
| `training/utils.py` | `detect_problem_type()` | Core ML decision - wrong detection = wrong model type |
| `training/utils.py` | `is_id_column()` | ID columns in training = data leakage |
| `training/utils.py` | `is_constant_column()` | Constant columns cause training failures |
| `training/utils.py` | `is_high_cardinality_categorical()` | High cardinality = overfitting risk |
| `training/preprocessor.py` | `detect_useless_columns()` | Column filtering affects model quality |
| `api/models/schemas.py` | Pydantic validation | Invalid data should fail at API boundary |

### 2. API Tests (Medium Value)

FastAPI endpoint tests using `TestClient`.

| Endpoint | Test Cases |
|----------|------------|
| `GET /health` | Returns 200, contains expected fields |
| `POST /upload` | Generates presigned URL, validates filename |
| `POST /train` | Validates required fields, creates job |
| `GET /jobs/{job_id}` | Returns job details, handles 404 |
| `POST /predict` | Validates input shape, returns prediction |

### 3. Integration Tests (Lower Priority)

Tests with mocked AWS services using `moto`.

| Service | Test Cases |
|---------|------------|
| `DynamoDBService` | CRUD operations, error handling |
| `S3Service` | Upload/download, presigned URLs |
| `BatchService` | Job submission, environment variables |

---

## High-Value Tests Identified

### Priority 1: Problem Type Detection (Critical)

Wrong problem type detection leads to training wrong model type.

**Test file**: `tests/unit/test_detect_problem_type.py`

```python
import pytest
import pandas as pd
from training.utils import detect_problem_type


class TestDetectProblemType:
    """Tests for detect_problem_type() - critical for correct model selection."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("target,expected", [
        # Binary classification (integers 0,1)
        (pd.Series([0, 1, 0, 1, 1]), 'classification'),
        
        # Multi-class classification (integers 0,1,2)
        (pd.Series([0, 1, 2, 0, 1, 2]), 'classification'),
        
        # Regression (float with decimals)
        (pd.Series([35.5, 42.1, 38.7, 41.2]), 'regression'),
        
        # String labels (always classification)
        (pd.Series(['cat', 'dog', 'bird', 'cat']), 'classification'),
        
        # Boolean (classification)
        (pd.Series([True, False, True, False]), 'classification'),
        
        # Low cardinality encoded as float but .0 (should be classification)
        (pd.Series([0.0, 1.0, 2.0, 0.0, 1.0]), 'classification'),
        
        # High cardinality integer (regression - prices, counts)
        (pd.Series(list(range(100))), 'regression'),
        
        # Continuous percentages (regression)
        (pd.Series([0.1, 0.23, 0.45, 0.67, 0.89]), 'regression'),
    ])
    def test_detect_problem_type_parametrized(self, target, expected):
        """Test various target distributions are correctly classified."""
        assert detect_problem_type(target) == expected
    
    @pytest.mark.unit
    def test_empty_series_defaults_to_classification(self):
        """Empty series should default to classification (safe fallback)."""
        assert detect_problem_type(pd.Series([], dtype=float)) == 'classification'
```

### Priority 2: ID Column Detection (Prevents Data Leakage)

ID columns in training cause overfitting and data leakage.

**Test file**: `tests/unit/test_id_detection.py`

```python
import pytest
import pandas as pd
from training.utils import is_id_column


class TestIsIdColumn:
    """Tests for is_id_column() - prevents data leakage."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("col_name,values,expected", [
        # Name-based detection
        ('id', [1, 2, 3, 4, 5], True),
        ('customer_id', [101, 102, 103, 104, 105], True),
        ('user_id', [1, 2, 3, 4, 5], True),
        ('order_id', [1001, 1002, 1003, 1004, 1005], True),
        ('transaction_id', [1, 2, 3, 4, 5], True),
        ('uuid', ['a1', 'b2', 'c3', 'd4', 'e5'], True),
        
        # NOT ID columns
        ('age', [25, 30, 35, 40, 45], False),
        ('income', [50000, 60000, 70000, 80000, 90000], False),
        ('price', [10.5, 20.5, 30.5, 40.5, 50.5], False),
        ('category', ['A', 'B', 'C', 'A', 'B'], False),
    ])
    def test_id_column_detection(self, col_name, values, expected):
        """Test ID column detection by name and data patterns."""
        series = pd.Series(values)
        assert is_id_column(col_name, series) == expected
    
    @pytest.mark.unit
    def test_sequential_integers_detected_as_id(self):
        """Sequential integers without ID name should be detected."""
        series = pd.Series(list(range(1, 101)))  # 1, 2, 3, ..., 100
        # This depends on implementation - may or may not flag
        # Adjust based on actual behavior
        assert is_id_column('row_num', series) == True
```

### Priority 3: API Health and Validation

**Test file**: `tests/api/test_health.py`

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with mocked settings."""
    # Mock environment variables before importing app
    import os
    os.environ.setdefault('AWS_REGION', 'us-east-1')
    os.environ.setdefault('S3_BUCKET_DATASETS', 'test-datasets')
    os.environ.setdefault('S3_BUCKET_MODELS', 'test-models')
    os.environ.setdefault('S3_BUCKET_REPORTS', 'test-reports')
    os.environ.setdefault('DYNAMODB_DATASETS_TABLE', 'test-datasets-table')
    os.environ.setdefault('DYNAMODB_JOBS_TABLE', 'test-jobs-table')
    os.environ.setdefault('CORS_ORIGINS', 'http://localhost:3000')
    os.environ.setdefault('BATCH_JOB_DEFINITION', 'test-job-def')
    os.environ.setdefault('BATCH_JOB_QUEUE', 'test-job-queue')
    
    from api.main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.api
    def test_root_endpoint(self, client):
        """GET / returns healthy status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    @pytest.mark.api
    def test_health_check(self, client):
        """GET /health returns detailed health info."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "automl-api"
```

### Priority 4: Pydantic Schema Validation

**Test file**: `tests/unit/test_schemas.py`

```python
import pytest
from pydantic import ValidationError
from datetime import datetime


class TestSchemaValidation:
    """Test Pydantic schema validation."""
    
    @pytest.mark.unit
    def test_train_request_valid(self):
        """Valid training request should pass validation."""
        from api.models.schemas import TrainRequest
        
        request = TrainRequest(
            dataset_id="abc123",
            target_column="price",
            time_budget=300
        )
        assert request.dataset_id == "abc123"
        assert request.target_column == "price"
        assert request.time_budget == 300
    
    @pytest.mark.unit
    def test_train_request_missing_required(self):
        """Missing required fields should raise ValidationError."""
        from api.models.schemas import TrainRequest
        
        with pytest.raises(ValidationError) as exc_info:
            TrainRequest(target_column="price")  # Missing dataset_id
        
        assert "dataset_id" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_train_request_invalid_time_budget(self):
        """Time budget outside range should raise ValidationError."""
        from api.models.schemas import TrainRequest
        
        with pytest.raises(ValidationError):
            TrainRequest(
                dataset_id="abc123",
                target_column="price",
                time_budget=10  # Too low (min is 60)
            )
```

---

## GitHub Actions Integration

Create new workflow for running tests on PRs.

**`.github/workflows/test-backend.yml`**:

```yaml
# Run Backend Tests
# Triggers on PRs to main/dev affecting backend code

name: Backend Tests

on:
  pull_request:
    branches: [main, dev]
    paths:
      - 'backend/**'
      - '.github/workflows/test-backend.yml'
  workflow_dispatch:

jobs:
  test:
    name: Run Unit Tests
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit -v --tb=short --junitxml=junit/test-results.xml --cov=. --cov-report=xml
      
      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: backend/junit/test-results.xml
      
      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: backend/coverage.xml
      
      - name: Post coverage to PR
        uses: codecov/codecov-action@v4
        if: github.event_name == 'pull_request'
        with:
          files: backend/coverage.xml
          fail_ci_if_error: false
          token: ${{ secrets.CODECOV_TOKEN }}
```

---

## Implementation Priority

Based on value vs effort analysis:

| Priority | Test Area | Value | Effort | Files |
|----------|-----------|-------|--------|-------|
| 🔴 **P1** | Problem type detection | **Critical** - Wrong model type | Low | 1 file |
| 🔴 **P1** | ID column detection | **High** - Data leakage | Low | 1 file |
| 🟡 **P2** | Health endpoints | Medium - Verify deployment | Low | 1 file |
| 🟡 **P2** | Schema validation | Medium - Catch bad input | Low | 1 file |
| 🟢 **P3** | Preprocessing pipeline | Medium - End-to-end flow | Medium | 1 file |
| 🟢 **P3** | DynamoDB service (mocked) | Low - Complex mocking | High | 1 file |
| ⚪ **P4** | S3 service (mocked) | Low - Boto3 wrapper | High | 1 file |

### Recommended Sprint Plan

**Sprint 1 (P1 - Immediate)**:
- [ ] Create `tests/` folder structure
- [ ] Add `requirements-dev.txt`
- [ ] Write `test_detect_problem_type.py`
- [ ] Write `test_id_detection.py`
- [ ] Create GitHub Actions workflow

**Sprint 2 (P2 - Next)**:
- [ ] Write `test_health.py`
- [ ] Write `test_schemas.py`
- [ ] Add coverage reporting

**Sprint 3 (P3 - Later)**:
- [ ] Write `test_preprocessor.py`
- [ ] Add moto-based integration tests

---

## Example Tests

### Complete Test Example: `test_detect_problem_type.py`

```python
"""
Unit tests for detect_problem_type() function.

This is one of the most critical functions in the training pipeline.
Wrong detection leads to training the wrong model type.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add training module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "training"))

from utils import detect_problem_type


class TestDetectProblemTypeClassification:
    """Test cases where classification is expected."""
    
    @pytest.mark.unit
    def test_binary_integers(self):
        """Binary 0/1 integers should be classification."""
        target = pd.Series([0, 1, 0, 1, 1, 0, 1, 0])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_multiclass_integers(self):
        """Multi-class integers (0,1,2,3) should be classification."""
        target = pd.Series([0, 1, 2, 3, 0, 1, 2, 3])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_string_labels(self):
        """String labels should always be classification."""
        target = pd.Series(['cat', 'dog', 'bird', 'cat', 'dog'])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_boolean_target(self):
        """Boolean target should be classification."""
        target = pd.Series([True, False, True, False, True])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_float_integers(self):
        """Float values that are whole numbers (1.0, 2.0) should be classification."""
        target = pd.Series([0.0, 1.0, 2.0, 0.0, 1.0, 2.0])
        assert detect_problem_type(target) == 'classification'


class TestDetectProblemTypeRegression:
    """Test cases where regression is expected."""
    
    @pytest.mark.unit
    def test_continuous_floats(self):
        """Continuous float values should be regression."""
        target = pd.Series([35.5, 42.1, 38.7, 41.2, 50.8])
        assert detect_problem_type(target) == 'regression'
    
    @pytest.mark.unit
    def test_prices(self):
        """Price values (many unique floats) should be regression."""
        target = pd.Series([199.99, 249.50, 89.99, 349.00, 129.95])
        assert detect_problem_type(target) == 'regression'
    
    @pytest.mark.unit
    def test_high_cardinality_integers(self):
        """Many unique integers (100+) should be regression."""
        target = pd.Series(list(range(100)))
        assert detect_problem_type(target) == 'regression'
    
    @pytest.mark.unit
    def test_percentages(self):
        """Percentage values (0.0-1.0 with decimals) should be regression."""
        target = pd.Series([0.15, 0.23, 0.45, 0.67, 0.89, 0.12])
        assert detect_problem_type(target) == 'regression'


class TestDetectProblemTypeEdgeCases:
    """Edge cases and boundary conditions."""
    
    @pytest.mark.unit
    def test_empty_series(self):
        """Empty series should default to classification."""
        target = pd.Series([], dtype=float)
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_single_value(self):
        """Single value series should be classification."""
        target = pd.Series([1])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_all_same_value(self):
        """Constant values should be classification."""
        target = pd.Series([5, 5, 5, 5, 5])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_with_nan_values(self):
        """Series with NaN values should still work."""
        target = pd.Series([0, 1, np.nan, 0, 1, np.nan, 0])
        result = detect_problem_type(target)
        assert result in ['classification', 'regression']  # Should not raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Coverage Summary

Current test coverage as of December 2025:

### API Module (69% coverage)

| File | Statements | Coverage | Notes |
|------|------------|----------|-------|
| `models/schemas.py` | 147 | 100% | Full Pydantic validation |
| `routers/datasets.py` | 53 | 91% | CRUD operations |
| `routers/training.py` | 51 | 90% | Training endpoints |
| `routers/upload.py` | 16 | 88% | Upload flow |
| `routers/models.py` | 150 | 65% | Job management |
| `routers/predict.py` | 146 | 23% | ONNX inference (complex mocking) |
| `services/s3_service.py` | 67 | 73% | S3 operations |
| `services/dynamo_service.py` | 143 | 64% | DynamoDB operations |

### Training Module (53% coverage)

| File | Coverage | Notes |
|------|----------|-------|
| `utils/detection.py` | 94% | Detection functions |
| `reports/eda.py` | 94% | EDA report generation |
| `reports/training.py` | 91% | Training report |
| `core/preprocessor.py` | 63% | Data preprocessing |
| `core/trainer.py` | 28% | FLAML training (requires mocking) |
| `core/exporter.py` | 0% | ONNX export (requires FLAML) |

---

## GitHub Actions Integration

Tests run automatically in CI/CD before deployment:

### API Pipeline (`deploy-lambda-api.yml`)

```yaml
- name: Run API tests
  run: |
    cd backend
    pytest tests/api \
      -v \
      --tb=short \
      --junitxml=test-results/api-tests.xml \
      --cov=api \
      --cov-report=xml:coverage/api-coverage.xml \
      --cov-report=term-missing
```

### Training Pipeline (`deploy-training-container.yml`)

```yaml
- name: Run training tests
  run: |
    cd backend
    pytest tests/training \
      -v \
      --tb=short \
      --junitxml=test-results/training-tests.xml \
      --cov=training \
      --cov-report=xml:coverage/training-coverage.xml \
      --cov-report=term-missing
```

### Test Reporting

Both pipelines include:
- `dorny/test-reporter` - Publishes test results to GitHub UI
- `irongut/CodeCoverageSummary` - Adds coverage summary to workflow

---

## Running Tests Locally

```bash
# Navigate to backend
cd backend

# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run API tests only (with coverage)
pytest tests/api --cov=api --cov-report=term-missing

# Run training tests only (with coverage)
pytest tests/training --cov=training --cov-report=term-missing

# Run specific test file
pytest tests/api/test_endpoints.py -v

# Run with verbose output and stop on first failure
pytest -v -x

# Generate HTML coverage report
pytest tests/api --cov=api --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Lessons Learned

Key challenges encountered during implementation:

### 1. httpx Version Incompatibility
- **Problem:** `httpx==0.28.0` broke TestClient with Starlette 0.35.1
- **Solution:** Pin to `httpx==0.27.2`

### 2. Router Service Mocking
- **Problem:** Mocking `api.services.dynamo_service.DynamoDBService.method` didn't work
- **Solution:** Use `patch.object(router_module.service_instance, 'method')`

### 3. Pydantic vs Endpoint Validation
- **Problem:** Expected 400 for invalid input, got 422
- **Solution:** Pydantic validation returns 422 (Unprocessable Entity), not 400

### 4. DynamoDB Decimal Conversion
- **Problem:** DynamoDB returns `Decimal` types, breaking JSON serialization
- **Solution:** Use `convert_decimals()` utility function

See [LESSONS_LEARNED.md](./LESSONS_LEARNED.md#8-unit--integration-testing) for detailed explanations.

---

## Summary

The testing implementation covers:

1. ✅ **104 API tests** - Endpoints, schemas, services
2. ✅ **159 Training tests** - Preprocessing, utils, EDA, training reports
3. ✅ **CI/CD integration** - Tests run before every deployment
4. ✅ **Coverage reporting** - Published to GitHub Actions

The test suite provides confidence that:
- Problem type detection works correctly (classification vs regression)
- ID columns are properly detected and excluded
- API endpoints validate input correctly
- AWS service integrations work as expected (via moto)

---

## References

- [Microsoft Learn - CI/CD Best Practices](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/ci-cd/best-practices)
- [pytest Official Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [moto - Mock AWS Services](https://github.com/getmoto/moto)
- [LESSONS_LEARNED.md - Testing Section](./LESSONS_LEARNED.md#8-unit--integration-testing)
