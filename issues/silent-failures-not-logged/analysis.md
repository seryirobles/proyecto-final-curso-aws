# Analysis — silent-failures-not-logged (issue 14)

## Defect, one sentence
`validate_and_preview` turns every validator rejection into a generic `INVALID_OUTPUT`, and nothing on the worker path logs which validator rejected it, the value it rejected, or what the model returned. The Bedrock parse error and the API's `422 UNKNOWN_PROMPT_VERSION` are just as uninformative.

## Reproduction
- **Staged test** `test_single_recipe_rejection_logs_validator_value_and_snippet`: a provider output with unit `puñado` (or a bad category, time, quantity, servings, or empty tools) ends `failed` with zero WARNING records.
- **Owner's run** 76fecd1c… showed the same: `invalid_output`, and the log said only "Processed single-recipe generation".
- **Bedrock:** a cut-off JSON body raises `unparseable model output: substring not found`, with no stop reason and no text.

## Root cause
- `core/domain/ai_output.py:145-158`: the `except` drops the exception, and `GenerationFailure` has nowhere to carry it. The callers `single_recipe_generation.py` and `week_generation.py`, in their `isinstance(outcome, GenerationFailure)` branches, record the failure without logging.
- `lambda_ai/adapters/bedrock.py:72, :98`: the error text leaves out `stopReason` and the model text.
- `lambda_api/errors.py:160-166`: only unmapped errors are logged. `UnknownPromptVersion` is a server config fault, yet it is mapped like a client 4xx.
- **Rules involved:** NFR-OBS-01 (centralised logs) and `architecture.md` §6 ("use logging"). No FR-AI-* requires logging the cause; R26 requires only the `failed` record, which works.

## Blast radius
The sweep is in `plan.md` § Sweep. Three sites are fixed here (F1–F3), three were already fixed by issue 13, eleven groups are left unchanged with reasons, and five borderline sites (B1–B5) were put to the owner (decisions in `plan.md`).

## Classification
`not_a_defect` against FR-*: the recorded behaviour matches the spec. The change is diagnosability under NFR-OBS-01, which the owner ordered directly ("Fix the logging. But not only here.").
