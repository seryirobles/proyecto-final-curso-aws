# Issue 22 — tasks

- [x] T1 Move the three staged test files verbatim; confirm the red result. E1–E6
- [x] T2 Explicit `lambda_handler(event, context)` + `is not None` in `planner_api/handler.py`. E1, E5
- [x] T3 Same in `authorizer.py`. E2, E5
- [x] T4 Same in `scheduled.py`. E3, E5
- [x] T5 Same in `planner_ai/handler.py`. E4, E5
- [x] T6 Optionally `config if config is not None else EnvConfig()` in `wiring.py`. E5 — skipped by owner ruling (no wiring.py change)
- [x] T7 `./init.sh` green, mypy included. all
