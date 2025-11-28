# Security Group for Batch (if not provided)
resource "aws_security_group" "batch" {
  count       = length(var.security_group_ids) == 0 ? 1 : 0
  name        = "${local.name_prefix}-batch-sg"
  description = "Security group for AutoML Batch compute environment"
  vpc_id      = local.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${local.name_prefix}-batch-sg"
  }
}

# Batch Compute Environment
resource "aws_batch_compute_environment" "training" {
  compute_environment_name = "${local.name_prefix}-compute"
  type                     = "MANAGED"
  state                    = "ENABLED"
  service_role             = aws_iam_role.batch_service.arn

  compute_resources {
    type      = "FARGATE_SPOT"
    max_vcpus = var.batch_max_vcpus

    subnets            = local.subnet_ids
    security_group_ids = local.security_group_ids
  }
}

# Batch Job Queue
resource "aws_batch_job_queue" "training" {
  name     = "${local.name_prefix}-training-queue"
  state    = "ENABLED"
  priority = 1

  compute_environment_order {
    order               = 1
    compute_environment = aws_batch_compute_environment.training.arn
  }
}

# Batch Job Definition
resource "aws_batch_job_definition" "training" {
  name = "${local.name_prefix}-training-job"
  type = "container"

  platform_capabilities = ["FARGATE"]

  container_properties = jsonencode({
    image = "${aws_ecr_repository.training.repository_url}:latest"

    resourceRequirements = [
      {
        type  = "VCPU"
        value = var.batch_vcpu
      },
      {
        type  = "MEMORY"
        value = var.batch_memory
      }
    ]

    jobRoleArn       = aws_iam_role.batch_job.arn
    executionRoleArn = aws_iam_role.batch_execution.arn

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.batch.name
        "awslogs-region"        = local.region
        "awslogs-stream-prefix" = "training"
      }
    }

    environment = [
      {
        name  = "AWS_DEFAULT_REGION"
        value = local.region
      }
    ]
  })

  retry_strategy {
    attempts = 1
  }

  timeout {
    attempt_duration_seconds = 3600
  }
}
