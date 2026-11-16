"""One deployed entry point in a fresh process, ordered as the Lambda runtime is:
root level and handler, module import, invocation. Moto and fake values only;
prints what reached the log as JSON."""

from __future__ import annotations

import importlib
import json
import logging
import os
import sys
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

_REGION = "eu-west-1"
_SESSION_KEY = "FAKE-HMAC-222"
_BEARER_TOKEN = "FAKE-BEARER-111"
_PASSWORD = "fake-password-123"
_USERNAME = "probe-user"
_USER_ID = "probe-user-id"
_GENERATION = "probe-generation"
_METHOD_ARN = "arn:aws:execute-api:eu-west-1:123:abc/dev/GET/v1/weeks/2026-W33"
_ENV_PREFIXES = ("AWS_", "AI_", "SESSION_SECRET_", "PLANNER_")
_ENV_NAMES = ("DYNAMODB_ENDPOINT_URL", "SQS_ENDPOINT_URL", "GENERATION_QUEUE_URL")
_SDK_NAMES = (
    "boto3",
    "boto3.resources.action",
    "botocore",
    "botocore.endpoint",
    "botocore.parsers",
    "s3transfer",
    "s3transfer.utils",
    "urllib3",
    "urllib3.connectionpool",
)


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.NOTSET)
        self.enabled = True
        self.records: list[dict[str, object]] = []
        self._formatter = logging.Formatter()

    def emit(self, record: logging.LogRecord) -> None:
        if not self.enabled:
            return
        # Every attribute: the JSON format prints `extra` keys too.
        attributes = " ".join(str(value) for value in record.__dict__.values())
        self.records.append(
            {
                "logger": record.name,
                "level": record.levelno,
                "text": f"{self._formatter.format(record)} {attributes}",
            }
        )


def _isolate_from_the_real_environment() -> None:
    for key in list(os.environ):
        if key.startswith(_ENV_PREFIXES) or key in _ENV_NAMES:
            del os.environ[key]
    os.environ.update(
        AWS_ACCESS_KEY_ID="testing",
        AWS_SECRET_ACCESS_KEY="testing",
        AWS_SESSION_TOKEN="testing",
        AWS_DEFAULT_REGION=_REGION,
        AWS_CONFIG_FILE=os.devnull,
        AWS_SHARED_CREDENTIALS_FILE=os.devnull,
        AWS_EC2_METADATA_DISABLED="true",
        AWS_MAX_ATTEMPTS="1",
        AWS_BEARER_TOKEN_BEDROCK=_BEARER_TOKEN,
        # Closed port: the ai run connects here and is refused; no request reaches AWS.
        AWS_ENDPOINT_URL_BEDROCK_RUNTIME="http://127.0.0.1:9",
        PLANNER_DATA_TABLE="probe-data",
        PLANNER_ENV="dev",
        GENERATION_QUEUE_URL="https://sqs.eu-west-1.amazonaws.com/123/probe",
        AI_PROMPT_VERSION_ID="v1",
        AI_GENERATION_SWITCH="true",
    )


def _seed_account() -> str:
    from planner_api.adapters.dynamo._table import create_data_table
    from planner_api.adapters.dynamo.accounts import DynamoAccountRepository
    from planner_core.domain.role import Role
    from planner_core.ports.accounts import AccountRecord
    from planner_core.ports.password_hasher import Pbkdf2PasswordHasher

    create_data_table()
    pass_hash = Pbkdf2PasswordHasher().hash(_PASSWORD)
    DynamoAccountRepository().create(
        AccountRecord(
            user_id=_USER_ID,
            username=_USERNAME,
            role=Role.USER,
            password_hash=pass_hash,
            password_reset_required=False,
            credentials_valid_since=datetime.now(UTC) - timedelta(hours=1),
        )
    )
    return pass_hash


def _seed_session_secret() -> None:
    import boto3

    secret = boto3.client("secretsmanager", region_name=_REGION).create_secret(
        Name="probe-session", SecretString=_SESSION_KEY
    )
    os.environ["SESSION_SECRET_ARN"] = str(secret["ARN"])


def _api() -> tuple[dict[str, Any], list[str]]:
    pass_hash = _seed_account()
    _seed_session_secret()
    body = json.dumps({"username": _USERNAME, "password": _PASSWORD})
    event: dict[str, Any] = {
        "httpMethod": "POST",
        "resource": "/v1/session",
        "pathParameters": None,
        "queryStringParameters": None,
        "headers": {},
        "body": body,
        "requestContext": {},
    }
    return event, [_SESSION_KEY, pass_hash]


def _authorizer_allow() -> tuple[dict[str, Any], list[str]]:
    from planner_core.ports.tokens import HmacTokenSigner

    pass_hash = _seed_account()
    _seed_session_secret()
    token = HmacTokenSigner(_SESSION_KEY.encode("utf-8")).issue(_USER_ID, datetime.now(UTC))
    event = {"methodArn": _METHOD_ARN, "headers": {"Cookie": f"session={token}"}}
    return event, [_SESSION_KEY, pass_hash]


def _authorizer_deny() -> tuple[dict[str, Any], list[str]]:
    return {"methodArn": _METHOD_ARN, "headers": {}}, []


def _rollover() -> tuple[dict[str, Any], list[str]]:
    from planner_api.adapters.dynamo._table import create_data_table

    create_data_table()
    return {}, []


def _ai() -> tuple[dict[str, Any], list[str]]:
    import boto3
    from planner_ai.adapters.dynamo import _table

    _table.create_data_table()
    _table.table().put_item(
        Item={"PK": f"PETICIONIA#{_GENERATION}", "SK": "METADATA", "estado": "pending"}
    )
    # Open under either gate, so the run reaches the provider if issue 23 is swapped back.
    boto3.client("ssm", region_name=_REGION).put_parameter(
        Name="/planner/dev/ai-generation-enabled", Value="true", Type="String"
    )
    body = {
        "type": "recipe",
        "idPeticionIA": _GENERATION,
        "target": {"kind": "library"},
        "source": {"kind": "specification", "ingredients": ["lentejas"], "tools": ["olla"]},
        "referenceRecipe": None,
        "promptVersionId": "v1",
        "authorUserId": _USER_ID,
    }
    return {"Records": [{"body": json.dumps(body)}]}, [_BEARER_TOKEN]


_SCENARIOS: dict[str, tuple[str, Callable[[], tuple[dict[str, Any], list[str]]]]] = {
    "api": ("planner_api.handler", _api),
    "authorizer": ("planner_api.authorizer", _authorizer_allow),
    "authorizer-deny": ("planner_api.authorizer", _authorizer_deny),
    "rollover": ("planner_api.scheduled", _rollover),
    "ai": ("planner_ai.handler", _ai),
}


def main(scenario: str, level_name: str) -> None:
    _isolate_from_the_real_environment()
    module_name, seed = _SCENARIOS[scenario]
    level = logging.getLevelName(level_name)
    capture = _Capture()
    root = logging.getLogger()
    root.addHandler(capture)
    root.setLevel(level)

    entry = importlib.import_module(module_name)

    capture.enabled = False
    from moto import mock_aws

    with mock_aws():
        event, secrets = seed()
        capture.enabled = True
        result = entry.lambda_handler(event, object())
        app_logger = logging.getLogger(f"{module_name.split('.')[0]}.probe")
        app_logger.debug("app-debug-line")
        capture.enabled = False

    print(
        json.dumps(
            {
                "module_file": entry.__file__,
                "result": result,
                "secrets": secrets,
                "root_level_after": root.level,
                "sdk_levels": {n: logging.getLogger(n).getEffectiveLevel() for n in _SDK_NAMES},
                "records": capture.records,
            }
        )
    )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
