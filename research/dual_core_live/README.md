# Live API validation and report-only model audit

This extension uses the existing maestro environment and both configured
providers: DeepSeek for public action proposals and Jev for typed advisory
questions. Registered executors, QC and evidence/terminal validators retain
authority. The generic report-only auditor has no repair or execution method.

The implemented optimization, literature comparison, experiment design, metrics
and pre-experiment hypotheses are in [DESIGN_REVIEW.md](DESIGN_REVIEW.md).
[API_DESIGN.md](API_DESIGN.md) records provider roles and official interface
references. Observed API results and their limits are in
[API_RESULTS.md](API_RESULTS.md); the dated record is
[log/20261001/README.md](../../log/20261001/README.md).
The subsequent negative-result repairs and fresh API check are in
[POST_FIX_RESULTS.md](POST_FIX_RESULTS.md). The optional
[support contract](support_contract.py) belongs to the research selector; it
does not grant the dedicated auditor repair authority or change production defaults.

## Implementation and verification

Six independently reproduced runtime defects were repaired: malformed provider
envelopes/UTF-8, usage lost for unusable completions, duplicate within-round
inference when cross-round cache reuse is disabled, aggregation of different Jev
served versions, nonfinite forecast history, and a stale default log date.
The shared provider envelope decoder removes duplicated decoding logic; the
dispatcher also removes redundant inference. No unrelated runtime imports or
historical research artifacts were deleted.

The new [ModelAuditAgent](../../src/agent/model_audit.py) reviews the registered
action card and proposal, returning immutable findings and hashes. A separate
collaborating review agent independently found the original defects, reviewed
the fixes and verified the auditor's own malformed-input boundaries. That agent
applied no repairs. Its original [defect review](DEFECT_REVIEW.md) and
[structured findings](defect_findings.json) describe the pre-fix baseline;
post-fix receipts are preserved separately.

The post-fix full regression reports **1,621 passed, one inherited historical
Markdown-language failure, two constructed fitting checks deselected**, and no
source drift. All 333 historical frozen files and 39 data-review source records
match. The failure remains a strict failed validation, not a green full suite.
The independent focused post-fix review passes 161 tests. These are engineering
checks, not biological efficacy measurements.

Replaying the original 24 saved proposals under the explicit support contract
changes only the four unsupported-forecast selections to defer, yielding 24/24
objective adherence instead of 20/24. This is deterministic enforcement on
exposed cases, not a new model result. A newly frozen eight-card check made eight
calls per provider: raw/base/support all achieved 8/8, so its incremental action
effect is zero. Jev still made two objective-judgment errors; its advisory output
cannot override the deterministic contract. Four single-chemical-unit reading
intervals are removed in a separate corrected summary; old summaries and means
remain byte-for-byte preserved.

The byte-verifiable [publication manifest](results/20261001/manifest.json) includes
all scientific/API receipts and exact source copies. Generated `test_temp`
fixtures, Python caches and configuration files remain local with exclusion
records; they are not scientific results. The independent API audits pass 4,016
original/recovery checks and 321 prospective checks, including the new visible
contract's information difference.

## Reproduction

From `D:\MAESTRO`, use the already installed environment. Each live rerun needs
a new output leaf directory and consumes provider requests. Recorded artifact
reconstruction is the appropriate route for an exact replay of observed API
answers; a future provider call may return another answer or served version.

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_live.live_api --smoke --out outputs/dual_core_live_20261001/api_smoke_new
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_live.benchmark freeze --out outputs/dual_core_live_20261001/fixed_benchmark_new
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_live.benchmark run --out outputs/dual_core_live_20261001/fixed_benchmark_new
& 'D:\anaconda\envs\maestro\python.exe' -m pytest tests/test_model_runtime_defects.py tests/test_model_audit_agent.py tests/test_live_api_contract.py
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_live.reanalyse --input outputs/dual_core_live_20261001/fixed_benchmark_recovered/summary.json --out outputs/dual_core_live_20261001/uncertainty_correction_new
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_live.prospective_check freeze --out outputs/dual_core_live_20261001/post_fix_prospective_new
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_live.prospective_check run --out outputs/dual_core_live_20261001/post_fix_prospective_new
```

The first capability smoke was executed at parent commit `8271e8a`. The formal
study froze that parent plus exact working-tree source hashes, explicitly naming
the four authorized runtime source changes relative to inherited inputs. Other
inherited input/source hashes remain mandatory. The published main commit
contains those changes and the complete receipts; the Git parent alone is not
the experimental source version.

All labels/development folds and ReferenceWorld hyperparameters are previously
exposed. The biological pilot does not train, fit or attribute its results to
STATE/WorldV2/case memory. Forecasts cannot become measurements. No diagnostic
oracle is deployed, no real predecision-state gain arm is run, and this small
study establishes neither broad biological superiority nor new STATE query
support.
