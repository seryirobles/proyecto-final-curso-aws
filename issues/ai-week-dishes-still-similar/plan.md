# Plan — issue 19 `ai-week-dishes-still-similar`

Owner ruling (2026-10-12): option (w) only, as a new prompt version v6 (v1-v5 untouched); no new Part; best effort for exact and near-duplicate names; general fix (v6 also drops the empty-needs line).

## Expected behaviour
- **E1** When a v6 week-slot prompt carries names to avoid, the rendered text SHALL contain every one of those names. (`G-95`, `FR-AI-06`)
- **E2** The v6 avoid instruction SHALL ask the model not to reuse the main ingredient or the style of the listed dishes, not only their names. (`G-95`, `FR-AI-06`)
- **E3** The v6 prompt SHALL place a positive variety instruction (a different cuisine) after the list of avoided names. (`G-95`, `FR-AI-06`)
- **E4** When there are no category needs, the v6 prompt SHALL render no line that ends in an empty value (`remaining needs: .`), and SHALL still render the needs when there are some. (`FR-AI-04`, `FR-AI-06`)
- **E5** v6 SHALL be the newest registry key, and the v1-v5 rendered text SHALL be byte-identical to triage. (`FR-AI-14`, `G-84`)

## Fix design
- `domain/ai_prompt.py`:
  - New v6 entry, appended. It reuses v5's fields except the category framing.
  - v6 framing renders without `${needs}`; the needs sentence becomes a separate template, emitted only when needs exist.
  - New `AVOID_NAMES_TEMPLATES["v6"]`: avoid names, main ingredient and style, then a positive cuisine/variety steer.
  - Follows the v5 precedent of a side registry keyed by version, so v1-v5 dataclass fields are untouched.
- `lambda_ai/adapters/bedrock.py` `_render`: emits the needs sentence only when needs exist and the version has the template. v1-v5 output must not change (golden digests).
- Consequential edits, the same pattern as issue 18:
  - `core/tests/domain/test_ai_prompt.py`: registry set adds `"v6"`; add a field-name entry if a field is added.
  - `docs/local_development.md`: `AI_PROMPT_VERSION_ID=v6`. Two live tests assert that this equals the newest key: `test_prompt_dish_framing.py` and `lambda_api/tests/test_local_development_env.py`.
- Owner: set `AI_PROMPT_VERSION_ID=v6` in every deployed config.
- Retry and mix use the same `_fill_slots` and `_render`, so they are covered.

## Rejected
- (p) Plan-then-fill: guarantees distinctness, but adds a call, a port method and a run-record field; the owner declined it.
- (c) Backend-assigned steer: needs a vocabulary no FR defines and may clash with category counts; declined.

## Tests that define solved
| Staged file | Destination |
|---|---|
| `tests/backend/lambda_ai/tests/test_prompt_week_variety_v6.py` | `backend/lambda_ai/tests/test_prompt_week_variety_v6.py` |

| E | Test | Red at triage (2026-10-12) |
|---|---|---|
| E1 | `test_every_avoided_name_still_reaches_the_model` | green (regression of G-95) |
| E2 | `test_the_avoid_instruction_covers_main_ingredient_and_style` | **red**: v5 text has no "main ingredient" |
| E3 | `test_a_positive_variety_steer_follows_the_avoided_names` | **red**: nothing after the list mentions a cuisine |
| E4 | `test_empty_needs_render_no_dangling_line[first_slot, later_slot]` | **red**: `This week's remaining needs: .` |
| E4 | `test_needs_still_render_when_present` | green (regression) |
| E5 | `test_v6_is_the_newest_prompt_version` | **red**: newest is `v5` |
| E5 | `test_retired_versions_render_byte_identical[v1..v5]` | green (golden sha256 of 6 renders per version) |

Result: 5 failed, 7 passed. ruff, format and mypy are clean. The live copy was removed and `git status` is unchanged.
Best effort: no test asserts that the live model stops repeating. Only the prompt content is testable offline.
