"""Test-tree root for planner_core.

Its main job is to exist, so ``support`` is importable from subdirectories
(pytest's default ``prepend`` import mode). It also sets the moto-stub AWS
env vars — `core` (alphabetically first) collects before `lambda_ai`/`lambda_api`,
so this runs before any adapter's module-level `_REGION` is resolved
(`tests/contract/dynamo_contract.py`'s own copy ran too late for that).
"""

from __future__ import annotations

import os

for _var, _value in {
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_SESSION_TOKEN": "testing",
}.items():
    os.environ.setdefault(_var, _value)
