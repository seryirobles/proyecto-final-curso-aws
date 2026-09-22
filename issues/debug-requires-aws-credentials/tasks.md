# debug-requires-aws-credentials — tasks

- [ ] T1 — Move `issues/debug-requires-aws-credentials/tests/backend/lambda_ai/tests/test_local_worker.py` to `backend/lambda_ai/tests/test_local_worker.py` verbatim; confirm 4 red / 1 green exactly as `plan.md` records. Covers: E1, E2, E3, E4.
- [ ] T2 — In `backend/lambda_ai/src/planner_ai/adapters/dynamo/_table.py`, give `resource()` and `client()` placeholder credentials when `_ENDPOINT_URL` is set (and only then). Covers: E2, E3.
- [ ] T3 — In `backend/lambda_ai/src/planner_ai/local_worker.py`, do the same for `_sqs()` when `_ENDPOINT_URL` is set. Covers: E1.
- [ ] T4 — In `main()`, replace the `NoCredentialsError` branch with a Bedrock-auth check that runs before the clients are built (no `AWS_BEARER_TOKEN_BEDROCK` and no resolvable credential chain -> one error line, `SystemExit(1)`); leave `ProfileNotFound`/`ClientError` untouched. Covers: E4.
- [ ] T5 — Run `cd backend && uv run pytest -q` plus `ruff format --check .`, `ruff check .`, `mypy .`; all five staged tests green, nothing else changed. Covers: E1, E2, E3, E4.
- [ ] T6 — Update `docs/local_development.md` §3 (the "Do NOT set AWS_ACCESS_KEY_ID..." block and the closing fast-fail paragraph) to match the new behaviour. Do not touch `.vscode/launch.json`. Covers: E1, E4.
- [ ] T7 — Record the `FR/NFR -> E<n> -> T<n> -> test` map in `progress/impl_debug-requires-aws-credentials.md`. Covers: E1, E2, E3, E4.
