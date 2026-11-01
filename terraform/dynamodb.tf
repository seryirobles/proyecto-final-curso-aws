resource "aws_dynamodb_table" "data" {
  name                        = "${local.name}-data"
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "PK"
  range_key                   = "SK"
  deletion_protection_enabled = true

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # "ttl" must exist only on generation records and the shopping-list lock, or other items would expire.
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = false # false = AWS owned key (no KMS cost); data is still encrypted at rest
  }

  lifecycle {
    prevent_destroy = true # remove before the final teardown
  }
}
