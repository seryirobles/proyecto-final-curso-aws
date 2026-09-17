"""moto-backed factories so the real DynamoDB / SQS adapters run the same
contract suites as the in-memory fakes (docs/architecture.md section 3.2).

Lives here, not in planner-core's test tree: it imports boto3/moto and
planner_api, which the planner-core member's tests must never pull in
(backend/core/tests/test_ports_are_storage_agnostic.py)."""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator

from planner_core.ports.accounts import AccountRepository
from planner_core.ports.generation_gate import GenerationGate
from planner_core.ports.generation_queue import GenerationQueue, GenerationResultSink
from planner_core.ports.recipes import RecipeRepository
from planner_core.ports.rules import RuleRepository
from planner_core.ports.shopping_list import ShoppingListRepository
from planner_core.ports.weeks import WeekRepository

# AWS stub env vars are set by ../../core/tests/conftest.py (collects
# first), before any test module here or in lambda_ai/lambda_api imports.


@contextlib.contextmanager
def aws_backend() -> Iterator[None]:
    """A fresh moto-mocked AWS with the `data` table and a generation queue."""
    import boto3
    from moto import mock_aws
    from planner_api.adapters.dynamo._table import create_data_table

    with mock_aws():
        create_data_table()
        sqs = boto3.client("sqs", region_name=os.environ["AWS_DEFAULT_REGION"])
        os.environ["GENERATION_QUEUE_URL"] = sqs.create_queue(QueueName="generation")["QueueUrl"]
        yield


def dynamo_account_repository() -> AccountRepository:
    from planner_api.adapters.dynamo.accounts import DynamoAccountRepository

    return DynamoAccountRepository()


def dynamo_week_repository() -> WeekRepository:
    from planner_api.adapters.dynamo.weeks import DynamoWeekRepository

    return DynamoWeekRepository()


def dynamo_recipe_repository() -> RecipeRepository:
    from planner_api.adapters.dynamo.recipes import DynamoRecipeRepository

    return DynamoRecipeRepository()


def dynamo_rule_repository() -> RuleRepository:
    from planner_api.adapters.dynamo.rules import DynamoRuleRepository

    return DynamoRuleRepository()


def dynamo_shopping_list_repository() -> ShoppingListRepository:
    from planner_api.adapters.dynamo.shopping_list import DynamoShoppingListRepository

    return DynamoShoppingListRepository()


def sqs_generation_queue() -> GenerationQueue:
    from planner_api.adapters.sqs import SqsGenerationQueue

    return SqsGenerationQueue()


def ai_dynamo_week_repository() -> WeekRepository:
    """The planner_ai copy of the DynamoDB week adapter — parametrized alongside
    the planner_api one so drift between the two copies fails the suite (owner,
    2026-09-06; specs/ai_lambda/design.md section 7)."""
    from planner_ai.adapters.dynamo.weeks import DynamoWeekRepository

    return DynamoWeekRepository()


def ai_generation_records() -> GenerationResultSink:
    """The planner_ai `GenerationResultSink` — the worker's claim/record_result
    write-back to PETICIONIA# (specs/ai_lambda/design.md section 6)."""
    from planner_ai.adapters.dynamo.generations import DynamoGenerationRecords

    return DynamoGenerationRecords()


def seed_ssm_parameter(name: str, value: str) -> None:
    """Put an SSM String parameter into the moto-mocked backend so the
    SsmGenerationGate contract case has something to read."""
    import boto3

    boto3.client("ssm", region_name=os.environ["AWS_DEFAULT_REGION"]).put_parameter(
        Name=name, Value=value, Type="String", Overwrite=True
    )


def ssm_generation_gate(env: str = "dev") -> GenerationGate:
    from planner_ai.adapters.ssm import SsmGenerationGate

    return SsmGenerationGate(env=env, ttl_seconds=0.0)
