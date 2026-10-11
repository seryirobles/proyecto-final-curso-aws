# ai_inference_config - Requirements

Depends on: features 17 (`ai_lambda`) and 28 (single-recipe generation), both done.

## Source

`feature_list.json` feature 33 has `covers: []`: no frozen `FR-*` is claimed. The
source is the owner decision of 2026-10-07, quoted verbatim:

> Model is Amazon Nova 2 Lite via EU geo inference (`AI_MODEL_ID=eu.amazon.nova-2-lite-v1:0`,
> already set locally). The ai worker reads Bedrock Converse settings from
> ENVIRONMENT VARIABLES (set in AWS on the Lambda; `.vscode/launch.json` locally).
> Reasoning on/off (default off); reasoning effort low|medium|high (default low);
> maxTokens (default 4096); temperature (0-1, unset); topP (0-1, unset); service
> tier standard|priority|flex (default standard). Fixed in code, NOT configurable:
> top-K, stop sequences, prompt caching, guardrails, client timeouts, forced
> tool-use JSON. With effort high, temperature/topP/topK must not be sent.

`Implements:` cites the existing `FR-*`/`NFR-*` the behaviour serves: the two
generation paths (FR-AI-01, FR-AI-03), cost (NFR-AI-01, reasoning tokens bill as
output), secrets (NFR-SEC-02), logs (NFR-OBS-01). No new product requirement.

Variables (all read by `planner_ai/adapters/bedrock.py`): `AI_MODEL_ID` (existing),
`AI_REASONING_ENABLED`, `AI_REASONING_EFFORT`, `AI_MAX_TOKENS`, `AI_TEMPERATURE`,
`AI_TOP_P`, `AI_SERVICE_TIER`.

## R1
Implements: FR-AI-01, FR-AI-03

The Bedrock provider SHALL read every inference variable from the process environment on each `generate` call.

## R2
Implements: FR-AI-01, FR-AI-03

WHEN none of `AI_REASONING_ENABLED`, `AI_REASONING_EFFORT`, `AI_MAX_TOKENS`, `AI_TEMPERATURE`, `AI_TOP_P`, `AI_SERVICE_TIER` is set, the Bedrock provider SHALL call `converse` with exactly `modelId`, `messages` and `inferenceConfig={"maxTokens": 4096}`.

## R3
Implements: FR-AI-01, FR-AI-03

WHERE `AI_MODEL_ID` is set, the Bedrock provider SHALL pass its value as `modelId`; WHEN it is unset, the provider SHALL use `eu.amazon.nova-2-lite-v1:0` (owner decision 2026-10-11, replaces the `global.openai.gpt-5.6-terra` code default).

## R4
Implements: FR-AI-01, FR-AI-03, NFR-AI-01

WHERE `AI_MAX_TOKENS` is an integer from 1 to 65000, the Bedrock provider SHALL pass it as `inferenceConfig.maxTokens`.

## R5
Implements: FR-AI-01, FR-AI-03

WHERE `AI_TEMPERATURE` is a number from 0 to 1, the Bedrock provider SHALL pass it as `inferenceConfig.temperature`.

## R6
Implements: FR-AI-01, FR-AI-03

WHERE `AI_TOP_P` is a number from 0 to 1, the Bedrock provider SHALL pass it as `inferenceConfig.topP`.

## R7
Implements: FR-AI-01, FR-AI-03, NFR-AI-01

WHERE `AI_SERVICE_TIER` is `priority` or `flex`, the Bedrock provider SHALL pass `serviceTier={"type": <value>}` to `converse`.

## R8
Implements: FR-AI-01, FR-AI-03

WHERE `AI_SERVICE_TIER` is `standard`, the Bedrock provider SHALL omit `serviceTier` from the `converse` call.

## R9
Implements: FR-AI-01, FR-AI-03, NFR-AI-01

WHERE `AI_REASONING_ENABLED` is `true`, the Bedrock provider SHALL pass `additionalModelRequestFields={"reasoningConfig": {"type": "enabled", "maxReasoningEffort": <effort>}}`.

## R10
Implements: FR-AI-01, FR-AI-03

WHERE `AI_REASONING_ENABLED` is `true` and `AI_REASONING_EFFORT` is unset, the Bedrock provider SHALL use the effort `low`.

## R11
Implements: FR-AI-01, FR-AI-03

WHILE `AI_REASONING_ENABLED` is `false` or unset, the Bedrock provider SHALL omit `additionalModelRequestFields` from the `converse` call.

## R12
Implements: FR-AI-01, FR-AI-03

IF `AI_REASONING_ENABLED` is `true`, the effort is `high` and `AI_TEMPERATURE` or `AI_TOP_P` is set, THEN the Bedrock provider SHALL raise `AiProviderError` before calling Bedrock (owner decision 2026-10-11: fail fast, never drop silently).

## R13
Implements: FR-AI-01, FR-AI-03, NFR-OBS-01

WHEN the Bedrock provider rejects settings under R12, it SHALL log one error naming each conflicting variable.

## R14
Implements: FR-AI-01, FR-AI-03

The Bedrock provider SHALL NOT send `topK`, `stopSequences`, a guardrail configuration or a cache point in any `converse` call.

## R15
Implements: FR-AI-01, FR-AI-03

IF an inference variable is set to a value outside its domain, THEN the Bedrock provider SHALL raise `AiProviderError` before calling Bedrock.

## R16
Implements: FR-AI-01, FR-AI-03, NFR-OBS-01

IF an inference variable is set to a value outside its domain, THEN the Bedrock provider SHALL log one error naming the variable and its accepted domain.

## R17
Implements: NFR-SEC-02

The Bedrock provider SHALL NOT include any AWS credential or Bedrock API key value in an inference-configuration log record or exception message.

## R18
Implements: FR-AI-01, FR-AI-03

WHEN an inference variable is set to an empty or whitespace-only string, the Bedrock provider SHALL treat it as unset.

## R19
Implements: FR-AI-01, FR-AI-03

WHEN a response contains a `reasoningContent` block, the Bedrock provider SHALL return the recipe parsed from the first `text` block.

## R20
Implements: FR-AI-01, FR-AI-03

The worker SHALL apply the same inference settings to single-recipe generation jobs and to whole-week generation jobs.

## R21
Implements: FR-AI-01, FR-AI-03

The `docs/local_development.md` worker section SHALL list each of the six new variables with its accepted values and default, its `AI_MODEL_ID` example SHALL be `eu.amazon.nova-2-lite-v1:0`, and the GPT-5.6 Terra Marketplace-activation paragraph SHALL be rewritten for Nova.

## R22
Implements: FR-AI-01, FR-AI-03

The `docs/architecture.md` AI-provider section SHALL contain a table listing each of the seven AI worker variables with accepted values and default (added by the leader on the owner's direct command, 2026-10-11; the implementer does not edit that file).

## Acceptance coverage

| Acceptance criterion | R |
|---|---|
| Each setting read from env with documented default; unset = current behaviour | R1-R11, R18, R21, R22 |
| Invalid values and effort-high + temperature/topP rejected, error logged, no credentials | R12, R13, R15, R16, R17 |
| local_development.md and architecture env table list every variable | R21, R22 |

## R23
Implements: FR-AI-01, FR-AI-03

WHEN `AI_REASONING_ENABLED` is `true` and the effort is `high`, the Bedrock provider SHALL omit `inferenceConfig.maxTokens` from the `converse` call, whether or not `AI_MAX_TOKENS` is set, because Bedrock rejects `maxTokens` with `maxReasoningEffort` `high` (probe 2026-10-11; owner decision 2026-10-11: omit silently rather than fail, unlike R12).
