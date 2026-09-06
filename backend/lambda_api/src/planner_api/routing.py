"""`(method, resourceTemplate) -> handler` dispatch table for every row of
docs/rest_api_contract.md section 2, plus `GET /v1/live-weeks`. `AP3`, `AP9`,
`AP29` and rollover have no entry (R26, R27, R33); no `GET` entry ever calls a
mutating port method (R2) - see test_routing_table.py's static scan."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any  # untyped JSON in/out is the wire boundary itself (conventions.md)

from planner_core.application import (
    account_admin,
    authentication,
    generation_submission,
    library_editing,
    live_weeks,
    rule_editing,
    shopping_editing,
    week_editing,
)
from planner_core.domain.authorization import require_admin
from planner_core.domain.calendar import civil_date
from planner_core.domain.candidate import (
    CandidateNotFound,
    SlotContents,
    new_candidate,
    summary,
    to_library_entry,
)
from planner_core.domain.generation import GenerationRequest
from planner_core.domain.recipe import snapshot
from planner_core.domain.role import Role
from planner_core.domain.rules import DisabledDay, rule_id
from planner_core.domain.text import normalize
from planner_core.ports.accounts import AccountNotFound
from planner_core.ports.recipes import LibraryRecipe, RecipeNotFound

from planner_api import serialization as ser
from planner_api.serialization import GenerationNotFound, MalformedRequest
from planner_api.wiring import Dependencies

_COOKIE_ATTRS = "HttpOnly; Secure; SameSite=Lax; Path=/"
_RESYNC_LOCK_SECONDS = 30
_RESYNC_ID_BATCH = 256


@dataclass(frozen=True)
class AuthContext:
    """`userId`/`role`/`passwordResetRequired`, as the authorizer context
    hands them to the handler (R8, R12)."""

    user_id: str
    role: Role
    password_reset_required: bool


@dataclass(frozen=True)
class RouteResult:
    status: int
    body: dict[str, Any] | None = None
    etag: str | None = None
    location: str | None = None
    set_cookie: str | None = None


RouteHandler = Callable[
    [dict[str, str], dict[str, str], dict[str, Any], AuthContext | None, Dependencies], RouteResult
]


@dataclass(frozen=True)
class RouteSpec:
    handler: RouteHandler
    public: bool = False
    requires_role: Role | None = None
    allow_during_password_reset: bool = False


def _quoted_etag(marker: int) -> str:
    """RFC 7232 strong validator syntax (docs/rest_api_contract.md section 6):
    the marker itself, quoted."""
    return f'"{marker}"'


def session_cookie(token: str) -> str:
    return f"session={token}; {_COOKIE_ATTRS}; Max-Age=2592000"


def expired_cookie() -> str:
    return f"session=; {_COOKIE_ATTRS}; Max-Age=0"


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


def _login(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    username = str(ser.require_field(body, "username"))
    password = str(ser.require_field(body, "password"))
    result = authentication.login(
        username,
        password,
        accounts=deps.accounts,
        hasher=deps.hasher,
        signer=deps.signer,
        clock=deps.clock,
    )
    return RouteResult(
        status=200,
        body={
            "userId": result.user_id,
            "role": result.role.value,
            "passwordResetRequired": result.password_reset_required,
        },
        set_cookie=session_cookie(result.token),
    )


def _logout(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    assert auth is not None
    authentication.logout(auth.user_id, accounts=deps.accounts, clock=deps.clock)
    return RouteResult(status=204, set_cookie=expired_cookie())


def _set_password(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    assert auth is not None
    new_password = str(ser.require_field(body, "newPassword"))
    authentication.set_password(
        auth.user_id, new_password, accounts=deps.accounts, hasher=deps.hasher
    )
    return RouteResult(status=204)


# ---------------------------------------------------------------------------
# Accounts (admin)
# ---------------------------------------------------------------------------


def _list_users(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    assert auth is not None
    accounts = account_admin.list_accounts(auth.role, accounts=deps.accounts)
    return RouteResult(200, {"users": [ser.encode_account(a) for a in accounts]})


def _get_user(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    assert auth is not None
    require_admin(auth.role)
    account = deps.accounts.get_by_id(path["userId"])
    if account is None:
        raise AccountNotFound(path["userId"])
    return RouteResult(200, ser.encode_account(account))


def _create_user(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    assert auth is not None
    ser.reject_keys(body, "id", "userId")
    username = str(ser.require_field(body, "username"))
    temp_password = str(ser.require_field(body, "temporaryPassword"))
    user_id = uuid.uuid4().hex
    password_hash = deps.hasher.hash(temp_password)
    account = account_admin.create_user(
        auth.role, user_id, username, password_hash, accounts=deps.accounts, clock=deps.clock
    )
    return RouteResult(201, ser.encode_account(account), location=f"/v1/users/{account.user_id}")


def _update_user(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    assert auth is not None
    user_id = path["userId"]
    if "username" in body:
        account_admin.rename_user(auth.role, user_id, str(body["username"]), accounts=deps.accounts)
    if "temporaryPassword" in body:
        target = deps.accounts.get_by_id(user_id)
        if target is None:
            raise AccountNotFound(user_id)
        new_hash = deps.hasher.hash(str(body["temporaryPassword"]))
        account_admin.admin_set_password(
            auth.role, auth.user_id, target, new_hash, accounts=deps.accounts, clock=deps.clock
        )
    account = deps.accounts.get_by_id(user_id)
    if account is None:
        raise AccountNotFound(user_id)
    return RouteResult(200, ser.encode_account(account))


def _delete_user(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    assert auth is not None
    user_id = path["userId"]
    target = deps.accounts.get_by_id(user_id)
    if target is None:
        raise AccountNotFound(user_id)
    account_admin.remove_user(auth.role, target, accounts=deps.accounts)
    return RouteResult(204)


# ---------------------------------------------------------------------------
# Live weeks
# ---------------------------------------------------------------------------


def _live_weeks(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    weeks = live_weeks.resolve_live_weeks(deps.clock)

    def _encode(week: Any) -> dict[str, Any]:
        monday, sunday = week.date_range
        return {"weekId": week.week_id, "monday": monday.isoformat(), "sunday": sunday.isoformat()}

    return RouteResult(
        200,
        {
            "today": weeks.today.isoformat(),
            "current": _encode(weeks.current_week),
            "next": _encode(weeks.next_week),
        },
    )


# ---------------------------------------------------------------------------
# Weeks
# ---------------------------------------------------------------------------


def _get_week(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    week = ser.parse_week_id(path["weekId"])
    view = week_editing.load_week(week, weeks=deps.weeks)  # marker-first read (feature 27 R34/R35)
    plans = view.slots
    slots = []
    for slot_ref in week.slots:
        contents = plans.get(slot_ref, SlotContents())
        slots.append(
            {
                **ser.encode_slot_ref(slot_ref),
                "candidates": [ser.encode_candidate(c) for c in contents.candidates],
                "definitiveId": contents.definitive_id,
            }
        )
    return RouteResult(
        200, {"weekId": week.week_id, "slots": slots}, etag=_quoted_etag(view.marker)
    )


def _get_week_summary(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    week = ser.parse_week_id(path["weekId"])
    view = week_editing.load_week(week, weeks=deps.weeks)  # /summary shares the week marker (R34)
    meals = [
        {**ser.encode_slot_ref(slot_ref), "candidate": ser.encode_candidate(candidate)}
        for slot_ref, candidate in summary(view.slots)
    ]
    return RouteResult(
        200, {"weekId": week.week_id, "meals": meals}, etag=_quoted_etag(view.marker)
    )


def _week_slot(path: dict[str, str]) -> tuple[Any, Any]:
    week = ser.parse_week_id(path["weekId"])
    day = ser.parse_day(path["day"])
    slot = ser.parse_slot(path["slot"])
    return week, ser.resolve_slot_ref(week, day, slot)


def _get_candidate(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    week, slot_ref = _week_slot(path)
    candidate = week_editing.load_candidate(week, slot_ref, path["candidateId"], weeks=deps.weeks)
    if candidate is None:
        raise CandidateNotFound(path["candidateId"])
    return RouteResult(200, ser.encode_candidate(candidate))


def _resolve_meal_source(body: dict[str, Any], deps: Dependencies) -> Any:
    source = ser.require_field(body, "source")
    if source == "library":
        recipe_id = str(ser.require_field(body, "recipeId"))
        entry = deps.recipes.get(recipe_id)
        if entry is None:
            raise RecipeNotFound(recipe_id)
        return snapshot(entry.recipe)
    if source == "manual":
        return snapshot(ser.decode_recipe(ser.require_field(body, "recipe")))
    if source == "generation":
        # No decoded preview shape exists in the shipped ports (spec gap,
        # progress/impl_rest_api_lambda.md): the stored result is treated as
        # the same JSON a manual recipe body would carry.
        generation_id = str(ser.require_field(body, "generationId"))
        stored = deps.queue.stored_generation(generation_id)
        if stored is None or stored.result is None:
            raise GenerationNotFound(generation_id)
        return snapshot(ser.decode_recipe(json.loads(stored.result)))
    raise MalformedRequest


def _add_candidate(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    assert auth is not None
    week, slot_ref = _week_slot(path)
    ser.reject_keys(body, "id", "author", "añadidoPor")
    meal = _resolve_meal_source(body, deps)
    candidate_id = uuid.uuid4().hex
    candidate = new_candidate(candidate_id, meal, auth.user_id)
    outcome = week_editing.add_slot_candidate(week, slot_ref, candidate, weeks=deps.weeks)
    location = (
        f"/v1/weeks/{week.week_id}/days/{path['day']}/slots/{path['slot']}"
        f"/candidates/{candidate_id}"
    )
    return RouteResult(
        201,
        {
            "candidate": ser.encode_candidate(candidate),
            "duplicateWarning": outcome.duplicate_warning,
        },
        etag=_quoted_etag(outcome.marker),
        location=location,
    )


def _edit_candidate(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    week, slot_ref = _week_slot(path)
    ser.reject_keys(body, "id", "author", "añadidoPor")
    meal = snapshot(ser.decode_recipe(ser.require_field(body, "recipe")))
    candidate_id = path["candidateId"]
    marker = week_editing.edit_slot_candidate(week, slot_ref, candidate_id, meal, weeks=deps.weeks)
    candidate = week_editing.load_candidate(week, slot_ref, candidate_id, weeks=deps.weeks)
    assert candidate is not None
    return RouteResult(
        200, {"candidate": ser.encode_candidate(candidate)}, etag=_quoted_etag(marker)
    )


def _delete_candidate(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    week, slot_ref = _week_slot(path)
    marker = week_editing.delete_slot_candidate(
        week, slot_ref, path["candidateId"], weeks=deps.weeks
    )
    return RouteResult(204, etag=_quoted_etag(marker))


def _set_definitive(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    week, slot_ref = _week_slot(path)
    candidate_id = str(ser.require_field(body, "candidateId"))
    marker = week_editing.set_definitive(week, slot_ref, candidate_id, weeks=deps.weeks)
    return RouteResult(200, {"candidateId": candidate_id}, etag=_quoted_etag(marker))


def _clear_definitive(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    week, slot_ref = _week_slot(path)
    marker = week_editing.clear_slot_definitive(week, slot_ref, weeks=deps.weeks)
    return RouteResult(204, etag=_quoted_etag(marker))


# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------


def _encode_library_entry(entry: LibraryRecipe) -> dict[str, Any]:
    return {"id": entry.id, "author": entry.author, **ser.encode_recipe(entry.recipe)}


def _list_library(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    view = library_editing.list_library(recipes=deps.recipes)  # marker-first read (R34/R35)
    entries = view.entries
    name_filter = query.get("name")
    category_filter = query.get("category")
    if name_filter:
        folded = normalize(name_filter)
        entries = tuple(e for e in entries if folded in normalize(e.recipe.name))
    if category_filter:
        entries = tuple(e for e in entries if e.recipe.category.value == category_filter)
    return RouteResult(
        200,
        {"recipes": [_encode_library_entry(e) for e in entries]},
        etag=_quoted_etag(view.marker),
    )


def _get_library_recipe(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    entry = deps.recipes.get(path["recipeId"])
    if entry is None:
        raise RecipeNotFound(path["recipeId"])
    return RouteResult(200, _encode_library_entry(entry))


def _save_library_recipe(*, create: bool) -> RouteHandler:
    def handler(
        path: dict[str, str],
        query: dict[str, str],
        body: dict[str, Any],
        auth: AuthContext | None,
        deps: Dependencies,
    ) -> RouteResult:
        assert auth is not None
        ser.reject_keys(body, "id", "author", "añadidoPor")
        source = body.get("source", "manual")
        if source == "weekCandidate":
            week = ser.parse_week_id(str(ser.require_field(body, "weekId")))
            day = ser.parse_day(str(ser.require_field(body, "day")))
            slot = ser.parse_slot(str(ser.require_field(body, "slot")))
            slot_ref = ser.resolve_slot_ref(week, day, slot)
            candidate_id = str(ser.require_field(body, "candidateId"))
            candidate = week_editing.load_candidate(week, slot_ref, candidate_id, weeks=deps.weeks)
            if candidate is None:
                raise CandidateNotFound(candidate_id)
            recipe = to_library_entry(candidate.meal, ()).recipe
        else:
            recipe = ser.decode_recipe(ser.require_field(body, "recipe"))
        recipe_id = uuid.uuid4().hex if create else path["recipeId"]
        entry = LibraryRecipe(id=recipe_id, recipe=recipe, author=auth.user_id)
        outcome = library_editing.save_recipe(entry, recipes=deps.recipes)
        location = f"/v1/library/recipes/{recipe_id}" if create else None
        return RouteResult(
            201 if create else 200,
            {**_encode_library_entry(entry), "duplicateWarning": outcome.duplicate_warning},
            etag=_quoted_etag(outcome.marker),
            location=location,
        )

    return handler


def _delete_library_recipe(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    confirm = query.get("confirmCascade") == "true"
    outcome = library_editing.delete_recipe(
        path["recipeId"], confirm_cascade=confirm, recipes=deps.recipes, rules=deps.rules
    )
    return RouteResult(204, etag=_quoted_etag(outcome.marker))


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


def _list_rules(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    view = rule_editing.read_rules(rules=deps.rules)  # marker-first read (R34/R35)
    rule_set = view.rule_set
    rules = [
        *(ser.encode_rule(r) for r in rule_set.category_counts),
        *(ser.encode_rule(r) for r in rule_set.pins),
        *(ser.encode_rule(DisabledDay(day=d)) for d in rule_set.disabled_days),
    ]
    return RouteResult(200, {"rules": rules}, etag=_quoted_etag(view.marker))


def _put_rule(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    rule = ser.decode_rule(body)
    if rule_id(rule) != path["ruleId"]:  # T9 - the path segment is authoritative
        raise MalformedRequest
    marker = rule_editing.save_rule(rule, rules=deps.rules)
    return RouteResult(200, ser.encode_rule(rule), etag=_quoted_etag(marker))


def _delete_rule(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    marker = rule_editing.delete_rule(path["ruleId"], rules=deps.rules)
    return RouteResult(204, etag=_quoted_etag(marker))


# ---------------------------------------------------------------------------
# Shopping list
# ---------------------------------------------------------------------------


def _get_shopping_list(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    view = shopping_editing.list_shopping(shopping=deps.shopping)  # marker-first read (R34/R35)
    return RouteResult(
        200,
        {"items": [ser.encode_shopping_item(i) for i in view.items]},
        etag=_quoted_etag(view.marker),
    )


def _add_shopping_item(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    item = ser.decode_shopping_item(body, item_id=uuid.uuid4().hex)
    marker = shopping_editing.save_item(item, shopping=deps.shopping)
    return RouteResult(
        201,
        ser.encode_shopping_item(item),
        etag=_quoted_etag(marker),
        location=f"/v1/shopping-list/items/{item.id}",
    )


def _put_shopping_item(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    item = ser.decode_shopping_item(body, item_id=path["itemId"])
    marker = shopping_editing.save_item(item, shopping=deps.shopping)
    return RouteResult(200, ser.encode_shopping_item(item), etag=_quoted_etag(marker))


def _patch_shopping_item(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    checked = bool(ser.require_field(body, "checked"))
    marker = shopping_editing.set_checked(path["itemId"], checked, shopping=deps.shopping)
    return RouteResult(200, {"id": path["itemId"], "checked": checked}, etag=_quoted_etag(marker))


def _delete_shopping_item(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    marker = shopping_editing.delete_item(path["itemId"], shopping=deps.shopping)
    return RouteResult(204, etag=_quoted_etag(marker))


def _delete_checked_items(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    marker = shopping_editing.delete_checked(shopping=deps.shopping)
    return RouteResult(204, etag=_quoted_etag(marker))


def _resync(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    assert auth is not None
    now = deps.clock.now()
    today = civil_date(now)
    lock_expires_at = now + timedelta(seconds=_RESYNC_LOCK_SECONDS)
    new_ids = [uuid.uuid4().hex for _ in range(_RESYNC_ID_BATCH)]
    outcome = shopping_editing.resync_shopping_list(
        auth.user_id, today, now, lock_expires_at, new_ids, shopping=deps.shopping, weeks=deps.weeks
    )
    marker = (
        outcome.marker
        if outcome.marker is not None
        else shopping_editing.list_shopping(shopping=deps.shopping).marker
    )
    return RouteResult(
        200,
        {"items": [ser.encode_shopping_item(i) for i in outcome.items]},
        etag=_quoted_etag(marker),
    )


# ---------------------------------------------------------------------------
# AI generation
# ---------------------------------------------------------------------------


def _submit_generation(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    if body.get("type", "week") != "week":
        raise MalformedRequest
    week = ser.parse_week_id(str(ser.require_field(body, "weekId")))
    mode = ser.parse_generation_mode(str(ser.require_field(body, "mode")))
    override = ser.decode_rule_override(body.get("ruleOverride"))
    request = GenerationRequest(week=week, mode=mode, rule_override=override)
    first_day = civil_date(deps.clock.now())
    outcome = generation_submission.submit_generation(
        request, first_day, weeks=deps.weeks, rules=deps.rules, queue=deps.queue
    )
    if outcome.stored is not None:
        return RouteResult(
            200,
            {
                "generationId": outcome.idempotency_key,
                "status": outcome.stored.status,
                "result": outcome.stored.result,
            },
        )
    return RouteResult(
        202,
        {
            "generationId": outcome.idempotency_key,
            "status": "pending",
            "targets": ser.encode_generation_targets(outcome.targets),
        },
        location=f"/v1/generations/{outcome.idempotency_key}",
    )


def _get_generation(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    generation_id = path["generationId"]
    stored = deps.queue.stored_generation(generation_id)
    if stored is None:
        raise GenerationNotFound(generation_id)
    return RouteResult(
        200,
        {"generationId": stored.idempotency_key, "status": stored.status, "result": stored.result},
    )


def _delete_generation(
    path: dict[str, str],
    query: dict[str, str],
    body: dict[str, Any],
    auth: AuthContext | None,
    deps: Dependencies,
) -> RouteResult:
    # AP27 (R42): direct port call, mirroring _get_generation. {generationId}
    # is the idempotency key; no ETag — PETICIONIA# has no MarcaCambio.
    deps.queue.discard(path["generationId"])
    return RouteResult(204)


# ---------------------------------------------------------------------------
# The dispatch table
# ---------------------------------------------------------------------------

ROUTES: dict[tuple[str, str], RouteSpec] = {
    ("POST", "/v1/session"): RouteSpec(_login, public=True),
    ("DELETE", "/v1/session"): RouteSpec(_logout, allow_during_password_reset=True),
    ("PUT", "/v1/session/password"): RouteSpec(_set_password, allow_during_password_reset=True),
    ("GET", "/v1/users"): RouteSpec(_list_users, requires_role=Role.ADMIN),
    ("GET", "/v1/users/{userId}"): RouteSpec(_get_user, requires_role=Role.ADMIN),
    ("POST", "/v1/users"): RouteSpec(_create_user, requires_role=Role.ADMIN),
    ("PATCH", "/v1/users/{userId}"): RouteSpec(_update_user, requires_role=Role.ADMIN),
    ("DELETE", "/v1/users/{userId}"): RouteSpec(_delete_user, requires_role=Role.ADMIN),
    ("GET", "/v1/live-weeks"): RouteSpec(_live_weeks, requires_role=Role.USER),
    ("GET", "/v1/weeks/{weekId}"): RouteSpec(_get_week, requires_role=Role.USER),
    ("GET", "/v1/weeks/{weekId}/summary"): RouteSpec(_get_week_summary, requires_role=Role.USER),
    ("GET", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}"): RouteSpec(
        _get_candidate, requires_role=Role.USER
    ),
    ("POST", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates"): RouteSpec(
        _add_candidate, requires_role=Role.USER
    ),
    ("PUT", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}"): RouteSpec(
        _edit_candidate, requires_role=Role.USER
    ),
    ("DELETE", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}"): RouteSpec(
        _delete_candidate, requires_role=Role.USER
    ),
    ("PUT", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/definitive"): RouteSpec(
        _set_definitive, requires_role=Role.USER
    ),
    ("DELETE", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/definitive"): RouteSpec(
        _clear_definitive, requires_role=Role.USER
    ),
    ("GET", "/v1/library/recipes"): RouteSpec(_list_library, requires_role=Role.USER),
    ("GET", "/v1/library/recipes/{recipeId}"): RouteSpec(
        _get_library_recipe, requires_role=Role.USER
    ),
    ("POST", "/v1/library/recipes"): RouteSpec(
        _save_library_recipe(create=True), requires_role=Role.USER
    ),
    ("PUT", "/v1/library/recipes/{recipeId}"): RouteSpec(
        _save_library_recipe(create=False), requires_role=Role.USER
    ),
    ("DELETE", "/v1/library/recipes/{recipeId}"): RouteSpec(
        _delete_library_recipe, requires_role=Role.USER
    ),
    ("GET", "/v1/rules"): RouteSpec(_list_rules, requires_role=Role.USER),
    ("PUT", "/v1/rules/{ruleId}"): RouteSpec(_put_rule, requires_role=Role.USER),
    ("DELETE", "/v1/rules/{ruleId}"): RouteSpec(_delete_rule, requires_role=Role.USER),
    ("GET", "/v1/shopping-list"): RouteSpec(_get_shopping_list, requires_role=Role.USER),
    ("POST", "/v1/shopping-list/items"): RouteSpec(_add_shopping_item, requires_role=Role.USER),
    ("PUT", "/v1/shopping-list/items/{itemId}"): RouteSpec(
        _put_shopping_item, requires_role=Role.USER
    ),
    ("PATCH", "/v1/shopping-list/items/{itemId}"): RouteSpec(
        _patch_shopping_item, requires_role=Role.USER
    ),
    ("DELETE", "/v1/shopping-list/items/{itemId}"): RouteSpec(
        _delete_shopping_item, requires_role=Role.USER
    ),
    ("DELETE", "/v1/shopping-list/checked-items"): RouteSpec(
        _delete_checked_items, requires_role=Role.USER
    ),
    ("POST", "/v1/shopping-list/resync"): RouteSpec(_resync, requires_role=Role.USER),
    ("POST", "/v1/generations"): RouteSpec(_submit_generation, requires_role=Role.USER),
    ("GET", "/v1/generations/{generationId}"): RouteSpec(_get_generation, requires_role=Role.USER),
    ("DELETE", "/v1/generations/{generationId}"): RouteSpec(
        _delete_generation, requires_role=Role.USER
    ),
}
