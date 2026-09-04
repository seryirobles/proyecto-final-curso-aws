# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 27 `rest_api_persistence_and_services` — **reviewer
  APPROVED**, awaiting owner `done` + commit
- **Started:** 2026-08-31
- **Agent:** _none running_ — feature 16 (`spec_ready`) starts once 27 is closed

## Plan

Previous session (2026-08-30) closed the architecture backlog: P4, P5, P6
all decided and folded. **No `P<n>` item remains pending.** See
`history.md` (2026-08-30 — "P4, P5, P6 all decided").

`./init.sh` reports **feature 16 `rest_api_lambda`** as the next actionable
feature — 26 features, 18 done, 4 pending (16, 17, 20, 26), 4 blocked,
480 tests.

## Log

- 2026-08-31 — Launched `spec_author` for feature 16 `rest_api_lambda`.
  Brief scoped to `docs/rest_api_contract.md` (whole), `architecture.md`
  §1.2/§1.2.5, `data_model.md` §4, feature 16 acceptance.
- 2026-08-31 — `spec_author` returned. `specs/rest_api_lambda/` written
  (42 EARS reqs), feature 16 -> `spec_ready`, `./init.sh` green.
- 2026-08-31 — Owner ruled the 4 gate questions:
  - GQ1 ratified — `covers` = `{NFR-SEC-03, NFR-OBS-01, FR-AUTH-09,
    FR-UX-03, FR-RT-01, FR-MENU-08, FR-AI-08}` (to be split across the two
    features).
  - GQ2 confirmed — f16 emits `ETag`/`Cache-Control`; f26 adds the
    `If-None-Match`/marker-first/`304` short-circuit (R28/R29 -> feature 26).
  - GQ3 approved — `RuleRepository`: `save_rule`/`delete_rule` marker-bumping,
    `DisabledDay` VO, natural-key rule ids.
  - GQ4 -> **SPLIT.** New feature owns the api-side DynamoDB adapters + the
    missing `core` application services + the port changes; feature 16 slims
    to the Lambda shell (handler / routing / errors / serialization /
    authorizer / scheduled entry / wiring / `ETag` emission).
  - Owner directive: the split is done by an **Opus** agent (one-off model
    override for this restructuring only; standing `spec_author = sonnet`
    unchanged).
- 2026-08-31 — Launched `spec_author` (model: opus) to perform the split.
- 2026-08-31 — **Split complete, `./init.sh` green** (27 features, 104/104
  requirement ids covered, 480 tests). GQ1–GQ4 all applied.
  - `specs/rest_api_lambda/` rewritten to shell scope — R1–R39.
  - `specs/rest_api_persistence_and_services/` new — R1–R30.
  - Feature 27 `rest_api_persistence_and_services`: tier 3, `sdd: true`,
    `pending`, `depends_on: [14]`,
    `covers: {NFR-BKP-01, FR-RT-01, FR-RULE-07, FR-SHOP-06, FR-AI-08}`.
  - Feature 16 stays `spec_ready`, `depends_on: [14, 27]`,
    `covers: {NFR-SEC-03, NFR-OBS-01, FR-AUTH-09, FR-UX-03, FR-RT-01,
    FR-MENU-08, FR-AI-08}`.
  - GQ2: old R28/R29 deleted from feature 16, note points at feature 26;
    feature 26's spec/acceptance untouched.

## Residual gate questions — OWNER RULED 2026-08-31

1. **`ArchiveRepository`** → **archive parked for the MVP.** No real
   DynamoDB adapter in feature 27; MVP `wiring.py` injects a no-op
   `ArchiveRepository` that logs the discarded `ArchivedWeek` (NFR-OBS-01).
   Real adapter + `FR-ARCH-02` snapshot item type is post-MVP
   (`data_model.md` §9). Follow-up spec edit in flight.
2–5. **Accepted as written** — `NFR-BKP-01` anchor for feature 27 adapter
   reqs; `FR-RULE-04`/`FR-SHOP-10` cited as preservation but out of
   `covers`; `FR-RULE-07` moved to 27 (16 keeps only the 422 mapping under
   `FR-UX-03`); the two feature-16 citation corrections.

## Implementer run — feature 27 (2026-08-31)

- Feature in progress: 27 `rest_api_persistence_and_services` (`in_progress`).
- Plan: tasks T1..T23 from `specs/rest_api_persistence_and_services/tasks.md`.
- Progress:
  - T1..T11 planner_core port/domain changes + application use cases + fakes + layer scans.
  - T12..T21 `planner_api/adapters/` DynamoDB + SQS, moto-backed contract registration.
  - T22 `./init.sh` green. T23 report at `progress/impl_rest_api_persistence_and_services.md`.
- **Done 2026-08-31.** All T1..T23 ticked. `./init.sh` green — 574 tests
  (+94), ruff/mypy/frontend clean. Report has the R1..R30 -> test table and
  9 spec-gap notes (chief: no `DatosPeticionIA` port existed, folded AP25/26
  into `GenerationQueue`; `UnsatisfiableRuleSet` carries no payload).
  Awaiting `reviewer`.

## Reviewer run 1 — feature 27 — CHANGES_REQUESTED (2026-08-31)

6 findings, **2 mutants survived**. FR->R coverage complete; T1–T23 verified
done not just ticked; C1–C7 all green; boundaries clean; both chief
spec-gap notes accepted with wording/shape fixes. Tree restored after
mutation testing, `./init.sh` re-run green.

**Required (fix round):**
1. **R27** survivor — `test_generation_submission` only asserts `first ==
   second` (a constant passes). Add: submitted id **equals**
   `domain.generation.build_plan(...).idempotency_key`, and two materially
   different requests get different ids.
2. **R20/R9** survivor — no test covers an *existing unchecked* item whose
   quantity must rise on re-sync. Shipped code is correct (persists merged
   qty, returns marker); under the weakened write-condition mutant the
   store stays stale and `marker` is `None` (so feature 16 emits no
   `ETag`). Add a merge-in-place re-sync test asserting `list_items()` and
   `outcome.marker`.
3. **R16 / feature-16 handshake** — `UnsatisfiableRuleSet` uses positional
   `.args`; give it a **typed payload attribute** mirroring
   `PinRulesAffected.pins` (`domain/rules.py:61`), carrying the
   *conflicting existing rules* not just the attempted one, populated at
   `application/rule_editing.py:31`.
4. **R28 wording** — `specs/rest_api_persistence_and_services/requirements.md`
   ~L255: "without calling `GenerationQueue`" -> "without calling
   `GenerationQueue.submit`" (AP26 lookup *is* a `GenerationQueue` call;
   the note-1 fold is accepted).

**Non-blocking follow-ups (folded here per owner directive):**
- `backend/core/tests/support/dynamo_contract.py` imports `boto3`/`moto`/
  `planner_api` from inside the **`core` member's** test tree — not a
  `src` breach (scan covers `core/src` only) but `planner-core`'s tests now
  depend on `planner-api`. Belongs in `backend/tests/contract/`.
- `test_rule_repository_contract.py:12` + `test_generation_queue_contract.py`
  register the real adapter in `try/except ImportError` — silently degrade
  to fake-only if `planner_api` import breaks. Make them match the other
  4 suites (direct factory import).
- `backend/pyproject.toml:17-21` — `moto` comment is 4 lines, over the
  3-line ceiling.
- `adapters/dynamo/_table.py:24-26` pins `PK`/`SK`/`"default"` ids not fixed
  by `data_model.md` — feature 21 IaC must match (already impl note 6).

- 2026-08-31 — `implementer` fix round 1 done. All 4 required changes +
  follow-ups 5/6/7 landed. `./init.sh` green, 576 tests (+2). Both
  previously-surviving mutants now killed (verified by hand). R16 exception
  carries typed `.conflicting`; `dynamo_contract.py` moved to
  `backend/tests/contract/`. See `progress/impl_rest_api_persistence_and_services.md`
  → "Fix round 1". Feature 27 awaits reviewer re-verification.

- 2026-08-31 — **Verification run: APPROVED — 0 findings, 0 mutants
  survived.** R27 + R20/R9 mutants both KILLED by the new tests; a bonus
  mutant confirmed the storage-agnostic scan still has teeth after the
  `dynamo_contract.py` move (narrow one-filename exemption, self-checks
  intact). R16 `.conflicting` traced — carries the *existing* conflicts,
  attempted rule provably excluded. R28 wording correct. `./init.sh` green,
  576 tests. No regressions from the fix round.

## gga gate fix round (2026-09-01)

External review (gga) rejected the commit on 2 verified `docs/conventions.md`
breaches + 1 consistency note. Fixed exactly those:

1. **Missing frozen-instance tests** — added one per new frozen dataclass
   (all 5 confirmed `frozen=True`): `SubmissionOutcome`, `SaveRecipeOutcome`,
   `DeleteRecipeOutcome`, `ResyncOutcome`, `AddCandidateOutcome`, in the
   matching `backend/core/tests/application/test_*_editing.py` /
   `test_generation_submission.py`.
2. **Bare `Any` w/o justification** — `adapters/dynamo/_table.py`
   `resource()/table()/client()` now carry one group comment (boto3 ships no
   type stubs).
3. **Fake/adapter divergence** — `SqsGenerationQueue.submit` was
   unconditionally overwriting `PETICIONIA#…/METADATA` back to
   `estado="pending"`; `FakeGenerationQueue` uses `setdefault`. Fixed the
   **adapter** (create-if-absent via `ConditionExpression=attribute_not_exists(PK)`,
   swallow `ConditionalCheckFailedException`) — `docs/data_model.md` §4.6:
   losing the stored `resultado` means paying for a result that then exists
   nowhere. Contract suite `test_generation_queue_contract.py` gains
   `test_resubmit_never_clobbers_a_stored_result` (parametrized fake+adapter).

`./init.sh` green — 583 tests (+7: 5 frozen + 1 contract test × 2 impls).

**Fix round 2 (gga L38 sweep)** — reviewer found two more bare `-> Any` of
the same class in files touched this round:
- `sqs.py` `_sqs(self)` — added the same boto3-no-stubs one-liner.
- `_table.py` `encode()` — narrowed `-> Any` to `-> object` (returns
  `Decimal | dict | list | object`; sole caller feeds boto3's untyped
  `TypeSerializer.serialize`, so mypy unaffected). No comment needed.
These were the only bare `-> Any` in backend source outside the feature's
files. `./init.sh` green, 583 tests hold.

**Fix round 3 (full `Any` sweep)** — `_table.py` `decode_number(value: Any)`
narrowed to `value: Decimal | int | str` (+ 2-line docstring note: boto3
hands back `Decimal`, tests/raw items pass `int`/`str`); mypy green across
all 9 call sites. Swept `adapters/`, `application/`,
`ports/generation_queue.py`, `domain/rules.py`: the last three have **zero**
`Any`; `adapters/` has only `dict[str, Any]` / `list[dict[str, Any]]`
(allowed) plus the 4 already-commented boto3-handle returns. No bare `Any`
left uncommented. `./init.sh` green, 583 tests.

**Fix round 4 (ExpressionAttributeNames sweep + test rename)** —
`docs/data_model.md` L240-242 (alias every attribute name in condition/update
expressions). Aliased every non-key data attribute in every expression
string across `adapters/dynamo/` + `sqs.py`:
- `accounts.py` — `#nombreUsuario` (rename Update), `#idUsuario` (reservation
  Delete cond), `#passHash`/`#isPassReseteada`/`#validoDesde` (update_credentials),
  `#validoDesde` (revoke_credentials); `_update` gained a `names` param.
- `shopping_list.py` — `#ownerId` (release_lock cond).
`PK`/`SK` inside `attribute_exists()`/`attribute_not_exists()` left bare —
they are key-schema names, not data attributes, and this matches the file's
existing coordinator-cited-compliant precedent (`shopping_list.py:84`
aliases `#ttl` but leaves `attribute_not_exists(SK)` bare). All other
expressions (`_table.py` `#marker`, `shopping_list.py` `#ttl`) already
aliased. `Key()`/`Attr()` builders untouched (SDK aliases them).
Also renamed `test_revoke_credentials_advances_the_marker` ->
`test_revoke_credentials_sets_valido_desde` (asserts only `validoDesde`;
`USUARIOS` has no `MarcaCambio` item — `docs/conventions.md` Tests: names
describe behaviour). Body unchanged. `./init.sh` green, 583 tests (moto
contract suites exercise every aliased path).

**Fix round 5 (mutation-coverage gaps on the round-4 alias paths)** —
reviewer's mutation run showed a broken alias survived the contract suite
on two paths. Added/strengthened, both parametrized over the moto adapter:
- `test_shopping_list_repository_contract.py` — new
  `test_release_lock_by_the_owner_frees_it_for_the_next_holder` (positive
  path: owner-a acquire -> owner-a release -> owner-b acquire, no raise).
  Kills `{"#ownerId": "PK"}`.
- `test_account_repository_contract.py` — `test_rename_releases_the_old_reservation`
  now also asserts `get_by_id("u1").username == "Beatriz"` and
  `get_by_username("beatriz") == renamed`. Kills
  `{"#nombreUsuario": "nombreUsuarioOtro"}`.
`./init.sh` green, **585 tests** (+2).

**Fix round 6 (gga split commits — owner directed the leader to commit)** —
Owner told the leader to do the commits this once (normally the owner's
alone). The gga pre-commit hook (`gga run`, PROVIDER=claude) timed out at the
default 300s on the ~40-file changeset and then surfaced one violation class
per pass. `.gga` `TIMEOUT` raised to 1200s (commit `ff5a850`). Owner then
ruled: **split feature 27 into three commits** so each gga pass is small
enough to review exhaustively, and **skip the internal `reviewer` for this
session** (gga is the adversarial gate; implementer self-verifies its own
mutation probes). Two more real findings from the small-commit passes:
- `id_peticion_ia` was a Spanish Python identifier in `planner_core`
  (`generation_queue.py` port + `generation_submission.py`) — renamed to
  `idempotency_key` (the name `domain/generation.py` already uses); Spanish
  mapping isolated to `adapters/sqs.py`. `docs/conventions.md` §Language
  policy; persisted `PETICIONIA#`/`idPeticionIA` literals unchanged.
- `remove_rule_by_id` raised bare `ValueError` for a known prefix with a
  malformed body (`cat#notacategory`, `pin#x#1`, `pin#9#9`, `day#abc`) —
  now wrapped to raise the named `InvalidRuleId` (`architecture.md` §4
  invariant 12; fed from `DELETE /v1/rules/{ruleId}`). New parametrized test.

`./init.sh` green, **589 tests** (+4).

## Feature 27 — COMMITTED (2026-09-01)

Five commits on `dev` (gga passed on all three code commits):

| SHA | Commit |
|---|---|
| `ff5a850` | `chore: raise gga review timeout for large changesets` |
| `1eb3e74` | `feat: split rest api feature into lambda shell and persistence substrate` |
| `57bd1dc` | `feat: rule per-rule port and rest api application services` (20 files) |
| `c4c5e3f` | `feat: dynamodb and sqs adapters for rest api persistence` (13 files) |
| `e3a1b6e` | `feat: contract-test the rest api persistence adapters` (11 files) |

`progress/current.md` deliberately left uncommitted (wiped at session close).

### gga non-blocking observations — NOT actioned (follow-ups)

From the 3b/3c passes, for a future touch of these files:
- `adapters/dynamo/accounts.py` `rename` — the `_table.get_item` pre-check
  before the `attribute_not_exists(SK)` Put is a redundant read window
  §5.1 warns against (`create` correctly omits it).
- `ttl` is written as a float string in `shopping_list.acquire_lock`
  (`str(expires_at.timestamp())`) but `int` in `sqs.submit`; DynamoDB TTL
  wants integer epoch seconds. Harmless (§5.3 doesn't trust TTL for the
  lock) but the two writers should agree.
- `adapters/dynamo/rules.py` `delete_rule(self, rule_id: str)` param shadows
  the imported `rule_id` function.
- `shopping_list.py` `_item_dict` has an unreachable `else` branch
  (`item.unit` is typed `Unit`).
- Three contract suites still carry feature-18 R-numbers in a section
  comment (`# --- change marker (FR-RT-01): R2, R4, ... ---`); only
  `test_rule_repository_contract.py` was retargeted.

## Next step — OWNER

Feature 27 is committed and every gga gate passed, but it stays
`in_progress` in `feature_list.json` until **you** mark it `done` (the
leader never does). `feature_list.json` was committed in `1eb3e74` with
feature 27 already `in_progress` and feature 16 `spec_ready` — the `done`
flip is a separate edit for you.

On your "done": feature 16 `rest_api_lambda` (`spec_ready`, already
owner-approved) flips to `in_progress` — `implementer` then `reviewer`, the
Lambda shell that calls this substrate.
