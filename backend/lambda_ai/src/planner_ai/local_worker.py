"""Dev-only entry point: a local poller standing in for the real SQS -> Lambda
trigger (there is no Lambda runtime here to deliver batches automatically) -
no `feature_list.json` entry, no spec, same category as
`planner_api.local_server` and `planner_api.seed_local_data`.
`uv run python -m planner_ai.local_worker` from `backend/lambda_ai/`."""

from __future__ import annotations

import logging
import os
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ProfileNotFound

from planner_ai.adapters.dynamo._table import create_data_table
from planner_ai.handler import handle

logger = logging.getLogger("planner_ai.local_worker")

_WAIT_TIME_SECONDS = 20
_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-south-2")
# Same override pattern as adapters/dynamo/_table.py: unset -> real AWS SQS,
# set -> the local ElasticMQ emulator (docker-compose.yml). connect_timeout
# still fails fast on an unreachable container; read_timeout must clear the
# long-poll wait below or every empty receive_message raises ReadTimeoutError.
_ENDPOINT_URL = os.environ.get("SQS_ENDPOINT_URL")
_CONFIG = (
    Config(connect_timeout=2, read_timeout=_WAIT_TIME_SECONDS + 5, retries={"max_attempts": 1})
    if _ENDPOINT_URL
    else None
)
# ClientError codes botocore raises for a misconfigured/expired credential.
_AUTH_ERROR_CODES = {"UnrecognizedClientException", "InvalidClientTokenId", "ExpiredToken"}


def _require_local_env() -> None:
    """This process holds real Bedrock credentials (module docstring); an
    unset local override must not silently fall through to real AWS."""
    missing = [
        name
        for name in ("DYNAMODB_ENDPOINT_URL", "SQS_ENDPOINT_URL", "GENERATION_QUEUE_URL")
        if not os.environ.get(name)
    ]
    if missing:
        logger.error(
            "planner_ai local worker only supports local-emulator mode: %s must be set.",
            ", ".join(missing),
        )
        raise SystemExit(1)


def _require_bedrock_auth() -> None:
    """Bedrock is the one call that leaves this machine; it needs a bearer API
    key or the AWS credential chain, checked before either client is built
    (E4, issues/debug-requires-aws-credentials/analysis.md)."""
    if os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        return
    if boto3.Session().get_credentials() is not None:
        return
    logger.error(
        "No Bedrock authentication configured. Set AWS_BEARER_TOKEN_BEDROCK "
        "(a Bedrock API key) or configure a real AWS credential chain (aws "
        "configure, environment variables, or SSO) before running the local "
        "worker."
    )
    raise SystemExit(1)


def _local_credentials() -> dict[str, str]:
    """Placeholder credentials for local-emulator traffic only, when an endpoint
    override is set (E1, issues/debug-requires-aws-credentials/analysis.md).
    Read at call time, like `_ENDPOINT_URL`, so tests patching it take effect."""
    if not _ENDPOINT_URL:
        return {}
    return {"aws_access_key_id": "local", "aws_secret_access_key": "local"}


def _sqs() -> Any:
    # boto3 ships no type stubs, so the client handle is untyped
    # (docs/conventions.md — no bare `Any` without a justification).
    return boto3.client(
        "sqs",
        region_name=_REGION,
        endpoint_url=_ENDPOINT_URL,
        config=_CONFIG,
        **_local_credentials(),
    )


def _queue_url() -> str:
    return os.environ["GENERATION_QUEUE_URL"]


def _poll_once(sqs: Any, queue_url: str) -> None:
    response = sqs.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=_WAIT_TIME_SECONDS
    )
    messages = response.get("Messages", [])
    if not messages:
        return
    event = {
        "Records": [
            {
                "messageId": m.get("MessageId"),
                "receiptHandle": m.get("ReceiptHandle"),
                "body": m["Body"],
            }
            for m in messages
        ]
    }
    handle(event)
    # handle()'s per-record exception isolation (handler.py R4) means a batch
    # always completes without raising, so a real SQS trigger would delete the
    # whole batch too — mirror that here.
    for message in messages:
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    _require_local_env()
    _require_bedrock_auth()
    try:
        sqs = _sqs()
        create_data_table()  # convenience for a fresh DynamoDB Local container
    except ProfileNotFound as error:
        logger.error("%s — fix AWS_PROFILE before running the local worker.", error)
        raise SystemExit(1) from None
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code")
        if code not in _AUTH_ERROR_CODES:
            raise
        logger.error(
            "AWS rejected the configured credentials (%s) — reconfigure them "
            "before running the local worker.",
            code,
        )
        raise SystemExit(1) from None

    queue_url = _queue_url()
    logger.info("planner_ai local worker polling %s", queue_url)
    try:
        while True:
            _poll_once(sqs, queue_url)
    except KeyboardInterrupt:
        logger.info("planner_ai local worker stopped")


if __name__ == "__main__":
    main()
