# Tasks — ai-generation-422-unavailable (issue 13, re-scoped 2026-10-07)

- [x] T1 — Move the four staged test files verbatim to their destinations (`plan.md` § Test plan); confirm 22 red / 3 green, including `test_override_true_enables_the_local_worker_whatever_ssm_says` and `test_single_recipe_generation_is_accepted_under_the_documented_env`. Covers: E1–E8.
- [x] T2 — `docs/local_development.md`: §2 `export AI_PROMPT_VERSION_ID=v3`, §3 `export AI_GENERATION_ENABLED=true`, one sentence each. Covers: E1, E2, E4.
- [x] T3 — `local_worker.py`: `build_local_dependencies()` (exact `"true"`/`"false"` replace the gate; anything else leaves `build_dependencies()` untouched); `main()` builds it once and passes it to `handle`. Do not touch `wiring.py` or `handler.py`. Covers: E5, E6.
- [x] T4 — `adapters/ssm.py`: warning on the fail-closed branch with the parameter name and error type/code, no credential values. Covers: E7.
- [x] T5 — `single_recipe_generation.py` and `week_generation.py`: warning in each `except AiProviderError`, with key and error text; stdlib `logging` only. Covers: E8.
- [x] T6 — All moved tests green; `./init.sh` green. Covers: E1–E8.
- [x] T7 (done by leader at owner request) — Report to the leader: the owner adds `"AI_GENERATION_ENABLED": "true"` to "ai: local worker" in `.vscode/launch.json` (gitignored, owner's file). Covers: E4, E5.
