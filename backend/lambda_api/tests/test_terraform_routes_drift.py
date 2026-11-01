"""`terraform/api_routes.json` must mirror `routing.ROUTES` (method, path, public)."""

from __future__ import annotations

import json
from pathlib import Path

from planner_api.routing import ROUTES

# Repo root: tests/ -> lambda_api/ -> backend/ -> root.
_ROUTES_JSON = Path(__file__).resolve().parents[3] / "terraform" / "api_routes.json"
_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def _terraform() -> dict[str, dict[str, object]]:
    assert _ROUTES_JSON.is_file(), f"missing {_ROUTES_JSON}"
    data: dict[str, dict[str, object]] = json.loads(_ROUTES_JSON.read_text(encoding="utf-8"))
    return data


def _backend() -> dict[str, bool]:
    return {f"{method} {path}": spec.public for (method, path), spec in ROUTES.items()}


def test_terraform_route_set_matches_backend_routes() -> None:
    tf, be = set(_terraform()), set(_backend())
    assert tf == be, f"only in terraform: {sorted(tf - be)}; only in backend: {sorted(be - tf)}"


def test_terraform_public_routes_match_backend_public_routes() -> None:
    tf = {key for key, value in _terraform().items() if value.get("public") is True}
    be = {key for key, public in _backend().items() if public}
    assert tf == be, f"public only in tf: {sorted(tf - be)}; only in backend: {sorted(be - tf)}"


def test_terraform_route_entries_are_well_formed() -> None:
    for key, value in _terraform().items():
        parts = key.split(" ")
        assert len(parts) == 2, f"{key!r}: expected 'METHOD /path'"
        method, path = parts
        assert method in _METHODS, f"{key!r}: unknown method"
        assert path.startswith("/v1/"), f"{key!r}: path must start with /v1/"
        assert isinstance(value.get("public"), bool), f"{key!r}: 'public' must be a boolean"
