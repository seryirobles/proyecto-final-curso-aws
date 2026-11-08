# No keepers: the key never rotates on apply, so sessions survive; the result is plain text in state (encrypted backend).
resource "random_password" "session" {
  length  = 64
  special = false # plain-text SecretString with nothing to escape
}

# needs role permission: secretsmanager:GetSecretValue
# To strip: delete only the two resources below; in locals.tf (api and authorizer env) use SESSION_SECRET_KEY = random_password.session.result.
# Default aws/secretsmanager key: the reader needs no extra KMS permission.
resource "aws_secretsmanager_secret" "session" {
  name        = "${local.name}-session-secret-key"
  description = "HMAC key that signs session tokens (planner_core.ports.tokens)."

  recovery_window_in_days = 0 # delete immediately so the same name can be re-created after destroy
}

resource "aws_secretsmanager_secret_version" "session" {
  secret_id     = aws_secretsmanager_secret.session.id
  secret_string = random_password.session.result
}

# Grants the shared Lambda role read access, since the role itself has no Secrets Manager permission.
resource "aws_secretsmanager_secret_policy" "session" {
  secret_arn = aws_secretsmanager_secret.session.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = data.aws_iam_role.lambda_exec.arn }
      Action    = "secretsmanager:GetSecretValue"
      Resource  = "*"
    }]
  })
}
