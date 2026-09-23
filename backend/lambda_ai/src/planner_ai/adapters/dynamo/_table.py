"""Shared DynamoDB plumbing for the api adapters.

Owns the single `data` table handle, the (PK, SK) prefixes and Spanish
attribute names (docs/data_model.md section 1/3), number (de)serialisation, and
the marker-bump leg every mutating write carries as the second item of its
`TransactWriteItems` (docs/data_model.md section 1.1/4.7/5.5 — never a separate
call, never a `ConditionExpression`)."""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeSerializer
from botocore.config import Config

TABLE_NAME = os.environ.get("PLANNER_DATA_TABLE", "data")
_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-south-2")
# Unset -> None -> boto3's own default (real AWS); local dev points this at
# DynamoDB Local, mirroring lambda_api's adapters/dynamo/_table.py exactly.
_ENDPOINT_URL = os.environ.get("DYNAMODB_ENDPOINT_URL")
# Real AWS keeps botocore's own default (None = no override). Local mode gets
# a short timeout so an unreachable container fails in seconds, not the
# default connect/retry budget of tens of seconds.
_CONFIG = (
    Config(connect_timeout=2, read_timeout=2, retries={"max_attempts": 1})
    if _ENDPOINT_URL
    else None
)

# Single-value partition ids kept as ids, not literals (docs/data_model.md
# section 7): a future multi-household model is then a prefix change.
LIBRARY_ID = "default"
RULES_ID = "default"
SHOPPING_LIST_ID = "default"

MARKER_SK = "MARCA"
MARKER_ATTR = "marcaCambio"

_serializer = TypeSerializer()


def _local_credentials() -> dict[str, str]:
    """Placeholder credentials for local-emulator traffic only, when an endpoint
    override is set (E2/E3, issues/debug-requires-aws-credentials/analysis.md).
    Read at call time, like `_ENDPOINT_URL`, so tests patching it take effect."""
    if not _ENDPOINT_URL:
        return {}
    return {"aws_access_key_id": "local", "aws_secret_access_key": "local"}


# boto3 ships no type stubs, so these resource/table/client handles are untyped
# (docs/conventions.md — no bare `Any` without a justification).
def resource() -> Any:
    return boto3.resource(
        "dynamodb",
        region_name=_REGION,
        endpoint_url=_ENDPOINT_URL,
        config=_CONFIG,
        **_local_credentials(),
    )


def table() -> Any:
    return resource().Table(TABLE_NAME)


def client() -> Any:
    return boto3.client(
        "dynamodb",
        region_name=_REGION,
        endpoint_url=_ENDPOINT_URL,
        config=_CONFIG,
        **_local_credentials(),
    )


def create_data_table() -> None:
    """Create `data` if absent — used by the moto-backed contract suites and
    local runs. Real provisioning is IaC (feature 21)."""
    ddb = client()
    try:
        ddb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    except ddb.exceptions.ResourceInUseException:
        pass


def encode(value: object) -> object:
    """float -> Decimal recursively; DynamoDB has no float type."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    return value


def decode_number(value: Decimal | int | str) -> float | int:
    """Decimal -> int when integral, else float. boto3 hands back `Decimal`;
    tests and raw items may pass `int`/`str`."""
    number = Decimal(value) if not isinstance(value, Decimal) else value
    return int(number) if number == number.to_integral_value() else float(number)


def get_item(pk: str, sk: str, *, consistent: bool = False) -> dict[str, Any] | None:
    resp = table().get_item(Key={"PK": pk, "SK": sk}, ConsistentRead=consistent)
    item = resp.get("Item")
    return dict(item) if item is not None else None


def query_prefix(pk: str, sk_prefix: str) -> list[dict[str, Any]]:
    """Single-partition Query scoped by an SK prefix — a KeyConditionExpression,
    so the excluded items (incl. MARCA) cost nothing (docs/data_model.md 3)."""
    condition = Key("PK").eq(pk) & Key("SK").begins_with(sk_prefix)
    rows: list[dict[str, Any]] = []
    kwargs: dict[str, Any] = {"KeyConditionExpression": condition}
    while True:
        resp = table().query(**kwargs)
        rows.extend(dict(row) for row in resp.get("Items", []))
        start = resp.get("LastEvaluatedKey")
        if not start:
            return rows
        kwargs["ExclusiveStartKey"] = start


def put_action(item: dict[str, Any]) -> dict[str, Any]:
    serialized = {key: _serializer.serialize(encode(value)) for key, value in item.items()}
    return {"Put": {"TableName": TABLE_NAME, "Item": serialized}}


def delete_action(pk: str, sk: str) -> dict[str, Any]:
    return {"Delete": {"TableName": TABLE_NAME, "Key": {"PK": {"S": pk}, "SK": {"S": sk}}}}


def marker_bump_action(pk: str) -> dict[str, Any]:
    """The `ADD marcaCambio 1` leg (docs/data_model.md section 1.1). No
    `ConditionExpression` — the marker is never a write precondition."""
    return {
        "Update": {
            "TableName": TABLE_NAME,
            "Key": {"PK": {"S": pk}, "SK": {"S": MARKER_SK}},
            "UpdateExpression": "ADD #marker :one",
            "ExpressionAttributeNames": {"#marker": MARKER_ATTR},
            "ExpressionAttributeValues": {":one": {"N": "1"}},
        }
    }


def transact_write(actions: list[dict[str, Any]]) -> None:
    client().transact_write_items(TransactItems=actions)


def read_marker(pk: str) -> int:
    """AP29 — strongly consistent, marker attribute only, 0 before any write."""
    resp = table().get_item(
        Key={"PK": pk, "SK": MARKER_SK},
        ConsistentRead=True,
        ProjectionExpression="#marker",
        ExpressionAttributeNames={"#marker": MARKER_ATTR},
    )
    item = resp.get("Item")
    return int(item[MARKER_ATTR]) if item is not None else 0


def commit(pk: str, data_actions: list[dict[str, Any]]) -> int:
    """Run the data writes plus the marker bump as one transaction, then return
    the advanced marker (docs/data_model.md section 5.5)."""
    transact_write([*data_actions, marker_bump_action(pk)])
    return read_marker(pk)
