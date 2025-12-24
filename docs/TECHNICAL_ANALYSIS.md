# AWS AutoML Lite - Technical Analysis for v1.1.0 and v2.0.0

## 📑 Table of Contents

- [Overview](#overview)
- [Phase 2 (v1.1.0) - Technical Analysis](#phase-2-v110---technical-analysis)
- [Phase 3 (v2.0.0) - Technical Analysis](#phase-3-v200---technical-analysis)
- [Breaking Changes Summary](#breaking-changes-summary)
- [Migration Guide](#migration-guide)
- [Risk Assessment](#risk-assessment)

---

## Overview

This document provides a detailed technical analysis of the changes required for v1.1.0 and v2.0.0, including:
- Breaking changes to data models, APIs, and infrastructure
- Impact assessment for each feature
- Migration strategies

**Analysis Date:** December 24, 2025  
**Based on:** v1.0.0 released December 3, 2025 / v1.1.0 December 2025

---

## Phase 2 (v1.1.0) - Technical Analysis

### Feature: Real-time Updates (SSE/WebSocket)

#### Current Implementation (v1.0.0)
- Frontend polls `/jobs/{job_id}` every 5 seconds
- Training container updates DynamoDB directly
- Job status values: `pending`, `running`, `completed`, `failed`

#### Analysis: SSE vs Polling (v1.1.0)

**Option Evaluated: Server-Sent Events (SSE)** ❌ Not Viable
- SSE was implemented but doesn't work on AWS Amplify
- Amplify uses Lambda@Edge with 30-second timeout
- Long-lived connections are incompatible with serverless

**Decision: Keep Polling** ✅ Implemented
- For training jobs lasting 5-15 minutes, 5-second delay is imperceptible
- Polling is simple, reliable, and works on all platforms
- No additional infrastructure required

```typescript
// useJobPolling.ts - Polling implementation
export function useJobPolling(jobId: string, options = {}) {
  const { pollingInterval = 5000, onComplete, onError } = options;
  
  useEffect(() => {
    const poll = async () => {
      const job = await getJobDetails(jobId);
      if (job.status === 'completed') {
        cleanup();
        onComplete?.(job);
      } else if (job.status === 'failed') {
        cleanup();
        onError?.(job.error_message);
      }
    };
    
    poll(); // Initial fetch
    const intervalId = setInterval(poll, pollingInterval);
    return () => clearInterval(intervalId);
  }, [jobId]);
}
```

#### Breaking Changes: **NONE**
- Polling was already the v1.0.0 behavior
- SSE code removed after testing revealed Amplify incompatibility

#### Infrastructure Changes
| Resource | Change Type | Impact |
|----------|-------------|--------|
| API Gateway | None | None |
| Lambda | None | None |
| DynamoDB | No changes | None |
| Frontend | Simplified polling hook | Low |

---

### Feature: ONNX Model Export

#### Current Implementation (v1.0.0)
- Models saved as `.pkl` (joblib/pickle format)
- Download via presigned S3 URL

#### Implementation (v1.1.0) ✅
- Added `skl2onnx` to training container
- Generate both `.pkl` and `.onnx` on training completion
- New field in JobResponse for ONNX download URL

#### Breaking Changes: **MINOR (Additive)**

**Schema Changes:**
```python
# schemas.py - ADDITIVE (no breaking change)
class JobResponse(BaseModel):
    # ... existing fields ...
    model_download_url: Optional[str] = None      # Existing (.pkl)
    onnx_model_download_url: Optional[str] = None # NEW (.onnx)
```

**DynamoDB Changes:**
```python
# New optional attribute in training_jobs table
{
    "onnx_model_path": "s3://bucket/models/job_id/model.onnx"  # NEW
}
```

#### Infrastructure Changes
| Resource | Change Type | Impact |
|----------|-------------|--------|
| Training Container | Add skl2onnx (~20MB) | Medium |
| S3 | Additional .onnx files | Low |
| DynamoDB | New optional attribute | None |
| API | New response field | Low |

#### Migration: No action required - backward compatible

---

### Feature: Model Comparison

#### Current Implementation (v1.0.0)
- Single job view at `/results/[jobId]`
- Job history at `/history` (list view)

#### Implementation (v1.1.0) ✅
- New `/compare` page with multi-select
- Side-by-side metrics comparison
- Feature importance diff visualization

#### Breaking Changes: **NONE**
- Purely frontend feature
- Uses existing API endpoints
- No schema changes

#### Infrastructure Changes
| Resource | Change Type | Impact |
|----------|-------------|--------|
| Frontend | New comparison page | Low |
| API | None | None |

---

### Feature: Dark Mode

#### Breaking Changes: **NONE**
- CSS/Tailwind theme changes only
- Uses `prefers-color-scheme` media query
- Persisted via localStorage

---

## Phase 3 (v2.0.0) - Technical Analysis

### Feature: Cognito Authentication

#### Current Implementation (v1.0.0)
- No authentication
- `user_id` field exists but always set to `"default"`
- DynamoDB GSI `user_id-created_at-index` exists (unused)

#### Proposed Implementation (v2.0.0)

**Architecture:**
```
Frontend → Cognito Hosted UI → JWT Token
                ↓
         API Gateway Cognito Authorizer
                ↓
         Lambda extracts user_id from JWT
                ↓
         DynamoDB queries filtered by user_id
```

#### Breaking Changes: **MAJOR**

**1. API Gateway Changes:**
```hcl
# api_gateway.tf - NEW authorizer
resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.api.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "${local.name_prefix}-cognito-authorizer"

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.frontend.id]
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
  }
}
```

**2. New Terraform Resources:**
```hcl
# cognito.tf - NEW FILE
resource "aws_cognito_user_pool" "main" {
  name = "${local.name_prefix}-users"
  
  auto_verified_attributes = ["email"]
  username_attributes      = ["email"]
  
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = true
  }
  
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
  }
}

resource "aws_cognito_user_pool_client" "frontend" {
  name         = "${local.name_prefix}-frontend"
  user_pool_id = aws_cognito_user_pool.main.id
  
  generate_secret = false
  
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]
  
  callback_urls        = [local.frontend_url]
  logout_urls          = [local.frontend_url]
  supported_identity_providers = ["COGNITO"]
}
```

**3. Schema Changes:**
```python
# schemas.py - user_id becomes required from JWT
class JobDetails(BaseModel):
    user_id: str  # Now populated from JWT, no longer "default"
```

**4. Backend Changes:**
```python
# helpers.py - Extract user from JWT
from fastapi import Request, HTTPException, Depends
from jose import jwt, JWTError

async def get_current_user(request: Request) -> str:
    """Extract user_id from Cognito JWT token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("sub")  # Cognito user ID
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**5. Frontend Changes:**
```typescript
// lib/auth.ts - NEW FILE
import { Amplify } from 'aws-amplify';
import { signIn, signOut, getCurrentUser } from 'aws-amplify/auth';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
      userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
    }
  }
});
```

#### Infrastructure Changes Summary
| Resource | Change Type | Breaking |
|----------|-------------|----------|
| Cognito User Pool | NEW | Yes |
| Cognito User Pool Client | NEW | Yes |
| API Gateway Authorizer | NEW | Yes |
| All API Routes | Add authorization | Yes |
| Frontend | Add Amplify Auth | Yes |
| DynamoDB | No schema change | No |

#### Migration Strategy
1. **Option A: Clean cut** - v2.0.0 requires new accounts
2. **Option B: Migration script** - Assign existing data to a default user

**Recommended:** Option A for simplicity (v1.0.0 data is ephemeral/experimental)

---

### Feature: Email Notifications (SES)

#### Proposed Implementation (v2.0.0)

**Architecture:**
```
Training completes → DynamoDB Streams → Lambda → SES → User Email
```

**Note:** DynamoDB Streams is already enabled in v1.0.0:
```hcl
# dynamodb.tf (existing)
stream_enabled   = true
stream_view_type = "NEW_AND_OLD_IMAGES"
```

#### Breaking Changes: **MINOR (Additive)**

**1. New Schema Field:**
```python
# schemas.py
class UserPreferences(BaseModel):  # NEW
    email_notifications: bool = True
    notification_types: List[str] = ["completed", "failed"]

# Stored in Cognito user attributes or separate DynamoDB table
```

**2. New Terraform Resources:**
```hcl
# ses.tf - NEW FILE
resource "aws_ses_email_identity" "notifications" {
  email = var.notification_sender_email
}

resource "aws_lambda_function" "notification_handler" {
  function_name = "${local.name_prefix}-notification-handler"
  # Triggered by DynamoDB Stream
}

resource "aws_lambda_event_source_mapping" "jobs_stream" {
  event_source_arn  = aws_dynamodb_table.training_jobs.stream_arn
  function_name     = aws_lambda_function.notification_handler.arn
  starting_position = "LATEST"
  
  filter_criteria {
    filter {
      pattern = jsonencode({
        eventName = ["MODIFY"]
        dynamodb = {
          NewImage = {
            status = { S = ["completed", "failed"] }
          }
        }
      })
    }
  }
}
```

**3. Lambda Handler:**
```python
# notification_handler.py - NEW
import boto3
from botocore.exceptions import ClientError

ses_client = boto3.client('ses')

def handler(event, context):
    for record in event['Records']:
        if record['eventName'] == 'MODIFY':
            new_image = record['dynamodb']['NewImage']
            status = new_image['status']['S']
            
            if status in ['completed', 'failed']:
                user_email = get_user_email(new_image['user_id']['S'])
                send_notification_email(user_email, new_image)
```

#### Infrastructure Changes
| Resource | Change Type | Breaking |
|----------|-------------|----------|
| SES Email Identity | NEW | No |
| Lambda (notification) | NEW | No |
| DynamoDB Stream Mapping | NEW | No |
| IAM (Lambda → SES) | NEW | No |

#### Dependencies
- **Requires:** Cognito Authentication (to get user email)
- **Order:** Authentication must be implemented first

---

### Feature: Step Functions Orchestration

#### Proposed Implementation (v2.0.0)

**Current Flow:**
```
API → Create Job → Batch → All steps in container
```

**Proposed Flow:**
```
API → Step Functions → Parallel: EDA + Preprocess → Train → Evaluate → Notify
```

#### Breaking Changes: **MEDIUM**

**1. Training Container Split:**
Current single container becomes multiple Lambda functions:
- `eda-generator` - Generate EDA report
- `preprocessor` - Data preprocessing
- `model-trainer` - FLAML training (stays as Batch)
- `evaluator` - Model evaluation

**2. Step Functions Definition:**
```json
{
  "StartAt": "ValidateInput",
  "States": {
    "ValidateInput": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:validate-input",
      "Next": "ParallelPrep"
    },
    "ParallelPrep": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "GenerateEDA",
          "States": {
            "GenerateEDA": { "Type": "Task", "End": true }
          }
        },
        {
          "StartAt": "Preprocess",
          "States": {
            "Preprocess": { "Type": "Task", "End": true }
          }
        }
      ],
      "Next": "TrainModel"
    },
    "TrainModel": {
      "Type": "Task",
      "Resource": "arn:aws:states:::batch:submitJob.sync",
      "Next": "EvaluateModel"
    },
    "EvaluateModel": {
      "Type": "Task",
      "Next": "NotifyUser"
    },
    "NotifyUser": {
      "Type": "Task",
      "End": true
    }
  }
}
```

#### Recommendation
**Defer to v2.1.0 or v3.0.0** - The current architecture works well. Step Functions adds complexity without significant user benefit until we have:
- Multiple preprocessing strategies
- Automated retraining pipelines
- Complex branching logic

---

## Breaking Changes Summary

### v1.1.0 - No Breaking Changes ✅

| Feature | Backend | Frontend | Database | Infrastructure |
|---------|---------|----------|----------|----------------|
| Serverless Inference | Additive | Additive | Additive | Lambda update |
| ONNX Export | Additive | Additive | Additive | Container update |
| Model Comparison | None | Additive | None | None |
| Dark Mode | None | CSS only | None | None |

**Conclusion:** v1.1.0 is **100% backward compatible**

---

### v2.0.0 - Breaking Changes ⚠️

| Feature | Backend | Frontend | Database | Infrastructure |
|---------|---------|----------|----------|----------------|
| Authentication | **Major** | **Major** | Minor | **Major** |
| Email Notifications | Minor | Minor | None | Medium |
| Step Functions | Major | None | None | Major |

**Breaking Changes:**
1. All API endpoints require authentication header
2. `user_id` populated from JWT (no longer "default")
3. Frontend requires Cognito Amplify integration
4. New infrastructure (Cognito, SES)

**Recommendation:** 
- Release authentication as **v2.0.0** (breaking)
- Email notifications in **v2.0.0** (depends on auth)
- Step Functions deferred to **v2.1.0** or later

---

## Migration Guide

### v1.0.0 → v1.1.0
**No migration required.** All changes are additive.

1. Deploy updated training container (ONNX support)
2. Deploy frontend updates
3. Existing jobs continue to work
4. New jobs get ONNX export option

### v1.0.0/v1.1.0 → v2.0.0

**Option A: Clean Migration (Recommended)**
1. Announce deprecation of v1.x data
2. Users export their models before upgrade
3. Deploy v2.0.0 with fresh database
4. Users create new accounts

**Option B: Data Migration**
1. Create Cognito user pool
2. Run migration script:
   ```python
   # Assign all user_id="default" to a system account
   # Or prompt users to claim their data via email
   ```
3. Deploy v2.0.0
4. Existing data accessible after login

---

## Risk Assessment

### v1.1.0 Risks: **LOW**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Lambda cold start (inference) | Medium | Low | Provisioned concurrency option |
| ONNX conversion failures | Medium | Low | Graceful fallback to pkl-only |
| Comparison UI complexity | Low | Low | Start with basic comparison |

### v2.0.0 Risks: **MEDIUM**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Cognito configuration complexity | Medium | High | Follow AWS best practices |
| User migration friction | High | Medium | Clear communication, export tools |
| SES deliverability | Low | Medium | Use verified domain |
| Cost increase | Low | Low | Cognito free tier: 50K MAU |

---

## Recommended Implementation Order

### v1.1.0 Sprint (1 week)
1. **Day 1-2:** Dark mode + UI polish
2. **Day 3-4:** ONNX export
3. **Day 5:** Model comparison page
4. **Day 6-7:** Serverless inference + testing

### v2.0.0 Sprint (2 weeks)
1. **Week 1:** Cognito integration (infrastructure + backend + frontend)
2. **Week 2:** Email notifications + testing + documentation

---

**Document Version:** 1.1  
**Last Updated:** 2025-12-24  
**Author:** Cristopher Coronado
