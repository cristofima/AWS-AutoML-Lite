# ECR Repository for Frontend
resource "aws_ecr_repository" "frontend" {
  name                 = "${local.name_prefix}-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  lifecycle {
    prevent_destroy = false
  }
}

# Push placeholder image if ECR is empty (production best practice)
resource "null_resource" "push_placeholder_image" {
  # Only run when ECR repo is created or changed
  triggers = {
    ecr_repo_url = aws_ecr_repository.frontend.repository_url
    environment  = var.environment
  }

  provisioner "local-exec" {
    command = <<-EOT
      # Check if image exists, if not push placeholder
      if ! aws ecr describe-images \
        --repository-name ${aws_ecr_repository.frontend.name} \
        --image-ids imageTag=${var.environment}-latest \
        --region ${var.aws_region} 2>/dev/null; then
        
        echo "Pushing placeholder nginx image..."
        docker pull nginx:alpine
        docker tag nginx:alpine ${aws_ecr_repository.frontend.repository_url}:${var.environment}-latest
        
        aws ecr get-login-password --region ${var.aws_region} | \
          docker login --username AWS --password-stdin ${aws_ecr_repository.frontend.repository_url}
        
        docker push ${aws_ecr_repository.frontend.repository_url}:${var.environment}-latest
        echo "Placeholder image pushed"
      else
        echo "Image already exists, skipping placeholder"
      fi
    EOT
  }

  depends_on = [aws_ecr_repository.frontend]
}

# ECR Lifecycle Policy (keep last 5 images)
resource "aws_ecr_lifecycle_policy" "frontend" {
  repository = aws_ecr_repository.frontend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus     = "tagged"
        tagPrefixList = [var.environment]
        countType     = "imageCountMoreThan"
        countNumber   = 5
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# IAM Role for App Runner
resource "aws_iam_role" "apprunner_instance" {
  name = "${local.name_prefix}-apprunner-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "tasks.apprunner.amazonaws.com"
      }
    }]
  })
}

# IAM Role for App Runner to access ECR
resource "aws_iam_role" "apprunner_ecr_access" {
  name = "${local.name_prefix}-apprunner-ecr-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "build.apprunner.amazonaws.com"
      }
    }]
  })
}

# Attach ECR read policy to App Runner role
resource "aws_iam_role_policy_attachment" "apprunner_ecr_access" {
  role       = aws_iam_role.apprunner_ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# App Runner Service
resource "aws_apprunner_service" "frontend" {
  service_name = "${local.name_prefix}-frontend"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.frontend.repository_url}:${var.environment}-latest"
      image_repository_type = "ECR"

      image_configuration {
        port = "3000"

        runtime_environment_variables = {
          NODE_ENV            = "production"
          NEXT_PUBLIC_API_URL = aws_api_gateway_stage.main.invoke_url
        }
      }
    }

    auto_deployments_enabled = false # Manual control via CI/CD
  }

  instance_configuration {
    cpu               = "1 vCPU"
    memory            = "2 GB"
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  # Auto-scaling configuration
  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.frontend.arn

  network_configuration {
    egress_configuration {
      egress_type = "DEFAULT" # Public internet access
    }
  }

  # Lifecycle: Ignore image changes (managed by CI/CD)
  lifecycle {
    ignore_changes = [
      source_configuration[0].image_repository[0].image_identifier,
      source_configuration[0].image_repository[0].image_configuration[0].runtime_environment_variables
    ]
  }

  # Ensure placeholder image exists before creating service
  depends_on = [
    null_resource.push_placeholder_image,
    aws_iam_role_policy_attachment.apprunner_ecr_access
  ]
}

# Auto-scaling configuration for App Runner
resource "aws_apprunner_auto_scaling_configuration_version" "frontend" {
  auto_scaling_configuration_name = "${local.name_prefix}-fe-autoscale"

  max_concurrency = 100 # Max concurrent requests per instance
  min_size        = 1   # Minimum instances (always 1 running)
  max_size        = 3   # Maximum instances for scaling
}
