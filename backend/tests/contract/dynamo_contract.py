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
from planner_core.ports.generation_queue import GenerationQueue
from planner_core.ports.recipes import RecipeRepository
from planner_core.ports.rules import RuleRepository
from planner_core.ports.shopping_list import ShoppingListRepository
from planner_core.ports.weeks import WeekRepository

for _var, _value in {
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_SESSION_TOKEN": "testing",
}.items():
    os.environ.setdefault(_var, _value)


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
