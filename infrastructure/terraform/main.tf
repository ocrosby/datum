terraform {
  required_version = ">= 1.0"
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

# S3 Bucket for raw data storage
resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.project_name}-raw-data-${random_string.bucket_suffix.result}"
}

resource "aws_s3_bucket_versioning" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket for processed data
resource "aws_s3_bucket" "processed_data" {
  bucket = "${var.project_name}-processed-data-${random_string.bucket_suffix.result}"
}

# DynamoDB for match data and RPI calculations
resource "aws_dynamodb_table" "matches" {
  name           = "${var.project_name}-matches"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "match_id"
  range_key      = "date"

  attribute {
    name = "match_id"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"
  }

  attribute {
    name = "home_team"
    type = "S"
  }

  attribute {
    name = "away_team"
    type = "S"
  }

  global_secondary_index {
    name     = "date-index"
    hash_key = "date"
    projection_type = "ALL"
  }

  global_secondary_index {
    name     = "teams-index"
    hash_key = "home_team"
    range_key = "away_team"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "rpi_calculations" {
  name           = "${var.project_name}-rpi-calculations"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "calculation_date"
  range_key      = "team_id"

  attribute {
    name = "calculation_date"
    type = "S"
  }

  attribute {
    name = "team_id"
    type = "S"
  }
}

# Cache table for storing RPI calculations and other cached data
resource "aws_dynamodb_table" "cache" {
  name           = "${var.project_name}-cache"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "cache_key"
  range_key      = "cache_type"

  attribute {
    name = "cache_key"
    type = "S"
  }

  attribute {
    name = "cache_type"
    type = "S"
  }

  # TTL for automatic cache expiration
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}

# Calculation status table for tracking ongoing RPI calculations
resource "aws_dynamodb_table" "calculation_status" {
  name           = "${var.project_name}-calculation-status"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "calculation_date"
  range_key      = "calculation_id"

  attribute {
    name = "calculation_date"
    type = "S"
  }

  attribute {
    name = "calculation_id"
    type = "S"
  }

  # TTL for automatic cleanup of old status records
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}

# Team metadata table for storing conference and organization information
resource "aws_dynamodb_table" "team_metadata" {
  name           = "${var.project_name}-team-metadata"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "team_id"

  attribute {
    name = "team_id"
    type = "S"
  }

  # GSI for organization queries
  global_secondary_index {
    name     = "organization-division-gender-index"
    hash_key = "organization"
    range_key = "division"
    projection_type = "ALL"
  }

  # GSI for conference queries
  global_secondary_index {
    name     = "conference-organization-index"
    hash_key = "conference"
    range_key = "organization"
    projection_type = "ALL"
  }

  # GSI for team name searches
  global_secondary_index {
    name     = "team_name-index"
    hash_key = "team_name"
    projection_type = "ALL"
  }
}

# Event Store for event sourcing
resource "aws_dynamodb_table" "event_store" {
  name           = "${var.project_name}-event-store"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "aggregate_id"
  range_key      = "event_id"

  attribute {
    name = "aggregate_id"
    type = "S"
  }

  attribute {
    name = "event_id"
    type = "S"
  }

  attribute {
    name = "event_type"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  # GSI for event type queries
  global_secondary_index {
    name     = "event-type-timestamp-index"
    hash_key = "event_type"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  # GSI for timestamp queries
  global_secondary_index {
    name     = "timestamp-index"
    hash_key = "timestamp"
    projection_type = "ALL"
  }
}

# Event Bus for decoupled communication
resource "aws_cloudwatch_event_bus" "main" {
  name = "${var.project_name}-event-bus"
}

# Event Bus for domain-specific events
resource "aws_cloudwatch_event_bus" "soccer_events" {
  name = "${var.project_name}-soccer-events"
}

# Event Bus for calculation events
resource "aws_cloudwatch_event_bus" "calculation_events" {
  name = "${var.project_name}-calculation-events"
}

# Event Bus for metadata events
resource "aws_cloudwatch_event_bus" "metadata_events" {
  name = "${var.project_name}-metadata-events"
}

# EventBridge for scheduling
resource "aws_cloudwatch_event_rule" "daily_rpi_calculation" {
  name                = "${var.project_name}-daily-rpi-calculation"
  description         = "Trigger daily RPI calculation"
  schedule_expression = "cron(0 6 * * ? *)"  # 6 AM UTC daily
}

resource "aws_cloudwatch_event_rule" "match_data_collection" {
  name                = "${var.project_name}-match-data-collection"
  description         = "Trigger match data collection"
  schedule_expression = "cron(0 */4 * * ? *)"  # Every 4 hours
}

# Lambda functions
resource "aws_lambda_function" "match_collector" {
  filename         = "../lambda/match_collector.zip"
  function_name    = "${var.project_name}-match-collector"
  role            = aws_iam_role.lambda_role.arn
  handler         = "match_collector.lambda_handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      RAW_DATA_BUCKET = aws_s3_bucket.raw_data.bucket
      MATCHES_TABLE   = aws_dynamodb_table.matches.name
    }
  }
}

resource "aws_lambda_function" "rpi_calculator" {
  filename         = "../lambda/rpi_calculator.zip"
  function_name    = "${var.project_name}-rpi-calculator"
  role            = aws_iam_role.lambda_role.arn
  handler         = "rpi_calculator.lambda_handler"
  runtime         = "python3.11"
  timeout         = 900
  memory_size     = 1024

  environment {
    variables = {
      PROCESSED_DATA_BUCKET = aws_s3_bucket.processed_data.bucket
      RPI_TABLE            = aws_dynamodb_table.rpi_calculations.name
      MATCHES_TABLE        = aws_dynamodb_table.matches.name
      GITHUB_TOKEN         = var.github_token
    }
  }
}

resource "aws_lambda_function" "gist_publisher" {
  filename         = "../lambda/gist_publisher.zip"
  function_name    = "${var.project_name}-gist-publisher"
  role            = aws_iam_role.lambda_role.arn
  handler         = "gist_publisher.lambda_handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 256

  environment {
    variables = {
      PROCESSED_DATA_BUCKET = aws_s3_bucket.processed_data.bucket
      GITHUB_TOKEN         = var.github_token
    }
  }
}

# EventBridge targets
resource "aws_cloudwatch_event_target" "match_collector_target" {
  rule      = aws_cloudwatch_event_rule.match_data_collection.name
  target_id = "MatchCollectorTarget"
  arn       = aws_lambda_function.match_collector.arn
}

resource "aws_cloudwatch_event_target" "rpi_calculator_target" {
  rule      = aws_cloudwatch_event_rule.daily_rpi_calculation.name
  target_id = "RPICalculatorTarget"
  arn       = aws_lambda_function.rpi_calculator.arn
}

# Lambda permissions
resource "aws_lambda_permission" "match_collector_permission" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.match_collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.match_data_collection.arn
}

resource "aws_lambda_permission" "rpi_calculator_permission" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rpi_calculator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_rpi_calculation.arn
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*",
          aws_s3_bucket.processed_data.arn,
          "${aws_s3_bucket.processed_data.arn}/*"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ],
        Resource = [
          aws_dynamodb_table.matches.arn,
          aws_dynamodb_table.rpi_calculations.arn,
          aws_dynamodb_table.cache.arn,
          aws_dynamodb_table.calculation_status.arn,
          aws_dynamodb_table.team_metadata.arn,
          aws_dynamodb_table.event_store.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Random string for bucket names
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ncaa-soccer-etl"
}

variable "github_token" {
  description = "GitHub token for gist creation"
  type        = string
  sensitive   = true
}

# Outputs
output "raw_data_bucket" {
  value = aws_s3_bucket.raw_data.bucket
}

output "processed_data_bucket" {
  value = aws_s3_bucket.processed_data.bucket
}

output "matches_table" {
  value = aws_dynamodb_table.matches.name
}

output "rpi_table" {
  value = aws_dynamodb_table.rpi_calculations.name
} 