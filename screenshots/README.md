# Screenshots

Visual documentation of AWS AutoML Lite's user interface and generated reports.

> **📌 Note:** Screenshots are organized by problem type. Common UI elements (same for both classification and regression) are in the root folder, while problem-specific screenshots are in their respective subfolders.

## 📁 Folder Structure

```
screenshots/
├── classification/          # Classification-specific screenshots (20 images)
├── regression/              # Regression-specific screenshots (14 images)
├── compare-page-*.png       # Compare Models page (common)
├── configure-page-3-*.png   # Time budget selection (common)
├── jobs-page.png            # Jobs history page (common)
├── results-page-4-6-*.png   # Download & usage guides (common)
└── README.md
```

---

## 🔄 Common UI (Root Folder)

These screenshots show functionality that is identical regardless of problem type.

### Compare Models (`/compare`) - 2 screenshots

**🆕 v1.1.0 Feature** - Side-by-side comparison of up to 4 training runs.

| Screenshot | Description |
|------------|-------------|
| `compare-page-1-select-models.png` | **Model Selection** - Interface to select up to 4 models for comparison |
| `compare-page-2-metrics-comparison.png` | **Metrics Comparison** - Side-by-side metrics table with best values highlighted (🏆) |

### Configure Training - Time Budget

| Screenshot | Description |
|------------|-------------|
| `configure-page-3-time-budget.png` | **Time Budget & Start** - Configure training time (auto-calculated based on dataset size) and launch training job |

### Jobs History (`/history`)

| Screenshot | Description |
|------------|-------------|
| `jobs-page.png` | **Training History** - List of all training jobs with status, metrics, and actions |

### Results - Download & Usage

| Screenshot | Description |
|------------|-------------|
| `results-page-4-download-usage.png` | **Download Models** - Download .pkl and .onnx model files with usage instructions |
| `results-page-5-how-to-use-model.png` | **Docker Usage Guide** - Step-by-step instructions for using the model locally with Docker |
| `results-page-6-python-usage.png` | **Python Code Example** - Direct Python code for loading and using the model without Docker |

---

## 🏷️ Classification (`classification/`)

Screenshots from a classification workflow (predicting discrete categories like Yes/No, A/B/C).

### Configure Training - 4 screenshots

| Screenshot | Description |
|------------|-------------|
| `configure-page-1-dataset-info.png` | **Dataset Overview** - Shows uploaded file metadata: filename, number of rows, and columns |
| `configure-page-2-target-selection.png` | **Target Selection** - Choose target column with unique value counts and auto classification detection |
| `configure-page-4-dataset-info-with-target-column.png` | **Dataset with Target** - Dataset info after target column selection |

### Training Progress - 3 screenshots

| Screenshot | Description |
|------------|-------------|
| `training-page-1-pending.png` | **Job Queued** - Training job submitted, waiting for AWS Batch to allocate resources |
| `training-page-2-running.png` | **Training In Progress** - Live status updates showing current training phase and elapsed time |
| `training-page-3-steps-actions.png` | **Progress Checklist** - Detailed steps (EDA → Preprocessing → Training → Reports) with action buttons |

### Results - 4 screenshots

| Screenshot | Description |
|------------|-------------|
| `results-page-1-overview.png` | **Results Overview** - Summary of training job with key metrics |
| `results-page-2-model-performance.png` | **Model Performance** - Classification metrics: Accuracy, F1 Score, Precision, Recall |
| `results-page-3-model-deployment.png` | **Model Deployment** - Options for deploying and using the trained model |
| `results-page-3-prediction.png` | **🆕 Prediction Playground** (v1.1.0) - Interactive form with serverless Lambda inference showing class prediction and probabilities |

### EDA Report - 6 screenshots

| Screenshot | Description |
|------------|-------------|
| `eda-report-1-overview.png` | **Dataset Overview** - Summary statistics, warnings, alerts, and data quality indicators |
| `eda-report-2-statistics.png` | **Descriptive Statistics** - Mean, median, std dev, quartiles for numeric features |
| `eda-report-3-correlations.png` | **Correlation Matrix** - Heatmap showing relationships between numeric features |
| `eda-report-4-column-details.png` | **Column Details** - Data type, missing values, unique values for each column |
| `eda-report-5-categorical-features.png` | **Categorical Analysis** - Frequency distributions and value counts |
| `eda-report-6-numeric-features.png` | **Numeric Analysis** - Histograms, distribution plots, and outlier detection |

### Training Report - 4 screenshots

| Screenshot | Description |
|------------|-------------|
| `training-report-1-summary.png` | **Model Summary** - Best estimator, training time, and evaluation metrics |
| `training-report-2-feature-importance.png` | **Feature Importance** - Bar chart showing feature contributions to predictions |
| `training-report-3-preprocessing.png` | **Preprocessing Details** - Features used vs. excluded (ID columns, constants) |
| `training-report-4-training-configuration.png` | **Training Configuration** - FLAML settings and hyperparameters |

---

## 📈 Regression (`regression/`)

Screenshots from a regression workflow (predicting continuous numeric values like price, temperature).

### Configure Training - 2 screenshots

| Screenshot | Description |
|------------|-------------|
| `configure-page-1-dataset-info.png` | **Dataset Overview** - Shows uploaded file metadata for regression dataset |
| `configure-page-2-dataset-info-with-target-column.png` | **Target Selection** - Dataset info with numeric target column selected for regression |

### Results - 1 screenshot

| Screenshot | Description |
|------------|-------------|
| `results-page-3-prediction.png` | **🆕 Prediction Playground** (v1.1.0) - Interactive form with serverless Lambda inference showing numeric prediction |

### EDA Report - 7 screenshots

| Screenshot | Description |
|------------|-------------|
| `eda-report-1-overview.png` | **Dataset Overview** - Summary statistics for regression dataset |
| `eda-report-2-target-variable-analysis.png` | **Target Variable Analysis** - Distribution and statistics of the target variable |
| `eda-report-3-processing-notes.png` | **Processing Notes** - Data quality notes and preprocessing recommendations |
| `eda-report-4-correlation-analysis.png` | **Correlation Analysis** - Feature correlations with target variable |
| `eda-report-5-column-details.png` | **Column Details** - Detailed information for each feature |
| `eda-report-6- categorical-features-summary.png` | **Categorical Summary** - Overview of categorical features |
| `eda-report-7-numeric-features-summary.png` | **Numeric Summary** - Overview of numeric features |

### Training Report - 4 screenshots

| Screenshot | Description |
|------------|-------------|
| `training-report-1-summary.png` | **Model Summary** - Best estimator with R², RMSE, MAE metrics |
| `training-report-2-feature-importance.png` | **Feature Importance** - Bar chart for regression model |
| `training-report-3-preprocessing.png` | **Preprocessing Details** - Features used in regression training |
| `training-report-4-training-configuration.png` | **Training Configuration** - FLAML settings for regression |

---

## 🎯 Problem Types Comparison

| Aspect | Classification | Regression |
|--------|---------------|------------|
| **Target Type** | Discrete categories (Yes/No, A/B/C) | Continuous numbers (price, temperature) |
| **Metrics** | Accuracy, F1 Score, Precision, Recall | R² Score, RMSE, MAE |
| **Prediction Output** | Class label + probability scores | Numeric value + confidence interval |
| **Auto-Detection** | ≤10 unique integer values | Float values with decimals |

---

## 🖼️ Usage in Main README

The main [README.md](../README.md) features these key screenshots from the **classification** folder:
- `classification/configure-page-2-target-selection.png` - Core configuration UI
- `classification/training-page-2-running.png` - Training progress monitoring
- `classification/results-page-2-model-performance.png` - Model evaluation metrics
- `classification/training-report-2-feature-importance.png` - Feature importance visualization
- `classification/eda-report-1-overview.png` - EDA report quality

---

## 📝 Screenshot Naming Convention

```
{section}-{page|report}-{number}-{description}.png

Examples:
- configure-page-2-target-selection.png
- training-page-1-pending.png
- results-page-3-prediction.png
- eda-report-1-overview.png
- training-report-2-feature-importance.png
```

---

## 📊 Screenshot Summary

| Location | Count | Description |
|----------|-------|-------------|
| Root (common) | 7 | Compare models, time budget, jobs history, download/usage |
| `classification/` | 20 | Complete classification workflow |
| `regression/` | 14 | Complete regression workflow |
| **Total** | **41** | Full documentation of both problem types |

**v1.1.0 Features Documented:**
- ✅ Prediction Playground (serverless inference) - both classification and regression
- ✅ ONNX model downloads
- ✅ Compare Models page
- ✅ Jobs History page
