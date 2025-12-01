output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_api_gateway_rest_api.main.id
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.api.arn
  sensitive   = true
}

output "datasets_bucket_name" {
  description = "S3 bucket for datasets"
  value       = aws_s3_bucket.datasets.id
}

output "models_bucket_name" {
  description = "S3 bucket for models"
  value       = aws_s3_bucket.models.id
}

output "reports_bucket_name" {
  description = "S3 bucket for reports"
  value       = aws_s3_bucket.reports.id
}

output "dynamodb_datasets_table" {
  description = "DynamoDB datasets table name"
  value       = aws_dynamodb_table.datasets.name
}

output "dynamodb_jobs_table" {
  description = "DynamoDB training jobs table name"
  value       = aws_dynamodb_table.training_jobs.name
}

output "batch_job_queue" {
  description = "Batch job queue name"
  value       = aws_batch_job_queue.training.name
}

output "batch_job_definition" {
  description = "Batch job definition ARN"
  value       = aws_batch_job_definition.training.arn
  sensitive   = true
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.training.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.training.name
}

output "frontend_url" {
  description = "CloudFront distribution URL for frontend"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "frontend_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for cache invalidation"
  value       = aws_cloudfront_distribution.frontend.id
}
