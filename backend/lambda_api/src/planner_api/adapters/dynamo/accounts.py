"""DynamoDB `AccountRepository` — USUARIOS partition (docs/data_model.md
section 1, section 5.1/5.2). Username uniqueness is enforced by the write's
condition, not a read-then-write; a rename releases its old reservation by
looking the key up, never by re-folding the old name (section 5.2's trap)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from botocore.exceptions import ClientError
from planner_core.domain.role import Role
from planner_core.domain.text import normalize
from planner_core.domain.username_policy import UsernameAlreadyTaken
from planner_core.ports.accounts import AccountAlreadyExists, AccountNotFound, AccountRecord

from planner_api.adapters.dynamo import _table

_PK = "USUARIOS"
_ID_PREFIX = "ID#"
_NAME_PREFIX = "NOMBRE#"


def _id_sk(user_id: str) -> str:
    return f"{_ID_PREFIX}{user_id}"


def _to_record(item: dict[str, Any]) -> AccountRecord:
    return AccountRecord(
        user_id=str(item["SK"]).removeprefix(_ID_PREFIX),
        username=str(item["nombreUsuario"]),
        role=Role(str(item["tipo"])),
        password_hash=str(item["passHash"]),
        password_reset_required=bool(item["isPassReseteada"]),
        credentials_valid_since=datetime.fromisoformat(str(item["validoDesde"])),
    )


def _account_item(account: AccountRecord) -> dict[str, Any]:
    return {
        "PK": _PK,
        "SK": _id_sk(account.user_id),
        "nombreUsuario": account.username,
        "tipo": account.role.value,
        "isPassReseteada": account.password_reset_required,
        "passHash": account.password_hash,
        "validoDesde": account.credentials_valid_since.isoformat(),
    }


class DynamoAccountRepository:
    def get_by_id(self, user_id: str) -> AccountRecord | None:
        item = _table.get_item(_PK, _id_sk(user_id))
        return _to_record(item) if item is not None else None

    def get_by_username(self, username: str) -> AccountRecord | None:
        reservation = _table.get_item(_PK, f"{_NAME_PREFIX}{normalize(username)}")
        if reservation is None:
            return None
        return self.get_by_id(str(reservation["idUsuario"]))

    def list_all(self) -> tuple[AccountRecord, ...]:
        return tuple(_to_record(row) for row in _table.query_prefix(_PK, _ID_PREFIX))

    def create(self, account: AccountRecord) -> None:
        reservation_sk = f"{_NAME_PREFIX}{normalize(account.username)}"
        id_put = _table.put_action(_account_item(account))
        id_put["Put"]["ConditionExpression"] = "attribute_not_exists(SK)"
        try:
            _table.transact_write(
                [
                    id_put,
                    {
                        "Put": {
                            "TableName": _table.TABLE_NAME,
                            "Item": {
                                "PK": {"S": _PK},
                                "SK": {"S": reservation_sk},
                                "idUsuario": {"S": account.user_id},
                            },
                            "ConditionExpression": "attribute_not_exists(SK)",
                        }
                    },
                ]
            )
        except ClientError as exc:
            _reraise_create_failure(exc, account)

    def rename(self, user_id: str, new_username: str) -> None:
        current = _table.get_item(_PK, _id_sk(user_id))
        if current is None:
            raise AccountNotFound(user_id)
        old_sk = self._reservation_sk_of(user_id)
        new_sk = f"{_NAME_PREFIX}{normalize(new_username)}"

        if new_sk != old_sk and _table.get_item(_PK, new_sk) is not None:
            raise UsernameAlreadyTaken(new_username)

        actions: list[dict[str, Any]] = [
            {
                "Update": {
                    "TableName": _table.TABLE_NAME,
                    "Key": {"PK": {"S": _PK}, "SK": {"S": _id_sk(user_id)}},
                    "UpdateExpression": "SET #nombreUsuario = :name",
                    "ExpressionAttributeNames": {"#nombreUsuario": "nombreUsuario"},
                    "ExpressionAttributeValues": {":name": {"S": new_username}},
                    "ConditionExpression": "attribute_exists(SK)",
                }
            }
        ]
        if new_sk != old_sk:
            actions.append(
                {
                    "Delete": {
                        "TableName": _table.TABLE_NAME,
                        "Key": {"PK": {"S": _PK}, "SK": {"S": old_sk}},
                        "ConditionExpression": "#idUsuario = :me",
                        "ExpressionAttributeNames": {"#idUsuario": "idUsuario"},
                        "ExpressionAttributeValues": {":me": {"S": user_id}},
                    }
                }
            )
            actions.append(
                {
                    "Put": {
                        "TableName": _table.TABLE_NAME,
                        "Item": {
                            "PK": {"S": _PK},
                            "SK": {"S": new_sk},
                            "idUsuario": {"S": user_id},
                        },
                        "ConditionExpression": "attribute_not_exists(SK)",
                    }
                }
            )
        try:
            _table.transact_write(actions)
        except ClientError as exc:
            _reraise_as_username_taken(exc, new_username)

    def update_credentials(
        self,
        user_id: str,
        password_hash: str,
        password_reset_required: bool,
        credentials_valid_since: datetime,
    ) -> None:
        self._update(
            user_id,
            "SET #passHash = :h, #isPassReseteada = :r, #validoDesde = :v",
            {
                "#passHash": "passHash",
                "#isPassReseteada": "isPassReseteada",
                "#validoDesde": "validoDesde",
            },
            {
                ":h": {"S": password_hash},
                ":r": {"BOOL": password_reset_required},
                ":v": {"S": credentials_valid_since.isoformat()},
            },
        )

    def reset_admin_credentials(
        self, user_id: str, password_hash: str, credentials_valid_since: datetime
    ) -> None:
        self._update(
            user_id,
            "SET #passHash = :h, #isPassReseteada = :r, #validoDesde = :v",
            {
                "#passHash": "passHash",
                "#isPassReseteada": "isPassReseteada",
                "#validoDesde": "validoDesde",
                "#tipo": "tipo",
            },
            {
                ":h": {"S": password_hash},
                ":r": {"BOOL": True},
                ":v": {"S": credentials_valid_since.isoformat()},
                ":admin": {"S": Role.ADMIN.value},
            },
            condition="attribute_exists(SK) AND #tipo = :admin",
        )

    def revoke_credentials(self, user_id: str, revoked_at: datetime) -> None:
        self._update(
            user_id,
            "SET #validoDesde = :v",
            {"#validoDesde": "validoDesde"},
            {":v": {"S": revoked_at.isoformat()}},
        )

    def delete(self, user_id: str) -> None:
        if _table.get_item(_PK, _id_sk(user_id)) is None:
            raise AccountNotFound(user_id)
        old_sk = self._reservation_sk_of(user_id)
        _table.transact_write(
            [
                {
                    "Delete": {
                        "TableName": _table.TABLE_NAME,
                        "Key": {"PK": {"S": _PK}, "SK": {"S": _id_sk(user_id)}},
                        "ConditionExpression": "attribute_exists(SK)",
                    }
                },
                _table.delete_action(_PK, old_sk),
            ]
        )

    def _reservation_sk_of(self, user_id: str) -> str:
        for row in _table.query_prefix(_PK, _NAME_PREFIX):
            if str(row["idUsuario"]) == user_id:
                return str(row["SK"])
        # No reservation row (should not happen): fall back to a key that
        # cannot match, so the conditional delete simply no-ops.
        return f"{_NAME_PREFIX}\x00{user_id}"

    def _update(
        self,
        user_id: str,
        expression: str,
        names: dict[str, str],
        values: dict[str, Any],
        condition: str = "attribute_exists(SK)",
    ) -> None:
        try:
            _table.client().update_item(
                TableName=_table.TABLE_NAME,
                Key={"PK": {"S": _PK}, "SK": {"S": _id_sk(user_id)}},
                UpdateExpression=expression,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ConditionExpression=condition,
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise AccountNotFound(user_id) from exc
            raise


_TAKEN_CODES = frozenset({"TransactionCanceledException", "ConditionalCheckFailedException"})


def _reraise_as_username_taken(exc: ClientError, username: str) -> None:
    """A failed reservation condition means the folded name is already reserved."""
    if exc.response["Error"]["Code"] in _TAKEN_CODES:
        raise UsernameAlreadyTaken(username) from exc
    raise exc


def _reraise_create_failure(exc: ClientError, account: AccountRecord) -> None:
    """Leg 1 (NOMBRE#) failing wins over leg 0 (ID#): name taken, else id taken (G-96)."""
    if exc.response["Error"]["Code"] != "TransactionCanceledException":
        raise exc
    reasons = exc.response.get("CancellationReasons") or []
    failed = [r.get("Code") == "ConditionalCheckFailed" for r in reasons]
    if len(failed) > 1 and failed[1]:
        raise UsernameAlreadyTaken(account.username) from exc
    if failed and failed[0]:
        raise AccountAlreadyExists(account.user_id) from exc
    raise exc
