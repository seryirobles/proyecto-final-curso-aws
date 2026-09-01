"""R8: current_version is a strongly-consistent, marker-only read that returns
0 before any write (AP29, docs/data_model.md section 4.7)."""

from __future__ import annotations

import inspect

from planner_api.adapters.dynamo import _table
from planner_core.domain.calendar import IsoWeek

from tests.contract.dynamo_contract import (
    dynamo_recipe_repository,
    dynamo_rule_repository,
    dynamo_shopping_list_repository,
    dynamo_week_repository,
)


def test_current_version_is_zero_before_any_write() -> None:
    assert dynamo_recipe_repository().current_version() == 0
    assert dynamo_rule_repository().current_version() == 0
    assert dynamo_shopping_list_repository().current_version() == 0
    assert dynamo_week_repository().current_version(IsoWeek(2026, 30)) == 0


def test_the_marker_read_is_strongly_consistent_and_projects_only_the_marker() -> None:
    source = inspect.getsource(_table.read_marker)
    assert "ConsistentRead=True" in source
    assert "ProjectionExpression" in source
    assert "marcaCambio" not in source  # the attribute is reached via an alias
