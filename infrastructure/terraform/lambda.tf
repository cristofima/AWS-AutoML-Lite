# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.name_prefix}-api"
  retention_in_days = var.cloudwatch_retention_days
}

# CloudWatch Log Group for Batch
resource "aws_cloudwatch_log_group" "batch" {
  name              = "/aws/batch/${local.name_prefix}-training"
  retention_in_days = var.cloudwatch_retention_days
}

# Package Lambda function
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../backend"
  output_path = "${path.module}/lambda_function.zip"
  excludes = [
    "training",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    "tests"
  ]
}

# Lambda Function
resource "aws_lambda_function" "api" {
  filename         = data.archive_file.lambda.output_path
  function_name    = "${local.name_prefix}-api"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "api.main.handler"
  source_code_hash = data.archive_file.lambda.output_base64sha256
  runtime          = "python3.11"
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout

  environment {
    variables = {
      ENVIRONMENT               = var.environment
      REGION                    = local.region
      S3_BUCKET_DATASETS        = aws_s3_bucket.datasets.id
      S3_BUCKET_MODELS          = aws_s3_bucket.models.id
      S3_BUCKET_REPORTS         = aws_s3_bucket.reports.id
      DYNAMODB_DATASETS_TABLE   = aws_dynamodb_table.datasets.name
      DYNAMODB_JOBS_TABLE       = aws_dynamodb_table.training_jobs.name
      BATCH_JOB_QUEUE           = aws_batch_job_queue.training.name
      BATCH_JOB_DEFINITION      = aws_batch_job_definition.training.arn
    }
  }

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy_attachment.lambda_basic
  ]
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}
