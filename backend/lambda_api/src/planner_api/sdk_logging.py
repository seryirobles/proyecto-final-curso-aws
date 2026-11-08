"""SDK loggers stay at WARNING: at DEBUG they write secrets to the log
(issues/deployed-lambdas-drop-info-logs). Terraform owns the root level; never set it here."""

from __future__ import annotations

import logging

_SDK_LOGGERS = ("boto3", "botocore", "urllib3", "s3transfer")


def quiet_sdk_loggers() -> None:
    for name in _SDK_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
