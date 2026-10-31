# Decision-focused selection MVP: negative static baseline

Date: 2026-10-31 (Asia/Shanghai). Status: exploratory / non-confirmatory.

## Decision

On the saved-run exploratory summaries from `dev_pool.npz`, a supervised top-10%
decision head did not improve cell-line selection utility over raw signature-neighbor
transfer or ordinary continuous ridge. The decision-focused surrogate is therefore
parked under this static input contract. This is not evidence against a
history-dependent functional state: the data contain no matched treatment history,
dose/time sequence, baseline state, or later action outcome.

No result is promoted to `src/` or `tools/`. AIVO and Agent work remain deferred.

## Frozen test

The study read only the exposed development pool: 1,403 compounds, 18 L1000 option
slots, 978 genes and 578 PRISM 19Q4 cell lines. Five InChIKey connectivity folds were
fixed as `[272, 274, 280, 294, 283]`, with 348 active compounds. All transformations
and fits used reference compounds only.

The new arm converted each reference compound's reference-generic-residualized profile
into a top-10% cell-line membership target, then fit a multi-output ridge on the raw
flattened L1000 signature. It was compared with raw k=20 cosine transfer and ordinary
continuous ridge using the same input and folds. The protocol and exact hashes are in
[`PROTOCOL.md`](PROTOCOL.md) and [`FREEZE.json`](FREEZE.json).

## Result

Values are saved-run exploratory summaries, not confirmation results.

| Arm | Active top-10 overlap | Active selection regret | All top-10 overlap | All selection regret |
|---|---:|---:|---:|---:|
| Raw cosine k=20 | 0.21203 | 0.99476 | 0.16029 | 0.73729 |
| Ordinary ridge | 0.19857 | 1.03248 | 0.15346 | 0.75476 |
| Decision top-10 ridge | 0.18684 | 1.12913 | 0.16809 | 0.78172 |

The saved-run summaries show the decision head lower on both primary active-compound
endpoints. Its slightly higher all-compound overlap does not translate into lower
regret in the saved run. Its output is a ranking score rather than a calibrated
viability profile; its raw correlation and MAE are not used as evidence of functional
calibration.

The original independent verifier remains `FAIL`: its implementation did not
reproduce all saved primary metrics, and the frozen prose left the
residualization/ranking/missing-mask/tie convention unresolved. A post-run
clarification recorded the distinction between calibrated profile scores and direct
decision scores without changing any output. The supplemental arithmetic recheck then
reproduced all `1,403 × 3` primary rows and summaries exactly
(`VERIFY_61_SUPPLEMENT`: PASS). This is an arithmetic check under the clarified
interpretation only; it does not validate the fit, outputs, protocol or scientific
claim. The scientific gate remains `INCONCLUSIVE`, and the original FAIL is retained
for provenance.

## Interpretation

Under the clarified saved-run arithmetic, this exploratory comparison does not support
the simple claim that replacing continuous prediction with a top-k decision surrogate
is sufficient to resolve the correlation/selection mismatch. It cannot adjudicate
the model comparison beyond that static run. The observed direction is compatible with
finite-sample instability, class imbalance in the top-10% labels, and the fact that
the current input does not contain treatment history or future-action information. It
does not show that decision-focused learning is useless, and it does not test SPO-style
training under a prospective action menu.

The cross-field review also limits the scientific claim: predictive-state, reward/value
equivalence, SPO and active system identification are established principles. Their
useful transfer is to define the biological target and falsification test, not to claim
a new architecture. See [`crossfield-state-learning/REPORT.md`](../2026-10-31-crossfield-state-learning/REPORT.md)
and its independent [`CHALLENGE.md`](../2026-10-31-crossfield-state-learning/CHALLENGE.md).

## What remains worth testing

The next core test should use easily obtainable measurements rather than require a
large virtual-cell model: baseline growth/viability, a small standardized functional
probe panel on exchangeable sister cultures, recorded preparation history, and a fixed
later action menu containing at least A and B. The bounded scientific question is
whether a measured state preserves the **next-action contrast** across histories:

```text
E[Y(A)-Y(B) | S, H] ≈ E[Y(A)-Y(B) | S]
```

This is weaker than full state sufficiency and directly tied to choosing A versus B.
It requires overlapping early states, randomized next actions, independent preparation
blocks, a prespecified equivalence margin, and a held history/preparation evaluated
without using its future outcomes for admission. Absolute efficacy, safety and tail
risk need separate endpoints.

Dynamic BH3 profiling and ordinary response-panel reconstruction are close biological
and statistical prior art. The possible contribution is only a reproducible, bounded
history/action contrast that transports to a reserved preparation range while the
later action menu remains fixed and supported, and identifies where it fails. Holding
out the chemistry used to create preparation histories tests preparation-chemistry
transport; holding out the chemotype of the later action is a separate, harder claim
requiring its own structural support. If a standard response panel or DBP reaches the
same decision value at the same cost, the special state claim stops.

## Limits and preservation

- This is one exposed static development run; no NCI-60, PRISM 24Q2 or external outcome
  was opened.
- It cannot test sequence, washout, dose response, causal transport, mechanism
  identification, organoid composition or Agent utility.
- The decision head is a conventional supervised baseline, not a new biological law.
- The cross-field audit identified concrete transform and metric differences that
  explain why the earlier all-arm replay is not comparable, but no corrected all-arm
  replay was executed. That mismatch remains unresolved and is not used as evidence
  for or against this static decision baseline.
- The cross-field reconnaissance report's statement that no decision experiment was
  run refers to that literature/replay round; this directory is a separate subsequent
  exploratory static baseline run.
- The first independent verifier remains FAIL under the frozen prose; the supplemental
  clarification-based arithmetic recheck is PASS and has no authority to promote a
  model or change the scientific gate.

Current status: **decision-focused static baseline PARKED; Virtual Cell core NOT_ADMITTED;
AIVO/Agent DEFERRED**.
