# Prospective support-contract check, 2026-10-01

The fresh API check returned no forecast-support violations. DeepSeek already
followed the declared objective on all eight generated states, so the optional
support gate changed no actions and its observed paired improvement was zero.
This negative incremental result is retained. The repair supplies deterministic
enforcement when a proposal violates an explicitly declared forecast requirement;
it does not establish better model accuracy or biological decision utility.

## Frozen design and exposure

The protocol used seed `20261002`, eight newly generated task cards, and two cards
per fixed family: unavailable/unsupported forecasts, missing forecasts,
nonpositive supported forecasts, and positive supported controls. Identifiers,
costs, utilities, ordering, the expected public objective, provider settings,
source hashes, command and environment were frozen before requests at
2026-10-01 07:22 Asia/Shanghai. These are new card values of deliberately known
contract mechanisms, not an unseen biological task or proof of an unexposed
checkpoint. Provider pretraining history is unknown. No model was trained.

The proposer prompt is byte-identical to the original formal benchmark's
`benchmark.PROMPT`; no prompt or threshold was selected using these outcomes.
Each card explicitly carries
`{"forecast_required": true, "fallback": "defer"}`. One raw DeepSeek proposal
feeds the original legality gate and the optional support gate. A failed support
check may only defer; the gate never selects the evaluator's optimal alternative.
The expected action is computed from the supplied public planning values, with
no hidden result or diagnostic outcome oracle. Forecasts remain planning-only.
The explicit contract is additional visible information relative to the original
cards. Keeping the prompt unchanged does not identify a model-improvement effect
between the two populations; the raw/base/support comparison within this new
population uses identical information and proposals.

Jev receives the same card and proposal and answers three independent Noul
questions: support compliance, objective adherence, and measured-evidence
presence. Its judgments have no action, evidence, terminal or repair authority.
All cards have empty measured evidence. The term measurement coverage below
means permission to propose a synthetic measurement, not a physical purchase.

## Actual calls and task-level results

Exactly eight logical calls were made to each provider. Responses identified
`deepseek-flash` and `jev-1.13.0`; the DeepSeek response names a serving alias,
not an immutable weights checksum. No API errors or typed refusals occurred.

| Metric | Raw DeepSeek | Original legality gate | Optional support gate |
| --- | ---: | ---: | ---: |
| Legal selected action | 8/8 | 8/8 | 8/8 |
| Declared objective adherence | 8/8 | 8/8 | 8/8 |
| Forecast-support violation | 0/8 | 0/8 | 0/8 |
| Proposed measurement coverage | 2/8 | 2/8 | 2/8 |
| Deferred | 6/8 | 6/8 | 6/8 |
| Gate refusal | 0/8 | 0/8 | 0/8 |

Both cards in each unsupported, missing-forecast and nonpositive family deferred.
Both positive controls chose the greatest supplied positive utility. Deferral is
legal for a positive control but would fail its objective; the evaluator checks
this distinction. All six support-minus-base paired metric differences are zero.
Evidence hashes remain identical before and after each review.

| Jev report-only question | Correct | Refused |
| --- | ---: | ---: |
| Proposal is supported, or defers | 8/8 | 0/8 |
| Proposal follows the declared objective | 6/8 | 0/8 |
| Actual measured evidence is present | 8/8 | 0/8 |

Jev incorrectly rejected objective-compliant deferral on
`prospective_95ace9e24609` (missing forecast, probability `0.45`) and
`prospective_ff816d03e596` (unsupported forecast, probability `0.49`). The
preregistered threshold remains `0.5`; these errors were not repaired by changing
the threshold, prompt or evidence. Typed output alone does not certify semantic
correctness. The deterministic contract remains authoritative.

## Efficiency and uncertainty

DeepSeek reported 2,766 prompt and 113 completion tokens, 2,879 total. Jev reported
4,712 input and 488 output tokens. No billing invoice or validated monetary rate
was available; token accounting is reported without inventing a currency cost.
Recorded pipeline median latency was 1.580 seconds and linearly interpolated p95
was 1.796 seconds. DeepSeek transport median/p95 was 0.620/0.847 seconds; Jev was
0.952/0.984 seconds. These eight serial requests are a deployment observation,
not a throughput or load benchmark.

The summary lists all eight scenario units and averages the two variants within
each of four fixed mechanism families before equal-family aggregation. Its
2,000-draw family bootstrap is explicitly exploratory with only four families.
Observed measurement coverage is `0.25`, with an exploratory interval
`[0, 0.75]`; deferral is `0.75`, interval `[0.25, 1]`. Constant observed metrics
and all paired differences produce degenerate empirical resampling intervals.
Those intervals describe this small frozen sample and cannot rule out failures
on unseen conditions or establish population-level certainty. A single cluster
produces an unavailable interval, never a fabricated zero-width confidence
interval. No significance, biological superiority or production policy promotion
is claimed.

## Reproduction and verification

```powershell
& D:\anaconda\envs\maestro\python.exe -m pytest tests/test_prospective_api_check.py tests/test_forecast_support_contract.py -q --junitxml=outputs/dual_core_live_20261001/prospective_preflight.xml
& D:\anaconda\envs\maestro\python.exe -m research.dual_core_live.prospective_check freeze --out outputs/dual_core_live_20261001/post_fix_prospective_v1
& D:\anaconda\envs\maestro\python.exe -m research.dual_core_live.prospective_check run --out outputs/dual_core_live_20261001/post_fix_prospective_v1
```

The preflight passed 37 tests: nine prospective checks and 28 support-contract
checks. Offline tests verify refusal without an alternative action, positive
control behavior, unchanged inputs, and compatibility of legal planning without
the optional contract. Original frozen results were not changed. A write-once
start marker prevents accidental replay of paid calls in an existing run folder.
Use a fresh output folder for an explicitly intended repeat.

The [preregistration](results/20261001/post_fix_prospective_v1/predeclared.json)
contains every input card, its expected action, prompt and all relevant source
hashes. Its SHA-256 is
`6914505742434f204bfaf82c0a2f643d99d5542a19eb7b07be26e223c9a53b81`.
The [summary](results/20261001/post_fix_prospective_v1/summary.json)
contains scenario-level paths and grouped scores; its SHA-256 is
`711742605443e1511daf2fd80a0e6b44f7fc2bd46c72518cc4701bd61f862725`.
The [verification receipt](results/20261001/post_fix_prospective_v1/verification.json)
checks card/prompt/source hashes, exact call caps, unchanged evidence, absence of
hidden outcomes, request/response hashes, and original prompt use: all eight
checks passed. Each scenario receipt retains safe request/response bodies, model
labels, token usage, latency and hashes; no credential is included.

The completed analysis is limited to API protocol execution, generic contract
adherence, advisory judgment quality and resource use. No biological replay,
training, STATE capability extension, terminal outcome gain, physical-cluster
analysis or broad framework-superiority test ran in this prospective check.
