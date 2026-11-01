# The main account cannot create IAM roles, so every function runs under one pre-existing role.
data "aws_iam_role" "lambda_exec" {
  name = var.lambda_execution_role_name
}
