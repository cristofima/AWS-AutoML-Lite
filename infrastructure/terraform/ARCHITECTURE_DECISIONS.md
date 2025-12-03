# Architecture Decision: Containers vs Lambda

## Current Architecture

### 1. Backend API (Lambda) - ✅ NO CONTAINERS

**Implementation:** Direct code deployment (ZIP)
```
backend/api/ → ZIP → Lambda Function
```

**Why not containers?**
- ✅ Small codebase (~5MB)
- ✅ Fast cold starts (<2s)
- ✅ Simple deployment
- ✅ No Docker/ECR overhead

**Dependencies:**
- FastAPI + Mangum (Lambda adapter)
- boto3 (AWS SDK)
- pydantic (validation)

**Total size:** ~5-10MB compressed

---

### 2. Training Pipeline (AWS Batch) - 🐳 REQUIRES CONTAINERS

**Implementation:** Docker container in ECR
```
backend/training/ → Dockerfile → ECR → AWS Batch (Fargate)
```

**Why containers are necessary:**

#### Size Constraints
```
FLAML:         ~50MB
scikit-learn:  ~80MB
pandas:        ~40MB
numpy:         ~30MB
xgboost:       ~20MB
lightgbm:      ~15MB
sweetviz:      ~10MB
plotly:        ~20MB
----------------------------
TOTAL:         ~265MB (uncompressed)
              ~150MB (compressed)
```

**Lambda limits:**
- ❌ ZIP deployment: 50MB max (uncompressed)
- ❌ With Layers: 250MB max (uncompressed)
- ⚠️ Training dependencies: **~265MB** → **EXCEEDS LIMIT**

#### Runtime Constraints

**Training time estimates:**
- Small dataset (Iris, 150 rows): 2-3 minutes
- Medium dataset (10K rows): 5-15 minutes
- Large dataset (100K rows): 15-60 minutes

**Lambda timeout:** ❌ **15 minutes maximum**

For datasets >10K rows, Lambda timeout is insufficient.

#### Computational Resources

**FLAML AutoML requirements:**
- Multiple models trained in parallel
- Hyperparameter tuning
- Cross-validation

**Lambda limits:**
- Max: 10GB RAM, 6 vCPUs (ephemeral)
- Cost: $0.0000166667 per GB-second

**Batch with Fargate:**
- Configurable: 2-4 vCPUs, 4-8GB RAM
- Fargate Spot: 70% cheaper than on-demand
- Cost: ~$0.04 per vCPU-hour (Spot)

**Training job cost comparison (10 min job):**
- Lambda (10GB): ~$0.17
- Fargate Spot (2 vCPU, 4GB): ~$0.013
- **Savings: 92%**

---

## Alternative Architectures Considered

### Option A: Lambda with Layers (All Serverless)

**Pros:**
- ✅ No Docker complexity
- ✅ Faster deployment
- ✅ Simpler infrastructure

**Cons:**
- ❌ Size limit: 250MB (our deps: ~265MB)
- ❌ Timeout: 15 min (insufficient for larger datasets)
- ❌ More expensive for long jobs
- ❌ Limited to small datasets only

**Verdict:** ❌ Not viable due to size constraints

---

### Option B: Lambda + Step Functions (Chunked Training)

**Pros:**
- ✅ No containers
- ✅ Can exceed 15min by chaining

**Cons:**
- ❌ Still size limit: 250MB
- ❌ Complex orchestration
- ❌ Multiple Lambda invocations (higher cost)
- ❌ Hard to parallelize model training

**Verdict:** ❌ Not viable due to size constraints + complexity

---

### Option C: AWS App Runner (Container as PaaS)

**Pros:**
- ✅ Simple container deployment
- ✅ Auto-scaling
- ✅ No cold starts

**Cons:**
- ❌ Always running (higher cost: ~$25/month)
- ❌ Not ideal for batch jobs
- ❌ Overkill for intermittent training

**Verdict:** ❌ Too expensive for batch workload

---

### Option D: ECS Fargate Task (Manual)

**Pros:**
- ✅ Containers without Batch complexity
- ✅ Direct ECS API

**Cons:**
- ❌ More manual orchestration
- ❌ No built-in job queue/retry
- ❌ Less cost-effective (no Spot support)

**Verdict:** ❌ Batch provides better abstraction

---

### Option E: AWS Batch + Fargate Spot (CURRENT) ✅

**Pros:**
- ✅ Handles large ML dependencies (no size limit)
- ✅ Unlimited execution time
- ✅ Cost-effective with Spot pricing (70% discount)
- ✅ Built-in job queue and retry logic
- ✅ Isolated execution environment
- ✅ Can scale to 4+ vCPUs if needed

**Cons:**
- ⚠️ Requires Docker + ECR setup
- ⚠️ Slightly more complex deployment

**Verdict:** ✅ **BEST CHOICE** for ML training workload

---

## Cost Analysis (20 training jobs/month)

### Current Architecture (Lambda API + Batch Training)
```
Lambda API (100K requests):        $0.80
AWS Batch (20 jobs × 10min):       $2.60  (Spot)
ECR storage (1 image, 500MB):      $0.05
Total:                             $3.45/month
```

### Alternative: Lambda-only (if it were possible)
```
Lambda API (100K requests):        $0.80
Lambda Training (20 jobs × 10min): $3.40  (10GB, 6 vCPU)
Total:                             $4.20/month
```

### Alternative: App Runner
```
App Runner (always on):            $25.00/month
Total:                             $25.00/month
```

**Current architecture is 20% cheaper than Lambda-only and 86% cheaper than App Runner.**

---

## Size Optimization Attempts

### Can we reduce training dependencies below 250MB?

**Attempted optimizations:**

1. **Remove Sweetviz (EDA library)** → Save 10MB
   - ❌ Loses important feature: automated EDA reports

2. **Use smaller ML library (e.g., scikit-learn only)** → Save 100MB
   - ❌ Loses AutoML capability (main project feature)

3. **Use AutoGluon Lite** → Save 50MB
   - ❌ Still exceeds 200MB total

4. **Compile dependencies to slim down**
   - ⚠️ Minimal savings (~10%)
   - ⚠️ Complex build process

**Conclusion:** Cannot reasonably fit dependencies in Lambda without removing core features.

---

## When to Use Containers in AWS Lambda

### ✅ Use Containers When:

1. **Dependencies exceed 250MB** (even with Layers)
2. **Need specific system libraries** (compiled binaries)
3. **Complex build process** (multi-stage builds)
4. **Consistent environment across services**
5. **Heavy ML/data science workloads**

### ❌ Avoid Containers When:

1. **Simple API with small dependencies** (<50MB)
2. **Fast cold start is critical** (<1s)
3. **Frequent code changes** (containers slower to build)
4. **No special system dependencies**
5. **Team unfamiliar with Docker**

---

## Project Compliance Check

### Container Usage Audit:

| Component | Uses Containers? | Justified? | Reason |
|-----------|------------------|------------|--------|
| **Frontend** | ❌ No | N/A | AWS Amplify (Next.js SSR) |
| **Backend API** | ❌ No | ✅ Correct | Small size (~5MB), fast deploys |
| **Training Job** | ✅ Yes | ✅ **JUSTIFIED** | Large deps (265MB), long runtime (>15min) |

**Verdict:** ✅ **Containers are used ONLY where necessary.**

---

## Deployment Simplification (If Needed)

If you want to eliminate Docker for demo purposes, you can:

### 1. Create "Lite" Version (Lambda-only)

**Modifications:**
- Remove FLAML, XGBoost, LightGBM
- Use only scikit-learn (single model)
- Limit to 5-minute time budget
- Datasets: <10K rows only

**Trade-offs:**
- ❌ No AutoML (single model)
- ❌ Lower accuracy
- ✅ No Docker needed
- ✅ Simpler deployment

### 2. Use Pre-built Lambda Layers

**AWS maintains layers for:**
- pandas, numpy, scikit-learn (via AWSDataWrangler)

**Still need to add:**
- FLAML (~50MB) → Still exceeds limit with other deps

**Verdict:** Not practical for full AutoML

---

## Conclusion

**Current architecture is optimal:**

1. ✅ **Backend API:** Lambda (no containers) - Simple, fast, cheap
2. ✅ **Training:** AWS Batch + Fargate Spot (containers) - Necessary for ML workload
3. ✅ **Cost:** ~$10-25/month (lowest possible for this feature set)
4. ✅ **Flexibility:** Can handle small to large datasets

**Containers are used ONLY in the training component, where they are technically required due to:**
- Dependency size constraints (265MB > 250MB Lambda limit)
- Runtime duration (can exceed 15 min Lambda limit)
- Cost optimization (Batch Spot 92% cheaper)

**This is not "unnecessary Docker complexity" - it's the right tool for the job.**

---

## References

- [AWS Lambda Limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html)
- [AWS Batch Pricing](https://aws.amazon.com/batch/pricing/)
- [Fargate Spot Pricing](https://aws.amazon.com/fargate/pricing/)
