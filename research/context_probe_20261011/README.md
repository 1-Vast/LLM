# Fixed eight-probe feedback in a masked response context

**Result: `NOT_ESTABLISHED`.** The first diagnostic proposed by the
[next-round review](../next_round_review_20261011/README.md) is implemented and executed.
Correct probe identities carry some information, but the low-rank update does not
improve later drug selection over the strong frozen prior. An empirical conditional
update reduces prediction MSE without improving top-10 functional utility. These
results do not justify advancing this branch to KG, adaptive acquisition or Agent
experiments. They do not rule out other endpoints, probes or source conditions.

All data are previously exposed public measurements. This is a **new algorithm task on
old data**, not an independent biological confirmation. No wet experiment or LLM call
was made. Published ComBat and replicate preprocessing were not reconstructed; the
verified masking boundary starts after those supplied transformations.

## Data and task

The [data packet](data/README.md) rebuilds the response matrix from exactly 2.5 uM HTS
treatment columns. It confirms the 36 mixed-dose groups in the old study, without
rewriting that study. Metadata-only drug identity groups use one deterministic source
column; aliases are never averaged or used to replace missing outcomes.

- 561 cell contexts, 3,621 eligible known-drug groups and 19,144 basal-expression inputs.
- Metadata-hash roles: 356 reference, 99 development, 106 evaluation contexts.
- Drugs qualify at >=95% observed reference responses. No target outcomes or target
  availability determine the library. Ten failed-STR and seven basal-unavailable
  contexts are excluded using input/identity metadata.
- The target task fixes one context and ranks ten drugs in the common 3,613-drug future
  menu. Eight fixed probes and their aliases are excluded from that menu for every arm,
  including zero purchase. This is not unrestricted whole-library discovery.
- The endpoint is negative mean published log2-fold-change of selected drugs, not
  apoptosis, mechanistic engagement, or a context-selectivity residual. Per-value
  treatment times, raw cultures and plate/day replicates are unavailable.

## Frozen diagnostic

One reference-only basal kNN15 model supplies crossfit differential residuals for a
fixed panel of eight diverse probes. The panel is saved before development outcomes
are scored. All six arms receive the same initial strong prior. Six prior settings
compete on the same complete-selection development subset; ridge with penalty 1,000
wins. Reference-only residual features are fitted from five context-crossfit folds;
each fold independently fits its basal normalization, gene selection and prior.

Development chooses rank 8 / ridge 10 for the low-rank correction and ridge 10 for the
conditional residual comparator. These settings are then frozen before evaluation
probe release. The conditional arm refits an existing method family to the functional
endpoint; it is not a claim to reproduce the old RNA weights or all prior algorithms.

Deployment APIs accept only the target basal vector and eight purchased scalar values.
The complete target response row is excluded from fitted means, features, covariance,
loadings and hyperparameters. Evaluation predictions and selected identities are saved
before terminal scoring. Full pipeline poisoning of unpurchased evaluation responses
leaves fitted settings, predictions and commitments identical.

Every paid arm is charged eight attempted scalar measurements and one turnaround:
10 declared read equivalents. Zero purchase pays zero. A missing probe causes all
update arms to use the frozen prior, without a refund or replacement. A missing
selected terminal result yields null utility, never a replacement drug. This pooled
PRISM replay does not establish that eight scalar queries equal eight real independent
cultures or actual laboratory assays.

## Results and decision

All 106 contexts remain in the ledger. Six have a missing probe and follow the frozen
fallback. Five lack a complete selected endpoint; paired utility summaries therefore
cover 101 contexts and cannot establish full-population performance.

| Arm | Top-10 utility on 101 complete contexts | Mean terminal MSE on available measurements | Mean changes in selected ten | Declared resource |
|---|---:|---:|---:|---:|
| Zero purchase | 4.29493 | 0.30973 | 0.000 | 0 |
| Paid no update | 4.29493 | 0.30973 | 0.000 | 10 |
| Offset calibration | 4.29493 | 0.78425 | 0.000 | 10 |
| Low-rank correction | 4.28300 | 0.78421 | 1.274 | 10 |
| Shuffled probe identities | 4.25209 | 0.88839 | 1.962 | 10 |
| Conditional residual update | 4.28912 | 0.27874 | 1.443 | 10 |

The offset control preserves every selected identity. The low-rank model can change
ranking, but does not improve it: 36 complete contexts improve, 47 worsen and 18 are
unchanged. The conditional comparator improves MSE by about 10%, while its top-10
utility increment is still negative. MSE improvement is not a decision benefit.

| Paired contrast | Mean utility increment | Nominal lineage-cluster 95% interval |
|---|---:|---|
| Low rank minus paid no update | -0.01193 | [-0.03530, +0.01025] |
| Low rank minus shuffled identities | +0.03092 | [+0.00628, +0.05609] |
| Low rank minus conditional update | -0.00611 | [-0.03343, +0.02180] |
| Conditional update minus paid no update | -0.00582 | [-0.03152, +0.02206] |
| Low rank minus zero purchase, price 0.001 per read equivalent | -0.02193 | [-0.04530, +0.00025] |

Intervals are exploratory, unadjusted dependence sensitivities on observed complete
pairs. Lineages are not independent cultures. Full prespecified price sensitivity
(0, 0.0001, 0.001, 0.01) is in [RESULTS.json](runs/fixed8/RESULTS.json). No price is a
laboratory quote or an estimated monetary exchange rate. No coverage interval is
constructed: selected errors are diagnostics, not JOMI, FCR, simultaneous coverage or
selection-conditional guarantees.

The decision is to stop this complex feedback branch under the tested setting. The
valid next question is why the selected probes fail to correct ranking usefully, or
whether a separately qualified functional endpoint supplies more useful feedback.
Any follow-up uses a new protocol and preserves this negative result. Selecting a
better-looking subgroup, probe panel or price after these outcomes is development,
not independent confirmation.

## Engineering and verification

The run took 22.45 seconds, recorded 636 arm/context commitments and made zero API calls.
The [independent audit](review/VERIFICATION.json) verifies original exact-dose response
alignment, artifact hashes, selected identities, missingness, charges, all nine paired
contrasts and independently reconstructed cluster bootstrap intervals. It does not
verify raw preprocessing isolation, biological replication or monetary costs. Sign-flip
p-values are not independently reconstructed and are not used in the study's gate.

Twelve research tests pass, including whole fit/commit poisoning, rank invariance and
missing-probe charging. The production suite has 784 passes and one existing failure:
the repository-shape test requires the tracked root `Innovation.md` to be absent.
That file was preserved.

Two bounded report defects from the review were repaired in
`tools/evaluation/decision_report.py`: pooled campaigns must share one endpoint/unit,
and nonfinite derived costs/differences/unsafe aggregates are rejected before inference.
CLI output uses strict JSON. Four new regression tests cover these cases. The empirical
predictor, probe policy and data preparation remain in research. Older engineering
receipts retain the file hashes applicable at their execution, rather than being
rewritten to match this later report fix.

## Reproduction

From the repository root, using the existing `maestro` environment:

```powershell
& D:/anaconda/envs/maestro/python.exe -m pytest research/context_probe_20261011/test_model.py research/context_probe_20261011/test_pipeline.py
& D:/anaconda/envs/maestro/python.exe research/context_probe_20261011/data/verify.py
& D:/anaconda/envs/maestro/python.exe research/context_probe_20261011/review/verify.py
& D:/anaconda/envs/maestro/python.exe research/context_probe_20261011/run.py --output research/context_probe_20261011/runs/new_replay
```

The runner requires a fresh output path and freezes source/data bytes before fitting.
`data/output.npz` and `runs/*/predictions.npz` are local generated assets ignored by Git.
The source files and identities are listed in `data/MANIFEST.json`; a clean checkout
needs those sources before `data/prepare.py` can reconstruct the matrix. Preserve
existing frozen files when preparing data again: a rebuilt artifact or changed
manifest must be followed by a new run, not attached to an old receipt. Row summaries
and engineering tests do not substitute for missing source measurements.
