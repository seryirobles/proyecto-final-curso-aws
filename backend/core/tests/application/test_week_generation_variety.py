"""Issue ai-week-dishes-repeat: each AI slot's prompt names the dishes already
in the week and those produced earlier in the same run, so the model can avoid
them. Run, retry and mix paths."""

from __future__ import annotations

from datetime import date

from support.fakes import (
    FakeAiProvider,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_core.application.week_generation import run_slot_retry, run_week_generation
from planner_core.domain.ai_output import RawIngredient, RawRecipeOutput
from planner_core.domain.ai_prompt import PROMPT_INSTRUCTION_VERSIONS
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationSnapshot,
    SlotProgress,
    SlotStatus,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot, Recipe
from planner_core.domain.rules import RuleSet
from planner_core.ports.ai_provider import AiPrompt
from planner_core.ports.generation_queue import StoredGeneration
from planner_core.ports.recipes import LibraryRecipe

WEEK = IsoWeek(2026, 34)
KEY = "hash-1"
SATURDAY = date.fromisocalendar(2026, 34, 6)  # 4 open slots: Sat + Sun, lunch + dinner
SUNDAY = date.fromisocalendar(2026, 34, 7)
LATEST = list(PROMPT_INSTRUCTION_VERSIONS)[-1]  # append-only registry: last key is newest
DISHES = (
    "Ensalada de quinoa con aguacate",
    "Lentejas estofadas",
    "Merluza en salsa verde",
    "Pollo al horno con patatas",
)


def _output(name: str) -> RawRecipeOutput:
    return RawRecipeOutput(
        name=name,
        ingredients=(RawIngredient(name="arroz", quantity=100.0, unit="g"),),
        tools=("olla",),
        procedure=("Cocer.",),
        category="carbohydrate",
    )


class _SpyProvider(FakeAiProvider):
    """Records every prompt; answers with DISHES in order."""

    def __init__(self) -> None:
        super().__init__(responses=[_output(name) for name in DISHES])
        self.prompts: list[AiPrompt] = []

    def generate(self, prompt: AiPrompt) -> RawRecipeOutput:
        self.prompts.append(prompt)
        return super().generate(prompt)


def _mentions(prompt: AiPrompt, name: str) -> bool:
    # Field-agnostic: the name may sit in any field of the prompt value object.
    return name.casefold() in repr(prompt).casefold()


def _meal(name: str) -> MealSnapshot:
    return MealSnapshot(
        name=name, ingredients=(), tools=(), procedure=(), category=IngredientCategory.MEAT
    )


def _queue() -> FakeGenerationQueue:
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending", slots=())
    return queue


def _run(
    provider: _SpyProvider,
    *,
    weeks: FakeWeekRepository | None = None,
    recipes: FakeRecipeRepository | None = None,
    mode: GenerationMode = GenerationMode.AI_ONLY,
    first_day: date = SATURDAY,
) -> None:
    run_week_generation(
        KEY,
        GenerationRequest(week=WEEK, mode=mode),
        RuleSet(),
        LATEST,
        "u-1",
        first_day,
        provider=provider,
        weeks=weeks or FakeWeekRepository(),
        recipes=recipes or FakeRecipeRepository(),
        queue=_queue(),
        gate=FakeGenerationGate(),
    )


def test_each_ai_slot_prompt_names_the_dishes_generated_earlier_in_the_run() -> None:
    """E1 — reproduction: today every slot gets the same prompt and no names."""
    provider = _SpyProvider()

    _run(provider)

    assert len(provider.prompts) == 4
    for index, prompt in enumerate(provider.prompts):
        missing = [name for name in DISHES[:index] if not _mentions(prompt, name)]
        assert missing == [], f"slot {index + 1} prompt omits {missing}"


def test_each_ai_slot_prompt_names_the_dishes_already_in_the_week() -> None:
    """E2 — candidates and definitives anywhere in the week, open slot or not."""
    weeks = FakeWeekRepository()
    monday = SlotRef(date.fromisocalendar(2026, 34, 1), MealSlot.LUNCH)  # past, not targeted
    sunday = SlotRef(SUNDAY, MealSlot.DINNER)  # open: candidate only
    chosen = Candidate(id="c0", meal=_meal("Cocido madrileno"), author="chef")
    weeks.save_slot(WEEK, monday, SlotContents(candidates=(chosen,), definitive_id="c0"))
    proposed = Candidate(id="c1", meal=_meal("Paella valenciana"), author="chef")
    weeks.save_slot(WEEK, sunday, SlotContents(candidates=(proposed,)))
    provider = _SpyProvider()

    _run(provider, weeks=weeks)

    assert provider.prompts
    for prompt in provider.prompts:
        assert _mentions(prompt, "Cocido madrileno")
        assert _mentions(prompt, "Paella valenciana")


def test_mix_ai_slots_are_told_the_library_picks_of_the_same_run() -> None:
    """E3 — a library pick is a dish of this run like any AI one."""
    library = FakeRecipeRepository()
    recipe = Recipe(
        name="Garbanzos con espinacas",
        ingredients=(),
        tools=("olla",),
        procedure=("Cocer.",),
        category=IngredientCategory.LEGUME,
    )
    library.entries["r1"] = LibraryRecipe(id="r1", recipe=recipe, author="chef")
    provider = _SpyProvider()

    _run(provider, recipes=library, mode=GenerationMode.MIX)

    assert len(provider.prompts) == 3
    assert all(_mentions(prompt, "Garbanzos con espinacas") for prompt in provider.prompts)


def test_a_retried_slot_prompt_names_the_week_s_other_dishes() -> None:
    """E4 — per-slot retry must not reintroduce the repeat."""
    weeks = FakeWeekRepository()
    dinner = SlotRef(SUNDAY, MealSlot.DINNER)
    sibling = Candidate(id="c1", meal=_meal("Ensalada de quinoa con aguacate"), author="ai")
    weeks.save_slot(WEEK, dinner, SlotContents(candidates=(sibling,)))
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(
        idempotency_key=KEY,
        status="running",
        slots=(
            SlotProgress(7, 1, SlotStatus.PENDING),
            SlotProgress(7, 2, SlotStatus.DONE),
        ),
        snapshot=GenerationSnapshot(WEEK, GenerationMode.AI_ONLY, RuleSet(), LATEST),
    )
    provider = _SpyProvider()

    run_slot_retry(
        KEY,
        7,
        1,
        GenerationRequest(week=WEEK, mode=GenerationMode.AI_ONLY),
        RuleSet(),
        LATEST,
        "u-2",
        SUNDAY,
        provider=provider,
        weeks=weeks,
        recipes=FakeRecipeRepository(),
        queue=queue,
        gate=FakeGenerationGate(),
    )

    assert len(provider.prompts) == 1
    assert _mentions(provider.prompts[0], "Ensalada de quinoa con aguacate")
