"""`quiet_sdk_loggers()` pins the four SDK loggers and nothing else."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

from planner_api.sdk_logging import quiet_sdk_loggers

_SDK = ("boto3", "botocore", "urllib3", "s3transfer")
_OTHERS = ("planner_core", "planner_api")


@pytest.fixture(autouse=True)
def _restore_levels() -> Iterator[None]:
    names = (*_SDK, *_OTHERS)
    saved = {n: logging.getLogger(n).level for n in names}
    for n in names:
        logging.getLogger(n).setLevel(logging.NOTSET)
    yield
    for n, level in saved.items():
        logging.getLogger(n).setLevel(level)


def test_the_four_sdk_loggers_are_set_to_warning() -> None:
    quiet_sdk_loggers()

    assert [logging.getLogger(n).level for n in _SDK] == [logging.WARNING] * 4


def test_application_loggers_are_left_unset() -> None:
    quiet_sdk_loggers()

    assert [logging.getLogger(n).level for n in _OTHERS] == [logging.NOTSET] * 2
