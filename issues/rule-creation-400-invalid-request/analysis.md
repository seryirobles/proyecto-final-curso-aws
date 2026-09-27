# Issue 1 — rule-creation-400-invalid-request: analysis

## Defect, one sentence

The SPA puts the raw rule id (`cat#meat`, `pin#3#2`, `day#5`) into the request URL, so the browser treats everything from `#` on as a fragment and sends `PUT /v1/rules/cat`. The api Lambda then finds that path id does not match the body's id and answers 400 `MALFORMED_REQUEST` ("La solicitud no es válida."). The API has no working encoded form either: it never percent-decodes the path parameter, so `cat%23meat` is rejected the same way.

## Not a feature 29 regression

The leader suspected feature 29 (`rules_dropdown_constraints_wiring`). The evidence rules it out:

- `computeRuleId` and both `apiFetch(`${RULES_URL}/${computeRuleId(rule)}`…)` calls are byte-identical in `HEAD` and in the working tree. Feature 29's diff touches no line that builds the URL or the body. `git blame` dates them to `80e34a8 feat: frontend` (2026-09-14, feature 20).
- The body sent after feature 29 (`{type:'categoryCount', category:'meat', count:3}`) is the same shape `test_rules_routes.py` already accepts with 200.
- Feature 29 only made the path reachable: it is the first feature the owner tested by creating a rule in a real browser. Rule create and delete have never worked in a browser since feature 20 shipped.

Why no test caught it: every hook test mocks `apiFetch` and asserts the raw string. `useRules.test.js` asserts `'/v1/rules/cat#meat'` (lines 67, 86, 103 and 122), so that suite pins the bug. Every backend route test builds the proxy event with an already-decoded `path_params={"ruleId": "cat#meat"}`, so no test ever sent an id through a real URL.

## Reproduction

1. Browser URL parsing (Node's WHATWG `URL`, which is what `fetch` uses): `new URL('/v1/rules/cat#meat', base)` gives pathname `/v1/rules/cat` and hash `#meat`. `fetch` never sends the hash. This matches the owner's log line `"PUT /v1/rules/cat HTTP/1.1" 400`. `cat` is the whole path segment the server received, not a truncated log.
2. Through `local_server.handle_request`, with fakes and an authenticated cookie, and the body `{"type":"categoryCount","category":"meat","count":2}`:

| Request | Observed | Expected |
|---|---|---|
| `PUT /v1/rules/cat` (what the browser sends today) | 400 `MALFORMED_REQUEST` "La solicitud no es válida." | 400 (the id really is truncated) |
| `PUT /v1/rules/cat%23meat` (the correctly encoded URL) | 400 `MALFORMED_REQUEST` | 200, rule saved |
| `DELETE /v1/rules/day` | 400 `INVALID_RULE_ID` | 400 |
| `DELETE /v1/rules/day%235` | 400 `INVALID_RULE_ID` | 204 |

3. The staged tests reproduce both halves (see `plan.md` § Test plan).

## Root cause

There are two defects on one chain. Fixing either one alone still leaves 400:

1. **Client, the cause of the symptom:** `frontend/src/hooks/useRules.js:16-19` (`computeRuleId`) returns an id that contains `#`, and lines 109 (PUT) and 132 (DELETE) paste it unencoded into the URL path. RFC 3986 reserves `#` as the fragment delimiter.
2. **Server, the reason the correct encoding also fails:** the `{ruleId}` path parameter is never percent-decoded:
   - `backend/lambda_api/src/planner_api/local_server.py:50` copies the raw segment.
   - `backend/lambda_api/src/planner_api/handler.py:77` passes `pathParameters` through as-is.
   - So `routing.py:598` compares `rule_id(rule)` (`cat#meat`) with `cat%23meat`, and `routing.py:611` hands `day%235` to `delete_rule`, which raises `InvalidRuleId` (`planner_core/domain/rules.py:257-258`).

**Where the symptom surfaces:** `backend/lambda_api/src/planner_api/routing.py:598-599` raises `MalformedRequest`. `errors.py:147` maps it to 400 with `messages.MALFORMED_REQUEST` (`planner_core/messages.py:40`, "La solicitud no es válida."). That check (T9, "the path segment is authoritative") is correct and must stay.

**Requirements violated:** FR-RULE-03 (rules editable via dropdowns), FR-RULE-04 (all three rule types), and FR-RULE-06 (any user may edit the shared rules). No user can add or remove any rule.

**Hypothesis, not verified:** I do not know whether the deployed API Gateway (REST proxy, v1 event format) URL-decodes `pathParameters`. The local server does not decode them. The plan decodes in the api Lambda, which is correct whichever way API Gateway behaves: rule ids never contain `%`, so decoding an already-decoded id changes nothing.

## Blast radius

- **The report is confirmed:** all three rule types fail to create for the same reason. `cat#…` arrives as `cat`, `pin#d#s` as `pin`, `day#d` as `day`. Each gives 400 `MALFORMED_REQUEST`.
- **Open scope question: rule delete is broken by the same cause but was not reported.** `remove` (`useRules.js:132`) builds its URL the same way, so `DELETE /v1/rules/cat` returns 400 `INVALID_RULE_ID` ("El identificador de regla indicado no es válido.") for every rule type. The owner could not see this because no rule could be created to delete. Delete can only be reached today with rules seeded outside the SPA. The human needs to choose:
  - **General fix (recommended by evidence, not assumed):** encode in `computeRuleId`'s callers and decode on the server for both PUT and DELETE. Both calls share one helper, so this is the natural single change.
  - **Specific fix:** PUT only. Delete becomes a separate issue. The `remove` test in `useRules.ruleIdEncoding.test.js` and `test_delete_with_a_percent_encoded_rule_id_removes_the_rule` would then be dropped from this issue and restaged under the new one.
- **Other routes are unaffected:** every other path parameter the SPA sends (`userId`, `recipeId`, `generationId` and shopping `itemId`) is a `uuid4().hex`, and week keys are ISO dates. None contains a reserved character.
- **Existing tests that assert the buggy URL** have to change with the fix. This is the named correction in `plan.md`, not a weakening:
  - `frontend/tests/hooks/useRules.test.js`: lines 67, 86, 103 and 122.
  - `frontend/tests/hooks/useRules.mutationVisibility.test.js:37`: its fake server compares the raw URL tail to `cat#…`.

## Classification

`defect`. The frozen requirements FR-RULE-03, -04 and -06 require rules to be editable, and no `G-xx` makes this deliberate. The encoding rule comes from RFC 3986 and the Fetch spec, not from a new requirement. Severity stays **high**: the whole Rules feature is unusable from the UI.
