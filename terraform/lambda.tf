# CI deploys code with aws lambda update-function-code; api/authorizer/rollover share the API package.

# Placeholder zip until CI's first deploy; until then every invoke fails with an import error.
data "archive_file" "placeholder" {
  type        = "zip"
  output_path = "${path.module}/build/placeholder.zip" # build/ is gitignored

  source {
    filename = "placeholder.py"
    content  = "def lambda_handler(event, context):\n    raise RuntimeError(\"placeholder: deploy code from CI\")\n"
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  for_each          = local.lambdas
  name              = "/aws/lambda/${local.name}-${each.key}"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "this" {
  for_each = local.lambdas

  function_name    = "${local.name}-${each.key}"
  role             = data.aws_iam_role.lambda_exec.arn
  handler          = each.value.handler
  runtime          = "python3.13" # backend requires-python >=3.13,<3.14
  architectures    = ["arm64"]    # pure-Python closure; Graviton is cheaper per GB-s
  memory_size      = each.value.memory
  timeout          = each.value.timeout
  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256

  environment {
    variables = local.lambda_env[each.key]
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = local.lambda_log_level
    system_log_level      = "INFO"
  }

  # Code is deployed by CI; Terraform owns configuration only.
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

# No function URLs: API Gateway is the only public entry; each permission is scoped to its caller's source ARN.

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this["api"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/${aws_api_gateway_stage.api.stage_name}/*/*"
}

resource "aws_lambda_permission" "authorizer" {
  statement_id  = "AllowApiGatewayAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this["authorizer"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/authorizers/*"
}

# Batch size 1: one message is a whole run of up to 14 Bedrock calls, processed within one timeout.
resource "aws_lambda_event_source_mapping" "ai" {
  event_source_arn        = aws_sqs_queue.generation.arn
  function_name           = aws_lambda_function.this["ai"].arn
  batch_size              = 1
  function_response_types = ["ReportBatchItemFailures"]

  scaling_config {
    maximum_concurrency = var.ai_max_concurrency
  }
}

# EventBridge rule, not Scheduler: Scheduler needs a role this account cannot create; rule cron is UTC-only.
resource "aws_cloudwatch_event_rule" "rollover" {
  name                = "${local.name}-week-rollover"
  description         = "Week rollover, Sunday night Europe/Madrid"
  schedule_expression = var.rollover_schedule
}

resource "aws_cloudwatch_event_target" "rollover" {
  rule = aws_cloudwatch_event_rule.rollover.name
  arn  = aws_lambda_function.this["rollover"].arn

  retry_policy {
    maximum_retry_attempts       = 3 # the job is idempotent
    maximum_event_age_in_seconds = 3600
  }
}

resource "aws_lambda_permission" "rollover" {
  statement_id  = "AllowEventBridgeRollover"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this["rollover"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rollover.arn
}
