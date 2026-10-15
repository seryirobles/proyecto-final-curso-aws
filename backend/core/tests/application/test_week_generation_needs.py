"""Issue ai-week-dishes-repeat E6 (G-95): each AI slot's category needs are
reduced by the category of the recipe the previous AI slot wrote."""

from __future__ import annotations

from datetime import date

from support.fakes import (
    FakeAiProvider,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_core.application.week_generation import run_week_generation
from planner_core.domain.ai_output import RawIngredient, RawRecipeOutput
from planner_core.domain.ai_prompt import CategoryPrompt
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.generation import GenerationMode, GenerationRequest
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot
from planner_core.domain.rules import CategoryCountRule, RuleSet
from planner_core.ports.ai_provider import AiPrompt
from planner_core.ports.generation_queue import StoredGeneration

WEEK = IsoWeek(2026, 34)
KEY = "hash-1"
SATURDAY = date.fromisocalendar(2026, 34, 6)  # 4 open slots


def _fish(name: str) -> RawRecipeOutput:
    return RawRecipeOutput(
        name=name,
        ingredients=(RawIngredient(name="merluza", quantity=100.0, unit="g"),),
        tools=("olla",),
        procedure=("Cocer.",),
        category="fish",
    )


class _Spy(FakeAiProvider):
    def __init__(self) -> None:
        super().__init__(responses=[_fish(f"Pescado {i}") for i in range(4)])
        self.prompts: list[AiPrompt] = []

    def generate(self, prompt: AiPrompt) -> RawRecipeOutput:
        self.prompts.append(prompt)
        return super().generate(prompt)


def test_ai_slots_do_not_overfill_a_category_capped_by_a_rule() -> None:
    """E6 — one fish needed: only the first AI slot is told so."""
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending", slots=())
    rules = RuleSet(category_counts=(CategoryCountRule(IngredientCategory.FISH, 1),))
    provider = _Spy()

    run_week_generation(
        KEY,
        GenerationRequest(week=WEEK, mode=GenerationMode.AI_ONLY),
        rules,
        "v4",
        "u-1",
        SATURDAY,
        provider=provider,
        weeks=FakeWeekRepository(),
        recipes=FakeRecipeRepository(),
        queue=queue,
        gate=FakeGenerationGate(),
    )

    fish_needed = [
        sum(r.count for r in p.category_counts if r.category is IngredientCategory.FISH)
        for p in provider.prompts
        if isinstance(p, CategoryPrompt)
    ]
    assert fish_needed == [1, 0, 0, 0]


def _meal(name: str) -> MealSnapshot:
    return MealSnapshot(
        name=name, ingredients=(), tools=(), procedure=(), category=IngredientCategory.MEAT
    )


def test_avoid_names_list_a_dish_once_whatever_its_case_or_accents() -> None:
    """G-95 — names match through domain.text.normalize, not by exact string."""
    weeks = FakeWeekRepository()
    monday = SlotRef(date.fromisocalendar(2026, 34, 1), MealSlot.LUNCH)  # not targeted
    week_dishes = (
        Candidate(id="c0", meal=_meal("Paella valenciana"), author="chef"),
        Candidate(id="c1", meal=_meal("Salmón al horno"), author="chef"),
    )
    weeks.save_slot(WEEK, monday, SlotContents(candidates=week_dishes))
    provider = _Spy()
    provider.responses[:] = [_fish(n) for n in ("paella Valenciana", "Salmon al horno", "A", "B")]
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending", slots=())

    run_week_generation(
        KEY,
        GenerationRequest(week=WEEK, mode=GenerationMode.AI_ONLY),
        RuleSet(),
        "v5",
        "u-1",
        SATURDAY,
        provider=provider,
        weeks=weeks,
        recipes=FakeRecipeRepository(),
        queue=queue,
        gate=FakeGenerationGate(),
    )

    last = provider.prompts[-1]
    assert isinstance(last, CategoryPrompt)
    folded = [n.casefold() for n in last.avoid_names]
    assert sum(n == "paella valenciana" for n in folded) == 1
    assert sum(n.startswith("salm") for n in folded) == 1
