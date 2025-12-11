# GitHub Copilot Custom Instructions - Terraform Code Generation

These instructions guide GitHub Copilot in generating clean, maintainable, and secure Terraform code following HashiCorp best practices and AWS well-architected patterns.

---

## I. Core Design Principles

### 1. DRY (Don't Repeat Yourself)

- **Use locals** for computed values referenced multiple times
- **Use modules** for repeatable infrastructure patterns
- **Use for_each/count** for similar resources
- **Extract common tags** into local variables

**Examples:**

```hcl
# ❌ BAD - Repeated computation
resource "aws_s3_bucket" "datasets" {
  bucket = "${var.project_name}-${var.environment}-datasets-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket" "models" {
  bucket = "${var.project_name}-${var.environment}-models-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket" "reports" {
  bucket = "${var.project_name}-${var.environment}-reports-${data.aws_caller_identity.current.account_id}"
}

# ✅ GOOD - Computed once in locals
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  account_id  = data.aws_caller_identity.current.account_id
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket" "buckets" {
  for_each = toset(["datasets", "models", "reports"])
  
  bucket = "${local.name_prefix}-${each.key}-${local.account_id}"
  tags   = local.common_tags
}
```

### 2. KISS (Keep It Simple, Stupid)

- **Avoid over-engineering** - don't create modules for single-use resources
- **Use simple conditionals** over complex expressions
- **Prefer explicit** over clever implicit configurations
- **Document complex logic** inline

**Examples:**

```hcl
# ❌ BAD - Over-engineered for simple use case
module "single_lambda" {
  source = "./modules/generic-lambda-with-all-options"
  
  # 20 optional parameters...
}

# ✅ GOOD - Direct resource for simple case
resource "aws_lambda_function" "api" {
  function_name = "${local.name_prefix}-api"
  handler       = "api.main.handler"
  runtime       = "python3.11"
  
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  
  role = aws_iam_role.lambda.arn
}
```

### 3. Fail Fast with Validation

- **Use variable validation** for input constraints
- **Use preconditions** for resource-level assumptions
- **Use postconditions** for verifying created resources
- **Provide actionable error messages**

**Examples:**

```hcl
# Variable validation - runs at plan time
variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "time_budget" {
  type        = number
  description = "Training time budget in seconds"
  default     = 300
  
  validation {
    condition     = var.time_budget >= 60 && var.time_budget <= 3600
    error_message = "Time budget must be between 60 and 3600 seconds."
  }
}

# Precondition - validates before resource creation
resource "aws_s3_bucket_cors_configuration" "datasets" {
  bucket = aws_s3_bucket.datasets.id
  
  cors_rule {
    allowed_origins = local.cors_origins
    allowed_methods = ["PUT", "GET"]
  }
  
  lifecycle {
    precondition {
      condition     = length(local.cors_origins) > 0
      error_message = "CORS origins cannot be empty. Set cors_allowed_origins or enable Amplify."
    }
  }
}

# Postcondition - validates after resource creation
data "aws_vpc" "selected" {
  id = var.vpc_id
  
  lifecycle {
    postcondition {
      condition     = self.enable_dns_support == true
      error_message = "Selected VPC must have DNS support enabled."
    }
  }
}
```

### 4. Single Responsibility

- **One file per logical grouping** (S3, IAM, Lambda, etc.)
- **Separate data sources** from resources when complex
- **Keep modules focused** on one concern
- **Don't mix unrelated resources** in same file

**Recommended file structure:**

```
infrastructure/terraform/
├── main.tf           # Provider configuration, terraform block
├── variables.tf      # All input variables
├── outputs.tf        # All outputs
├── data.tf           # Data sources and common locals
├── s3.tf             # S3 buckets and configurations
├── lambda.tf         # Lambda function and related
├── api_gateway.tf    # API Gateway configuration
├── iam.tf            # IAM roles and policies
├── dynamodb.tf       # DynamoDB tables
├── batch.tf          # AWS Batch resources
├── ecr.tf            # ECR repositories
├── amplify.tf        # Amplify app (if used)
├── dev.tfvars        # Development environment values
└── prod.tfvars       # Production environment values
```

---

## II. Naming Conventions

### 1. Resources and Data Sources

- **Use lowercase with underscores** for resource names
- **Use descriptive names** that indicate purpose
- **Avoid redundant prefixes** (no `aws_` in resource name)
- **Use singular nouns** for single resources

**Examples:**

```hcl
# ❌ BAD - Redundant, unclear
resource "aws_s3_bucket" "aws_s3_bucket_for_data" { }
resource "aws_lambda_function" "func1" { }

# ✅ GOOD - Clear, descriptive
resource "aws_s3_bucket" "datasets" { }
resource "aws_s3_bucket" "models" { }
resource "aws_lambda_function" "api" { }
resource "aws_dynamodb_table" "training_jobs" { }
```

### 2. Variables

- **Use lowercase with underscores**
- **Use positive statements** for feature flags (`xxx_enabled` not `xxx_disabled`)
- **Group related variables** with common prefix
- **Include units in name** when applicable (`timeout_seconds`, `size_mb`)

**Examples:**

```hcl
# ❌ BAD - Negative, unclear
variable "disable_encryption" { }
variable "t" { }  # Unclear

# ✅ GOOD - Positive, descriptive
variable "encryption_enabled" {
  type        = bool
  default     = true
  description = "Enable server-side encryption for S3 buckets"
}

variable "lambda_timeout_seconds" {
  type        = number
  default     = 30
  description = "Lambda function timeout in seconds"
}

variable "batch_memory_mb" {
  type        = number
  default     = 4096
  description = "Memory allocation for Batch jobs in MB"
}
```

### 3. Locals

- **Use for computed values** referenced more than once
- **Use for complex expressions** to improve readability
- **Group related locals** together
- **Document purpose** with comments

**Examples:**

```hcl
locals {
  # Naming
  name_prefix = "${var.project_name}-${var.environment}"
  account_id  = data.aws_caller_identity.current.account_id
  region      = data.aws_region.current.name
  
  # Feature flags
  amplify_enabled = var.github_repository != "" && var.github_token != ""
  
  # Computed values
  cors_origins = length(var.cors_allowed_origins) > 0 ? var.cors_allowed_origins : concat(
    local.amplify_enabled ? ["https://${aws_amplify_app.frontend[0].default_domain}"] : [],
    var.environment == "dev" ? ["http://localhost:3000"] : []
  )
  
  # Common tags applied to all resources
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

---

## III. Variable Best Practices

### 1. Always Include

- **type** - Explicit type constraint
- **description** - What the variable is for
- **default** - When there's a sensible default
- **validation** - For constrained values

**Examples:**

```hcl
variable "project_name" {
  type        = string
  description = "Name of the project, used as prefix for all resources"
  default     = "automl-lite"
  
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name))
    error_message = "Project name must start with letter, contain only lowercase letters, numbers, and hyphens."
  }
}

variable "s3_lifecycle_days" {
  type        = number
  description = "Number of days before S3 objects expire"
  default     = 30
  
  validation {
    condition     = var.s3_lifecycle_days >= 1 && var.s3_lifecycle_days <= 365
    error_message = "S3 lifecycle days must be between 1 and 365."
  }
}
```

### 2. Sensitive Variables

- **Mark secrets as sensitive** - prevents display in logs
- **Never set defaults** for secrets
- **Use environment variables** or secret managers

**Examples:**

```hcl
variable "github_token" {
  type        = string
  description = "GitHub personal access token for Amplify"
  default     = ""
  sensitive   = true
}

variable "database_password" {
  type        = string
  description = "Database password"
  sensitive   = true
  # No default - must be provided
}
```

---

## IV. Resource Patterns

### 1. Conditional Resources

- **Use count for simple on/off** conditions
- **Use for_each for collections**
- **Reference with [0]** when using count

**Examples:**

```hcl
# count for optional resources
resource "aws_amplify_app" "frontend" {
  count = local.amplify_enabled ? 1 : 0
  
  name       = local.name_prefix
  repository = var.github_repository
}

# for_each for multiple similar resources
resource "aws_s3_bucket" "storage" {
  for_each = toset(["datasets", "models", "reports"])
  
  bucket = "${local.name_prefix}-${each.key}-${local.account_id}"
  tags   = local.common_tags
}

# Referencing conditional resources
output "amplify_url" {
  value = local.amplify_enabled ? aws_amplify_app.frontend[0].default_domain : null
}
```

### 2. IAM Policies

- **Use least privilege** - only grant required permissions
- **Use specific resource ARNs** - avoid wildcards when possible
- **Separate policies by concern** - one policy per service/action group
- **Use data sources** for AWS-managed policies

**Examples:**

```hcl
# ❌ BAD - Overly permissive
data "aws_iam_policy_document" "lambda" {
  statement {
    effect    = "Allow"
    actions   = ["s3:*"]
    resources = ["*"]
  }
}

# ✅ GOOD - Least privilege
data "aws_iam_policy_document" "lambda" {
  # S3 read access to datasets bucket
  statement {
    sid    = "S3ReadDatasets"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.datasets.arn,
      "${aws_s3_bucket.datasets.arn}/*"
    ]
  }
  
  # DynamoDB access to jobs table only
  statement {
    sid    = "DynamoDBAccess"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query"
    ]
    resources = [
      aws_dynamodb_table.training_jobs.arn,
      "${aws_dynamodb_table.training_jobs.arn}/index/*"
    ]
  }
}
```

### 3. S3 Buckets

- **Block public access** by default
- **Enable versioning** for important data
- **Set lifecycle rules** for cost management
- **Configure CORS** with specific origins

**Examples:**

```hcl
resource "aws_s3_bucket" "datasets" {
  bucket = "${local.name_prefix}-datasets-${local.account_id}"
  tags   = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "datasets" {
  bucket = aws_s3_bucket.datasets.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "datasets" {
  bucket = aws_s3_bucket.datasets.id
  
  rule {
    id     = "expire-old-datasets"
    status = "Enabled"
    
    expiration {
      days = var.s3_lifecycle_days
    }
  }
}
```

### 4. Lambda Functions

- **Use archive_file** for deployment packages
- **Set appropriate timeout and memory**
- **Configure environment variables** from Terraform
- **Enable X-Ray tracing** for debugging

**Examples:**

```hcl
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../backend/api"
  output_path = "${path.module}/lambda_build/api.zip"
  excludes    = ["__pycache__", "*.pyc", ".pytest_cache"]
}

resource "aws_lambda_function" "api" {
  function_name = "${local.name_prefix}-api"
  role          = aws_iam_role.lambda.arn
  handler       = "api.main.handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256
  
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  
  environment {
    variables = {
      ENVIRONMENT          = var.environment
      S3_BUCKET_DATASETS   = aws_s3_bucket.datasets.id
      DYNAMODB_JOBS_TABLE  = aws_dynamodb_table.training_jobs.name
      LOG_LEVEL            = var.environment == "prod" ? "INFO" : "DEBUG"
    }
  }
  
  tracing_config {
    mode = "Active"
  }
  
  tags = local.common_tags
}
```

---

## V. Output Best Practices

### 1. Structure

- **Group related outputs**
- **Include descriptions**
- **Mark sensitive outputs**
- **Use consistent naming**

**Examples:**

```hcl
# API Gateway outputs
output "api_gateway_url" {
  description = "Base URL for the API Gateway endpoint"
  value       = aws_apigatewayv2_stage.api.invoke_url
}

output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_apigatewayv2_api.api.id
}

# S3 bucket outputs
output "s3_bucket_datasets" {
  description = "Name of the S3 bucket for datasets"
  value       = aws_s3_bucket.datasets.id
}

# Sensitive outputs
output "database_connection_string" {
  description = "Database connection string"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}"
  sensitive   = true
}
```

---

## VI. State Management

### 1. Remote State

- **Use S3 backend** with DynamoDB locking
- **Enable encryption** for state files
- **Use separate state** per environment
- **Never commit state files**

**Examples:**

```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state-bucket"
    key            = "automl-lite/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### 2. Lifecycle Rules

- **Use prevent_destroy** for critical resources
- **Use create_before_destroy** for zero-downtime updates
- **Use ignore_changes** for external modifications

**Examples:**

```hcl
resource "aws_dynamodb_table" "training_jobs" {
  name         = "${local.name_prefix}-training-jobs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"
  
  lifecycle {
    prevent_destroy = true  # Prevent accidental deletion
  }
}

resource "aws_lambda_function" "api" {
  # ... configuration ...
  
  lifecycle {
    create_before_destroy = true  # Zero-downtime deployments
  }
}
```

---

## VII. Security Patterns

### 1. Encryption

- **Enable encryption at rest** for all storage
- **Use KMS keys** for sensitive data
- **Enable encryption in transit**

**Examples:**

```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "datasets" {
  bucket = aws_s3_bucket.datasets.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_dynamodb_table" "training_jobs" {
  name = "${local.name_prefix}-training-jobs"
  
  server_side_encryption {
    enabled = true
  }
}
```

### 2. Network Security

- **Use VPC endpoints** for AWS services
- **Configure security groups** with minimal access
- **Use private subnets** for compute resources

---

## VIII. Documentation

### 1. Comments

- **Document complex logic** inline
- **Explain non-obvious configurations**
- **Reference external docs** when helpful

**Examples:**

```hcl
# =============================================================================
# S3 Buckets - Storage for datasets, models, and reports
# =============================================================================
# Each bucket includes:
# - Public access blocking (security)
# - Lifecycle rules (cost management)
# - CORS configuration (frontend access)
# =============================================================================

resource "aws_s3_bucket" "datasets" {
  bucket = "${local.name_prefix}-datasets-${local.account_id}"
  
  # Account ID suffix ensures globally unique name without random strings
  # This allows predictable bucket names for CI/CD and documentation
}

# CORS origins are computed based on:
# 1. Manual override (highest priority)
# 2. Amplify domain (if enabled)
# 3. localhost (dev environment only)
locals {
  cors_origins = length(var.cors_allowed_origins) > 0 ? var.cors_allowed_origins : concat(
    local.amplify_enabled ? ["https://${aws_amplify_app.frontend[0].default_domain}"] : [],
    var.environment == "dev" ? ["http://localhost:3000"] : []
  )
}
```

### 2. README

- **Include prerequisites**
- **Document all variables**
- **Provide example usage**
- **List outputs**

---

## IX. Remember

- **Validate inputs** - use variable validation and preconditions
- **Fail fast** - catch configuration errors at plan time
- **Use locals** - compute once, reference many times
- **Least privilege** - only grant required permissions
- **Tag everything** - use common_tags for all resources
- **Document why** - explain non-obvious configurations
- **Keep it simple** - avoid over-engineering
- **Secure by default** - encryption, private access, minimal permissions
