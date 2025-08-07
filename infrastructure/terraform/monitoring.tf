# CloudWatch Log Groups for Lambda functions
resource "aws_cloudwatch_log_group" "match_collector_logs" {
  name              = "/aws/lambda/${aws_lambda_function.match_collector.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "rpi_calculator_logs" {
  name              = "/aws/lambda/${aws_lambda_function.rpi_calculator.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "gist_publisher_logs" {
  name              = "/aws/lambda/${aws_lambda_function.gist_publisher.function_name}"
  retention_in_days = 14
}

# CloudWatch Alarms for Lambda errors
resource "aws_cloudwatch_metric_alarm" "match_collector_errors" {
  alarm_name          = "${var.project_name}-match-collector-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors match collector lambda errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.match_collector.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "rpi_calculator_errors" {
  alarm_name          = "${var.project_name}-rpi-calculator-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors RPI calculator lambda errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.rpi_calculator.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "gist_publisher_errors" {
  alarm_name          = "${var.project_name}-gist-publisher-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors gist publisher lambda errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.gist_publisher.function_name
  }
}

# CloudWatch Alarms for Lambda duration
resource "aws_cloudwatch_metric_alarm" "match_collector_duration" {
  alarm_name          = "${var.project_name}-match-collector-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "240000"  # 4 minutes
  alarm_description   = "This metric monitors match collector lambda duration"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.match_collector.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "rpi_calculator_duration" {
  alarm_name          = "${var.project_name}-rpi-calculator-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "840000"  # 14 minutes
  alarm_description   = "This metric monitors RPI calculator lambda duration"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.rpi_calculator.function_name
  }
}

# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"
}

# SNS Topic subscription (email)
resource "aws_sns_topic_subscription" "email_alerts" {
  count     = length(var.alert_emails)
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_emails[count.index]
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.match_collector.function_name],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Match Collector Lambda Metrics"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.rpi_calculator.function_name],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "RPI Calculator Lambda Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.gist_publisher.function_name],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Gist Publisher Lambda Metrics"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.matches.name],
            [".", "ConsumedWriteCapacityUnits", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "DynamoDB Metrics"
        }
      }
    ]
  })
}

# Variables for monitoring
variable "alert_emails" {
  description = "List of email addresses to receive alerts"
  type        = list(string)
  default     = []
} 