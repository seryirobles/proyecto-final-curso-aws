# REST API, not HTTP API: the handler reads the v1 proxy event, the authorizer reads methodArn, and Gateway Responses are REST-only.

locals {
  api_paths = distinct([for r in local.api_routes : split(" ", r)[1]])

  # problem+json bodies for API Gateway's own errors; detail strings are copied verbatim from planner_core/messages.py.
  session_expired = {
    status = 401
    code   = "SESSION_EXPIRED"
    title  = "Session expired"
    detail = "La sesión ha caducado. Vuelve a iniciar sesión."
  }

  gateway_problems = {
    UNAUTHORIZED  = local.session_expired # no Cookie header: authorizer never runs
    ACCESS_DENIED = local.session_expired # authorizer returned Deny
    MISSING_AUTHENTICATION_TOKEN = {      # unknown resource/method
      status = 404
      code   = "NOT_FOUND"
      title  = "Not found"
      detail = "El recurso solicitado no existe."
    }
    DEFAULT_5XX = {
      status = 500
      code   = "INTERNAL_ERROR"
      title  = "Internal error"
      detail = "Se ha producido un error inesperado. Inténtalo de nuevo más tarde."
    }
  }

  # Gateway responses live in the body: put mode "overwrite" wipes anything defined outside it.
  openapi = {
    openapi = "3.0.1"
    info    = { title = "${local.name}-api", version = "1" }

    paths = {
      for p in local.api_paths : p => {
        for r in local.api_routes : lower(split(" ", r)[0]) => {
          parameters = [
            for n in flatten(regexall("\\{([^}]+)\\}", p)) :
            { "name" = n, "in" = "path", "required" = true, "schema" = { type = "string" } }
          ]
          security = [for s in [{ session = [] }] : s if !contains(local.api_public_routes, r)]
          "x-amazon-apigateway-integration" = {
            type                = "aws_proxy"
            httpMethod          = "POST"
            uri                 = aws_lambda_function.this["api"].invoke_arn
            passthroughBehavior = "when_no_match"
          }
        } if split(" ", r)[1] == p
      }
    }

    components = {
      securitySchemes = {
        session = {
          type                           = "apiKey"
          name                           = "Cookie"
          "in"                           = "header"
          "x-amazon-apigateway-authtype" = "custom"
          "x-amazon-apigateway-authorizer" = {
            type           = "request"
            identitySource = "method.request.header.Cookie"
            authorizerUri  = aws_lambda_function.this["authorizer"].invoke_arn
            # TTL 0 so removing a user or resetting a password takes effect immediately.
            authorizerResultTtlInSeconds = 0
          }
        }
      }
    }

    "x-amazon-apigateway-gateway-responses" = {
      for type, p in local.gateway_problems : type => {
        statusCode = tostring(p.status)
        responseParameters = {
          "gatewayresponse.header.Content-Type"  = "'application/problem+json'"
          "gatewayresponse.header.Cache-Control" = "'no-store'"
        }
        responseTemplates = {
          "application/json" = jsonencode({
            type   = "urn:planner:${replace(lower(p.code), "_", "-")}"
            title  = p.title
            status = p.status
            detail = p.detail
            code   = p.code
          })
        }
      }
    }
  }
}

resource "aws_api_gateway_rest_api" "api" {
  name = "${local.name}-api"
  body = jsonencode(local.openapi)

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(aws_api_gateway_rest_api.api.body)
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.api.id
  stage_name    = var.environment # deliberately not the API version
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.api.stage_name
  method_path = "*/*"

  settings {
    throttling_rate_limit  = var.api_throttle_rate_limit
    throttling_burst_limit = var.api_throttle_burst_limit
  }
}

# Tight login throttle against brute force (global, not per IP).
resource "aws_api_gateway_method_settings" "login" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.api.stage_name
  method_path = "v1/session/POST"

  settings {
    throttling_rate_limit  = var.login_throttle_rate_limit
    throttling_burst_limit = var.login_throttle_burst_limit
  }
}
