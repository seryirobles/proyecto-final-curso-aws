resource "aws_sqs_queue" "generation_dlq" {
  name                      = "${local.name}-generation-dlq"
  message_retention_seconds = 1209600 # 14 days, the SQS maximum
  sqs_managed_sse_enabled   = true
}

# Visibility >= 6x function timeout and maxReceiveCount >= 5, per Lambda's SQS guidance.
resource "aws_sqs_queue" "generation" {
  name                       = "${local.name}-generation"
  visibility_timeout_seconds = 6 * local.ai_timeout
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.generation_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue_redrive_allow_policy" "generation_dlq" {
  queue_url = aws_sqs_queue.generation_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.generation.arn]
  })
}
