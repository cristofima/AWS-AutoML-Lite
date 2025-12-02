# =============================================================================
# AWS Amplify - Frontend Hosting for Next.js SSR
# =============================================================================
# Amplify automatically builds and deploys on push to connected branches.
# This provides SSR support for dynamic routes like /configure/[datasetId]
#
# To enable: Set github_repository and github_token variables
# Example:
#   github_repository = "https://github.com/cristofima/AWS-AutoML-Lite"
#   github_token      = "ghp_xxxxxxxxxxxx"  # or use TF_VAR_github_token
# =============================================================================

locals {
  amplify_enabled = var.github_repository != "" && var.github_token != ""
}

# -----------------------------------------------------------------------------
# Amplify App
# -----------------------------------------------------------------------------
resource "aws_amplify_app" "frontend" {
  count = local.amplify_enabled ? 1 : 0

  name       = "${var.project_name}-${var.environment}"
  repository = var.github_repository

  # OAuth token for GitHub access (set via TF_VAR_github_token or terraform.tfvars)
  access_token = var.github_token

  # Build settings - Amplify will use amplify.yml from the repo
  build_spec = <<-EOT
    version: 1
    applications:
      - appRoot: frontend
        frontend:
          phases:
            preBuild:
              commands:
                - npm install -g pnpm
                - pnpm install --frozen-lockfile
            build:
              commands:
                - echo "NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL" >> .env.production
                - pnpm run build
          artifacts:
            baseDirectory: .next
            files:
              - '**/*'
          cache:
            paths:
              - node_modules/**/*
              - .next/cache/**/*
  EOT

  # Platform for Next.js SSR
  platform = "WEB_COMPUTE"

  # Environment variables available during build
  environment_variables = {
    NEXT_PUBLIC_API_URL = aws_api_gateway_stage.main.invoke_url
    AMPLIFY_MONOREPO_APP_ROOT = "frontend"
  }

  # Auto branch creation settings (optional - for feature branches)
  enable_auto_branch_creation = false

  # Note: No custom_rule needed - Next.js SSR handles all routing server-side

  tags = {
    Name        = "${var.project_name}-${var.environment}-frontend"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

# -----------------------------------------------------------------------------
# Branch Configuration
# -----------------------------------------------------------------------------
resource "aws_amplify_branch" "main" {
  count = local.amplify_enabled ? 1 : 0

  app_id      = aws_amplify_app.frontend[0].id
  branch_name = var.environment == "prod" ? "main" : "dev"

  # Enable auto build on push
  enable_auto_build = true

  # Framework for Next.js SSR
  framework = "Next.js - SSR"

  # Stage (PRODUCTION, BETA, DEVELOPMENT, EXPERIMENTAL, PULL_REQUEST)
  stage = var.environment == "prod" ? "PRODUCTION" : "DEVELOPMENT"

  # Environment variables specific to this branch (override app-level)
  environment_variables = {
    NEXT_PUBLIC_API_URL = aws_api_gateway_stage.main.invoke_url
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-branch"
    Environment = var.environment
    Project     = var.project_name
  }
}

# -----------------------------------------------------------------------------
# Webhook for CI/CD integration (optional - for manual triggers)
# -----------------------------------------------------------------------------
resource "aws_amplify_webhook" "main" {
  count = local.amplify_enabled ? 1 : 0

  app_id      = aws_amplify_app.frontend[0].id
  branch_name = aws_amplify_branch.main[0].branch_name
  description = "Webhook for ${var.environment} deployments"
}
