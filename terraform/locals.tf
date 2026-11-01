data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

locals {
  name       = "${var.project_name}-${var.environment}"
  account_id = data.aws_caller_identity.current.account_id
  partition  = data.aws_partition.current.partition
  dns_suffix = data.aws_partition.current.dns_suffix

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  # One Region for both accounts: a long-term Bedrock API key works only in its own Region.
  region = "eu-west-1"

  # Lambda maximum: a whole-week run calls Bedrock once per slot.
  ai_timeout = 900

  # Path fixed by the backend's SSM adapter.
  kill_switch_parameter = "/planner/${var.environment}/ai-generation-enabled"

  # Bare foundation-model id behind the "eu." Geo inference profile.
  ai_foundation_model_id = replace(var.ai_model_id, "/^[a-z]+\\./", "")

  # All three api-package functions build the whole dependency graph eagerly, so all need the secret and queue URL.
  api_package_env = {
    PLANNER_DATA_TABLE   = aws_dynamodb_table.data.name
    GENERATION_QUEUE_URL = aws_sqs_queue.generation.url
    AI_PROMPT_VERSION_ID = var.ai_prompt_version_id
    # needs role permission: secretsmanager:GetSecretValue
    # To strip: replace with SESSION_SECRET_KEY = random_password.session.result (backend fallback; see secrets.tf).
    SESSION_SECRET_ARN = aws_secretsmanager_secret.session.arn
  }

  ai_env = merge(var.ai_inference_settings, {
    PLANNER_DATA_TABLE = aws_dynamodb_table.data.name
    PLANNER_ENV        = var.environment
    AI_MODEL_ID        = var.ai_model_id
    # Cross-account Bedrock auth; only the bedrock-runtime client uses it.
    AWS_BEARER_TOKEN_BEDROCK = aws_iam_service_specific_credential.bedrock.service_credential_secret
  })

  # Separate from local.lambdas: a for_each map must not carry sensitive values.
  lambda_env = {
    api        = local.api_package_env
    authorizer = local.api_package_env
    rollover   = local.api_package_env
    ai         = local.ai_env
  }

  # One function per entry point (a Lambda has one handler); `package` = which CI-built zip it runs.
  lambdas = {
    api = {
      package = "api"
      handler = "planner_api.handler.lambda_handler"
      memory  = 512 # PBKDF2 on login is CPU-bound; CPU scales with memory
      timeout = 29  # REST API integration timeout default
    }
    authorizer = {
      package = "api"
      handler = "planner_api.authorizer.lambda_handler"
      memory  = 256
      timeout = 10
    }
    rollover = {
      package = "api"
      handler = "planner_api.scheduled.lambda_handler"
      memory  = 256
      timeout = 60
    }
    ai = {
      package = "ai"
      handler = "planner_ai.handler.lambda_handler"
      memory  = 256
      timeout = local.ai_timeout
    }
  }

  # Must mirror backend routing.py ROUTES (no {proxy+}); a backend drift test guards it.
  api_route_table   = jsondecode(file("${path.module}/api_routes.json"))
  api_routes        = keys(local.api_route_table)
  api_public_routes = [for k, v in local.api_route_table : k if v.public]
}
