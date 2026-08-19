"""Test-tree root for planner_core.

Its only job is to exist. Under pytest's default ``prepend`` import mode the
directory holding a ``conftest.py`` is inserted on ``sys.path``, which is what
lets ``support`` be imported from test modules in subdirectories.
"""

from __future__ import annotations
