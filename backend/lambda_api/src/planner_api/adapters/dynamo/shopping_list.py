"""DynamoDB `ShoppingListRepository` — COMPRA partition (docs/data_model.md
section 1, section 4.4, section 5.3). The re-sync lock compares `ttl` itself
rather than trusting DynamoDB TTL deletion, which may lag up to 48h."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from botocore.exceptions import ClientError
from planner_core.domain.shopping import ShoppingItem, ShoppingItemNotFound
from planner_core.domain.units import Unit, parse_unit
from planner_core.ports.shopping_list import ShoppingListLockHeld

from planner_api.adapters.dynamo import _table

_ITEM_PREFIX = "INGREDIENTE#"
_LOCK_SK = "LOCK"


def _pk() -> str:
    return f"COMPRA#{_table.SHOPPING_LIST_ID}"


def _sk(item_id: str) -> str:
    return f"{_ITEM_PREFIX}{item_id}"


def _to_item(row: dict[str, Any]) -> ShoppingItem:
    return ShoppingItem(
        id=str(row["SK"]).removeprefix(_ITEM_PREFIX),
        name=str(row["nombreIngrediente"]),
        quantity=_table.decode_number(row["cantidad"]),
        unit=parse_unit(str(row["unidad"])),
        checked=bool(row["isComprado"]),
    )


def _item_dict(item: ShoppingItem) -> dict[str, Any]:
    return {
        "PK": _pk(),
        "SK": _sk(item.id),
        "nombreIngrediente": item.name,
        "cantidad": item.quantity,
        "unidad": item.unit.value if isinstance(item.unit, Unit) else str(item.unit),
        "isComprado": item.checked,
    }


class DynamoShoppingListRepository:
    def current_version(self) -> int:
        return _table.read_marker(_pk())

    def list_items(self) -> tuple[ShoppingItem, ...]:
        return tuple(_to_item(row) for row in _table.query_prefix(_pk(), _ITEM_PREFIX))

    def save_item(self, item: ShoppingItem) -> int:
        return _table.commit(_pk(), [_table.put_action(_item_dict(item))])

    def delete_item(self, item_id: str) -> int:
        if _table.get_item(_pk(), _sk(item_id)) is None:
            raise ShoppingItemNotFound(item_id)
        return _table.commit(_pk(), [_table.delete_action(_pk(), _sk(item_id))])

    def delete_checked_items(self) -> int:
        checked = [
            row for row in _table.query_prefix(_pk(), _ITEM_PREFIX) if bool(row["isComprado"])
        ]
        if not checked:
            return _table.read_marker(_pk())  # no bump when nothing was removed
        actions = [_table.delete_action(_pk(), str(row["SK"])) for row in checked]
        return _table.commit(_pk(), actions)

    def acquire_lock(self, owner_id: str, now: datetime, expires_at: datetime) -> None:
        try:
            _table.client().put_item(
                TableName=_table.TABLE_NAME,
                Item={
                    "PK": {"S": _pk()},
                    "SK": {"S": _LOCK_SK},
                    "ownerId": {"S": owner_id},
                    "ttl": {"N": str(expires_at.timestamp())},
                },
                ConditionExpression="attribute_not_exists(SK) OR #ttl < :now",
                ExpressionAttributeNames={"#ttl": "ttl"},
                ExpressionAttributeValues={":now": {"N": str(now.timestamp())}},
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
            existing = _table.get_item(_pk(), _LOCK_SK, consistent=True)
            holder = str(existing["ownerId"]) if existing is not None else owner_id
            raise ShoppingListLockHeld(holder) from exc

    def release_lock(self, owner_id: str) -> None:
        try:
            _table.client().delete_item(
                TableName=_table.TABLE_NAME,
                Key={"PK": {"S": _pk()}, "SK": {"S": _LOCK_SK}},
                ConditionExpression="#ownerId = :me",
                ExpressionAttributeNames={"#ownerId": "ownerId"},
                ExpressionAttributeValues={":me": {"S": owner_id}},
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
