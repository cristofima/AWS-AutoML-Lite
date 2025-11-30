# DynamoDB Table for Datasets
resource "aws_dynamodb_table" "datasets" {
  name         = "${local.name_prefix}-datasets"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "dataset_id"

  attribute {
    name = "dataset_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "uploaded_at"
    type = "S"
  }

  global_secondary_index {
    name            = "user_id-uploaded_at-index"
    hash_key        = "user_id"
    range_key       = "uploaded_at"
    projection_type = "ALL"
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${local.name_prefix}-datasets"
  }
}

# DynamoDB Table for Training Jobs
resource "aws_dynamodb_table" "training_jobs" {
  name         = "${local.name_prefix}-training-jobs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "user_id-created_at-index"
    hash_key        = "user_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${local.name_prefix}-training-jobs"
  }
}
