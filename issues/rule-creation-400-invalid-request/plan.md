# Issue 1 — rule-creation-400-invalid-request: plan

## Expected behaviour

- **E1** — When a user saves a category-count, pin or disabled-day rule, the SPA SHALL send `PUT /v1/rules/{ruleId}` with the complete rule id (`cat#<category>`, `pin#<day>#<slot>`, `day#<day>`) percent-encoded in the path, carrying no URL fragment. Implements: FR-RULE-03, FR-RULE-04, FR-RULE-06.
- **E2** — When the api Lambda receives `PUT /v1/rules/{ruleId}` whose path segment is the percent-encoded id of the body's rule, it SHALL save the rule and answer 200. Implements: FR-RULE-03, FR-RULE-04, FR-RULE-06.
- **E3** — When a user confirms removal of a rule, the SPA SHALL send `DELETE /v1/rules/{ruleId}` with the complete percent-encoded id, and the api Lambda SHALL delete that rule and answer 204. Implements: FR-RULE-03, FR-RULE-06. *(Blast radius — open scope question, `analysis.md`.)*
- **E4** — When the `{ruleId}` path segment decodes to an id different from the body's rule id (e.g. the truncated `cat`), the api Lambda SHALL answer 400 `MALFORMED_REQUEST` and store nothing. Implements: FR-RULE-07 (regression guard of the existing T9 check).

## Fix design

1. **`backend/lambda_api/src/planner_api/handler.py:77`** (api adapter, `docs/architecture.md` §3 — wire translation, no domain change): percent-decode each `pathParameters` value (`urllib.parse.unquote`, stdlib) before routing. One site covers PUT, DELETE and the local server. Idempotent for every existing id (uuid hex, ISO dates, rule ids — none contains `%`), so it is correct whether or not API Gateway already decodes.
2. **`frontend/src/hooks/useRules.js:109` and `:132`**: wrap `computeRuleId(rule)` in `encodeURIComponent(...)` in both URL builds (or encode inside a small URL helper). `computeRuleId` itself stays the domain id.

Rejected:
- *Decode only in `local_server.py`*: mirrors API Gateway only if API Gateway decodes `pathParameters`, which is unverified (`analysis.md`); the deployed path could stay broken.
- *Change the rule-id separator away from `#`*: the natural-key format is fixed by `data_model.md` §2 / feature 27 and stored in DynamoDB; a persistence change for a transport bug.

## Test plan

Staged files -> destinations:

| Staged | Destination |
|---|---|
| `issues/rule-creation-400-invalid-request/tests/backend/lambda_api/tests/test_rule_id_path_encoding.py` | `backend/lambda_api/tests/test_rule_id_path_encoding.py` |
| `issues/rule-creation-400-invalid-request/tests/frontend/tests/hooks/useRules.ruleIdEncoding.test.js` | `frontend/tests/hooks/useRules.ruleIdEncoding.test.js` |

| E | Test | Red at triage (2026-09-27) |
|---|---|---|
| E1 | `useRules.ruleIdEncoding.test.js` — *saveCategoryCount…*, *savePin…*, *saveDisabledDay…* (reproduction) | red: received `{hash:'#meat', ruleId:'cat'}` / `'#3#2','pin'` / `'#5','day'` |
| E2 | `test_put_with_a_percent_encoded_rule_id_saves_the_rule` [cat, pin, day] (reproduction, server half) | red: 400 `MALFORMED_REQUEST` |
| E2 | `test_put_saves_a_category_count_rule_under_its_decoded_id` | red: nothing stored |
| E2 | `test_the_handler_accepts_an_undecoded_rule_id_path_parameter` | red: 400 |
| E3 | `useRules.ruleIdEncoding.test.js` — *remove sends the full rule id…* | red: `{hash:'#fish', ruleId:'cat'}` |
| E3 | `test_delete_with_a_percent_encoded_rule_id_removes_the_rule` | red: 400 `INVALID_RULE_ID` |
| E4 | `test_a_rule_id_truncated_at_the_hash_is_still_rejected` | green (guard; must stay green) |

ruff check/format and eslint/prettier pass on both staged files.

### Existing tests the fix must correct (named here, not a weakening)

They assert the defect itself and turn red once E1 is met:
- `frontend/tests/hooks/useRules.test.js` lines 67, 86, 103, 122: `'/v1/rules/cat#meat'`, `'/v1/rules/pin#3#2'`, `'/v1/rules/day#5'`, `'/v1/rules/day#7'` -> `'/v1/rules/cat%23meat'`, `'/v1/rules/pin%233%232'`, `'/v1/rules/day%235'`, `'/v1/rules/day%237'`.
- `frontend/tests/hooks/useRules.mutationVisibility.test.js:37`: `url.replace('/v1/rules/', '')` -> `decodeURIComponent(url.replace('/v1/rules/', ''))` (the fake server must decode, as the real one will).

If the human picks the **specific** fix (PUT only), drop the E3 tests from this issue and restage them under a new issue.
