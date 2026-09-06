"""handler.py: thin dispatch, auth gating, error mapping, logging and
`Cache-Control` (R1, R3-R5, R11-R25, R30, R38, R39)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from _helpers import api_event, authorizer_context, make_deps, seed_user
from planner_core.domain.role import Role
from planner_core.ports.accounts import AccountRecord

from planner_api.handler import handle

_SRC = Path(__file__).resolve().parents[1] / "src" / "planner_api"


class _ExplodingAccounts:
    """An `AccountRepository` that fails any call - proof a gate decision
    never reaches for it (R12)."""

    def _boom(self) -> AccountRecord | None:
        raise AssertionError("the gate must not read the account record")

    def get_by_id(self, user_id: str) -> AccountRecord | None:
        return self._boom()

    def get_by_username(self, username: str) -> AccountRecord | None:
        return self._boom()

    def list_all(self) -> tuple[AccountRecord, ...]:
        raise AssertionError("the gate must not read the account record")

    def create(self, account: AccountRecord) -> None:
        raise AssertionError("the gate must not read the account record")

    def rename(self, user_id: str, new_username: str) -> None:
        raise AssertionError("the gate must not read the account record")

    def update_credentials(self, *args: object, **kwargs: object) -> None:
        raise AssertionError("the gate must not read the account record")

    def delete(self, user_id: str) -> None:
        raise AssertionError("the gate must not read the account record")

    def revoke_credentials(self, user_id: str, revoked_at: object) -> None:
        raise AssertionError("the gate must not read the account record")


def test_login_sets_the_session_cookie_with_the_contract_attributes() -> None:
    deps = make_deps()
    deps.accounts.create(
        AccountRecord(
            user_id="u-1",
            username="marta",
            role=Role.USER,
            password_hash=deps.hasher.hash("s3cret1234"),
            password_reset_required=False,
            credentials_valid_since=deps.clock.now(),
        )
    )
    event = api_event("POST", "/v1/session", body={"username": "marta", "password": "s3cret1234"})

    response = handle(event, deps)

    assert response["statusCode"] == 200
    cookie = response["headers"]["Set-Cookie"]
    assert cookie.startswith("session=")
    assert "HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=2592000" in cookie


def test_login_never_places_the_token_in_the_response_body() -> None:
    deps = make_deps()
    deps.accounts.create(
        AccountRecord(
            user_id="u-1",
            username="marta",
            role=Role.USER,
            password_hash=deps.hasher.hash("s3cret1234"),
            password_reset_required=False,
            credentials_valid_since=deps.clock.now(),
        )
    )
    event = api_event("POST", "/v1/session", body={"username": "marta", "password": "s3cret1234"})

    response = handle(event, deps)

    body = json.loads(response["body"])
    cookie_token = response["headers"]["Set-Cookie"].split("session=", 1)[1].split(";", 1)[0]
    assert cookie_token not in json.dumps(body)
    assert "token" not in body


def test_logout_expires_the_cookie_on_the_same_response() -> None:
    deps = make_deps()
    token = seed_user(deps, user_id="u-1")
    event = api_event(
        "DELETE", "/v1/session", cookie=token, context=authorizer_context(user_id="u-1")
    )

    response = handle(event, deps)

    assert response["statusCode"] == 204
    assert "Max-Age=0" in response["headers"]["Set-Cookie"]


def test_logout_is_allowed_while_password_reset_is_pending() -> None:
    deps = make_deps()
    token = seed_user(deps, user_id="u-1", password_reset_required=True)
    event = api_event(
        "DELETE",
        "/v1/session",
        cookie=token,
        context=authorizer_context(user_id="u-1", password_reset_required=True),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 204


def test_set_password_is_allowed_while_password_reset_is_pending() -> None:
    deps = make_deps()
    token = seed_user(deps, user_id="u-1", password_reset_required=True)
    event = api_event(
        "PUT",
        "/v1/session/password",
        body={"newPassword": "a-new-long-password"},
        cookie=token,
        context=authorizer_context(user_id="u-1", password_reset_required=True),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 204


def test_a_role_mismatch_is_rejected_with_403_forbidden() -> None:
    deps = make_deps()
    event = api_event("GET", "/v1/users", context=authorizer_context(role=Role.USER))

    response = handle(event, deps)

    assert response["statusCode"] == 403
    assert json.loads(response["body"])["code"] == "FORBIDDEN"


def test_an_admin_is_rejected_from_a_user_only_route_with_403_forbidden() -> None:
    """R11 - the gate denies both directions, not just USER-on-admin-route."""
    deps = make_deps()
    event = api_event(
        "GET", "/v1/live-weeks", context=authorizer_context(user_id="u-1", role=Role.ADMIN)
    )

    response = handle(event, deps)

    assert response["statusCode"] == 403
    assert json.loads(response["body"])["code"] == "FORBIDDEN"


def test_password_reset_pending_blocks_an_unrelated_route() -> None:
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    event = api_event(
        "GET",
        "/v1/live-weeks",
        context=authorizer_context(user_id="u-1", password_reset_required=True),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 403
    assert json.loads(response["body"])["code"] == "PASSWORD_RESET_PENDING"


def test_the_role_and_password_reset_gate_never_reads_the_account_record() -> None:
    """R12 - the gate raises from the authorizer context alone; a Forbidden
    response never touches AccountRepository."""
    deps = make_deps(accounts=_ExplodingAccounts())
    event = api_event("GET", "/v1/users", context=authorizer_context(role=Role.USER))

    response = handle(event, deps)

    assert response["statusCode"] == 403


def test_malformed_json_body_returns_400() -> None:
    deps = make_deps()
    event = api_event("POST", "/v1/session", body=None)
    event["body"] = "{not json"

    response = handle(event, deps)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["code"] == "MALFORMED_REQUEST"


def test_a_client_supplied_author_is_rejected_at_the_route_level() -> None:
    """R39 - reject_keys must actually run inside a route, not just in
    isolation (test_serialization.py). The body is otherwise valid and
    decodable, so a 400 can only come from the reject_keys guard."""
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    event = api_event(
        "POST",
        "/v1/library/recipes",
        body={
            "author": "someone",
            "source": "manual",
            "recipe": {
                "name": "Tortilla",
                "category": "eggs",
                "ingredients": [{"name": "huevo", "quantity": 3, "unit": "unit"}],
                "tools": [],
                "procedure": [],
            },
        },
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["code"] == "MALFORMED_REQUEST"


_VALID_RECIPE = {
    "name": "Tortilla",
    "category": "eggs",
    "ingredients": [{"name": "huevo", "quantity": 3, "unit": "unit"}],
    "tools": [],
    "procedure": [],
}


def test_a_client_supplied_author_is_rejected_when_adding_a_candidate() -> None:
    """R39 — reject_keys runs at the _add_candidate site (routing.py:375). The
    body is otherwise valid and decodable, so the 400 is only the guard."""
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    event = api_event(
        "POST",
        "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates",
        path_params={"weekId": "2026-W30", "day": "1", "slot": "1"},
        body={"author": "someone", "source": "manual", "recipe": _VALID_RECIPE},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["code"] == "MALFORMED_REQUEST"


def test_a_client_supplied_author_is_rejected_when_editing_a_candidate() -> None:
    """R39 — reject_keys runs at the _edit_candidate site (routing.py:403). The
    recipe decodes; without `author` this body 404s on the missing candidate,
    so a 400 can only be the guard firing."""
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    event = api_event(
        "PUT",
        "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}",
        path_params={
            "weekId": "2026-W30",
            "day": "1",
            "slot": "1",
            "candidateId": "c-1",
        },
        body={"author": "someone", "recipe": _VALID_RECIPE},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["code"] == "MALFORMED_REQUEST"


def test_a_domain_rejection_maps_to_the_contract_status() -> None:
    deps = make_deps()
    event = api_event("POST", "/v1/session", body={"username": "ghost", "password": "wrong-pass"})

    response = handle(event, deps)

    assert response["statusCode"] == 401
    assert json.loads(response["body"])["code"] == "INVALID_CREDENTIALS"


def test_an_unrouted_request_returns_404_without_a_traceback() -> None:
    deps = make_deps()
    event = api_event("GET", "/v1/does-not-exist")

    response = handle(event, deps)

    assert response["statusCode"] == 404
    assert "Traceback" not in response["body"]


def test_cache_control_no_store_is_set_on_success_and_error_responses() -> None:
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    success_event = api_event("GET", "/v1/live-weeks", context=authorizer_context(user_id="u-1"))
    error_event = api_event("GET", "/v1/does-not-exist")

    success = handle(success_event, deps)
    error = handle(error_event, deps)

    assert success["statusCode"] == 200
    assert success["headers"]["Cache-Control"] == "no-store"
    assert error["headers"]["Cache-Control"] == "no-store"


def test_handling_a_request_emits_a_structured_log_record(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO", logger="planner_api")
    deps = make_deps()

    handle(api_event("GET", "/v1/does-not-exist"), deps)

    records = [r for r in caplog.records if r.name == "planner_api"]
    assert len(records) >= 1
    assert records[0].__dict__["method"] == "GET"  # extra fields land in __dict__, not statically


class _BrokenAccounts(_ExplodingAccounts):
    """Raises a plain bug, not a domain exception - the unmapped-error path."""

    def get_by_id(self, user_id: str) -> AccountRecord | None:
        raise RuntimeError("adapter blew up")


def test_a_500_response_logs_the_causing_exception_with_its_traceback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("ERROR", logger="planner_api")
    deps = make_deps(accounts=_BrokenAccounts())
    event = api_event(
        "GET",
        "/v1/users/{userId}",
        path_params={"userId": "u-9"},
        context=authorizer_context(role=Role.ADMIN),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 500
    assert "Traceback" not in response["body"]  # R25 - never in the body
    logged = [r for r in caplog.records if r.exc_info is not None]
    assert len(logged) == 1  # R24 - the traceback is logged, exactly once


def test_no_source_module_calls_print() -> None:
    for path in _SRC.rglob("*.py"):  # R23 - includes planner_api/adapters/**
        content = path.read_text(encoding="utf-8")
        assert not re.search(r"(?<!\w)print\(", content), f"{path.name} calls print()"
