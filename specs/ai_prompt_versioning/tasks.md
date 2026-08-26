# ai_prompt_versioning — Tasks

> Feature 24 · tier 1. Read `requirements.md` and `design.md` first.
> `design.md` §9's gate question is resolved: a general-purpose `ConfigPort`,
> shaped like `Clock`, with prompt version selection as its first consumer.
> The `implementer` ticks `[x]` as each task completes; the `reviewer`
> rejects if any `[ ]` remains without a documented justification.

- [x] T1 — Add `planner_core/ports/config.py`: `ConfigPort` (`Protocol`,
  `get(key: str) -> str | None`) and `EnvConfig` (default implementation
  reading `os.environ`), per `design.md` §3. Covers: R3.

- [x] T2 — Add `PromptInstructionsVersion` (`@dataclass(frozen=True)`),
  `PROMPT_INSTRUCTION_VERSIONS` (the `v1` entry, carrying feature 11's
  existing `CONFIGURED_SERVINGS` / `OUTPUT_LANGUAGE` /
  `HEALTHY_BALANCED_INSTRUCTION` values unchanged), `PROMPT_VERSION_CONFIG_KEY`,
  `UnknownPromptVersion` and `resolve_prompt_version(version_id)` in
  `backend/core/src/planner_core/domain/ai_prompt.py`, per `design.md` §4.
  Covers: R1, R2, R4, R6.

- [x] T3 — Change `build_instructions()` to accept `version_id: str` and
  source `servings`, `output_language` and `healthy_balanced_instruction`
  from `resolve_prompt_version(version_id)`. Change
  `build_specification_prompt`, `build_reference_prompt` and
  `build_category_prompt` to accept and forward the same parameter. Covers:
  R5.

- [x] T4 — Add `planner_core/application/prompt_version.py`:
  `resolve_active_prompt_version(config: ConfigPort) ->
  PromptInstructionsVersion`, per `design.md` §5. Covers: R3, R4, R7.

- [x] T5 — Amend `specs/ai_prompt_builder/requirements.md` (feature 11, not
  yet signed off) to reflect `build_instructions()`'s and the three
  builders' new `version_id` parameter — R6–R9, R13, R16, R19 there
  currently pin them as taking no extra argument. Flag the amendment
  explicitly in the implementation report; do not silently diverge from an
  approved-looking spec. Covers: (feature 11's own R6–R9, R13, R16, R19,
  amended).

- [x] T6 — Add `FakeConfig` to `backend/core/tests/support/fakes.py` (a
  `dict`-backed `ConfigPort`, named per `docs/conventions.md`'s `Fake` +
  port-name convention, mirroring `FakeClock`). Covers: R3, R4, R7 (test
  support only).

- [x] T7 — Extend `backend/core/tests/domain/test_ai_prompt.py`:
  - update every existing feature-11 test for the new `version_id`
    parameter;
  - a registry test asserting every expected version id (currently just
    `"v1"`) resolves via `resolve_prompt_version` and carries the values
    feature 11 already approved (R1, R2, R6);
  - a test asserting `resolve_prompt_version` raises `UnknownPromptVersion`
    for an id absent from `PROMPT_INSTRUCTION_VERSIONS` (R4);
  - a test asserting `build_instructions(version_id)`'s result matches that
    version's `servings` / `output_language` / `healthy_balanced_instruction`
    (R5).
  Covers: R1, R2, R4, R5, R6.

- [x] T8 — Add `backend/core/tests/application/test_prompt_version.py`:
  - a test asserting `resolve_active_prompt_version(FakeConfig({...}))`
    returns the `PromptInstructionsVersion` named by
    `PROMPT_VERSION_CONFIG_KEY`, with its `version_id` field present
    alongside its content (R3, R7);
  - a test asserting it raises `UnknownPromptVersion` when the key is unset
    (`FakeConfig({})`) and when it names an unregistered version id (R4);
  - a test asserting `ConfigPort.get` is called exactly once per resolution
    (mirrors `FakeClock.readings`' single-read assertion for
    `resolve_live_weeks`).
  Covers: R3, R4, R7.

- [x] T9 — Run `./init.sh`; confirm `ruff format`, `ruff check`, `mypy
  --strict` and `pytest` (deselecting `-m 'not aws'`) all pass, and that
  `test_shared_kernel_guards.py` and `test_no_ambient_time.py` still pass
  unmodified (`ConfigPort`/`EnvConfig` add no ambient-time call and no new
  shared-kernel enum). Covers: R1–R7.
