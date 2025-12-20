# Changelog

All notable changes to AWS AutoML Lite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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

- **Real-time Training Updates (SSE)** - Server-Sent Events for live status updates
  - New `/api/jobs/[jobId]/stream` SSE endpoint in Next.js
  - Custom `useJobSSE` hook with automatic fallback to polling
  - Visual SSE connection status indicator on training page
  - Updates every 3 seconds instead of 5 seconds polling
  - Graceful handling of connection errors and timeouts

- **Model Comparison** - Side-by-side comparison of training runs
  - New `/compare` page for comparing up to 4 models
  - Metrics comparison table with best model highlighting
  - Feature importance comparison with visual bars
  - Quick job selection from completed training history
  - Link to compare from history page header

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
- Training page now uses SSE for real-time updates instead of polling
- Header component supports `showCompare` prop for compare page link

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

- **v1.0.0** (2025-12-03) - Initial release with full serverless architecture and comprehensive documentation

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Links

- [Documentation](./docs/README.md)
- [Quickstart Guide](./docs/QUICKSTART.md)
- [Architecture Decisions](./infrastructure/terraform/ARCHITECTURE_DECISIONS.md)
- [Lessons Learned](./docs/LESSONS_LEARNED.md)
