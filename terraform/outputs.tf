output "app_url" {
  description = "Public HTTPS URL: SPA at /, API at /v1/*."
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "For cache invalidations after an SPA deploy."
  value       = aws_cloudfront_distribution.main.id
}

output "frontend_bucket" {
  description = "Bucket the Vite build (frontend/dist) is synced to."
  value       = aws_s3_bucket.frontend.bucket
}

output "api_invoke_url" {
  description = "Direct API Gateway stage URL (the SPA uses app_url/v1 instead)."
  value       = aws_api_gateway_stage.api.invoke_url
}

output "data_table_name" {
  description = "DynamoDB single table (PLANNER_DATA_TABLE)."
  value       = aws_dynamodb_table.data.name
}

output "generation_queue_url" {
  description = "api -> ai generation queue (GENERATION_QUEUE_URL)."
  value       = aws_sqs_queue.generation.url
}

output "lambda_function_names" {
  description = "Function name per entry point, for CI's update-function-code (api/authorizer/rollover share the API package)."
  value       = { for k, f in aws_lambda_function.this : k => f.function_name }
}

# needs role permission: ssm:GetParameter (remove with aws_ssm_parameter.ai_generation_enabled)
output "ai_kill_switch_parameter" {
  description = "Set to \"false\" to stop AI generation by hand."
  value       = aws_ssm_parameter.ai_generation_enabled.name
}
