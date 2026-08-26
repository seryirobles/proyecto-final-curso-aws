# ai_prompt_versioning — Design

> Feature 24 · tier 1
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 11 `ai_prompt_builder` (`backend/core/src/planner_core/domain/ai_prompt.py`,
> implemented, not yet signed off) — this feature versions the three
> wording constants it already builds; it does not re-derive them.
>
> **§9's gate question is resolved** (human decision, recorded below): a
> general-purpose `ConfigPort`, shaped exactly like the existing `Clock`
> port, with prompt-version selection as its first consumer rather than its
> only reason to exist.

## 0. The invariant this feature exists to protect

`docs/gaps_and_resolutions.md`, `G-84`:

> `ai_prompt.py`'s `build_instructions()` ... compiles
> `HEALTHY_BALANCED_INSTRUCTION`, `OUTPUT_LANGUAGE` and `CONFIGURED_SERVINGS`
> as plain module constants with no version identity — every generation uses
> whatever the current source tree happens to contain ... nothing says how
> that wording is allowed to change over time, or how a past AI-generated
> recipe could be traced back to the exact wording that produced it.

`G-64` solved this shape of problem for the servings count alone by marking
it deployment configuration; `G-84` generalizes that reasoning to all three
wording constants and adds two things `G-64` never needed: a stable identity
per version (so retired wording stays nameable) and retention of retired
versions (so a past generation's wording is never lost).

---

## 1. Scope boundary

**This feature does not touch `ALLOWED_UNITS`, `PromptInstructions`'s field
set, `SpecificationPrompt`, `ReferencePrompt` or `CategoryPrompt`.** It
versions the three wording constants (`servings`, `output_language`,
`healthy_balanced_instruction`) that `build_instructions()` already
composes, and changes how their values are selected — not what
`PromptInstructions` or any downstream type looks like. See
`requirements.md`'s Scope note for why `ALLOWED_UNITS` and the
`Recipe`/`MealSnapshot` field question are both out of scope.

**This feature builds `ConfigPort` as a general-purpose port**, per the
human's decision (§9). Prompt version selection is its first consumer, not
its only justification — this spec still only *implements* the prompt-version
consumer; it does not anticipate or scaffold future `ConfigPort` consumers
beyond leaving the port itself generic (a string-keyed lookup, not a
prompt-version-shaped one).

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is *"Pure logic. No IO, no AWS SDK, no
framework, no clock."* Reading configuration is IO, exactly like reading the
system clock — so `ConfigPort` follows `Clock`'s own boundary precisely:

| Piece | Layer | Why |
|---|---|---|
| `ConfigPort` (`Protocol`) + `EnvConfig` (default implementation) | `planner_core/ports/config.py` | A `Protocol` is an interface, not IO; `EnvConfig` imports only `os` (standard library), so it is a **default implementation** under §1.2.2, not an adapter — same reasoning `SystemClock` already established for `Clock`. |
| `PromptInstructionsVersion`, `PROMPT_INSTRUCTION_VERSIONS`, `UnknownPromptVersion`, `resolve_prompt_version`, `PROMPT_VERSION_CONFIG_KEY`, `build_instructions` (signature changed, §5) | `planner_core/domain/ai_prompt.py` | Pure values and pure functions over a `version_id: str` parameter. Domain never imports `ports/` (§3.1 rule 1), so it cannot read `ConfigPort` itself — same ruling already made for `Clock` at the `week_calendar` gate: **domain takes a plain value, never a port.** |
| `resolve_active_prompt_version(config: ConfigPort) -> PromptInstructionsVersion` | `planner_core/application/prompt_version.py` | Reads the port exactly once and passes the resulting plain `version_id` down to `domain/` — the same shape `application/live_weeks.py`'s `resolve_live_weeks(clock)` already established for `Clock` (`docs/specs.md`'s own worked example). |

No piece of this feature imports an adapter or a Lambda package. `wiring.py`
(each Lambda's composition root) is the only place that constructs
`EnvConfig` for real use; that wiring itself is out of this spec's scope
(feature 17 `ai_lambda`, still architecture-pending on P4) — this spec adds
the port and its domain/application consumers only.

---

## 3. `ConfigPort` — the general-purpose port

```python
"""The config port: the only source of deployment configuration inside planner_core."""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class ConfigPort(Protocol):
    """Supplies a deployment configuration value by key.

    Mirrors Clock's contract shape (planner_core/ports/clock.py): one small
    method, no assumption about where a real implementation reads from.
    """

    def get(self, key: str) -> str | None:
        """Return the configured value for `key`, or None if unset."""
        ...


class EnvConfig:
    """The default `ConfigPort`: reads `os.environ`.

    Ships beside the `Protocol` it satisfies (docs/architecture.md section
    1.2.2) because it imports nothing outside the standard library — the
    same reasoning that keeps `SystemClock` beside `Clock` rather than in a
    Lambda's `adapters/`. Reading `os.environ` is the one sanctioned IO
    boundary this port exists to isolate, mirroring section 1.2.2's "one
    sanctioned exception" language for `SystemClock.now`.
    """

    def get(self, key: str) -> str | None:
        return os.environ.get(key)
```

**Never a singleton, never read ambiently.** Every consumer receives a
`ConfigPort` as an injected constructor or function argument — `wiring.py`
selects `EnvConfig` for real deployments, tests inject a fake, exactly as
`FakeClock` already stands in for `Clock`. No module-level "the current
config" object exists anywhere in this design; see §6 for why that shape was
rejected outright, not merely deferred.

`ConfigPort` lives in `planner_core/ports/config.py` — a new file, general
enough that a later feature needing a different deployment-configured value
(a second `os.environ` key) can depend on it without adding a second port.

---

## 4. The versioned registry (domain layer, unchanged in shape from the earlier draft)

> **Amended by feature 25 (`recipe_metadata_fields`), human-approved
> 2026-08-26 (`G-85`, corrected by `G-86`).** The block below is retained as
> the historical, as-approved-at-this-gate shape (`servings: int`,
> `servings=4`). As of feature 25, `servings` is removed from
> `PromptInstructionsVersion` and from the `v1` entry;
> `recipe_metadata_instruction` (an instruction, not a target value) takes
> its place — see `specs/recipe_metadata_fields/design.md` §6 for the
> as-shipped shape.

```python
@dataclass(frozen=True)
class PromptInstructionsVersion:
    """One version of the wording FR-AI-06, FR-AI-07 and FR-AI-13 require."""

    version_id: str
    servings: int
    output_language: str
    healthy_balanced_instruction: str


PROMPT_INSTRUCTION_VERSIONS: Final[dict[str, PromptInstructionsVersion]] = {
    "v1": PromptInstructionsVersion(
        version_id="v1",
        servings=4,
        output_language="es-ES",
        healthy_balanced_instruction=(
            "Genera un menu saludable y equilibrado, variando las fuentes de "
            "proteina entre los platos. Esta indicacion tiene fines de "
            "planificacion domestica y no constituye un consejo medico."
        ),
    ),
}
"""Append-only (R2): a version is added here when wording changes; an
existing key is never removed or overwritten. A guard test enumerates the
version ids expected to exist and asserts each still resolves, the same
mechanism test_shared_kernel_guards.py already uses to protect Unit and
IngredientCategory from silent shrinkage."""

PROMPT_VERSION_CONFIG_KEY: Final[str] = "AI_PROMPT_VERSION_ID"
"""The ConfigPort key naming which entry of PROMPT_INSTRUCTION_VERSIONS is
active. Declared in domain/ because it is not itself configuration — it is
the *name* of a configuration key, a plain string constant like any other."""


class UnknownPromptVersion(PlannerError):
    """Raised when a version identifier does not resolve, or none is
    configured (R4)."""


def resolve_prompt_version(version_id: str) -> PromptInstructionsVersion:
    """R6: every retained version is retrievable by its identifier."""
    try:
        return PROMPT_INSTRUCTION_VERSIONS[version_id]
    except KeyError:
        raise UnknownPromptVersion(version_id) from None
```

`v1`'s content is exactly `CONFIGURED_SERVINGS`, `OUTPUT_LANGUAGE` and
`HEALTHY_BALANCED_INSTRUCTION`'s current, already-approved values (feature
11's design.md §4) — this feature gives existing wording a name, it does not
change it. `UnknownPromptVersion` follows this module's own naming precedent
(`UnknownUnit` in `units.py`, `UnknownIngredientCategory` in
`ingredient_category.py`).

---

## 5. `build_instructions()` — the breaking change to feature 11

`domain/ai_prompt.py`'s `build_instructions()` cannot read `ConfigPort`
itself (§2). Its signature changes to accept the plain value the
application layer resolves:

> **Amended by feature 25 (`recipe_metadata_fields`), human-approved
> 2026-08-26 (`G-85`, corrected by `G-86`).** The block below is retained as
> the historical, as-approved-at-this-gate shape. As of feature 25,
> `PromptInstructions` carries `recipe_metadata_instruction` instead of
> `servings` — see `specs/recipe_metadata_fields/design.md` §6.

```python
def build_instructions(version_id: str) -> PromptInstructions:
    """R5. version_id names which PROMPT_INSTRUCTION_VERSIONS entry supplies
    servings, output_language and healthy_balanced_instruction; raises
    UnknownPromptVersion (R4) if it does not resolve."""
    version = resolve_prompt_version(version_id)
    return PromptInstructions(
        servings=version.servings,
        output_language=version.output_language,
        healthy_balanced_instruction=version.healthy_balanced_instruction,
        allowed_units=ALLOWED_UNITS,
    )
```

`build_specification_prompt`, `build_reference_prompt` and
`build_category_prompt` each gain the same `version_id: str` parameter and
forward it to `build_instructions(version_id)` unchanged otherwise.

**This is a breaking change to feature 11's already-implemented, not-yet-signed-off
`build_instructions()` signature** — feature 11's `requirements.md` R6–R9
pin it as taking no arguments, and R13/R16/R19 pin the three builders as
calling it with no arguments. Adopting this design means amending
`specs/ai_prompt_builder/requirements.md` (feature 11) alongside this
feature — see `tasks.md` T5.

```python
def resolve_active_prompt_version(config: ConfigPort) -> PromptInstructionsVersion:
    """The one place ConfigPort meets domain/ai_prompt.py: reads the port
    exactly once (R3) and resolves the plain id it returns (R4, R6, R7)."""
    version_id = config.get(PROMPT_VERSION_CONFIG_KEY)
    if version_id is None:
        raise UnknownPromptVersion(PROMPT_VERSION_CONFIG_KEY)
    return resolve_prompt_version(version_id)
```

This is `planner_core/application/prompt_version.py`'s entire content. A
caller building a specific prompt (feature 12/17) calls
`resolve_active_prompt_version(config)` once to get the active
`PromptInstructionsVersion` (content plus `version_id` together, R7), then
passes `.version_id` into whichever `build_*_prompt(..., version_id=...)`
domain function it needs. Kept as two small, independently callable
functions rather than one that both reads the port and builds a specific
prompt shape — the same "accept the plain value, not the whole request"
split `generation_request`'s design (§8, alternative C) already modelled for
`resolve_targets`/`idempotency_key`.

---

## 6. Rejected alternatives

**A module-level singleton `ConfigPort` instance, read ambiently instead of
injected.** Rejected outright, not merely deferred. `docs/architecture.md`
§3.1 rule 6 closed exactly this hole for time — *"Time is a port, never
`datetime.now()` inside `core`"* — precisely because an ambiently-read global
sits within reach of every test and every call site, defeating the one thing
a port buys: a test can supply a different value without monkeypatching a
module attribute, and production code cannot silently diverge from what
`wiring.py` decided to inject. A `ConfigPort` singleton would reopen that
same hole for configuration instead of time — the *why* is identical, only
the *what* differs. `test_no_ambient_time.py` is `Clock`'s mechanical
enforcement of this rule for `SystemClock`; this design keeps `ConfigPort`
to the same discipline by injection alone (no mechanical test is proposed
here, since unlike `SystemClock.now`, `EnvConfig` has no historical footgun
of a "naive" bare call to guard against — but injection-only is still the
rule, enforced by review, same as every other port in `docs/architecture.md`
§3.1 rule 4's "nothing imports an adapter except `wiring.py`").

**Index-keyed list instead of an id-keyed dict** for
`PROMPT_INSTRUCTION_VERSIONS` (e.g. `list[PromptInstructionsVersion]`
selected by position, `[-1]` for "latest"). Rejected. This project already
has a standing rule against treating position as identity —
`AGENTS.md`'s working conventions: *"Row numbers and `AP` numbers are
positions, not identifiers... refer to... by title... not position."* A list
index shifts if an earlier entry is ever reordered; a string `version_id`
keyed dict cannot drift that way, and it is also the natural shape for
`ConfigPort.get()`'s return value to name directly.

**A prompt-version-specific port (`PromptVersionSelector`) instead of a
general `ConfigPort`.** Considered during drafting, superseded by the
human's explicit direction: a narrowly-typed port would need a second,
near-identical port the next time any deployment-varying value needs
injecting outside `domain/`, whereas one string-keyed `ConfigPort` serves
every future case of this shape. The cost — callers must know which key
name to ask for — is small and already paid once, in `PROMPT_VERSION_CONFIG_KEY`.

---

## 7. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/ports/config.py` | `ConfigPort` (`Protocol`), `EnvConfig` (default implementation). |
| `backend/core/src/planner_core/application/prompt_version.py` | `resolve_active_prompt_version(config)`. |
| `backend/core/tests/application/test_prompt_version.py` | Tests for `resolve_active_prompt_version`, using a `FakeConfig`. |

### Modified

| Path | Change |
|---|---|
| `backend/core/src/planner_core/domain/ai_prompt.py` | Add `PromptInstructionsVersion`, `PROMPT_INSTRUCTION_VERSIONS`, `PROMPT_VERSION_CONFIG_KEY`, `UnknownPromptVersion`, `resolve_prompt_version`. Change `build_instructions()`, `build_specification_prompt()`, `build_reference_prompt()` and `build_category_prompt()` to accept `version_id: str`. |
| `backend/core/tests/domain/test_ai_prompt.py` | Extend with R1–R7; update existing feature-11 tests for the new `version_id` parameter. |
| `backend/core/tests/support/fakes.py` | Add `FakeConfig` (a `dict`-backed `ConfigPort`), named per `docs/conventions.md`'s `Fake` + port-name convention. |
| `specs/ai_prompt_builder/requirements.md` (feature 11) | Amend R6–R9, R13, R16, R19 for the new `version_id` parameter — see `tasks.md` T5. |

---

## 8. Exceptions

`UnknownPromptVersion(PlannerError)` — new, in `domain/ai_prompt.py` (§4).
No other new exception. `ConfigPort.get()` itself never raises — a missing
key returns `None`, and `resolve_active_prompt_version` is what turns that
into `UnknownPromptVersion` (§5), keeping the port's own contract as simple
as `Clock`'s.

No function returns `None` to signal failure except `ConfigPort.get()`
itself, whose `None` is a documented "unset" sentinel consumed one layer up
— the same shape `dict.get()` already uses throughout the standard library,
not a violation of `docs/architecture.md` §4 invariant 12 (which governs
*failure* signalling, not optionality of configuration).

---

## 9. `docs/architecture.md` §2.1 items

None new. The concrete wording of `v1` is `HEALTHY_BALANCED_INSTRUCTION`'s
existing, already-approved text (feature 11's design.md §4) given a version
id; `CONFIGURED_SERVINGS = 4` was already approved as a §2.1 item at feature
11's gate and is not reopened here.

---

## 10. Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs
  P2–P6. `ConfigPort`'s real (env-backed) wiring for a deployed Lambda is
  feature 17 `ai_lambda`'s job, still gated on P4 — this spec only adds the
  port, its default implementation, and its domain/application consumers.
- **Frozen docs:** none modified. `specs/ai_prompt_builder/requirements.md`
  is a spec, not a frozen requirements doc — amending it is expected
  cross-feature spec maintenance, not a `docs/requirements.md`-style freeze
  violation.
- **User-facing strings:** none. `v1`'s wording is prompt content sent to a
  future AI provider, never shown to a user — same reasoning as feature 11's
  design.md §4.
- **Runtime dependencies:** none added. `ConfigPort`'s `Protocol` and
  `EnvConfig` both import only `os` and `typing` (standard library);
  `planner-core` keeps `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites `FR-AI-14`, the one id
  in this feature's `covers` array.

---

## 11. Gate question — resolved

Recorded for history: `design.md`'s original draft posed two options —
Option A (a prompt-version-only constant, like `CONFIGURED_SERVINGS`) and
Option B (a narrowly-typed `PromptVersionSelector` port, like `Clock`). The
human resolved this in favour of a **generalized Option B**: `ConfigPort`,
scoped to arbitrary string-keyed deployment configuration rather than one
value, with prompt version selection as its first consumer. Sections 2–8
above describe that decision in full; nothing in this design remains open.
