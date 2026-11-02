variable "aws_profile" {
  description = "Named AWS CLI profile used by the providers."
  type        = string
  default     = "commitacademy-srobles"
}

variable "bedrock_aws_profile" {
  description = "Named AWS CLI profile for the separate account that has Bedrock model access."
  type        = string
  default     = "personal-srobles"
}

variable "project_name" {
  description = "Prefix for every resource name (followed by the environment)."
  type        = string
  default     = "lab-final-srobles"
}

variable "environment" {
  description = "Environment: in every resource name, the Environment tag, the API stage name and PLANNER_ENV (SSM path /planner/<env>/...)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "stg", "prod"], var.environment)
    error_message = "environment must be one of dev, stg, prod."
  }
}

variable "alert_email" {
  description = "Email that receives alarm and budget notifications."
  type        = string
}

variable "lambda_execution_role_name" {
  description = "Existing IAM role every Lambda runs as (the main account cannot create roles)."
  type        = string
  default     = "studentLambdaExecutionRole"
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention for every Lambda log group."
  type        = number
  default     = 14

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.log_retention_days)
    error_message = "log_retention_days must be a value CloudWatch Logs accepts (1, 3, 5, 7, 14, 30, 60, 90, ... 3653)."
  }
}

variable "ai_prompt_version_id" {
  description = "AI_PROMPT_VERSION_ID for the api Lambda (no default in code; unset => 422 UNKNOWN_PROMPT_VERSION)."
  type        = string
  default     = "v6"
}

variable "ai_model_id" {
  description = "AI_MODEL_ID: Bedrock inference-profile id (EU Geo profile)."
  type        = string
  default     = "eu.amazon.nova-2-lite-v1:0"
}

variable "bedrock_api_key_age_days" {
  description = "Lifetime of the Bedrock API key; replace the credential before it expires or AI calls fail."
  type        = number
  default     = 90

  validation {
    condition     = var.bedrock_api_key_age_days >= 1 && var.bedrock_api_key_age_days <= 36600
    error_message = "bedrock_api_key_age_days must be between 1 and 36600."
  }
}

variable "ai_inference_settings" {
  description = "Optional AI_* env vars for the ai Lambda (AI_REASONING_ENABLED, AI_MAX_TOKENS, ...). Unset = code default."
  type        = map(string)
  default     = {}
}

variable "ai_max_concurrency" {
  description = "SQS event-source maximum concurrency for the ai worker."
  type        = number
  default     = 2

  validation {
    condition     = var.ai_max_concurrency >= 2 && var.ai_max_concurrency <= 1000
    error_message = "ai_max_concurrency must be between 2 and 1000 (SQS event source limit)."
  }
}

variable "rollover_schedule" {
  description = "EventBridge rule cron (UTC) for week rollover. Must fire before Monday 00:00 Madrid in both CET and CEST (scheduled.py archives current_week(today)): 21:55 UTC = 22:55 CET / 23:55 CEST."
  type        = string
  default     = "cron(55 21 ? * SUN *)"
}

variable "api_throttle_rate_limit" {
  description = "Stage-wide steady-state requests per second."
  type        = number
  default     = 20
}

variable "api_throttle_burst_limit" {
  description = "Stage-wide burst."
  type        = number
  default     = 40
}

variable "login_throttle_rate_limit" {
  description = "POST /v1/session requests per second (login brute-force protection)."
  type        = number
  default     = 1
}

variable "login_throttle_burst_limit" {
  description = "POST /v1/session burst (login brute-force protection)."
  type        = number
  default     = 5
}

variable "cloudfront_price_class" {
  description = "CloudFront price class; PriceClass_100 covers Europe + North America at the lowest cost."
  type        = string
  default     = "PriceClass_100"
}

variable "monthly_budget_usd" {
  description = "Overall monthly AWS budget in USD for the main account."
  type        = number
  default     = 60
}

variable "ai_budget_usd" {
  description = "Monthly AI spend cap in the Bedrock account, in USD (Budgets limits are USD)."
  type        = number
  default     = 50
}
