# Read-only defect review: dual-core runtime and provider interfaces

Review date: 2026-10-01 (Asia/Shanghai). Baseline: `8271e8a119138d0e9c60fd9938f0abe11e081a79`. This agent inspected defects and suggested changes; it did not repair production code, retrain a model, call a provider, or alter frozen research artifacts. The findings are reproducible offline engineering cases, not measured frequencies of live-provider failures or biological results.

## Confirmed defects

| ID | Priority | Trigger and observed behavior | Consequence |
|---|---|---|---|
| D001 | P2 | A JSON `null` envelope raises raw `AttributeError` in DeepSeek and raw `TypeError` in Jev. Invalid UTF-8 raises raw `UnicodeDecodeError` in both clients. | Jev's advisory evaluation can escape its named-refusal boundary and end a turn; DeepSeek's named provider-error contract is also incomplete. |
| D002 | P2 | A response with `content=null` and reported usage of 7 prompt/3 completion/10 total tokens raises the intended protocol error, but the client's usage remains `{"calls":0}`. | Successful-response parsing determines metering, so benchmark token totals omit provider-reported usage for unusable completions. This does not establish an actual monetary charge. |
| D003 | P3 | Two identical requests with two prediction workers invoke the backend twice when persistent prediction reuse is disabled; the same case with reuse enabled invokes it once. | The round dispatcher promises one inference per distinct input, but its duplicate handling depends on the persistent cache. Disabling reuse exposes redundant computation. |
| D004 | P2 | Repeated Jev evaluations return served models `v1` and `v2`, with probabilities 0.1 and 0.9; the critic records their mean 0.5 solely under `v1`, without refusing or distinguishing versions. | Repeated judgments and their stability/calibration attribution can combine different models under one identity. This is relevant to aliases that may serve changing versions. |
| D005 | P2 | A history containing valid action/outcome strings and an additional `NaN` field returns no validation errors, then raises a raw `ValueError` when computing the prediction-cache key. | Structurally accepted requests can fail before the safe prediction/refusal boundary. The example is invalid JSON input, not a supported biological history. |
| D006 | P3 | With no log-directory setting, the client settings resolve to the literal directory `log/20260910` on 2026-10-01. | The documented dated default does not follow the execution date. Explicitly configured directories and existing frozen logs are unaffected. |

Exact locations, source hashes, expected contracts and proposed minimal changes are in [defect_findings.json](defect_findings.json). Each defect remains open in this report. No finding grants an LLM or prediction evidence authority.

D001 is the first reliability priority: validate the response envelope and normalize decoding failures into each provider's own error/refusal type. D002 requires metering provider-reported usage before interpreting completion text, with attempted/received/usable calls named separately. D004 requires a served-model identity check before aggregation; mixed-version responses should remain separately attributable or be refused. These are proposed changes for the implementation owner, not repairs performed by this agent.

D003 can be addressed by a temporary, per-round result map with request-ID rebinding independent of the persistent reuse setting. Preserve abstention reasons and account actual inference calls. D005 requires strict recursive JSON validation before cache serialization, rather than treating serialization errors as model failures. D006 requires an explicit execution-date policy for the default path; retain existing dated artifacts.

## Role placement and framework boundaries

DeepSeek belongs in task interpretation and registered-plan proposal. The client itself executes no tools; the planner validates shape and registered action/hypothesis scope, while deterministic orchestration owns budget, execution authority, prerequisite admission and final evidence. A faster or more accurate text model does not override these contracts.

Jev belongs in bounded, typed advisory review: ranking registered options, naming plan gaps and flagging applicability limits. Its judgments remain `model_prediction`; they are not measurements, prerequisite satisfactions, causal findings or hypothesis eliminations. The existing tests verify that even confident advisory answers cannot bypass missing premises. D001 concerns failure containment in this placement, and D004 concerns the identity of repeated advisory output. Returned confidence and repetition consistency are not local biological probability calibration.

Production STATE remains a registered condition-response interface. Its explicit refusal of unsupported histories, hypothesis modes, new continuous doses/times or unregistered labels is a capability limit, not a runtime defect. Target-expression invariance or sensitivity to row count/grouping concerns the registered query's interface and sampling; it does not measure predictive accuracy or prove support for an unseen chemical. This review ran no new STATE inference or accuracy experiment. Existing invariance receipts are preserved.

Research WorldV2 is a distinct reading predictor. Missing fitted transition artifacts prevent a new no-training swap; ReferenceWorld is not its replacement. Case-memory serves hypothesis-conditional outcome distributions for its declared sampling frame. The completed denominator experiment demonstrates valid-readout support and missing complete attempted-experiment support on the exposed LINCS2020 proxy population; this review does not manufacture failed-attempt probabilities or reinterpret those proxy labels as biological truth.

## Batching, caching and efficiency

The prediction cache includes model version, biological context, requested readouts, hypotheses, history, observation context and forecast mode, while deliberately excluding request/case/contrast tracking identifiers. The existing cache and parallel tests pass for supported predictions. D003 shows that the current within-round deduplication is coupled to persistent reuse; D005 shows incomplete validation before serialization.

Case-memory cache keys include user-state identity, outcome mode, calibration identity and the episode-store snapshot. Store changes invalidate the snapshot. History in that key does not establish history-conditioned estimation: the registered case-memory path currently allows only `hypothesis_conditional`, and unsupported history modes must remain refused. Batch retrieval only where the actual biological/assay context, state, reference snapshot, hypotheses and sampling frame agree. Never merge `valid_readout` and `attempted_experiment`, or share a forecast merely because action identifiers match.

Parallel prediction is opt-in and documented as requiring a thread-safe backend. It is not a general safety guarantee for arbitrary custom backends. Per-controller prediction reuse assumes stable registered model/assets; name/version keys alone do not authenticate changing files. Asset digest caching uses path, size and modification time, which is an optimization rather than a replacement for content authentication. This review did not observe stale asset reuse in an actual production run and does not label these assumptions as reproduced defects.

## Redundant-code review

The two provider transport loops duplicate byte decoding, JSON parsing and retry handling (`llm.py` and `decision_critic.py`). Both reproduce the same uncaught UTF-8 failure. A small shared decoding/envelope guard is an evidence-backed consolidation candidate, provided provider-specific retries, errors, metering and Jev's refusal boundary remain explicit. General transport refactoring is unnecessary to establish the defects.

An AST name-use scan found seven apparent unused imports. Manual inspection confirmed all seven are `TYPE_CHECKING` imports used by quoted annotations in `context.py`, `contrast.py` and `repair.py`; they must not be removed. No genuinely unused runtime import or safely deletable public API was established. Research outputs, frozen code and compatibility gates are outside cleanup scope. First-eligible composite routing and explicit refusal of unsupported forecasts are deliberate boundaries, not demonstrated dead paths.

## Verification and reproduction

The existing focused regression scope passed **124 tests in 15.38 seconds**: provider transport, typed critic, conditional forecasts, case-memory modes, agent/world-model integration, execution authority, tool boundaries, condition-response refusals and virtual-cell contracts. Passing these tests does not cover or disprove the reproduced defects. No fitting or live API request was executed.

From `D:\MAESTRO`, with the existing maestro interpreter:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -B outputs/dual_core_live_20261001/defect_review/reproduce.py
```

The script writes its receipt once; reruns require a fresh copied output directory. Local receipts are in `outputs/dual_core_live_20261001/defect_review/`: the reproduction script and JSON record, existing-test XML, test execution receipt and artifact ledger. They record source/input/output hashes, command, environment, baseline commit and scope. Provider responses use synthetic bytes and placeholder credentials; no credential was loaded or sent.

Not run: live-provider incidence/rates, load or concurrency benchmarks against an external service, full biological accuracy tests, new fitting, and proposed repairs. This is a focused interface/defect audit, not exhaustive proof that every module is defect-free.
