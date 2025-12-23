# =============================================================================
# CORS Origins - Computed once and validated
# =============================================================================
# The cors_origins local calculates allowed origins by combining:
# 1. Manual origins from var.cors_allowed_origins (if any)
# 2. Amplify branch domain (e.g., https://dev.xxx.amplifyapp.com) when enabled
# 3. Amplify default domain (e.g., https://xxx.amplifyapp.com) when enabled
# 4. localhost:3000 (only in dev environment)
#
# IMPORTANT: In production, either enable Amplify OR set cors_allowed_origins
# =============================================================================
locals {
  cors_origins = distinct(concat(
    # Manual origins (can be empty)
    var.cors_allowed_origins,
    # Amplify branch domain (e.g., https://dev.xxx.amplifyapp.com)
    local.amplify_enabled ? ["https://${aws_amplify_branch.main[0].branch_name}.${aws_amplify_app.frontend[0].default_domain}"] : [],
    # Amplify default domain (e.g., https://xxx.amplifyapp.com) - for main/production
    local.amplify_enabled ? ["https://${aws_amplify_app.frontend[0].default_domain}"] : [],
    # localhost for dev
    var.environment == "dev" ? ["http://localhost:3000"] : []
  ))
}

# S3 Bucket for Datasets
resource "aws_s3_bucket" "datasets" {
  bucket = "${local.name_prefix}-datasets-${local.account_id}"
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
    id     = "delete-old-datasets"
    status = "Enabled"

    filter {
      prefix = "datasets/"
    }

    expiration {
      days = var.s3_lifecycle_days
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "datasets" {
  bucket = aws_s3_bucket.datasets.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "GET"]
    allowed_origins = local.cors_origins
    max_age_seconds = 3600
  }

  lifecycle {
    precondition {
      condition     = length(local.cors_origins) > 0
      error_message = "CORS allowed_origins cannot be empty. Either enable Amplify (set github_repository and github_token), use dev environment, or set cors_allowed_origins manually."
    }
  }
}

# S3 Bucket for Models
resource "aws_s3_bucket" "models" {
  bucket = "${local.name_prefix}-models-${local.account_id}"
}

resource "aws_s3_bucket_public_access_block" "models" {
  bucket = aws_s3_bucket.models.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "models" {
  bucket = aws_s3_bucket.models.id

  rule {
    id     = "delete-old-models"
    status = "Enabled"

    filter {
      prefix = "models/"
    }

    expiration {
      days = var.s3_lifecycle_days
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "models" {
  bucket = aws_s3_bucket.models.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = local.cors_origins
    expose_headers  = ["Content-Disposition"]
    max_age_seconds = 3600
  }

  lifecycle {
    precondition {
      condition     = length(local.cors_origins) > 0
      error_message = "CORS allowed_origins cannot be empty. Either enable Amplify (set github_repository and github_token), use dev environment, or set cors_allowed_origins manually."
    }
  }
}

# S3 Bucket for Reports
resource "aws_s3_bucket" "reports" {
  bucket = "${local.name_prefix}-reports-${local.account_id}"
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    id     = "delete-old-reports"
    status = "Enabled"

    filter {
      prefix = "reports/"
    }

    expiration {
      days = var.s3_lifecycle_days
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = local.cors_origins
    expose_headers  = ["Content-Disposition"]
    max_age_seconds = 3600
  }

  lifecycle {
    precondition {
      condition     = length(local.cors_origins) > 0
      error_message = "CORS allowed_origins cannot be empty. Either enable Amplify (set github_repository and github_token), use dev environment, or set cors_allowed_origins manually."
    }
  }
}
