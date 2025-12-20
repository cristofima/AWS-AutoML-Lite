# GitHub Copilot Custom Instructions - Python Backend Code Review

These instructions guide GitHub Copilot in reviewing Python code to ensure adherence to clean code principles, SOLID design patterns, type safety, and Python best practices.

---

## Review Mindset

**Focus on:**

- Code maintainability and readability
- Type safety and error handling
- Security vulnerabilities
- Performance implications
- Adherence to established patterns

**Balance:**

- Be constructive, not just critical
- Prioritize issues by severity (Critical → Major → Minor → Nitpick)
- Suggest concrete improvements with examples
- Acknowledge good practices when present

---

## I. Core Design Principles Review

### 1. DRY (Don't Repeat Yourself) Violations

**Check for:**

- [ ] Duplicated logic across functions or classes
- [ ] Repeated AWS client creation
- [ ] Similar data transformations that could be unified
- [ ] Copy-pasted exception handling

**Examples of issues to flag:**

```python
# 🚨 CRITICAL - Duplicated S3 operations
def upload_model(bucket, key, data):
    client = boto3.client('s3')  # Created each time
    client.put_object(Bucket=bucket, Key=key, Body=data)

def upload_report(bucket, key, data):
    client = boto3.client('s3')  # Duplicated
    client.put_object(Bucket=bucket, Key=key, Body=data)

# ✅ SUGGESTION: Extract to S3Service class
class S3Service:
    def __init__(self):
        self._client = boto3.client('s3')
    
    def upload(self, bucket: str, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=bucket, Key=key, Body=data)
```

### 2. KISS (Keep It Simple, Stupid) Violations

**Check for:**

- [ ] Over-engineered patterns for simple problems
- [ ] Unnecessary class hierarchies
- [ ] Complex nested comprehensions
- [ ] Overly abstract code that sacrifices readability

**Examples of issues to flag:**

```python
# 🚨 MAJOR - Over-engineered for simple task
class DataProcessorFactory:
    _processors: dict[str, Type[IProcessor]] = {
        'csv': CSVProcessor,
        'json': JSONProcessor,
    }
    
    @classmethod
    def create(cls, data_type: str) -> IProcessor:
        return cls._processors.get(data_type, DefaultProcessor)()

# ✅ SUGGESTION: Simple function is sufficient
def process_data(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    if data_type == 'csv':
        return df.dropna()
    return df
```

### 3. Single Responsibility Principle (SRP) Violations

**Check for:**

- [ ] Functions doing multiple unrelated things
- [ ] Classes with mixed concerns (data access + business logic + formatting)
- [ ] Large functions (>50 lines) that should be split
- [ ] Files with unrelated exports

**Examples of issues to flag:**

```python
# 🚨 CRITICAL - Multiple responsibilities
def train_and_save_and_notify(dataset_id: str, target: str):
    # Downloads data
    data = boto3.client('s3').get_object(...)
    # Preprocesses
    data = data.dropna()
    # Trains
    model = train_model(data, target)
    # Saves
    boto3.client('s3').put_object(...)
    # Updates DB
    boto3.resource('dynamodb').Table('jobs').update_item(...)
    # Sends notification
    boto3.client('sns').publish(...)

# ✅ SUGGESTION: Separate concerns into services
# s3_service.py - data access
# dynamo_service.py - database operations
# training_service.py - ML logic
# notification_service.py - notifications
```

### 4. Dependency Inversion Principle (DIP) Violations

**Check for:**

- [ ] Direct boto3 client creation in business logic
- [ ] Hardcoded external service dependencies
- [ ] Classes tightly coupled to specific AWS services
- [ ] No abstraction layers for external services

**Examples of issues to flag:**

```python
# 🚨 CRITICAL - Tight coupling to AWS
class JobService:
    def get_job(self, job_id: str) -> dict:
        table = boto3.resource('dynamodb').Table('jobs')  # Direct dependency
        return table.get_item(Key={'id': job_id})['Item']

# ✅ SUGGESTION: Inject dependency
from typing import Protocol

class JobRepository(Protocol):
    def get(self, job_id: str) -> dict: ...

class JobService:
    def __init__(self, repository: JobRepository):
        self._repository = repository
    
    def get_job(self, job_id: str) -> dict:
        return self._repository.get(job_id)
```

---

## II. Type Safety Review

### 1. Missing Type Hints

**Check for:**

- [ ] Functions without parameter type hints
- [ ] Functions without return type hints
- [ ] `Any` type used without justification
- [ ] Inconsistent typing in similar functions

**Examples of issues to flag:**

```python
# 🚨 MAJOR - No type hints
def process_data(data, columns):
    result = []
    for col in columns:
        result.append(data[col].mean())
    return result

# ✅ SUGGESTION: Add comprehensive type hints
def process_data(
    data: pd.DataFrame,
    columns: list[str]
) -> list[float]:
    return [float(data[col].mean()) for col in columns]
```

### 2. Improper None Handling

**Check for:**

- [ ] Missing `| None` for nullable parameters
- [ ] No null checks before attribute access
- [ ] Implicit None returns without annotation
- [ ] `Optional[X]` instead of `X | None` (Python 3.10+)

**Examples of issues to flag:**

```python
# 🚨 MAJOR - Missing None handling
def get_user_name(user: dict) -> str:
    return user['profile']['name']  # KeyError if missing

# ✅ SUGGESTION: Safe access with default
def get_user_name(user: dict) -> str:
    return user.get('profile', {}).get('name', 'Unknown')

# Or with explicit None type
def get_user_name(user: dict) -> str | None:
    profile = user.get('profile')
    return profile.get('name') if profile else None
```

---

## III. Error Handling Review

### 1. Bare Except Clauses

**Check for:**

- [ ] `except:` without exception type
- [ ] `except Exception:` when specific exceptions are known
- [ ] Silent exception swallowing
- [ ] Missing error logging

**Examples of issues to flag:**

```python
# 🚨 CRITICAL - Bare except hides bugs
try:
    model = joblib.load(path)
except:
    model = None

# ✅ SUGGESTION: Catch specific exceptions
try:
    model = joblib.load(path)
except FileNotFoundError:
    logger.warning(f"Model not found: {path}")
    raise ModelNotFoundError(path)
except (pickle.UnpicklingError, EOFError) as e:
    logger.error(f"Corrupted model: {path}", exc_info=True)
    raise ModelCorruptedError(path, str(e)) from e
```

### 2. Missing Error Context

**Check for:**

- [ ] Exceptions without meaningful messages
- [ ] Missing `from e` in exception chaining
- [ ] No logging before raising
- [ ] Generic error messages

**Examples of issues to flag:**

```python
# 🚨 MAJOR - No context
def load_dataset(dataset_id: str) -> pd.DataFrame:
    try:
        return pd.read_csv(f"s3://.../datasets/{dataset_id}.csv")
    except Exception:
        raise ValueError("Failed")  # Useless message

# ✅ SUGGESTION: Include context
def load_dataset(dataset_id: str) -> pd.DataFrame:
    try:
        return pd.read_csv(f"s3://.../datasets/{dataset_id}.csv")
    except FileNotFoundError:
        raise DatasetNotFoundError(
            f"Dataset '{dataset_id}' not found in S3"
        )
    except pd.errors.ParserError as e:
        raise DatasetParseError(
            f"Failed to parse dataset '{dataset_id}': {e}"
        ) from e
```

---

## IV. Security Review

### 1. Hardcoded Secrets

**Check for:**

- [ ] API keys, passwords in code
- [ ] AWS credentials hardcoded
- [ ] Bucket/table names hardcoded
- [ ] URLs with embedded credentials

**Examples of issues to flag:**

```python
# 🚨 CRITICAL - Hardcoded credentials
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"  # Never do this
client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY)

# 🚨 CRITICAL - Hardcoded resource names
BUCKET = "my-production-bucket"  # Should be from config

# ✅ SUGGESTION: Use environment/settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    s3_bucket: str
    
    model_config = {"env_file": ".env"}

settings = Settings()
bucket = settings.s3_bucket
```

### 2. Input Validation

**Check for:**

- [ ] Unvalidated user input used in file paths
- [ ] SQL injection vulnerabilities (if using raw SQL)
- [ ] Missing request body validation
- [ ] Unbounded list/string sizes

**Examples of issues to flag:**

```python
# 🚨 CRITICAL - Path traversal vulnerability
@router.get("/files/{filename}")
def get_file(filename: str):
    return open(f"/data/{filename}").read()  # ../../../etc/passwd

# ✅ SUGGESTION: Validate and sanitize
from pathlib import Path

@router.get("/files/{filename}")
def get_file(filename: str):
    base_path = Path("/data").resolve()
    file_path = (base_path / filename).resolve()
    
    if not file_path.is_relative_to(base_path):
        raise HTTPException(400, "Invalid filename")
    
    return file_path.read_text()
```

---

## V. Performance Review

### 1. Inefficient Data Operations

**Check for:**

- [ ] Row-by-row DataFrame iteration
- [ ] Unnecessary DataFrame copies
- [ ] Loading full dataset when only subset needed
- [ ] N+1 query patterns

**Examples of issues to flag:**

```python
# 🚨 MAJOR - Row-by-row iteration
for idx, row in df.iterrows():
    df.at[idx, 'normalized'] = row['value'] / max_value

# ✅ SUGGESTION: Vectorized operation
df['normalized'] = df['value'] / max_value
```

### 2. Resource Leaks

**Check for:**

- [ ] Files opened without context manager
- [ ] Database connections not closed
- [ ] Large objects not cleaned up
- [ ] Missing cleanup in error paths

**Examples of issues to flag:**

```python
# 🚨 MAJOR - File not closed on error
def read_config(path: str) -> dict:
    f = open(path)
    data = json.load(f)
    f.close()  # Never reached if json.load fails
    return data

# ✅ SUGGESTION: Use context manager
def read_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)
```

---

## VI. Code Quality Review

### 1. Naming Issues

**Check for:**

- [ ] Single-letter variable names (except `i`, `j`, `x`, `y` in small scopes)
- [ ] Misleading names that don't match behavior
- [ ] Inconsistent naming conventions
- [ ] Abbreviations that aren't obvious

**Examples of issues to flag:**

```python
# 🚨 MINOR - Poor naming
def p(d, c):  # What does this do?
    r = []
    for x in c:
        r.append(d[x])
    return r

# ✅ SUGGESTION: Descriptive names
def extract_columns(data: pd.DataFrame, columns: list[str]) -> list:
    return [data[col] for col in columns]
```

### 2. Documentation Issues

**Check for:**

- [ ] Public functions without docstrings
- [ ] Outdated docstrings that don't match code
- [ ] Missing parameter descriptions
- [ ] Missing return type documentation

**Examples of issues to flag:**

```python
# 🚨 MINOR - Missing docstring
def calculate_metrics(predictions: np.ndarray, actual: np.ndarray) -> dict:
    return {
        'accuracy': accuracy_score(actual, predictions),
        'f1': f1_score(actual, predictions, average='weighted')
    }

# ✅ SUGGESTION: Add docstring
def calculate_metrics(
    predictions: np.ndarray,
    actual: np.ndarray
) -> dict[str, float]:
    """Calculate classification metrics for model evaluation.
    
    Args:
        predictions: Model predictions array.
        actual: Ground truth labels array.
    
    Returns:
        Dictionary with 'accuracy' and 'f1' scores.
    """
    return {
        'accuracy': accuracy_score(actual, predictions),
        'f1': f1_score(actual, predictions, average='weighted')
    }
```

---

## VII. AWS-Specific Review

### 1. DynamoDB Issues

**Check for:**

- [ ] Decimal not used for numeric values
- [ ] Missing error handling for ConditionalCheckFailed
- [ ] Unbounded scans without pagination
- [ ] Missing TTL for temporary data

**Examples of issues to flag:**

```python
# 🚨 MAJOR - Float causes DynamoDB error
table.put_item(Item={
    'id': job_id,
    'accuracy': 0.95  # TypeError: Float not supported
})

# ✅ SUGGESTION: Convert to Decimal
from decimal import Decimal

table.put_item(Item={
    'id': job_id,
    'accuracy': Decimal(str(0.95))
})
```

### 2. S3 Issues

**Check for:**

- [ ] Missing content type on uploads
- [ ] Hardcoded bucket names
- [ ] No error handling for missing objects
- [ ] Presigned URLs without expiration consideration

---

## VIII. Testing Review

### 1. Test Quality

**Check for:**

- [ ] Tests without assertions
- [ ] Tests that test implementation, not behavior
- [ ] Missing edge case tests
- [ ] No mocking of external services

**Examples of issues to flag:**

```python
# 🚨 MAJOR - No assertion
def test_upload():
    service = S3Service()
    service.upload("bucket", "key", b"data")
    # Test passes even if upload fails silently

# ✅ SUGGESTION: Verify behavior
def test_upload_success(mock_s3_client):
    service = S3Service()
    service.upload("bucket", "key", b"data")
    
    mock_s3_client.put_object.assert_called_once_with(
        Bucket="bucket",
        Key="key",
        Body=b"data"
    )
```

---

## IX. Review Checklist Summary

### Critical (Must Fix)

- [ ] Security vulnerabilities (hardcoded secrets, SQL injection)
- [ ] Bare except clauses hiding bugs
- [ ] Missing type hints on public API
- [ ] DynamoDB Decimal conversion errors

### Major (Should Fix)

- [ ] DRY violations (duplicated logic)
- [ ] SRP violations (functions doing too much)
- [ ] Missing error handling context
- [ ] Inefficient data operations
- [ ] Resource leaks

### Minor (Nice to Fix)

- [ ] Naming improvements
- [ ] Missing docstrings
- [ ] KISS violations (over-engineering)
- [ ] Import organization

### Nitpick (Optional)

- [ ] Code style preferences
- [ ] Comment formatting
- [ ] Whitespace issues
