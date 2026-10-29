# Terraform Infrastructure-as-Code for AWS Free-Tier Deployment
# 100% Free-Tier Compliant ($0.00 Monthly Cost)

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

# 1. Amazon S3 Bucket for Historical Sales Datasets (5 GB Free Tier)
resource "aws_s3_bucket" "dataset_bucket" {
  bucket = "demand-forecast-datasets-freetier"

  tags = {
    Project     = "ProductDemandPrediction"
    CostCenter  = "FreeTier"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "s3_crypto" {
  bucket = aws_s3_bucket.dataset_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 2. Amazon DynamoDB Table for Demand Forecasts (25 GB Free Tier, 25 WCU/RCU)
resource "aws_dynamodb_table" "forecasts_table" {
  name           = "ProductDemandForecasts"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = "id"
  range_key      = "timestamp"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Project    = "ProductDemandPrediction"
    CostCenter = "FreeTier"
  }
}

output "s3_bucket_name" {
  value = aws_s3_bucket.dataset_bucket.bucket
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.forecasts_table.name
}
