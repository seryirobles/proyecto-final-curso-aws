# The AI cap lives in bedrock.tf because Bedrock spend is billed to the Bedrock account.

# needs role permission: ssm:GetParameter (to strip: delete this resource and the ai_kill_switch_parameter output)
# Seeded "true" and manual flips are kept; set "false" on the AI budget email to get the friendly "unavailable" message.
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
