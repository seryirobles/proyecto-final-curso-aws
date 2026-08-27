"""The two roles FR-AUTH-01 names."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    USER = "user"
