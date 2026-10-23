# Feedback propagation to unmeasured compound/line pairs: report

**Decision: STOP. No program search is drafted or launched.** The registered deterministic repair (analogue-anchored update, R1)
does not beat ridge-plus-feedback on identical histories, the conventional kNN analogue explains whatever it does, and the
feedback-only diagnosis has weak identification. Development-grade, exposed data; `verify.py` VERIFIED; no sealed outcome opened;
nothing frozen edited; no commit, no push.

## 1. Verified facts

* HEAD equals 5d713d5ca3194fbd131ce45835355538d10a4b66; the working tree differs only by this study and the seed-attribution
  erratum. Tables match `indication_triage_20261016/BUILD.json` by sha256.
* **Erratum (task 1).** The secondary equal-lineage interval of `seed_attribution_20261017` collapsed repeated lineage draws
  (`set(groups)`). Recomputed from the public per-lineage means (`ERRATUM_20261018.md` there): policy +0.057 [-0.206, +0.355]
  (saved [-0.175, +0.267]); I2 +0.100 [+0.002, +0.202] (saved [+0.023, +0.176]); I1 +0.076 [-0.105, +0.278]. Primary tests and
  stop decisions are unchanged; the statement that the I2 equal-lineage interval excludes zero survives only marginally and was
  never a registered test. Pointers added to `research/EVIDENCE.md` and the study's `DEVIATIONS.json`.
* **The saved indication-triage totals reproduce (395 vs 293), and 394 of 395 (MAESTRO loop) and 293 of 293 (two-stage) hits are
  pairs the arm itself probed.** The old grading is a noisy re-read of the graded cell, not propagation to unmeasured pairs.
* Chemistry: MoA-family folds (1,145 families, none crosses a fold); 28-38% of evaluation compounds have a Tanimoto ≥ 0.5
  analogue elsewhere; the purge (402-468 training compounds per fold) leaves max Tanimoto < 0.5 for all. Murcko scaffolds are
  not disjoint (24-29% of evaluation compounds share one with a retained training compound).
* Masking: scrambling every unqueried cell changes no query, observation, score or list for four rules; a leaky control is caught.
  Missingness: 97.6% finite; 506 of 545 lines admissible; ~8% of events are on inadmissible lines.
* Granularity: a well reads a pool of ~24 lines (23 pools); plate/well/replicate mapping is absent, so every cost is hypothetical.

## 2. Data limitations

PRISM 19Q4 folds 2-4 were opened by the indication-triage study, so this is a fresh protocol on exposed data and not a
confirmation. The probe is the published value plus synthetic noise, not an independent assay of the graded cell. Unmeasured
pairs avoid the re-read, but the history still comes from the same matrix. No independent data exist locally for this task; the
sealed tiers stay closed. Two noise draws give R1 - ridge +0.14 (registered) and +0.86 (second draw): the realisation of the
synthetic noise moves the answer by about the width of the interval.

## 3. Task and hypothesis

Task (distinct from the old triage): an unseen, chemically purged compound batch; B = 3 pool reads per compound (hypothetical
units); 32 nominations per 64 compounds (≤ 3 per compound) from pairs no unit was spent on; events as registered.
Question: can observed feedback identify and repair a failure in how responses propagate to unmeasured pairs?
Only the feedback-update program varies; the base predictor, endpoint, nomination and acquisition rules are fixed.
* H1 R1 > ridge-plus-feedback by ≥ δ* = 0.1875 events per 64 compounds (δ* from the cost of one more pool for the baseline,
  derived from folds 0-1 before the comparison; minimum detectable gain at this size expected 0.68 (the realised half-width, 0.72, implies about 0.9), so δ* itself is unresolvable and the
  rule needs the lower bound ≥ δ*).
* H2 R1 > the strongest conventional method (kNN, K = 10). H3 a leave-one-pool-out diagnosis adds to R1.

## 4. Implemented (all in `research/feedback_propagation_20261018/`)

`bench.py` (fold, purge, oracle with masking, pool order), `rules.py` (ridge, scale mixture, empirical-covariance, kNN, forest),
`repair.py` (R1 and the gated variant), `loop.py` (identical-history and closed functional loops: acquire, update, recompute
admissible actions, continue; nomination and grading), `metrics.py`, `develop.py` / `thresholds.py` (Phase D), `compare.py` /
`analyse.py` (Phase E), `audit_task.py`, `test_science.py` (10 tests), `seal.py`, `verify.py`. Registered in `research/STUDIES.json`.
R1: prior replaced by the mean profile of the 10 nearest training compounds on the probed lines, then the Gaussian update of the
residual (reduces to ridge at lam = 0). Existing infrastructure (`World`, `call_score`, `tc.nominate`, `tc.events`) is reused.

## 5. Results (folds 2-4, 2,398 compounds, 36 complete campaigns; events among nominated unmeasured pairs per 64 compounds)

| arm | unmeasured events | unique compounds | oracle |
|---|---|---|---|
| structure prior (history-matched) | 1.58 | 1.31 | 32 |
| ridge-plus-feedback | 2.64 | 2.33 | |
| mixture mean / empirical covariance | 2.67 / 2.61 | 2.33 / 2.22 | |
| kNN K = 10 (C\*) / 20 / 40 | 2.69 / 2.61 / 2.36 | 2.25 / 2.14 / 1.92 | |
| random forest | 2.39 | 2.11 | |
| **R1** | 2.78 | 2.33 | |
| gated (diagnosis) | 3.06 | 2.58 | |

Registered contrasts (family-cluster bootstrap 95%, one-sided family sign-flip; Holm over P1, P2):
* **P1 R1 - ridge +0.139 [-0.579, +0.870]**, p 0.38 (Holm 0.75); unique candidates +0.000 [-0.637, +0.618]. Per fold +0.82, +0.17,
  -0.46. Development had +0.81 [+0.24, +1.37], a selected maximum.
* **P2 R1 - C\* +0.083 [-0.279, +0.437]**, p 0.38. R1 versus the best conventional method chosen on these folds: the same.
* **P3 gated - R1 +0.278 [-0.165, +0.775]**, p 0.16.
* Feedback itself propagates: ridge - prior +1.056 [+0.626, +1.526] (21 of 36 campaigns positive, 6 negative), but not at the logical cost:
  at 16 logical lines ridge - prior is +0.167 [-0.108, +0.451] and R1 - ridge -0.333 [-1.186, +0.458]. Budget (B = 2, 4): R1 - ridge
  -0.056, +0.083.
* The feedback is item-specific: R1 on its own histories versus on another compound's histories +2.361 [+1.596, +3.242]. Misleading
  histories are harmful and R1/kNN amplify it more than ridge (deranged R1 0.42, kNN 0.56, ridge 1.47 against prior 1.58).
* Prediction error improves consistently while the decision utility does not: R1's error on unmeasured cells is lower than ridge's in
  all three folds (0.265 vs 0.287, 0.296 vs 0.327, 0.243 vs 0.255).
* Identification: the leave-one-pool-out gate's loss difference separates the truly better rule per compound with AUC 0.59-0.63
  (development 0.59, folds 2-4 0.63, 0.59, 0.61). A perfect two-way choice would add +0.528 [+0.058, +1.049] to R1 (an unattainable ceiling, 19% of R1);
  the realised gate adds the P3 +0.278, not distinguishable from 0.
* Second noise draw (sensitivity, not a rescue): R1 - ridge +0.861 [0.000, +1.690], R1 - C\* +0.472 [+0.076, +0.862].
* Closed loops (3 pools per compound, 70 lines): unmeasured events loop-R1 2.25, loop-kNN 2.00, loop-gated 2.28, loop-ridge 1.33,
  two-stage 1.25, against the fixed design 2.64 (ridge) and 2.78 (R1). Inside loops R1 - ridge is +0.917 [+0.270, +1.605]
  and the loop update matters, but every loop is below the fixed A-optimal design (loop-R1 vs fixed R1 -0.528 [-1.193, +0.140]; on all pairs
  -1.167 [-2.219, -0.109]) because value-greedy acquisition measures the pairs it would have nominated. Total events over all
  pairs are all on measured pairs (R1 9.83, every arm's all-pair hits are measured-pair hits) and are not evidence of propagation.
* Absolute level: the best method nominates about 2.8-3.1 true unmeasured events per 32 slots (9-10%) against 32 for the oracle.

## 6. Reading and decision

* H1 not supported: R1 is not distinguishable from ridge-plus-feedback on U1 or U2, the development gain did not replicate, and the
  sign changes across folds (+0.82, +0.17, -0.46) and the size moves six-fold between the two noise draws.
* H2 not supported: a kNN analogue (a conventional method) gives the same result; the repair is a kNN prior plus ridge residual
  update, a standard hybrid. Conventional methods explain the gain that exists.
* H3 not supported: feedback identifies the failing compounds only weakly (AUC ≤ 0.63).
* Answer to the question: observed feedback does propagate to unmeasured pairs at pool cost (+1.06 over the prior), but no
  deterministic repair of that propagation produced a reproducible, practically meaningful additional gain, and the only
  identifiable headroom is a ceiling that no feedback-only diagnosis reached.
* **STOP at the first registered condition (P1 not practical).** No agent-generated program search, no LLM, no grammar search,
  no new foundation model or evaluator. Preserved: all registered NO-GO decisions.
* What would reopen it: an independent, physically costed measurement source with pool/plate mapping and non-synthetic repeated
  measurements, powered for a gain of ~0.7 per 64 compounds (this size resolves only that); until then the ridge-plus-feedback
  update, with kNN as the conventional comparator, stays the reference.

## 7. Reproduce

``python -B verify.py`` (freeze, wiring, δ\*, recomputation of RESULTS.json from `records/`); ``python -B -m pytest research/feedback_propagation_20261018``.
Amendment to `PROTOCOL.md` section 1.3: the first run of the old-loop audit mixed local and global indices (1.5% on probed pairs); see `DEVIATIONS.json`.

## 8. Clarification appended 2026-10-18 (hindsight diagnostics)

`D_hindsight` in `compare.py` selects between rules **per compound by squared error on unmeasured cells**, a model-fit
criterion that reads the hidden side. It is not terminal decision utility, so its "hindsight gate" (+0.528) and "best-of
rules" figures are not ceilings on nomination hits. Recomputed from the public records
(`research/acquisition_program_20261018/hindsight_clarification.py`): choosing, per complete campaign, the better of the
ridge and R1 nomination lists by realised hits gives **131 hits versus R1's 100 (ridge 95) across 36 campaigns**. This
is an unavailable hindsight diagnostic (it reads the outcome), never a policy; it shows that campaign-level list
variation is large relative to the mean difference. The registered decision (STOP at P1) is unchanged.
