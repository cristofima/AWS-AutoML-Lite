# Get AWS account ID and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Get default VPC if not specified
data "aws_vpc" "default" {
  count   = var.vpc_id == "" ? 1 : 0
  default = true
}

# Get subnets if not specified
data "aws_subnets" "default" {
  count = length(var.subnet_ids) == 0 ? 1 : 0

  filter {
    name   = "vpc-id"
    values = [var.vpc_id != "" ? var.vpc_id : data.aws_vpc.default[0].id]
  }
}

locals {
  account_id         = data.aws_caller_identity.current.account_id
  region             = data.aws_region.current.name
  vpc_id             = var.vpc_id != "" ? var.vpc_id : data.aws_vpc.default[0].id
  subnet_ids         = length(var.subnet_ids) > 0 ? var.subnet_ids : data.aws_subnets.default[0].ids
  security_group_ids = length(var.security_group_ids) > 0 ? var.security_group_ids : [aws_security_group.batch[0].id]

  name_prefix = "${var.project_name}-${var.environment}"
}
