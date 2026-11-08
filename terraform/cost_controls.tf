# The AI cap lives in bedrock.tf because Bedrock spend is billed to the Bedrock account.

# Not read while the ai Lambda has AI_GENERATION_SWITCH: the shared role has no ssm:GetParameter. Kept for the swap back.
# To stop AI today: ai_generation_enabled = false in terraform.tfvars, then terraform apply.
resource "aws_ssm_parameter" "ai_generation_enabled" {
  name  = local.kill_switch_parameter
  type  = "String"
  value = "true"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_budgets_budget" "monthly" {
  name         = "${local.name}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}
