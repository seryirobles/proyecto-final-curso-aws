# IAM role Lambdas will assume during execution
# resource "aws_iam_role" "lambda_exec" {
#   name = "${var.project_name}-lambda-role"

#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [{
#       Action = "sts:AssumeRole"
#       Effect = "Allow"
#       Principal = {
#         Service = "lambda.amazonaws.com"
#       }
#       }
#     ]
#   })
# }

# Reuse existing role
data "aws_iam_role" "lambda_exec" {
  name = "studentLambdaExecutionRole"
}

# resource "aws_iam_role_policy_attachment" "lambda_policy" {
#  role = data.aws_iam_role.lambda_exec.name
#  policy_arn = "arn:aws:iam::aws:policy/service-role/AwsLambdaBasicExecutionRole"
# }