# Scripts

Utility scripts for running AutoML operations locally. All scripts are cross-platform (Windows/Linux/Mac).

## Available Scripts

| Script | Purpose |
|--------|---------|
| `run-training-local.py` | Run training in local Docker container |
| `predict.py` | Make predictions using trained models |
| `generate_architecture_diagram.py` | Generate AWS architecture diagrams |

---

## Training Script

### `run-training-local.py`
Run training in local Docker container (for development/testing).

**Prerequisites:**
- Python 3.x installed
- Docker running
- AWS CLI configured
- `backend/.env` file configured (see `backend/.env.example`)

**Usage:**
```bash
# Basic usage
python scripts/run-training-local.py <dataset-id> <target-column>

# With options
python scripts/run-training-local.py abc123 loan_status --time-budget 120
python scripts/run-training-local.py abc123 loan_status --job-id my-test-job
```

**Options:**
| Option | Description |
|--------|-------------|
| `--job-id`, `-j` | Custom job ID (default: auto-generated) |
| `--time-budget`, `-t` | Training time in seconds (default: 60) |
| `--api-url`, `-u` | API URL (default: http://localhost:8000) |
| `--region`, `-r` | AWS region (default: us-east-1) |

---

## Prediction Script

### `predict.py`
Make predictions using trained models. Runs in Docker container with all required dependencies.

**Build the container (one time):**
```bash
docker build -f scripts/Dockerfile.predict -t automl-predict .
```

**Usage:**
```bash
# Show model info (features, importance, etc.)
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl --info

# Generate sample input JSON from model (auto-detects features)
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl --generate-sample /data/sample_input.json

# Single prediction with inline JSON
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl '{"age": 35, "credit_score": 720, ...}'

# Single prediction from JSON file
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl --json /data/sample_input.json

# Batch predictions from CSV
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl -i /data/test.csv -o /data/predictions.csv
```

**Options:**
| Option | Description |
|--------|-------------|
| `--info` | Display model information (features, importance, etc.) |
| `--generate-sample FILE`, `-g` | Generate sample input JSON based on model features |
| `--json FILE`, `-j` | Read input from JSON file |
| `--input FILE`, `-i` | Batch prediction from CSV |
| `--output FILE`, `-o` | Output CSV file (default: predictions.csv) |

**Shell Variables for Current Directory:**
| Shell | Variable |
|-------|----------|
| PowerShell | `${PWD}` |
| Bash/Linux | `$(pwd)` or `$PWD` |
| CMD | `%cd%` |

---

## Workflow Example

```bash
# 1. Build prediction container (one time)
docker build -f scripts/Dockerfile.predict -t automl-predict .

# 2. Check model info to see required features
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl --info

# 3. Generate sample input JSON (auto-detects features from model)
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl -g /data/sample_input.json

# 4. Edit sample_input.json with your actual values

# 5. Run prediction
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl --json /data/sample_input.json
```

---

## Docker Images

| Image | Size | Purpose |
|-------|------|---------|
| `automl-predict` | ~1.3GB | Run predictions |
| `automl-training` | ~1.4GB | Train models |

---

## Quick Reference

```bash
# Train locally
python scripts/run-training-local.py my-dataset-id target_column

# Build prediction container
docker build -f scripts/Dockerfile.predict -t automl-predict .

# Show model info
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl --info

# Generate sample input from model
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl -g /data/sample_input.json

# Run prediction
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl --json /data/sample_input.json

# Batch predictions
docker run --rm -v ${PWD}:/data automl-predict /data/model.pkl -i /data/test.csv -o /data/predictions.csv
```

---

## Architecture Diagrams

### `generate_architecture_diagram.py`
Generate AWS architecture diagrams for documentation using the Python `diagrams` library.

**Prerequisites:**
- Python 3.x installed
- Install diagrams library: `pip install diagrams`
- Graphviz installed: https://graphviz.org/download/

**Usage:**
```bash
python scripts/generate_architecture_diagram.py
```

**Output:**
Generates 5 PNG diagrams in `docs/diagrams/`:

| File | Description |
|------|-------------|
| `architecture-main.png` | Main architecture overview |
| `architecture-dataflow.png` | Data flow from upload to prediction |
| `architecture-cost.png` | AutoML Lite vs SageMaker cost comparison |
| `architecture-cicd.png` | CI/CD pipeline with GitHub Actions |
| `architecture-training.png` | Training container detail |

**Example:**
```bash
# Install dependencies (one time)
pip install diagrams
# Windows: winget install graphviz
# Mac: brew install graphviz
# Ubuntu: sudo apt install graphviz

# Generate diagrams
python scripts/generate_architecture_diagram.py
# Output: docs/diagrams/architecture-*.png (5 files)
```
