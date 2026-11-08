# Implementation report: issue 23 ai-kill-switch-unreadable-under-shared-role

## Traceability (FR -> E -> T -> test)

| FR | E | T | Code | Test |
|---|---|---|---|---|
| FR-AI-01/02/03 | E1 | T2 | `adapters/env_switch.py` | `test_env_switch_wiring.py`, `test_env_switch_off_run.py` |
| NFR-AI-01 | E2 | T2 | same | `test_env_switch_wiring.py`, `test_env_switch_gate_contract.py` |
| FR-AI-01/03 | E3 | T2/T3 | no SSM read while set | `test_env_switch_wiring.py` |
| NFR-AI-01 | E4 | T3 | `wiring.py::_build_gate` | `test_env_switch_wiring.py` |
| NFR-AI-01 | E5 | T2 | read on every call | `test_env_switch_wiring.py` |
| NFR-AI-01 | E6 | T2 | one INFO per transition | `test_env_switch_logging.py`, `test_env_switch_log_value.py` (new) |
| NFR-AI-01, FR-AI-12 | E7 | T3 | wiring | `test_env_switch_off_run.py` |
| NFR-AI-01 | E8 | T3 | `_build_gate` ignores `AI_GENERATION_ENABLED` | `test_env_switch_wiring.py` |
| NFR-AI-01 | E9 | T2 | no user argument | `test_env_switch_gate_contract.py` |
| FR-AI-01/03 | E10 | T6 | `terraform/` (leader, at the owner's command) | `test_terraform_ai_switch_env.py`, `test_terraform_ai_switch_default.py` (new) |

## Tests

- Six staged tests were **copied** to their destinations; the originals were kept
  in `issues/.../tests/`, not moved, for the reviewer's byte diff.
- Added after review: `backend/lambda_ai/tests/test_env_switch_log_value.py`
  (the INFO line never carries the value) and
  `backend/tests/test_terraform_ai_switch_default.py` (`default = true`).
- Comment edits (T4): `wiring.py`, `adapters/__init__.py`, `local_worker.py`,
  core `ports/generation_gate.py`, docstring of `test_local_worker_gate.py`.

## T6 stays open

Its remaining work is the owner's: `terraform apply`, the
`get-function-configuration` check, and the docs explanation. The leader made
the Terraform file edits at the owner's command; the implementer touched no
`terraform/` file.

## Not anticipated

`wiring.py` needed `import os`; the port file lives in `backend/core`.
