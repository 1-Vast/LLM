# Live API validation and provider roles

DeepSeek proposes actions and can explain a future repair; TypeSafe Jev answers
narrow typed advisory questions. Registered action legality, evidence admission,
QC, costs and terminal permission remain deterministic. A separate defect reviewer
reports failures and never applies a repair. No API response is a measurement.

The repository already supplies both transports in `agent.llm` and
`agent.decision_critic`. This research runner records their safe request bodies,
response envelopes, served-model identifiers, hashes, usage and latency. It does
not copy a key into an artifact, change provider configuration, train a model,
or modify production source.

## Capability smoke, declared before requests

Two logical calls per provider use identical small task states. The first state
has one affordable unblocked measurement and one action blocked by both budget and
an unmet prerequisite. The second has no affordable action and only a forecast,
which cannot be treated as qualified evidence. Expected selections are `m1` and
`defer`; neither state authorizes a terminal decision. The saved preregistration
contains complete cards, prompt, expected answers, source hashes, command and
environment. Existing bounded transport retries are retained and included in call
latency. This is a capability check, not a biological efficacy benchmark.

```powershell
& D:\anaconda\envs\maestro\python.exe -m research.dual_core_live.live_api --smoke --out outputs/dual_core_live_20261001/api_smoke
```

## Fixed comparative benchmark

The approved population contains 24 generated contract scenarios, with four
registered variants of each of six families: budget, repeated actions, forecast
provenance, failed QC, late availability, and unsupported forecasts. Blinded review
has 24 clean controls and 24 defects, six each of terminal-authority claims,
unregistered actions, missing required fields, and non-object proposals. Twelve
biological episodes are selected by identifier hash, six per task with coverage
of the five existing folds. Each replay permits at most two registered purchases.
The complete population, prompts, thresholds, settings, inputs and sources are
written before requests; the cap is 49 logical calls per provider, serially. Keep
symbolic complete-information scores separate from biological reading outcomes:
synthetic task success cannot establish biological superiority.

Compare a deterministic fixed ordering, a one-step optimizer of the exact public
forecast card, a DeepSeek direct proposal, the same
DeepSeek proposal under deterministic contract gates, and a Jev advisory review of
the exact same proposal. Jev receives no hidden result and cannot add evidence.
The report-only Jev arm has the gated DeepSeek action by construction; it measures
judgment quality and overhead, and supplies no claim of Jev decision improvement.
The original baseline planner comparisons remain in the earlier frozen audit.
Report raw and gated legality, task success/regret, refusal/coverage, evidence
boundary violations, provider latency (median/p95), usage, served-model variation
and error counts. Defect detection uses known inserted defects with clean paired
controls, precision/recall and false-positive rate; the reviewer has no write or
repair tool. No prompt or threshold is selected using benchmark outcomes.

The framework can be superior on contract enforcement and resource accounting
without outperforming a complete-information deterministic optimizer. Promote a
research change only when its preregistered quantitative comparison supports the
claim. A null or negative result is retained in the run record.

The `ModelAuditAgent` produces immutable findings and hashes; its caller can
decline a proposal with findings. The auditor supplies no replacement action,
repair, measured evidence or terminal verdict. The experiment tests this same
review contract across the six families and the two registered biological
adapters. Defect-review clean/bad pairs are grouped by scenario and then family.
General success intervals resample families; biological paired estimates and
interval endpoints average episodes within chemical skeleton/component units
before averaging units. Physical plate/batch uncertainty is reported separately;
one connected physical component cannot support a physical-cluster interval.

Biological terminal reward remains `+1` correct, `-2` wrong, `0` undetermined or
deferred. The planning price is `.02` per attempted measurement; assay days are
a separate budget. `net_utility` explicitly subtracts `.02 * measurements` from
terminal reward. All reachable source uncertainty is retained as declared bounds;
reading losses and registered-path counts remain diagnostic where linkage is
unresolved. Selected-action prediction quality averages readings within an
episode and episodes within a chemical unit, with raw pooled losses separately
labelled descriptive. No loss based on selected reading count is treated as an
independent replication count.

```powershell
& D:\anaconda\envs\maestro\python.exe -m research.dual_core_live.benchmark freeze --out outputs/dual_core_live_20261001/fixed_benchmark_v1
& D:\anaconda\envs\maestro\python.exe -m research.dual_core_live.benchmark run --out outputs/dual_core_live_20261001/fixed_benchmark_v1
& D:\anaconda\envs\maestro\python.exe -m pytest tests/test_live_api_contract.py tests/test_model_audit_agent.py tests/test_model_runtime_defects.py -q
```

The first freeze attempt in `fixed_benchmark` stopped before a provider call:
the inherited ledger classified executable Python alongside data and encountered
four independently authorized runtime fixes. That attempt and its failure
receipt remain preserved. The fresh freeze checks every inherited hash except
an exact allowlist of those four source files, records their old/current hashes,
and freezes all current executable sources. No task, selection rule, prompt,
threshold, data value or endpoint changed in response to an experimental result.

## Capability result and hypotheses

The initial actual smoke calls returned the expected action in both states from
both providers. DeepSeek used 475 total tokens across two requests; Jev reported
872 input and 122 output tokens and served `jev-1.13.0`. One Jev evidence-presence
answer incorrectly labelled an empty-evidence state as measured (`p=0.51`),
while the forecast-only state's answer was false (`p=0.13`). No evidence hash
changed. This semantic error is retained; a typed response is not a correctness
certificate or a measurement.

The expected design outcome is measurable contract reliability with explicit
overhead and support boundaries. The strong one-step optimizer is expected to
match or outperform a language-model selection when the exact objective is
already supplied numerically. Jev's useful role must be judged through defect
detection precision/recall and false positives, rather than an action improvement
that the report-only arm cannot produce. Better biological correctness would
require positive paired effects under matched coverage, adequate independent
units and source identification; the 12-case previously exposed pilot can reject
an implausible claim but cannot establish general biological superiority.

## Official interface references checked on 2026-10-01

DeepSeek documents Chat Completions, an explicit thinking toggle, and JSON output.
The current production client uses a strict JSON prompt for `deepseek-flash`; the
live probe records the payload actually used. Documentation and a serving endpoint
can differ, so an observed response has priority over assumed support.
([Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/),
[thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/),
[JSON output](https://api-docs.deepseek.com/guides/json_mode/))

TypeSafe documents state plus independent typed Choice, Score and Noul questions;
question decomposition is appropriate for narrow feasibility and provenance
checks. Provider confidence is recorded but is not assumed calibrated on MAESTRO's
task distribution. ([Introduction](https://docs.typesafe.ai/introduction),
[official documentation index](https://docs.typesafe.ai/llms.txt))
