output "api-endpoint" {
  description = "API Gateway base URL"
  value       = aws_apigatewayv2_stage.prod.invoke_url
}