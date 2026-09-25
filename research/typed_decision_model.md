# Typed decision model (TypeSafe Jev) in MAESTRO

Added 2026-09-25. This describes what was integrated, what the integration is allowed to do,
and the provider contract verified against a live Jev response.

## 1. What Jev is

TypeSafe AI released **Jev** on 15 September 2026 as a "System One" model. It answers typed
questions about a supplied state and returns only structured values: it does not generate
prose. Three question kinds exist and nothing else:

| Kind | Answer | Reported alongside |
|---|---|---|
| `noul` | yes / no | probability of yes |
| `choice` | one option from a declared list (up to 255) | a probability per option, plus a separate confidence |
| `score` | a position on an ordered scale (2 to 10 points) | confidence |

It is described as trained with reinforcement learning against outcomes rather than human
preference, so its probabilities are intended to be calibrated in aggregate. Published pricing
is $0.042 per 1M input tokens with no output charge.

Sources (the TypeSafe API reference is primary; see section 5):
[LiteLLM pass-through](https://docs.litellm.ai/docs/pass_through/typesafe) ·
[TypeSafe API reference](https://docs.typesafe.ai/api) ·
[TypeSafe introduction](https://typesafe.ai/blog/introducing-system-one-models-and-jev) ·
[OpenRouter guide](https://openrouter.ai/docs/guides/community/jev) ·
[MarkTechPost release note](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/) ·
[LangChain write-up](https://www.langchain.com/blog/building-a-harness-with-jev)

## 2. Why it fits MAESTRO

MAESTRO's architecture is already "a model proposes, a deterministic layer validates". Its
recurring problem with a text model is that prose can name an action that does not exist,
assert a mechanism, or describe a result that was never measured — which is why the planner
has a contract parser, a critic loop and a repair re-check.

A model that *cannot emit text* removes that failure mode structurally rather than by
validation. A `choice` question's options are exactly the registered action identifiers, so an
answer outside the menu is impossible to express. And because the answers are calibrated
probabilities, they can be scored against later measured outcomes and revoked — the same
accountability the repository already applies to virtual-cell predictions.

## 3. What was built

| File | Role |
|---|---|
| `src/agent/typesafe.py` | Settings from `.env`, the three question kinds with their limits, strict fail-closed answer parsing, transport retries, redacted secrets |
| `src/maestro/judgment.py` | `TypedJudgment` (the planning-only boundary) and `JudgmentLedger` (Brier scoring, down-weighting, revocation) |
| `src/agent/decision_critic.py` | Builds questions from MAESTRO objects; turns confident answers into advisory findings and judgments |
| `src/agent/planner.py` | `extra_critique` hook on `propose`; `advisory_findings` section in the repair prompt |
| `src/agent/orchestrator.py` | One review per round; findings reach the repair planner; judgments are logged and attached to the turn |

### The boundary, stated in code

`TypedJudgment.satisfies_premise`, `.eliminates_hypothesis` and `.is_measurement` are
properties that return `False` and take no arguments. There is no call site that could make
one of them true. `JudgmentScope` has four members — plan critique, action ranking,
applicability advisory, hypothesis advisory — and deliberately **no** mechanism-contrast
member, because removing an explanation stays the job of a qualified real result read through
an interpretation rule.

A judgment's `evidence_kind` is `model_prediction`, the same class as a virtual-cell
prediction. It is never written to the evidence ledger.

### Questions asked each round

Built from the registered contrast, the action menu, the deterministic check, the menu's
dependency topology and the virtual-cell briefing:

- `decision_separation` (noul) — do the two explanations lead to two different decisions?
- `plan_discriminates` (noul) — would the planned action's declared outcomes separate them?
- `boundary_stated` (noul) — does the plan state a limit on what its result establishes?
- `evidence_sufficiency` (score 1–5) — is current evidence enough to choose?
- `best_separating_action` (choice over registered action identifiers, plus "none of these")
- `prediction_reliance` (noul) — should this round's predictions break ties? *(only when a
  virtual-cell briefing exists)*
- `candidate_regulator` (choice) — which supplied network regulator fits the response summary?
  *(only when candidates are supplied; answered as a hypothesis, never a causal finding)*

### Virtual cell and gene regulatory networks

The virtual-cell link is deliberately advisory in one direction only: the round's per-action
predictions, with their validation status, distribution membership and reliability weight, are
shown to the decision model, which may say they are not a sound basis for breaking ties. It
cannot make a prediction applicable, and it cannot override the `SupportRegistry`.

The GRN link takes a caller-supplied candidate regulator list and ranks it. Every network edge
is labelled a hypothesis in the state text and in the finding itself. No edge becomes evidence,
and no ranking licenses a mechanism claim.

### Accountability

`JudgmentLedger` scores `noul` and `choice` answers against later measured outcomes with a
Brier score. A scope stays provisional until it has enough graded records, is down-weighted as
calibration degrades, and is revoked outright after repeated confident misses or once its
Brier score is no better than always answering 0.5. A revoked scope still produces judgments
for the record and produces no findings.

`score` answers are recorded but never graded: an ordered scale is not a probability forecast,
and grading it as one would invent a calibration claim the answer never made.

## 4. Configuration

In `.env` (git-ignored; see `.env.example`):

```
TYPESAFE_API_KEY=...
TYPESAFE_ENDPOINT=https://api.typesafe.ai
TYPESAFE_MODEL=jev-1.13
TYPESAFE_TIMEOUT_SECONDS=30
```

The process environment wins over `.env`. If `TYPESAFE_API_KEY` or `TYPESAFE_MODEL` is absent
the critic is simply not built and the loop behaves exactly as before — a partly configured
block counts as absent, so a half-enabled critic cannot fail on the first call.
`--decision-critic off` disables it explicitly. The key is never written to a log, an
exception or a `repr`, and never appears in the request body.

## 5. Live HTTP contract

The [TypeSafe HTTP API reference](https://docs.typesafe.ai/api) specifies
`POST https://api.typesafe.ai/v1/systemone` with a bearer key. Choice questions require
`criteria` as an option-to-description map (null descriptions are allowed). Score questions
require `criteria` as an ordered list of level descriptions. Noul answers use the `noul`
field; Choice answers use `choice`, `probabilities` and `confidence`; Score answers use a
zero-indexed, potentially fractional `score`, `probabilities` and `confidence`. MAESTRO
converts that score to its existing rounded 1–5 advisory scale.

The first local probe reached the endpoint but received HTTP 422 because the client sent
`options` and `scale` instead of the two required `criteria` fields. After correcting the
request and parser, a live three-question evaluation returned three usable answers, no
refusals, and token usage. The critic loop then recorded five `model_prediction` judgments;
its deterministic check and selected action matched the critic-off trace. The
[measured run](local_verification/2026-09-25-maestro.md) records the result;
the raw artifacts remain git-ignored under `outputs/` on the verifying machine.

Parsing still fails closed on unrecognised fields or out-of-range values, naming the keys
the provider returned. A refusal never becomes a finding. Provider outages still leave the
round runnable without a critic judgment.

## 6. Limits

The integration adds a calibrated second opinion about a plan. It does not add evidence, does
not measure anything, and does not make a biological claim. A high-confidence judgment that a
plan is sound is not a statement that the underlying biology is understood; it is a statement
about this model's own accuracy on questions of that shape, and it is only worth what the
judgment ledger's later scoring says it is worth.
