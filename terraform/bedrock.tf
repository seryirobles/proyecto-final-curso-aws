# Bedrock lives in a separate account; the worker authenticates with a long-term API key in AWS_BEARER_TOKEN_BEDROCK, read natively by boto3.

data "aws_caller_identity" "bedrock" {
  provider = aws.bedrock
}

locals {
  bedrock_account_id  = data.aws_caller_identity.bedrock.account_id
  bedrock_profile_arn = "arn:${local.partition}:bedrock:${local.region}:${local.bedrock_account_id}:inference-profile/${var.ai_model_id}"
}

resource "aws_iam_user" "bedrock_invoker" {
  provider = aws.bedrock
  name     = "${local.name}-bedrock-invoker"
}

# Invoke only the configured Geo profile and its EU foundation models.
resource "aws_iam_user_policy" "bedrock_invoker" {
  provider = aws.bedrock
  name     = "${local.name}-invoke-model"
  user     = aws_iam_user.bedrock_invoker.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "UseApiKey"
        Effect   = "Allow"
        Action   = "bedrock:CallWithBearerToken"
        Resource = "*"
      },
      {
        Sid      = "InvokeProfile"
        Effect   = "Allow"
        Action   = "bedrock:InvokeModel"
        Resource = local.bedrock_profile_arn
      },
      {
        Sid       = "InvokeModelViaProfile"
        Effect    = "Allow"
        Action    = "bedrock:InvokeModel"
        Resource  = "arn:${local.partition}:bedrock:eu-*::foundation-model/${local.ai_foundation_model_id}"
        Condition = { StringLike = { "bedrock:InferenceProfileArn" = local.bedrock_profile_arn } }
      },
    ]
  })
}

# Secret lands in state (encrypted S3 backend); rotate with terraform apply -replace=aws_iam_service_specific_credential.bedrock.
resource "aws_iam_service_specific_credential" "bedrock" {
  provider            = aws.bedrock
  service_name        = "bedrock.amazonaws.com"
  user_name           = aws_iam_user.bedrock_invoker.name
  credential_age_days = var.bedrock_api_key_age_days

  lifecycle {
    create_before_destroy = true # rotation without a gap (IAM allows 2 keys per user and service)
  }
}

resource "aws_budgets_budget" "ai" {
  provider     = aws.bedrock
  name         = "${local.name}-ai"
  budget_type  = "COST"
  limit_amount = tostring(var.ai_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "Service"
    values = ["Amazon Bedrock"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}

# At 100% the Budget action attaches this Deny to the API-key user; the friendly message still needs the manual SSM flip.
resource "aws_iam_policy" "ai_kill_switch" {
  provider    = aws.bedrock
  name        = "${local.name}-ai-kill-switch"
  description = "Attached by the AI Budget action to stop Bedrock spend."
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Deny"
      Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream", "bedrock:CallWithBearerToken"]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role" "budget_action" {
  provider = aws.bedrock
  name     = "${local.name}-budget-action"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "budgets.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = local.bedrock_account_id }
        ArnLike      = { "aws:SourceArn" = "arn:${local.partition}:budgets::${local.bedrock_account_id}:budget/*" }
      }
    }]
  })
}

resource "aws_iam_role_policy" "budget_action" {
  provider = aws.bedrock
  name     = "${local.name}-attach-kill-switch"
  role     = aws_iam_role.budget_action.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = ["iam:AttachUserPolicy", "iam:DetachUserPolicy"]
      Resource  = aws_iam_user.bedrock_invoker.arn
      Condition = { ArnEquals = { "iam:PolicyARN" = aws_iam_policy.ai_kill_switch.arn } }
    }]
  })
}

resource "aws_budgets_budget_action" "ai_kill_switch" {
  provider           = aws.bedrock
  budget_name        = aws_budgets_budget.ai.name
  action_type        = "APPLY_IAM_POLICY"
  approval_model     = "AUTOMATIC"
  notification_type  = "ACTUAL"
  execution_role_arn = aws_iam_role.budget_action.arn

  action_threshold {
    action_threshold_type  = "PERCENTAGE"
    action_threshold_value = 100
  }

  definition {
    iam_action_definition {
      policy_arn = aws_iam_policy.ai_kill_switch.arn
      users      = [aws_iam_user.bedrock_invoker.name]
    }
  }

  subscriber {
    address           = var.alert_email
    subscription_type = "EMAIL"
  }

  depends_on = [aws_iam_role_policy.budget_action]
}
