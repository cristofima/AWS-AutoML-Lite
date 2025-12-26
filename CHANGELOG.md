# Changelog

All notable changes to AWS AutoML Lite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-12-24

### Added
- **Serverless Model Inference** - Deploy and make predictions without SageMaker
  - One-click model deploy button on results page
  - `POST /jobs/{job_id}/deploy` endpoint to deploy/undeploy models
  - `POST /predict/{job_id}` endpoint for making predictions with ONNX Runtime
  - `GET /predict/{job_id}/info` endpoint for model metadata
  - ONNX model caching in Lambda memory for fast subsequent predictions
  - Prediction Playground UI with interactive feature input form
  - Real-time prediction results with confidence (classification) and R² score (regression)
  - Regression predictions show value with ± RMSE error margin (e.g., 0.0991 ± 0.002)
  - R² displayed as coefficient (0-1) per ML standards, not percentage
  - Target column name shown in prediction results panel
  - Cost comparison panel: Lambda ($0 idle) vs SageMaker (~$50-100/month)
  - ONNX Runtime >=1.16.3 for serverless inference (uses 1.16.3 on Lambda, 1.20.x locally)

- **Dark Mode Support** - Full dark/light/system theme support across all pages
  - Integrated `next-themes` for flicker-free theme switching
  - `ThemeToggle` component with 3-way cycling (Light → Dark → System)
  - System preference detection with `enableSystem`
  - localStorage persistence (automatic via next-themes)
  - Tailwind v4 `@custom-variant` for dark mode classes

- **ONNX Model Export** - Cross-platform model export for production deployment
  - Added `skl2onnx`, `onnx`, `onnxruntime`, `onnxmltools` to training container
  - Automatic ONNX generation alongside .pkl on training completion
  - New `onnx_model_download_url` field in API responses
  - Frontend download button with tooltip explaining ONNX benefits
  - Supports: sklearn models (Random Forest, Extra Trees) and LightGBM
  - Verification step ensures exported ONNX model is valid

- **Model Comparison** - Side-by-side comparison of training runs
  - New `/compare` page for comparing up to 4 models
  - Metrics comparison table with best model highlighting
  - Feature importance comparison with visual bars
  - Quick job selection from completed training history
  - Link to compare from history page header

- **Training Run Tags & Notes** - Organize and annotate your training experiments
  - Add custom tags (up to 10) and notes (up to 1000 chars) to any training job
  - `JobMetadataEditor` component with edit/save workflow
  - New `PATCH /jobs/{job_id}` API endpoint for metadata updates
  - History page displays tags and supports filtering by tag
  - Compact tag display mode in tables

- **Enhanced Error Handling** - Comprehensive error boundaries for better UX
  - Global `error.tsx` with network error detection and troubleshooting tips
  - Custom `not-found.tsx` (404) page with quick navigation links
  - `global-error.tsx` for critical root layout failures
  - Route-specific error boundaries for `/training/[jobId]` and `/results/[jobId]`
  - Development mode error details display
  - Root `loading.tsx` with animated spinner

- **Dataset Preview Enhancements** - Rich dataset visualization on configure page
  - `ColumnStatsDisplay` component with dataset overview stats
  - Visual column type distribution (numeric vs categorical)
  - Missing values warning with affected columns list
  - Selected column details with unique ratio visualization

### Dependencies
- **Dependency Audit & Version Updates** - Production-stable versions with flexible ranges
  - FastAPI upgraded from 0.109.0 to >=0.115.0 (fixes ReDoc CDN issue with `redoc@next`)
  - scikit-learn pinned to <1.6.0 (skl2onnx compatibility, avoids breaking API changes)
  - LightGBM updated to >=4.3.0,<5.0.0 (tested with 4.6.0) for improved memory efficiency and faster training
  - Pydantic 2.x with better validation performance and error messages
  - ONNX Runtime updated to >=1.18.0,<1.20.0 for training and >=1.16.0,<2.0.0 for API (tested with 1.19.x for training and 1.23.x for API, latest optimizations)
  - All 263 tests passing with updated dependencies

### Fixed
- **Problem Type Detection** - Regression datasets were incorrectly classified as classification
  - Fixed heuristic logic: now requires BOTH integer-like values AND low cardinality
  - Previously used `OR` condition which misclassified float targets (e.g., 35.5, 40.2) as classification
  - Regression correctly detected for continuous numerical targets
  - Fixes "The least populated class in y has only 1 member" FLAML error

### Changed
- **Code Quality (DRY Refactoring)** - Centralized shared utilities in training module
  - Created `backend/training/utils.py` with shared detection functions
  - `detect_problem_type()`, `is_id_column()`, `is_constant_column()` now in single location
  - Both `preprocessor.py` and `eda.py` import from utils (eliminated ~140 lines of duplication)
  - Prevents future inconsistencies between preprocessing and EDA reports
- Updated all pages with dark mode styling (`dark:` Tailwind variants)
- Updated status badge colors for dark mode compatibility
- Training container now outputs both .pkl and .onnx model formats
- Training page uses optimized polling hook (SSE not viable on Amplify)
- Header component supports `showCompare` prop for compare page link

### Testing
- **Comprehensive Test Suite** - Unit and integration tests for backend (v1.1.0)
  - 263 total tests (104 API + 159 Training)
  - API coverage: 69%, Training coverage: 53%+
  - Tests run automatically in CI/CD before deployment
  - Coverage reports published to GitHub Actions

- **API Tests** (`backend/tests/api/`)
  - Endpoint tests for all routers (datasets, training, models, predict)
  - Pydantic schema validation tests (23 tests)
  - S3 and DynamoDB service integration tests using `moto`
  - Deploy/undeploy endpoint tests
  - Job CRUD operation tests

- **Training Tests** (`backend/tests/training/`)
  - Preprocessor unit tests (ID detection, constant columns, cardinality)
  - Problem type detection tests (classification vs regression)
  - Model trainer tests with mock datasets
  - Utils module tests

- **CI/CD Integration**
  - `deploy-lambda-api.yml` runs API tests before deployment
  - `deploy-training-container.yml` runs training tests before deployment
  - `dorny/test-reporter` for test result visualization
  - `irongut/CodeCoverageSummary` for coverage reports in PRs

## [1.0.0] - 2025-12-03

### Added
- Complete serverless AutoML platform on AWS
- FastAPI backend with Lambda deployment
- FLAML AutoML integration for automatic model training
- Next.js 16 frontend with SSR support via AWS Amplify
- AWS Batch + Fargate Spot for cost-effective training
- Automatic problem type detection (classification/regression)
- EDA report generation with Sweetviz
- Training history and job tracking with DynamoDB
- Model download and export (.pkl format)
- Docker-based prediction script
- CI/CD with GitHub Actions + OIDC
- Comprehensive documentation and architecture diagrams

### Infrastructure
- S3 buckets for datasets, models, and reports
- DynamoDB tables for metadata and job tracking
- Lambda function for API endpoints (direct ZIP deployment)
- API Gateway for REST API
- AWS Batch with Fargate Spot for training jobs
- ECR repository for training container
- CloudWatch logging and monitoring
- AWS Amplify for frontend hosting

### Features
- CSV file upload with drag & drop
- Auto-calculated time budget based on dataset size
- Smart column detection (ID columns automatically excluded)
- Feature importance visualization
- Training progress monitoring
- Portable model export for local use

### Documentation
- Complete quickstart guide
- Architecture decision records
- Terraform best practices analysis
- Lessons learned document
- CI/CD setup guide with OIDC
- Git commit message conventions (713 lines)
- Table of contents for long documents
- CONTRIBUTING.md for collaboration
- CHANGELOG.md for version tracking
- Version badges in README

### Cost Optimization
- ~$10-25/month total cost for moderate usage
- Fargate Spot pricing (70% discount)
- No always-on infrastructure
- Training cost: ~$0.02/job

---

## Version History

- **v1.1.0** (2025-12-24) - Serverless inference, dark mode, ONNX export, model comparison
- **v1.0.0** (2025-12-03) - Initial release with full serverless architecture and comprehensive documentation

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Links

- [Documentation](./docs/README.md)
- [Quickstart Guide](./docs/QUICKSTART.md)
- [Architecture Decisions](./infrastructure/terraform/ARCHITECTURE_DECISIONS.md)
- [Lessons Learned](./docs/LESSONS_LEARNED.md)
