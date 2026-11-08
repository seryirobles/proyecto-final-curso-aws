# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Issue in progress:** 24 `deployed-lambdas-drop-info-logs` — implemented,
  reviewed, **APPROVED**, awaiting deployment, the dev check and the owner's
  `done`
- **Feature in progress:** 37 `bootstrap_admin_cli` — awaiting the owner's `done`
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

## Next step

Owner: deploy the code, **then** run `terraform apply`, never the reverse. Then
the dev checks in `issues/deployed-lambdas-drop-info-logs/plan.md`.
