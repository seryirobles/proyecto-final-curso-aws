"""Secrets Manager reader for the session HMAC key (SecretString is the raw key)."""

from __future__ import annotations

import functools
import os

import boto3

_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


@functools.cache
def fetch_session_secret(arn: str) -> str:
    """Fetched once per ARN per cold start; failures and empty values are never cached."""
    try:
        value = (
            boto3.client("secretsmanager", region_name=_REGION)
            .get_secret_value(SecretId=arn)
            .get("SecretString")
        )
    except Exception as error:
        raise RuntimeError(f"Could not read the session secret {arn}") from error
    if not value:
        raise RuntimeError(f"The session secret {arn} is empty")
    return str(value)
