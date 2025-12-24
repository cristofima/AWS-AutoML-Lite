# AWS AutoML Lite - Product Roadmap

## 📑 Table of Contents

- [Overview](#overview)
- [Release Timeline](#release-timeline)
- [Phase 1: MVP (v1.0.0)](#phase-1-mvp-v100---completed-)
- [Phase 2: Enhanced UX (v1.1.0)](#phase-2-enhanced-ux-v110)
- [Phase 3: Multi-user Platform (v2.0.0)](#phase-3-multi-user-platform-v200)
- [Future Considerations](#future-considerations)
- [Contributing](#contributing)

---

## Overview

This roadmap outlines the planned features and improvements for AWS AutoML Lite. The project follows semantic versioning and is developed iteratively with each phase building on the previous one.

**Development Philosophy:**
- 🎯 User-first: Focus on real-world ML practitioner needs
- 💰 Cost-effective: Maintain serverless, pay-per-use architecture
- 📚 Educational: Clear documentation for learning AWS serverless patterns
- 🔧 Extensible: Modular design for easy customization

---

## Release Timeline

| Version | Phase | Target | Focus | Status |
|---------|-------|--------|-------|--------|
| v1.0.0 | MVP | Dec 2025 | Core AutoML functionality | ✅ Released |
| v1.1.0 | Inference | Dec 2025 | Serverless predictions, UX improvements | ✅ Released |
| v1.2.0 | Validation | Q1 2026 | Batch predictions, prediction history | 📋 Planned |
| v2.0.0 | Multi-user | Q2 2026 | Authentication, notifications | 📋 Backlog |

---

## Phase 1: MVP (v1.0.0) - Completed ✅

**Release Date:** December 3, 2025  
**Article:** AWS Community Builder - Part 1

### Features Delivered

#### Backend ✅
- [x] FastAPI + Mangum for Lambda deployment
- [x] S3 presigned URLs for secure file uploads
- [x] DynamoDB for job tracking and metadata
- [x] AWS Batch + Fargate Spot for training
- [x] FLAML AutoML with LightGBM, Random Forest, Extra Trees
- [x] Automatic problem type detection (classification/regression)
- [x] EDA report generation with Sweetviz
- [x] Training report with feature importance charts
- [x] Model export (.pkl format)

#### Frontend ✅
- [x] Next.js 16 with App Router
- [x] Drag & drop CSV upload
- [x] Column selection with type detection
- [x] Training progress polling
- [x] Results visualization (metrics, charts)
- [x] Training history with pagination
- [x] Job deletion with cleanup

#### Infrastructure ✅
- [x] Terraform IaC (44 AWS resources)
- [x] CI/CD with GitHub Actions (OIDC)
- [x] Multi-environment support (dev/prod)
- [x] Component-specific deployment workflows

#### Documentation ✅
- [x] Quick start guide
- [x] Architecture decision records
- [x] Lessons learned document
- [x] Contributing guidelines

---

## Phase 2: Enhanced UX (v1.1.0)

**Target:** December 2025  
**Article:** AWS Community Builder - Part 2  
**Theme:** Serverless model inference and better developer experience  
**Status:** ✅ Released

### 🎯 Goals
1. **Enable serverless model inference** (Lambda as SageMaker alternative)
2. Enable cross-platform model deployment (ONNX export)
3. Enable model comparison workflows
4. Polish UI/UX based on v1.0.0 feedback

### 📋 Features

#### Export Options (Priority: Medium) ✅ COMPLETED
- [x] **ONNX model export** ✅
  - Added `skl2onnx`, `onnx`, `onnxruntime`, `onnxmltools` to training container
  - Generates both `.pkl` and `.onnx` on completion
  - New `onnx_model_download_url` field in API response
  - Frontend download button with tooltip
  - Supports: sklearn models (Random Forest, Extra Trees) and LightGBM
  - **Breaking changes:** None (additive schema field)

- [x] **Model metadata export** ✅
  - Training report includes configuration and preprocessing info
  - Feature list and dropped columns documented
  - Performance metrics summary in HTML report

#### Model Deployment & Inference (Priority: High) ✅ COMPLETED
> **Key Feature for Article 2:** Serverless inference as cost-effective alternative to SageMaker

- [x] **One-click model deploy** ✅
  - Deploy button on results page after successful training
  - Sets `deployed: true` flag in DynamoDB
  - No model upload needed - uses existing S3 artifacts
  - Undeploy option to deactivate

- [x] **Prediction endpoint** ✅
  - `POST /predict/{job_id}` - single prediction
  - Loads ONNX model from S3 (cached in Lambda memory)
  - Returns prediction + probability + inference time
  - Only works for deployed models
  - `GET /predict/{job_id}/info` - returns model metadata for playground

- [x] **Prediction playground UI** ✅
  - Interactive form with model's input features
  - Auto-generated from training metadata (preprocessing_info)
  - Test predictions without code
  - Shows prediction, confidence, probabilities, and inference time
  - Cost comparison vs SageMaker info panel

**Architecture:**
```
Results page → [Deploy Model] → DynamoDB flag set
                    ↓
Playground UI → POST /predict/{job_id} → Lambda loads ONNX from S3
                    ↓
              Returns { prediction, probability, inference_time_ms }
```

**Cost comparison vs SageMaker:**
| Aspect | Lambda Inference | SageMaker Endpoint |
|--------|------------------|-------------------|
| Idle cost | $0 | ~$50-100/month |
| Per prediction | ~$0.0001 | ~$0.0001 |
| Cold start | 1-3 seconds | None |
| Best for | Sporadic use, MVPs | Production 24/7 |

#### Model Comparison (Priority: High) ✅ COMPLETED
- [x] **Compare multiple training runs** ✅
  - New `/compare` page with job selection
  - Side-by-side metrics comparison table
  - Best model highlighting with 🏆 indicator
  - Feature importance visual comparison
  - Support for up to 4 models simultaneously
  - **Breaking changes:** None (new page)

- [x] **Training run tags/notes** ✅
  - Add custom tags (up to 10) and notes (up to 1000 chars)
  - `JobMetadataEditor` component with edit/save workflow
  - New `PATCH /jobs/{job_id}` API endpoint
  - History page displays tags and supports filtering
  - Compact tag display in tables

#### UI/UX Improvements (Priority: Medium) ✅ COMPLETED
- [x] **Dark mode support** ✅
  - System preference detection via `next-themes`
  - 3-way dropdown (Light → Dark → System)
  - Persisted preference in localStorage
  - All pages updated with `dark:` Tailwind variants

- [x] **Improved error handling** ✅
  - Global `error.tsx` with network error detection
  - Custom `not-found.tsx` (404) page
  - `global-error.tsx` for root layout failures
  - Route-specific error boundaries for training/results pages
  - Development mode error details display
  - Root `loading.tsx` with animated spinner

- [x] **Dataset preview enhancements** ✅
  - `ColumnStatsDisplay` component with visual statistics
  - Column type distribution (numeric vs categorical)
  - Missing value warnings with affected columns
  - Selected column details with unique ratio visualization

#### Performance (Priority: Low) 📋 DEFERRED to v1.2.0
- [ ] **Lambda cold start optimization**
  - Provisioned concurrency option
  - Package size reduction
  - Lazy imports

### 📊 Success Metrics
| Metric | Target | Current Status |
|--------|--------|----------------|
| Model inference | < 500ms per prediction | ✅ Implemented |
| Deploy to predict | < 30 seconds | ✅ One-click deploy |
| Model comparison | Available in <2 clicks | ✅ `/compare` page from history |
| ONNX export | All supported models | ✅ Complete |
| Dark mode preference | Persisted | ✅ Complete |

### ⚠️ Breaking Changes: **NONE**
v1.1.0 is 100% backward compatible with v1.0.0.
All features are additive - existing functionality unchanged.

> 📋 **Technical details:** See [TECHNICAL_ANALYSIS.md](./TECHNICAL_ANALYSIS.md) for implementation specifics.

### ⚙️ Technical Implementation

#### Serverless Inference Architecture ✅ IMPLEMENTED
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│  API Gateway │────▶│    Lambda   │
│  Playground  │     │  /predict/*  │     │  ONNX Runtime│
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                     ┌───────────────────────────┤
                     ▼                           ▼
              ┌──────────────┐           ┌──────────────┐
              │   DynamoDB   │           │      S3      │
              │  deployed:   │           │  model.onnx  │
              │  true/false  │           │  (cached)    │
              └──────────────┘           └──────────────┘
```

**Why Lambda over SageMaker?**
- $0 idle cost (vs ~$50-100/month for SageMaker endpoint)
- Pay only for actual predictions
- Sufficient for sporadic use and MVPs
- ONNX Runtime works great in Lambda environment
- Trade-off: 1-3s cold start (acceptable for non-real-time use)

#### ONNX Export Flow ✅ IMPLEMENTED
```
Training completion → FLAML model extracted → skl2onnx/onnxmltools conversion
                                              ↓
                       Verify with onnxruntime → Save .onnx to S3 → Update DynamoDB
```

#### Code Quality Improvements ✅ IMPLEMENTED (v1.1.0)
- **Shared utility module**: Created `backend/training/utils.py` for DRY principle
  - `detect_problem_type()` - Single source of truth for classification vs regression
  - `is_id_column()` - Identifier detection with regex patterns
  - `is_constant_column()` - Constant feature detection
  - `is_high_cardinality_categorical()` - High-cardinality detection
- **Problem type detection fix**: Changed `OR` to `AND` logic for classification heuristics
  - Float values with decimals (35.5, 40.2) now correctly detected as regression
  - Integer-like values (0, 1, 2) with ≤10 unique values = classification
- **Environment separation**: Added `.env.development.local` for safe local testing

---

## Phase 2.5: Batch Validation (v1.2.0)

**Target:** Q1 2026  
**Article:** AWS Community Builder - Part 2.5 (optional)  
**Theme:** Model validation and prediction history

### 🎯 Goals
1. Enable batch predictions on new datasets
2. Store prediction history for analysis
3. Compare predictions vs actuals for model validation

### 📋 Features Planned

#### Batch Predictions (Priority: High)
- [ ] **Upload validation dataset**
  - CSV with same columns as training data (without target)
  - Validate schema matches model's expected features
  - Preview data before prediction

- [ ] **Batch prediction endpoint**
  - `POST /predict/{job_id}/batch` with CSV file
  - Returns predictions for all rows
  - Download results as CSV

#### Prediction History (Priority: Medium)
- [ ] **Store prediction batches**
  - New DynamoDB table: `prediction_batches`
  - Link to job_id and timestamp
  - Store input/output in S3

- [ ] **Prediction history UI**
  - List all prediction batches per model
  - Download historical predictions
  - Compare across batches

#### Model Validation (Priority: Medium)
- [ ] **Validation mode**
  - Upload CSV with target column (actuals)
  - Compare predictions vs actuals
  - Calculate validation metrics (accuracy, F1, etc.)
  - Detect model drift

### ⚠️ Breaking Changes: **NONE**
v1.2.0 is backward compatible with v1.1.0.

---

## Phase 3: Multi-user Platform (v2.0.0)

**Target:** Q2 2026  
**Article:** AWS Community Builder - Part 3  
**Theme:** Production-ready multi-tenant platform

> ⚠️ **Breaking Changes:** v2.0.0 introduces authentication which is a **major breaking change**.
> All API endpoints will require JWT tokens. See migration guide below.

### 🎯 Goals
1. Enable user authentication and workspaces
2. Add email notifications for training completion
3. ~~Orchestrate complex ML pipelines~~ → Deferred to v2.1.0
4. Production hardening

### 📋 Features Planned

#### Authentication (Priority: Critical)
- [ ] **Amazon Cognito integration**
  - User sign-up/sign-in
  - Email verification
  - Password reset flow
  - Social login (Google, GitHub)
  - Estimated: 3-4 days

- [ ] **User workspaces**
  - Isolated datasets per user
  - Private training history
  - User quotas/limits (optional)

- [ ] **API security**
  - JWT token validation
  - Per-user rate limiting
  - Audit logging

#### Email Notifications (Priority: High)
- [ ] **Training completion emails**
  - Amazon SES integration
  - Summary of metrics
  - Direct link to results
  - Estimated: 2 days

- [ ] **Notification preferences**
  - Enable/disable emails
  - Notification types (success, failure, both)
  - Custom email templates

- [ ] **Training failure alerts**
  - Detailed error information
  - Suggested fixes
  - Retry button link

#### Pipeline Orchestration (Priority: Low - Deferred to v2.1.0)
> **Deferred:** Step Functions adds complexity without significant user benefit
> in v2.0.0. Current single-container architecture works well for MVP users.
> Will revisit when we need:
> - Multiple preprocessing strategies
> - Automated retraining pipelines
> - Complex branching logic

- [ ] **Step Functions workflow** *(v2.1.0)*
  - Parallel: EDA + Preprocess → Train → Evaluate
  - Retry logic with exponential backoff
  - Estimated: 4-5 days

- [ ] **Custom preprocessing options** *(v2.1.0)*
  - Feature selection strategies
  - Encoding preferences
  - Handling missing values

#### Production Features (Priority: Medium)
- [ ] **Custom domain with SSL**
  - Route 53 + ACM
  - CloudFront distribution
  - API custom domain

- [ ] **Multi-region deployment**
  - Active-passive setup
  - Cross-region S3 replication
  - DynamoDB global tables

- [ ] **Observability enhancements**
  - X-Ray distributed tracing
  - Custom CloudWatch dashboards
  - Cost tracking per user

### 📊 Success Metrics
- User registration to first training < 5 minutes
- Email delivery within 1 minute of completion
- 99.9% uptime SLA
- Support for 100+ concurrent users

### ⚠️ Breaking Changes Summary

| Change | Impact | Migration |
|--------|--------|-----------|
| All APIs require JWT | High | Add auth header to all requests |
| `user_id` from JWT | Medium | Data isolation per user |
| New Cognito resources | Medium | Terraform apply |
| Frontend auth flow | High | Add Amplify Auth |

### 🔄 Migration Guide (v1.x → v2.0.0)

**Recommended: Clean Migration**
1. Announce deprecation timeline for v1.x data
2. Users download their trained models (.pkl files)
3. Deploy v2.0.0 with fresh DynamoDB tables
4. Users create Cognito accounts
5. Start fresh with authenticated workspaces

> **Why clean migration?** v1.0.0/v1.1.0 data is experimental.
> The cost of migration scripts exceeds the value of preserving test data.

**Alternative: Data Migration Script** *(if needed)*
```python
# Assign existing jobs to a system/admin user
# Prompt original users to claim via email verification
```

> 📋 **Full technical details:** See [TECHNICAL_ANALYSIS.md](./TECHNICAL_ANALYSIS.md)

### ⚙️ Technical Implementation

#### Authentication Flow
```
Frontend → Cognito Hosted UI → JWT Token
                ↓
         API Gateway Authorizer
                ↓
         Lambda extracts user_id from token
                ↓
         DynamoDB queries filtered by user_id
```

#### Email Notification Architecture
```
Training completes → DynamoDB Stream (already enabled) → Lambda → SES
                                        ↓
                              Email template + metrics
                                        ↓
                              User receives notification
```

> **Note:** DynamoDB Streams is already enabled in v1.0.0 infrastructure.
> Only need to add Lambda trigger and SES resources.

---

## Future Considerations (v2.1.0+)

These features are under consideration for future releases but not yet scheduled:

### Model Deployment
- [x] ~~Lambda inference endpoint~~ ✅ v1.1.0
- [x] ~~API for real-time predictions~~ ✅ v1.1.0
- [ ] SageMaker endpoint deployment (alternative to Lambda)
- [ ] Batch prediction jobs (v1.2.0 planned)

### Advanced ML Features
- [ ] Time series forecasting support
- [ ] AutoML for NLP (text classification)
- [ ] Hyperparameter tuning UI
- [ ] Ensemble model creation
- [ ] Neural architecture search (NAS)

### Collaboration
- [ ] Team workspaces
- [ ] Shared datasets
- [ ] Model registry
- [ ] Experiment tracking (MLflow integration)

### Enterprise Features
- [ ] SSO integration (SAML/OIDC)
- [ ] VPC deployment option
- [ ] Compliance reports (SOC2, HIPAA)
- [ ] Cost allocation by project/team

### Developer Experience
- [ ] CLI tool for training
- [ ] Python SDK
- [ ] Jupyter notebook integration
- [ ] VS Code extension

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### How to Propose Features
1. Check if the feature is already on the roadmap
2. Open a GitHub Discussion for new ideas
3. For approved features, create an Issue with:
   - Problem statement
   - Proposed solution
   - Implementation approach

### Priority Labels
- `P0`: Critical - Blocking users
- `P1`: High - Important for upcoming release
- `P2`: Medium - Nice to have
- `P3`: Low - Future consideration

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-24 | v1.1.0 | Released: Serverless inference, dark mode, ONNX export, model comparison. Fixed SSE (not viable on Amplify → using polling). |
| 2025-12-09 | - | Initial roadmap created |
| 2025-12-03 | v1.0.0 | MVP released |

---

**Last Updated:** 2025-12-24  
**Maintained By:** [@cristofima](https://github.com/cristofima)
