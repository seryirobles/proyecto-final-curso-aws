# Implementation report — issue 1 `rule-creation-400-invalid-request`

## What changed

- `backend/lambda_api/src/planner_api/handler.py`: `path_params` is now built
  with `urllib.parse.unquote` applied to every value before routing (one site,
  covers PUT, DELETE and the local server per `plan.md` § Fix design 1).
- `frontend/src/hooks/useRules.js`: both URL builds (`putRule` line ~109,
  `remove` line ~132) wrap `computeRuleId(rule)` in `encodeURIComponent(...)`.
  `computeRuleId` itself is unchanged.
- Named corrections to existing tests (pre-fix URL shape, not a weakening,
  `plan.md` § Existing tests):
  - `frontend/tests/hooks/useRules.test.js` lines 67, 86, 103, 122:
    `'/v1/rules/cat#meat'` → `'/v1/rules/cat%23meat'`,
    `'/v1/rules/pin#3#2'` → `'/v1/rules/pin%233%232'`,
    `'/v1/rules/day#5'` → `'/v1/rules/day%235'`,
    `'/v1/rules/day#7'` → `'/v1/rules/day%237'`.
  - `frontend/tests/hooks/useRules.mutationVisibility.test.js:37`:
    `url.replace('/v1/rules/', '')` → `decodeURIComponent(url.replace('/v1/rules/', ''))`.
- Staged tests moved verbatim (diffed byte-identical against
  `issues/rule-creation-400-invalid-request/tests/` both before and after the
  fix):
  - `backend/lambda_api/tests/test_rule_id_path_encoding.py`
  - `frontend/tests/hooks/useRules.ruleIdEncoding.test.js`

## Red → green evidence

Before the fix (T1): 6 backend tests red (`test_put_with_a_percent_encoded_rule_id_saves_the_rule` ×3, `test_put_saves_a_category_count_rule_under_its_decoded_id`, `test_delete_with_a_percent_encoded_rule_id_removes_the_rule`, `test_the_handler_accepts_an_undecoded_rule_id_path_parameter`), 1 backend guard test green (`test_a_rule_id_truncated_at_the_hash_is_still_rejected`); 4 frontend tests red (`saveCategoryCount`, `savePin`, `saveDisabledDay`, `remove`) — all matching `plan.md` § Test plan exactly.

After the fix (T2-T4): `backend/lambda_api/tests/test_rule_id_path_encoding.py` — 7 passed. `frontend/tests/hooks/useRules.ruleIdEncoding.test.js` + `useRules.test.js` + `useRules.mutationVisibility.test.js` — 18 passed. `./init.sh` green end to end: 1043 backend tests (pytest), ruff format/check, mypy all `[OK]`; frontend prettier/eslint/vitest all `[OK]`.

## Traceability — FR → E<n> → T<n> → test

| FR | E<n> | T<n> | Test |
|---|---|---|---|
| FR-RULE-03, FR-RULE-04, FR-RULE-06 | E1 (SPA sends complete percent-encoded id, PUT) | T3 | `frontend/tests/hooks/useRules.ruleIdEncoding.test.js` — *saveCategoryCount…*, *savePin…*, *saveDisabledDay…* |
| FR-RULE-03, FR-RULE-04, FR-RULE-06 | E2 (api Lambda decodes and saves on PUT) | T2 | `backend/lambda_api/tests/test_rule_id_path_encoding.py::test_put_with_a_percent_encoded_rule_id_saves_the_rule` [cat, pin, day]; `::test_put_saves_a_category_count_rule_under_its_decoded_id`; `::test_the_handler_accepts_an_undecoded_rule_id_path_parameter` |
| FR-RULE-03, FR-RULE-06 | E3 (SPA + api Lambda, DELETE) | T2, T3 | `useRules.ruleIdEncoding.test.js` — *remove sends the full rule id…*; `test_rule_id_path_encoding.py::test_delete_with_a_percent_encoded_rule_id_removes_the_rule` |
| FR-RULE-07 | E4 (truncated id still rejected — T9 regression guard) | T2 (no change to the check itself) | `test_rule_id_path_encoding.py::test_a_rule_id_truncated_at_the_hash_is_still_rejected` |
| FR-RULE-03, -04, -06 (existing coverage, corrected to the fixed URL shape) | E1, E3 | T4 | `useRules.test.js` lines 67, 86, 103, 122; `useRules.mutationVisibility.test.js:37` |

`tasks.md` T1-T5 all ticked `[x]`. `issue_list.json` id 1 left untouched at
`in_progress` — status changes past this point (`reviewed`, `done`) are the
reviewer's and the human's.
