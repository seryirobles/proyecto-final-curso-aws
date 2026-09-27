# Issue 1 — rule-creation-400-invalid-request: tasks

- [x] T1 — Move the two staged tests to their destinations verbatim (`plan.md` § Test plan); confirm the six backend tests and four frontend tests listed there are red. Covers: E1, E2, E3, E4.
- [x] T2 — Percent-decode path parameters in `handler.py` before routing. Covers: E2, E3, E4.
- [x] T3 — Percent-encode the rule id in both `useRules.js` URL builds (PUT and DELETE). Covers: E1, E3.
- [x] T4 — Correct the stale literals in `useRules.test.js` (67, 86, 103, 122) and decode in `useRules.mutationVisibility.test.js:37`, exactly as `plan.md` § Existing tests states. Covers: E1, E3.
- [x] T5 — `./init.sh` green; staged tests byte-identical to `issues/rule-creation-400-invalid-request/tests/`. Covers: E1–E4.
