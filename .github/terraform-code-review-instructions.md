# GitHub Copilot Custom Instructions - Terraform Code Review

These instructions guide GitHub Copilot in reviewing Terraform code to ensure adherence to HashiCorp best practices, security standards, and infrastructure-as-code principles.

---

## Review Mindset

**Focus on:**

- Security vulnerabilities and misconfigurations
- Resource naming and organization
- Input validation and fail-fast patterns
- IAM least privilege
- Cost implications
- State management safety

**Balance:**

- Be constructive, not just critical
- Prioritize issues by severity (Critical → Major → Minor → Nitpick)
- Suggest concrete improvements with examples
- Acknowledge good practices when present

---

## I. Security Review

### 1. Overly Permissive IAM Policies

**Check for:**

- [ ] `*` wildcards in actions
- [ ] `*` wildcards in resources
- [ ] Missing resource ARN constraints
- [ ] Policies granting more than needed

**Examples of issues to flag:**

```hcl
# 🚨 CRITICAL - Overly permissive
data "aws_iam_policy_document" "lambda" {
  statement {
    effect    = "Allow"
    actions   = ["s3:*"]
    resources = ["*"]
  }
}

# ✅ SUGGESTION: Least privilege with specific resources
data "aws_iam_policy_document" "lambda" {
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
}
```

### 2. Public Access to Resources

**Check for:**

- [ ] S3 buckets without public access blocks
- [ ] Security groups with 0.0.0.0/0 ingress
- [ ] RDS instances publicly accessible
- [ ] API Gateway without authentication

**Examples of issues to flag:**

```hcl
# 🚨 CRITICAL - Missing public access block
resource "aws_s3_bucket" "data" {
  bucket = "my-bucket"
  # No public access block = potentially public
}

# ✅ SUGGESTION: Block public access
resource "aws_s3_bucket" "data" {
  bucket = "my-bucket"
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

### 3. Missing Encryption

**Check for:**

- [ ] S3 buckets without encryption
- [ ] DynamoDB tables without encryption
- [ ] RDS without encryption at rest
- [ ] EBS volumes unencrypted

**Examples of issues to flag:**

```hcl
# 🚨 MAJOR - No encryption
resource "aws_dynamodb_table" "jobs" {
  name = "training-jobs"
  # Missing server_side_encryption block
}

# ✅ SUGGESTION: Enable encryption
resource "aws_dynamodb_table" "jobs" {
  name = "training-jobs"
  
  server_side_encryption {
    enabled = true
  }
}
```

### 4. Hardcoded Secrets

**Check for:**

- [ ] Credentials in .tf files
- [ ] Secrets in default values
- [ ] API keys in environment variables
- [ ] Missing sensitive = true on secret variables

**Examples of issues to flag:**

```hcl
# 🚨 CRITICAL - Hardcoded credentials
variable "db_password" {
  default = "supersecret123"  # Never do this!
}

# 🚨 CRITICAL - Missing sensitive flag
variable "api_key" {
  type = string
  # Should be marked sensitive
}

# ✅ SUGGESTION: Proper secret handling
variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
  # No default - must be provided externally
}
```

---

## II. Validation Review

### 1. Missing Variable Validation

**Check for:**

- [ ] Variables without type constraints
- [ ] Enum-like variables without validation
- [ ] Numeric variables without range checks
- [ ] String variables without pattern validation

**Examples of issues to flag:**

```hcl
# 🚨 MAJOR - No validation
variable "environment" {
  type = string
  # Any string accepted, could cause issues
}

# ✅ SUGGESTION: Add validation
variable "environment" {
  type        = string
  description = "Deployment environment"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}
```

### 2. Missing Preconditions

**Check for:**

- [ ] Resources with implicit assumptions
- [ ] Conditional logic that could result in invalid state
- [ ] Dependencies on external configuration
- [ ] Edge cases not handled

**Examples of issues to flag:**

```hcl
# 🚨 MAJOR - Edge case not handled
# If amplify disabled AND not dev AND no manual origins = empty CORS
resource "aws_s3_bucket_cors_configuration" "datasets" {
  cors_rule {
    allowed_origins = local.cors_origins  # Could be []
  }
}

# ✅ SUGGESTION: Add precondition
resource "aws_s3_bucket_cors_configuration" "datasets" {
  cors_rule {
    allowed_origins = local.cors_origins
  }
  
  lifecycle {
    precondition {
      condition     = length(local.cors_origins) > 0
      error_message = "CORS origins cannot be empty. Either enable Amplify, use dev environment, or set cors_allowed_origins."
    }
  }
}
```

---

## III. DRY Review

### 1. Repeated Values

**Check for:**

- [ ] Same expression computed multiple times
- [ ] Resource names with repeated patterns
- [ ] Tags duplicated across resources
- [ ] Similar resource blocks

**Examples of issues to flag:**

```hcl
# 🚨 MINOR - Repeated computation
resource "aws_s3_bucket" "datasets" {
  bucket = "${var.project_name}-${var.environment}-datasets-${data.aws_caller_identity.current.account_id}"
  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "models" {
  bucket = "${var.project_name}-${var.environment}-models-${data.aws_caller_identity.current.account_id}"
  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# ✅ SUGGESTION: Use locals
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  account_id  = data.aws_caller_identity.current.account_id
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket" "datasets" {
  bucket = "${local.name_prefix}-datasets-${local.account_id}"
  tags   = local.common_tags
}
```

### 2. Similar Resources Without for_each

**Check for:**

- [ ] Multiple resources with identical structure
- [ ] Copy-paste patterns
- [ ] Resources differing only by name

**Examples of issues to flag:**

```hcl
# 🚨 MINOR - Could use for_each
resource "aws_s3_bucket" "bucket_a" {
  bucket = "${local.name_prefix}-a"
}

resource "aws_s3_bucket" "bucket_b" {
  bucket = "${local.name_prefix}-b"
}

resource "aws_s3_bucket" "bucket_c" {
  bucket = "${local.name_prefix}-c"
}

# ✅ SUGGESTION: Use for_each
resource "aws_s3_bucket" "buckets" {
  for_each = toset(["a", "b", "c"])
  
  bucket = "${local.name_prefix}-${each.key}"
}
```

---

## IV. Naming Review

### 1. Inconsistent Naming

**Check for:**

- [ ] Mixed naming conventions (snake_case vs camelCase)
- [ ] Inconsistent prefixes
- [ ] Unclear resource names
- [ ] Missing environment/project identifiers

**Examples of issues to flag:**

```hcl
# 🚨 MINOR - Inconsistent naming
resource "aws_s3_bucket" "MyBucket" { }      # PascalCase
resource "aws_lambda_function" "func-1" { }  # kebab-case
resource "aws_dynamodb_table" "table" { }    # Too generic

# ✅ SUGGESTION: Consistent snake_case, descriptive
resource "aws_s3_bucket" "datasets" { }
resource "aws_lambda_function" "api_handler" { }
resource "aws_dynamodb_table" "training_jobs" { }
```

### 2. Variable Naming Issues

**Check for:**

- [ ] Negative naming (disabled instead of enabled)
- [ ] Missing units in numeric variables
- [ ] Single-letter or cryptic names
- [ ] Inconsistent conventions

**Examples of issues to flag:**

```hcl
# 🚨 MINOR - Poor variable naming
variable "dis_enc" { }          # Cryptic abbreviation
variable "disable_logging" { }  # Negative (avoid double negatives)
variable "timeout" { }          # Missing units

# ✅ SUGGESTION: Clear, positive, with units
variable "encryption_enabled" {
  type        = bool
  default     = true
  description = "Enable server-side encryption"
}

variable "lambda_timeout_seconds" {
  type        = number
  default     = 30
  description = "Lambda function timeout in seconds"
}
```

---

## V. Resource Configuration Review

### 1. Missing Tags

**Check for:**

- [ ] Resources without tags
- [ ] Missing required tags (Project, Environment)
- [ ] Inconsistent tag keys

**Examples of issues to flag:**

```hcl
# 🚨 MINOR - No tags
resource "aws_lambda_function" "api" {
  function_name = "api-handler"
  # No tags = hard to manage/track costs
}

# ✅ SUGGESTION: Include standard tags
resource "aws_lambda_function" "api" {
  function_name = "${local.name_prefix}-api"
  tags          = local.common_tags
}
```

### 2. Missing Lifecycle Rules

**Check for:**

- [ ] Critical resources without prevent_destroy
- [ ] Resources that need create_before_destroy
- [ ] External modifications not ignored

**Examples of issues to flag:**

```hcl
# 🚨 MAJOR - Critical table can be destroyed accidentally
resource "aws_dynamodb_table" "production_data" {
  name = "production-user-data"
  # No lifecycle block - can be destroyed with terraform destroy
}

# ✅ SUGGESTION: Protect critical resources
resource "aws_dynamodb_table" "production_data" {
  name = "production-user-data"
  
  lifecycle {
    prevent_destroy = true
  }
}
```

### 3. Hardcoded Values

**Check for:**

- [ ] Hardcoded region
- [ ] Hardcoded account IDs
- [ ] Hardcoded ARNs
- [ ] Magic numbers without explanation

**Examples of issues to flag:**

```hcl
# 🚨 MAJOR - Hardcoded values
resource "aws_iam_policy" "lambda" {
  policy = jsonencode({
    Statement = [{
      Resource = "arn:aws:s3:::my-bucket-123456789012/*"  # Hardcoded
    }]
  })
}

# ✅ SUGGESTION: Use references
resource "aws_iam_policy" "lambda" {
  policy = jsonencode({
    Statement = [{
      Resource = "${aws_s3_bucket.datasets.arn}/*"
    }]
  })
}
```

---

## VI. State Safety Review

### 1. Destructive Changes

**Check for:**

- [ ] Resource replacements that could cause data loss
- [ ] Name changes on stateful resources
- [ ] Missing data migration plans

**Examples of issues to flag:**

```hcl
# 🚨 CRITICAL - Changing name forces replacement
# Before:
resource "aws_dynamodb_table" "jobs" {
  name = "training-jobs"
}

# After (in PR):
resource "aws_dynamodb_table" "jobs" {
  name = "training-jobs-v2"  # Forces new table, data lost!
}
```

### 2. Count/For_Each Changes

**Check for:**

- [ ] Changing from count to for_each (causes replacement)
- [ ] Reordering count-based resources
- [ ] Index-based references

**Examples of issues to flag:**

```hcl
# 🚨 MAJOR - Index-based reference is fragile
resource "aws_subnet" "private" {
  count = 3
}

resource "aws_instance" "app" {
  subnet_id = aws_subnet.private[0].id  # Fragile if order changes
}

# ✅ SUGGESTION: Use for_each with stable keys
resource "aws_subnet" "private" {
  for_each = toset(["a", "b", "c"])
}
```

---

## VII. Output Review

### 1. Missing Outputs

**Check for:**

- [ ] Important values not exposed
- [ ] Outputs needed by other configurations missing
- [ ] No outputs for API URLs, resource IDs

**Examples of issues to flag:**

```hcl
# 🚨 MINOR - No outputs for important values
# File has Lambda, API Gateway, DynamoDB but no outputs
# Other configurations/users can't reference these

# ✅ SUGGESTION: Add essential outputs
output "api_gateway_url" {
  description = "Base URL for the API"
  value       = aws_apigatewayv2_stage.api.invoke_url
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.api.function_name
}
```

### 2. Sensitive Output Issues

**Check for:**

- [ ] Sensitive values not marked sensitive
- [ ] Credentials in outputs
- [ ] Secrets exposed

**Examples of issues to flag:**

```hcl
# 🚨 CRITICAL - Sensitive data exposed
output "database_password" {
  value = var.database_password
  # Missing sensitive = true
}

# ✅ SUGGESTION: Mark as sensitive
output "database_password" {
  value     = var.database_password
  sensitive = true
}
```

---

## VIII. Documentation Review

### 1. Missing Descriptions

**Check for:**

- [ ] Variables without descriptions
- [ ] Outputs without descriptions
- [ ] Complex logic without comments

**Examples of issues to flag:**

```hcl
# 🚨 MINOR - No descriptions
variable "vpc_id" {
  type = string
}

output "bucket_name" {
  value = aws_s3_bucket.main.id
}

# ✅ SUGGESTION: Add descriptions
variable "vpc_id" {
  type        = string
  description = "ID of the VPC to deploy resources in"
}

output "bucket_name" {
  description = "Name of the main S3 bucket"
  value       = aws_s3_bucket.main.id
}
```

### 2. Missing File Headers

**Check for:**

- [ ] Files without purpose explanation
- [ ] Complex files without overview
- [ ] Missing resource grouping comments

---

## IX. Review Checklist Summary

### Critical (Must Fix)

- [ ] Overly permissive IAM policies (`*` actions/resources)
- [ ] Public access to S3, databases
- [ ] Hardcoded secrets or credentials
- [ ] Sensitive outputs not marked sensitive
- [ ] Destructive changes without migration plan

### Major (Should Fix)

- [ ] Missing encryption at rest
- [ ] Missing variable validation
- [ ] Missing preconditions for edge cases
- [ ] Critical resources without prevent_destroy
- [ ] Hardcoded account IDs, regions, ARNs

### Minor (Nice to Fix)

- [ ] DRY violations (repeated values)
- [ ] Inconsistent naming conventions
- [ ] Missing tags
- [ ] Missing descriptions
- [ ] Could use for_each instead of copy-paste

### Nitpick (Optional)

- [ ] File organization preferences
- [ ] Comment formatting
- [ ] Whitespace/indentation style
