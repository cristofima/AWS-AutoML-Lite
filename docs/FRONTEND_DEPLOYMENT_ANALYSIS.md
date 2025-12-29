# Frontend Deployment Analysis - AWS AutoML Lite

> **Status:** Decision made - AWS Amplify selected as final solution  
> **Last Updated:** After failed attempts with App Runner, ECS, and S3+CloudFront

## 📋 Current State

| Component | Technology | Status |
|-----------|------------|--------|
| Backend API | Lambda + API Gateway | ✅ Deployed |
| Training | ECR + AWS Batch | ✅ Deployed |
| Infrastructure | Terraform | ✅ Deployed |
| **Frontend** | **AWS Amplify** | ✅ **Final Solution** |

---

## 🎯 Final Decision: AWS Amplify

### Why Amplify?

| Requirement | Amplify | S3+CloudFront | App Runner | ECS+ALB |
|-------------|---------|---------------|------------|---------|
| Next.js 16+ SSR | ✅ Native | ❌ Static only | ❌ Health fails | ✅ Works |
| Dynamic routes | ✅ Works | ❌ Needs export | ❌ N/A | ✅ Works |
| Auto deploy | ✅ Webhooks | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual |
| **Cost/month** | **$5-15** | $1-2 | $12-15 | $27-40 |
| Terraform | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Complexity | ⭐ Low | ⭐⭐ Low | ⭐ Low | ⭐⭐⭐⭐ High |

### Architecture

```
GitHub Push → Amplify (auto-build) → CDN → Users
                  ↓
            Terraform manages:
            - aws_amplify_app
            - aws_amplify_branch  
            - Environment variables (API URL)
```

---

## 🔴 Options That FAILED

### ❌ App Runner (80+ minutes wasted)

**Problem:** Health checks failed consistently despite Next.js starting successfully.

```
CloudWatch: "✓ Next.js Ready in 150ms"
Service:    "Health check failed on port 3000"
```

**Root Cause:** App Runner's health check timing is fundamentally incompatible with Next.js standalone initialization.

**Verdict:** Never use App Runner for Next.js applications.

---

### ❌ S3 + CloudFront (Incompatible with dynamic routes)

**Problem:** Next.js dynamic routes require SSR.

```typescript
// /configure/[datasetId]/page.tsx
const datasetId = params.datasetId; // Unknown at build time!
```

Static export (`output: 'export'`) doesn't support dynamic route segments without knowing all possible values at build time via `generateStaticParams`.

**Verdict:** Only works for truly static sites.

---

### ⚠️ ECS Fargate + ALB (Too expensive)

**Problem:** Works but costs $27+/month (ALB alone is $16/month).

**When to use:** Only if you need custom networking, security groups, or already have ECS infrastructure.

**Verdict:** Overkill for a simple frontend.

---

## ✅ Amplify Implementation

### Terraform Configuration

```hcl
# infrastructure/terraform/amplify.tf
resource "aws_amplify_app" "frontend" {
  count        = local.amplify_enabled ? 1 : 0
  name         = "${var.project_name}-${var.environment}"
  repository   = var.github_repository
  access_token = var.github_token
  platform     = "WEB_COMPUTE"  # Required for Next.js 16+ SSR

  environment_variables = {
    NEXT_PUBLIC_API_URL       = aws_api_gateway_stage.main.invoke_url
    AMPLIFY_MONOREPO_APP_ROOT = "frontend"
  }
}

resource "aws_amplify_branch" "main" {
  count             = local.amplify_enabled ? 1 : 0
  app_id            = aws_amplify_app.frontend[0].id
  branch_name       = var.environment == "prod" ? "main" : "dev"
  framework         = "Next.js - SSR"
  enable_auto_build = true
}
```

### Required Configuration

| File | Content | Purpose |
|------|---------|---------|
| `frontend/.npmrc` | `node-linker=hoisted` | pnpm compatibility |
| `amplify.yml` (root) | Build commands | Monorepo + pnpm |

### GitHub Token

Create PAT with scopes: `repo`, `admin:repo_hook`  
Add as secret: `GH_PAT_AMPLIFY`

### IAM Permissions

Add to GitHub Actions deploy role:
```json
{
  "Effect": "Allow",
  "Action": "amplify:*",
  "Resource": "*"
}
```

---

## 💰 Cost Comparison

| Solution | Status | Cost/month |
|----------|--------|------------|
| App Runner | ❌ Failed | $12-15 |
| S3+CloudFront | ❌ Incompatible | $1-2 |
| ECS+ALB | ⚠️ Overkill | $27-40 |
| **Amplify** | ✅ **Selected** | **$5-15** |

### Total Project Cost

| Component | Cost/month |
|-----------|------------|
| Frontend (Amplify) | $5-15 |
| Backend (Lambda) | $1-2 |
| Training (Batch) | $2-5 |
| Storage (S3/DynamoDB) | $1-2 |
| **Total** | **~$2-15** |

---

## 📋 Implementation Checklist

### Done
- [x] Create `amplify.tf`
- [x] Add Terraform variables
- [x] Add Terraform outputs
- [x] Create `.npmrc` for pnpm
- [x] Create `amplify.yml`
- [x] Update deploy workflow

### Pending (User Actions)
- [ ] Create GitHub PAT
- [ ] Add `GH_PAT_AMPLIFY` secret
- [ ] Add `amplify:*` to IAM role
- [ ] Run `terraform apply`

---

## 🔄 Deployment Flow

```
1. Push to dev/main branch
        ↓
2. Amplify webhook triggers
        ↓
3. Amplify builds (pnpm + Next.js)
        ↓
4. Deploys to CDN
        ↓
5. Available at Amplify URL
```

**No GitHub Actions needed** - Amplify handles everything via webhooks.

---

## 📚 Key Learnings

1. **App Runner ≠ Next.js** - Health check timing incompatibility
2. **Static export ≠ Dynamic routes** - Can't pre-generate unknown IDs
3. **ECS is overkill** - $27/month for a frontend is excessive
4. **Amplify = Purpose-built** - Native Next.js support, auto-deploy, reasonable cost
5. **Research first** - Would have saved 80+ minutes of App Runner debugging

---

## 🔗 References

- [AWS Amplify + Next.js SSR](https://docs.aws.amazon.com/amplify/latest/userguide/ssr-nextjs.html)
- [Terraform aws_amplify_app](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/amplify_app)
- [Amplify Monorepo Config](https://docs.aws.amazon.com/amplify/latest/userguide/monorepo-configuration.html)
