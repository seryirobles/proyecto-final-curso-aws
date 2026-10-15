# Create zip with the code
data "archive_file" "python_lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/"
  output_path = "nametest.zip"
  excludes    = [".venv", "_pycache_", ".ruff_cache"]
}

# Create lambda
resource "aws_lambda_function" "hello" {
  filename         = data.archive_file.python_lambda_package.output_path
  function_name    = "${var.project_name}-hello"
  role             = data.aws_iam_role.lambda_exec.arn
  handler          = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.python_lambda_package.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["x86_64"]
}

# Create integration with api gateway
resource "aws_apigatewayv2_integration" "hello" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.hello.invoke_arn
}

# Create apigateway route
resource "aws_apigatewayv2_route" "hello" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /hello"
  target    = "integrations/${aws_apigatewayv2_integration.hello.id}"

}

# Give apigw permission to run lambda
resource "aws_lambda_permission" "api_gw_hello" {
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
  function_name = aws_lambda_function.hello.function_name
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
}