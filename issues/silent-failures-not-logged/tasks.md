# Tasks — silent-failures-not-logged (issue 14)

Prerequisite: issue 13's changes are in the tree. This plan builds on its logging.

- [ ] T1 — Move the six staged test files verbatim (`plan.md` § Test plan); confirm 21 red / 3 green, including the `test_single_recipe_rejection_logs_validator_value_and_snippet` cases. Covers: E1–E8.
- [ ] T2 — `ai_output.py`: `GenerationFailure.cause` (compare=False, default None); `validate_and_preview` fills it with class name + value capped at 100. Covers: E1, E3.
- [ ] T3 — `single_recipe_generation.py` and `week_generation.py`: WARNING on the `GenerationFailure` branch with key, `cause`, `repr(raw)[:500]`. Covers: E1, E2, E3.
- [ ] T4 — `bedrock.py`: no-text and parse errors carry `stopReason` and `text[:500]`. Covers: E4.
- [ ] T5 — `errors.py`: per-row WARNING opt-in, set only on `UnknownPromptVersion`. Covers: E5, E6.
- [ ] T6 — `ssm.py`: remember the last read outcome; INFO only on a transition into disabled-by-switch; the fail-closed WARNING is unchanged. Covers: E7.
- [ ] T7 — `lambda_api/handler.py:104`, `scheduled.py:36`, `lambda_ai/handler.py:33, :61`: message text carries method/resource/status, week id, and generation key; keep `extra`; no logging config. Covers: E8.
- [ ] T8 — All moved tests green; `./init.sh` green. Covers: E1–E8.

Optional, **awaiting owner** (only if he says yes to B1, `plan.md` § Optional block B1):

- [ ] TB1 — `core/ports/password_hasher.py:45`: WARNING "malformed stored password hash" (no hash, password or username), still returns `False`; add its test first. Covers: EB1.
