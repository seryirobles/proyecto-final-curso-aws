"""local_worker.py's credential requirements: the clients it builds for the
local emulators must sign without generic AWS credentials, since Bedrock — the
only call that leaves the machine — is authenticated by an API key."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import boto3
import pytest
from botocore.config import Config
from botocore.exceptions import NoCredentialsError

from planner_ai import local_worker
from planner_ai.adapters.dynamo import _table
from planner_ai.wiring import Dependencies

_LOCAL_DYNAMODB = "http://localhost:8000"
_LOCAL_SQS = "http://localhost:9324"
_QUEUE_URL = f"{_LOCAL_SQS}/000000000000/generation-queue"
_LOCAL_CONFIG = Config(connect_timeout=2, read_timeout=2, retries={"max_attempts": 1})


class _RequestSigned(Exception):
    """Signing succeeded — raised from a `before-send` hook so the request never
    leaves the process (docs/conventions.md: no test hits the network)."""


# boto3 ships no type stubs, so client handles and hook arguments are untyped
# (docs/conventions.md — no bare `Any` without a justification).
def _raise_once_signed(request: Any, **kwargs: Any) -> None:
    raise _RequestSigned(request.headers.get("Authorization"))


def _block_send(client: Any) -> None:
    client.meta.events.register("before-send", _raise_once_signed)


@pytest.fixture
def no_ambient_credentials(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A developer whose only AI credential is a Bedrock API key: no key pair,
    no profile, no shared credentials file, no instance metadata."""
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "credentials"))
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "config"))
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "test-bedrock-api-key")
    # boto3's default session caches resolved credentials process-wide.
    monkeypatch.setattr(boto3, "DEFAULT_SESSION", None)


@pytest.fixture
def local_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Endpoint state is frozen at import, so patch the module attributes too
    (same reason as lambda_api/tests/_docker_fixtures.py)."""
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", _LOCAL_DYNAMODB)
    monkeypatch.setenv("SQS_ENDPOINT_URL", _LOCAL_SQS)
    monkeypatch.setenv("GENERATION_QUEUE_URL", _QUEUE_URL)
    monkeypatch.setattr(local_worker, "_ENDPOINT_URL", _LOCAL_SQS)
    monkeypatch.setattr(local_worker, "_CONFIG", _LOCAL_CONFIG)
    monkeypatch.setattr(_table, "_ENDPOINT_URL", _LOCAL_DYNAMODB)
    monkeypatch.setattr(_table, "_CONFIG", _LOCAL_CONFIG)


def test_the_local_sqs_client_signs_without_ambient_aws_credentials(
    no_ambient_credentials: None, local_mode: None
) -> None:
    client = local_worker._sqs()
    _block_send(client)

    with pytest.raises(_RequestSigned) as signed:
        client.receive_message(QueueUrl=_QUEUE_URL, WaitTimeSeconds=0)

    assert signed.value.args[0] is not None


def test_the_local_dynamodb_client_signs_without_ambient_aws_credentials(
    no_ambient_credentials: None, local_mode: None
) -> None:
    client = _table.client()
    _block_send(client)

    with pytest.raises(_RequestSigned) as signed:
        client.list_tables()

    assert signed.value.args[0] is not None


def test_the_local_dynamodb_resource_signs_without_ambient_aws_credentials(
    no_ambient_credentials: None, local_mode: None
) -> None:
    """Reviewer finding: E2 covers `resource()` too, not just `client()`
    (plan.md/analysis.md say "client and resource")."""
    table = _table.table()
    _block_send(table.meta.client)

    with pytest.raises(_RequestSigned) as signed:
        table.get_item(Key={"PK": "x", "SK": "y"})

    assert signed.value.args[0] is not None


def test_the_real_aws_dynamodb_client_still_requires_real_credentials(
    no_ambient_credentials: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No endpoint override means the deployed Lambda's own path: a missing
    credential must still fail loudly instead of signing with a placeholder."""
    monkeypatch.setattr(_table, "_ENDPOINT_URL", None)
    monkeypatch.setattr(_table, "_CONFIG", None)
    client = _table.client()
    _block_send(client)

    with pytest.raises(NoCredentialsError):
        client.list_tables()


def test_the_worker_polls_when_only_a_bedrock_api_key_is_configured(
    no_ambient_credentials: None, local_mode: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    polled: list[Any] = []
    created: list[str] = []

    def fake_create_data_table() -> None:
        created.append(_table.TABLE_NAME)

    def stop_after_the_first_poll(sqs: Any, queue_url: str, deps: Any) -> None:
        polled.append(sqs)
        raise KeyboardInterrupt

    monkeypatch.setattr(local_worker, "create_data_table", fake_create_data_table)
    monkeypatch.setattr(local_worker, "_poll_once", stop_after_the_first_poll)

    local_worker.main()

    assert created == [_table.TABLE_NAME]
    assert len(polled) == 1
    _block_send(polled[0])
    with pytest.raises(_RequestSigned):
        polled[0].receive_message(QueueUrl=_QUEUE_URL, WaitTimeSeconds=0)


def test_the_worker_polls_when_a_credential_chain_is_configured_without_a_bedrock_key(
    no_ambient_credentials: None, local_mode: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No AWS_BEARER_TOKEN_BEDROCK, but a resolvable credential chain: the E4
    fallback passes and main() reaches the poll instead of exiting."""
    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "chain-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "chain-secret")

    polled: list[Any] = []

    def stop_after_the_first_poll(sqs: Any, queue_url: str, deps: Any) -> None:
        polled.append(sqs)
        raise KeyboardInterrupt

    monkeypatch.setattr(local_worker, "create_data_table", lambda: None)
    monkeypatch.setattr(local_worker, "_poll_once", stop_after_the_first_poll)

    local_worker.main()

    assert len(polled) == 1


def test_the_worker_fails_fast_when_no_bedrock_credential_is_configured(
    no_ambient_credentials: None, local_mode: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither a Bedrock API key nor an AWS credential chain: the one clear log
    line at startup, not a per-record Bedrock failure later."""

    def stop_the_loop(sqs: Any, queue_url: str) -> None:
        raise KeyboardInterrupt  # reached only if the startup check is missing

    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
    monkeypatch.setattr(local_worker, "create_data_table", lambda: None)
    monkeypatch.setattr(local_worker, "_poll_once", stop_the_loop)

    with pytest.raises(SystemExit) as exit_info:
        local_worker.main()

    assert exit_info.value.code == 1


def test_main_builds_the_override_aware_dependencies_once(
    no_ambient_credentials: None, local_mode: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E5: the loop must use build_local_dependencies, not the plain wiring."""
    local_deps, seen = object(), []
    monkeypatch.setattr(local_worker, "create_data_table", lambda: None)
    monkeypatch.setattr(local_worker, "build_local_dependencies", lambda: local_deps)
    monkeypatch.setattr(local_worker, "build_dependencies", lambda: object())

    def stop(sqs: Any, queue_url: str, deps: Any) -> None:
        seen.append(deps)
        raise KeyboardInterrupt

    monkeypatch.setattr(local_worker, "_poll_once", stop)

    local_worker.main()

    assert seen == [local_deps]


def test_poll_once_forwards_deps_to_handle(monkeypatch: pytest.MonkeyPatch) -> None:
    """E5: the gate override only works if handle() receives the deps."""
    calls: list[Any] = []
    deps = cast(Dependencies, object())

    class _Sqs:
        def receive_message(self, **kwargs: Any) -> Any:
            return {"Messages": [{"MessageId": "m", "ReceiptHandle": "r", "Body": "{}"}]}

        def delete_message(self, **kwargs: Any) -> None:
            pass

    monkeypatch.setattr(local_worker, "handle", lambda event, d=None: calls.append(d))

    local_worker._poll_once(_Sqs(), _QUEUE_URL, deps)

    assert calls == [deps]
