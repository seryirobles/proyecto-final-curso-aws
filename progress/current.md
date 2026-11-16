# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Issue in progress:** none. 25 `ai-failed-messages-never-retried` is `pending`,
  awaiting the owner's go/no-go
- **Feature in progress:** none. The owner marked 37 `bootstrap_admin_cli` and
  22 `cicd_pipeline` `done` in `1b6d4dd`
- **Started:** 2026-11-02
- **Agent:** leader

## Log

- 2026-11-07: Issue 23 `ai-kill-switch-unreadable-under-shared-role` implemented
  and APPROVED; the owner marked it `done`. Owner ruling: the Lambda env var is a
  temporary workaround and SSM stays the design. Not yet deployed. The docs
  explanation is the owner's.
- 2026-11-07: Issue 24 implemented and APPROVED. Owner rulings: JSON logs, `DEBUG`
  on dev and `INFO` elsewhere, SDK loggers at WARNING in code, one INFO line on
  the authorizer's Allow path, no `logger.debug` lines. Recorded in
  `docs/architecture.md` §1.5. Terraform added by the leader at the owner's
  command.
- 2026-11-07: The owner accepted `./init.sh` exit 1 from known section 4 failures
  for the approvals of issues 23 and 24.
- 2026-11-07: Issues 25, 26 and 27 logged as `reported`. **On hold: the owner said
  not to triage or work on them yet.**
- 2026-11-07: The owner committed issues 20 to 24 as `3b82d9a` and marked 23 and 24
  `done`. The owner deleted `issues/`, so the docs for 20 to 24 are gone.
- 2026-11-08: The owner lifted the hold on 25 only ("correct 25"); 26 and 27 stay on
  hold. Triaged as `defect`; docs and staged tests in
  `issues/ai-failed-messages-never-retried/`. Leader re-ran the staged tests on a
  scratch copy of `HEAD`: 37 failed, 40 passed, matching the triager. `./init.sh`
  will fail on the missing docs for 20 to 24 (15 files); the owner has not accepted
  that yet, and the 25 plan's task T8 expects green.
- 2026-11-08: The owner challenged the plan's retries at 90 minutes and 7.5 hours as
  useless to a user. Leader proposed: only the first delivery may call Bedrock, later
  ones only close the run, and the worker stops before its timeout. Not yet accepted;
  if accepted, `plan.md`, `tasks.md` and the staged tests need a new triage.

- 2026-11-08: Owner rulings on 25: specific fix (slots after a failure become
  `error`); poison logged and acknowledged; no alarm and no Terraform; spinner
  deadline is its own issue. Logged issues 28 (general slot isolation) and 29 (poll
  deadline) as `reported`, on hold. Plan sent back to the triager: only the first
  delivery calls Bedrock, settle on the spot, deadline before the Lambda timeout,
  Bedrock call timeout.

- 2026-11-09: Triager redid 25 under the new policy (E1 to E17, T1 to T11, four
  staged test files). Leader re-ran the staged tests on a scratch copy of `HEAD`: 49
  failed, 42 passed, matching the triager. The owner removed issues 20 to 24 from
  `issue_list.json` to clear the `init.sh` docs failures.

- 2026-11-09: Owner said no-go on 25 for now ("let's leave it for now"). It stays
  `pending`; not `wontfix`. Nothing was implemented. Issues 26 to 29 stay on hold.

- 2026-11-09: Doc-drift sweep against the code, Terraform and CI. Fixed `AGENTS.md`,
  `CHECKPOINTS.md`, `docs/{architecture,conventions,verification,local_development,
  rest_api_contract,frontend_prototype}.md` and the `implementer`, `spec_author` and
  `leader` agent files. Owner-level contradictions were listed, not resolved.

## Next step

None queued. When the owner picks 25 back up, the triage in
`issues/ai-failed-messages-never-retried/` is current (E1 to E17, T1 to T11).

Owner, for issues 23 and 24: deploy the code, **then** run `terraform apply`, never
the reverse (neither confirmed yet). Then check on dev:

- `aws lambda get-function-configuration --profile commitacademy-srobles --region eu-west-1 --function-name lab-final-srobles-dev-ai --query Environment.Variables.AI_GENERATION_SWITCH`
  prints `"true"`, then try a generation.
- After a login, `/aws/lambda/lab-final-srobles-dev-api` shows the JSON record
  `Handled request POST /v1/session -> 200`.
- After a page load, `/aws/lambda/lab-final-srobles-dev-authorizer` shows
  `Allowing authorizer request`.
- Searching the `api`, `authorizer` and `ai` log groups for `"Response body"` finds
  nothing. If it finds anything, treat the session key and Bedrock token as exposed.
