# Report: contract repair, access trace and what explains the fixed-seed benefit (`seed_attribution_20261017`)

**Status: DEVELOPMENT on exposed data.** The PRISM 19Q4 target strata were opened by
`program_revision_20261017`; a same-screen stratum is not an independent confirmation, and the 247 lines
are 21 lineage clusters, not 247 independent domains. Nothing in the three predecessor studies was edited
(`verify.py` re-checks their freeze digests). No sealed tier was opened, nothing was pushed, no LLM was called.

**Run.**

* `PROTOCOL.md`, the corrected predictor, the replay contract, the 20 null libraries, the runner, the
  analysis and the tests were frozen before the run (`FREEZE.json`). Smoke runs on 12 lines checked code
  only.
* In frozen mode the runner reproduces the previous implementation's strong and seed hits and unknown
  nominations at I1, I2 and the exploit-first campaign to 1e-9 (parity record in `RESULTS.json`).
* `RESULTS.json` was written once by `analyse.py` from `records/units.json`; `verify.py` recomputes it and
  prints VERIFIED. 19 synthetic tests pass (`test_science.py`).
* Cost: 0 wells, $0, local compute 147 s for the run (about 18 min for the access audit).

## 1. Is the evaluation contract one contract?

No. `AUDIT_CONTRACT.json` finds the following in `program_revision_20261017`:

| Defect | Size |
|---|---|
| The score reference was `(X2+X3)/2`, NaN when a pair has one replicate; labels use the mean of the available replicates. | 23.2% of source pairs have one replicate, 15.2% none; 27.3% of known source pairs rest on one replicate. 5,942 of 18,679 future hits (31.8%) rest on one replicate. |
| Frozen thresholds were undefined for 100 source drugs. The contract defines all but 24 (no known source pair: refused by name, never nominated). | 76 drugs restored; they carry 4.8% of future hits. |
| Thresholds of drugs defined in both versions differ. | 527 of 866 drugs (absolute shift up to 0.46); 1,777 future labels would flip under the old threshold. |
| The predictive variance of a library arm used its in-sample fit. | Out-of-sample variance changes the in-scope variance by about 1% (standardised squared error 1.058 frozen, 1.042 cross-fitted, 1.034 base); it does not change a decision. |
| The Gaussian crossing score was read as a probability. | It ranks well (AUROC 0.834 on known pairs) and is close to the observed rate in the top deciles (0.381 against 0.382) but under-predicts the lowest deciles about tenfold (0.0002 against 0.0021). The sign condition fails for 0.17% of crossing pairs. It is **not** shown to be a calibrated probability of the complete qualified-hit event, and this report never uses it as one. |
| The strong-model fit cache was keyed by lines, settings and shape, not by the data. | A relabelled domain reused the stale fit (`AUDIT_ACCESS.json`, stale-cache demo). Repaired: the key now includes the data. |

**Consequence for the reported decisions** (seed library minus strong model, 247 future lines, single-shot):

| Layer | Frozen contract | Repaired contract | Repaired, availability-weighted nomination |
|---|---|---|---|
| I2 (8 probe wells) | +0.211 [+0.097, +0.340] | +0.117 [-0.026, +0.248] | +0.166 [+0.039, +0.282] |
| I1 (DNA panel) | +0.445 [+0.084, +0.921] | +0.283 [-0.065, +0.699] | +0.385 [+0.038, +0.809] |
| Exploit-first campaign (28 wells) | +0.437 [+0.041, +0.889] | +0.356 [-0.088, +0.856] | — |

At I2 the median/threshold change and the restoration of the 76 drugs each account for about 0.05 of the
shrinkage (0.166 and 0.162 when applied alone). The restored drugs are mostly unknown pairs (62.7% unknown,
hit rate 0.21 among their known pairs against 0.54 otherwise). Point estimates stay positive; the lower bounds cross zero. The frozen "CONFIRMED (unadjusted)"
labels do not survive the repair at any layer without an availability weight, and the weight is a
sensitivity choice, not a registered primary.

## 2. Which development-query outcomes entered the development bench?

`AUDIT_ACCESS.json` (structural trace plus perturbation of three projects, bone, lung and uterus, on the
frozen and on a masked bench, at I1 and I2):

* **Every fold of the frozen bench trains on the reserved query lines**: each fold's training set holds
  74-101 of the 103 query lines. The masked bench trains on the 128 historical lines only and its folds
  contain no query line.
* **Perturbing query outcomes changes the frozen bench** in the quantities that decide proposals and
  selection: the fold base means (up to 3.1 units), the cross-fitted residuals (up to 12.2), the
  out-of-sample variance (up to 4.8), the probe design (none of the 8 probes is shared at I2), the committed
  digests, the proposals and the diagnosis. Scrambling 2-29 query lines changes 57-100% of the nominations of
  a project's folds, and 60-88% (I1) or 65-70% (I2) of a project's own nominations through the thresholds and
  replicate variance alone. The masked bench is **exactly invariant** (every quantity, proposal and distinguishing pair identical) in
  all six project-by-condition perturbations.
* **Consequence for quoted numbers.** On the 103 development query lines the seed library obtains 4.41 hits
  per line on the frozen bench and 3.87 on the masked bench at I2 (2.84 against 2.94 at I1). The empty
  library moves the same way (4.35 against 3.80), so the inflation is common to the arms; the
  library-minus-empty contrast is 0.058 against 0.078 hits per line at I2 and 0.049 against 0.146 at I1.
  The absolute development numbers, and the development arena that the revision loop optimised on, were
  not prospective. The frozen and masked diagnoses share only 20-60% of their top-10 clusters at I1 and
  0-40% at I2.
* **Legitimate offline model selection** (fitting a corrector or library on source lines and comparing
  held-out source folds) is kept and is not what the frozen bench did wrong. **Prospective-style
  acquisition** is only `replay.MaskedBench`: the reserved pool is masked before every upstream fit and
  `reveal` is the only costed access. A measurement edit on the masked bench refuses with
  `MEASURE_EDIT_NEEDS_PURCHASE`.

### Cost units (`COST_UNITS.json`)

Six accounts are no longer one number: shared historical data (966 source drugs x 231 source lines,
inherited by every arm), incremental research (the frozen convention is 2 wells per newly revealed pair
and is a logical charge), deployment (28 wells and one assay unit per line), bundles and rounds
(turnaround), compute/API/curation, and logical replay queries (one pair, not one plate well). A PRISM
well measures every line of a pool (6-21 source lines), so the development "wells" of the earlier report
are an upper bound on physical effort; the retained trajectories keep counts, not pairs, so only bounds
are reported. Deployment wells and rounds are identical across all arms of this study.

## 3. What explains the fixed-seed benefit?

Corrected contract, 247 future lines, 21 lineage clusters, hits per line (unknown is never a hit).

| Layer | Strong (A) | Seed (B) | Shared-only (D) | 20 null libraries (mean; range) | Global ridge on seed features (C1) | Per-drug ridge (C2) | Pooled GBM (C3) |
|---|---|---|---|---|---|---|---|
| Policy (exploit-first, 28 wells) | 4.514 | 4.870 | 4.838 | 4.523 (4.466-4.603) | 4.874 | 4.781 | 4.583 |
| I2 | 4.202 | 4.320 | 4.296 | 4.179 (4.154-4.198) | 4.312 | 4.243 | 4.190 |
| I1 | 2.923 | 3.206 | 3.069 | 2.896 (2.850-2.923) | 3.040 | 3.117 | 2.947 |

**Registered primary family (Holm over three).** The seed signal does **not** survive.

| Test | Mean [95% CI] | Holm p | Result |
|---|---|---|---|
| P1 policy, B - A | +0.356 [-0.088, +0.856] | 0.31 | NOT_CONFIRMED |
| P2 I2, B - A | +0.117 [-0.026, +0.248] | 0.29 | NOT_CONFIRMED |
| P3 I1, B - A | +0.283 [-0.065, +0.699] | 0.31 | NOT_CONFIRMED |

The registered consequence applies: the seed signal is not confirmed under the corrected contract at the
complete-policy layer, and no revision study follows.

**Attribution (policy layer unless stated; unadjusted unless a Holm value is given).**

| Question | Contrast | Mean [95% CI] | Reading |
|---|---|---|---|
| Biological correspondence | B - mean(20 nulls) | policy +0.348 [-0.063, +0.826]; I2 +0.140 [+0.001, +0.273]; I1 +0.311 [-0.025, +0.730] | The seed exceeds **every** null at every layer (exact permutation p 1/21 = 0.048, the smallest possible). Registered reading: supported at I2 only (lower bound +0.001, Holm p 0.22), not established at policy or I1. |
| Capacity alone | mean(nulls) - A | +0.009 / -0.023 / -0.027 | None. Equal capacity and 4-20% **more** observed cell support than the seed give no gain. |
| Per-drug loadings | B - D | +0.032 [-0.194, +0.231] (policy); +0.024 [-0.039, +0.088] (I2) | Not distinguishable; equivalent within margin at I2. |
| Shared structure | D - A | +0.324 [+0.059, +0.638] (policy); +0.093 [0.000, +0.179] (I2) | Shared loadings carry most of the policy-layer effect (Holm p 0.069). |
| Uncertainty estimation | B with the seed variance only, minus A | I2 +0.012 [-0.006, +0.034]; I1 +0.004 [-0.012, +0.019] | None. The mean carries the gain (mean-only +0.113 at I2 against full +0.117). |
| Conventional counterpart | B - C1 (global ridge on the same ten scope-by-gate products) | -0.004 [-0.198, +0.166] (policy); +0.008 [-0.051, +0.075] (I2) | The hierarchical library does no better than a ridge on the same ten interaction features. C1 - A is +0.360 [+0.068, +0.714] (policy), +0.109 [+0.009, +0.210] (I2). |
| Learn the pairing from data | B - C1x (all 72 scope-by-gate products) | +0.263 [-0.099, +0.668] | A ridge given all 72 products gains +0.093 [-0.018, +0.191]: it did not find the seed's pairings. |
| Other conventional | B - C3 pooled GBM | I2 +0.130 [+0.004, +0.266] | The GBM on the same flags gains nothing. |

**Reading.** The benefit, to the extent it exists, is carried by *which* ten scope-by-gate interactions
are present (the textbook pairings), entered as a mean correction, and is matched by a plain ridge that
receives the same ten features. It is not explained by extra capacity, by per-drug calibration, or by
uncertainty estimation, and no conventional model reproduces it without being given the pairings. That
supports "the information is in the pairings"; it does not support "the library architecture adds
something", and it does not by itself show the pairings are biologically right (a permuted pairing can be
accidentally informative, which would understate the correspondence effect).

**Support and transport.**

* **Gate-positive and gate-negative lines.** 225 of 247 lines are positive for at least one seed gate.
  Policy-layer gain: +0.422 [-0.051, +0.935] on gate-positive lines (108% of the total gain) and -0.318
  [-0.500, -0.048] on the 22 gate-negative lines (8 lineages), where the seed library costs hits. By gene:
  BRAF-positive lines (39) +1.59, NRAS-positive (13) +1.08, KRAS-positive (62) -0.13, TP53-positive (167)
  +0.27; EGFR-positive lines (4) cannot be scored.
* **Nominations that differ.** 3.02 of 10 policy nominations per line differ between A and B (206 of 247 lines).
  B-only nominations yield 0.365 hits each against 0.247 for A-only, with equal unknown rates (0.21 and
  0.22). The 272 B-only hits fall in 87 distinct structure groups (largest 7.4%), so the gain is not a
  single scaffold.
* **Lineage support.** The policy gain is concentrated: skin (39 lines) contributes 82% of it
  (+1.85 hits per line) and urinary tract another +0.96; only 5 of 21 lineages are positive and 9 negative.
  Leaving out one lineage moves the pooled mean between +0.08 and +0.44. With equal lineage weights the
  contrast is +0.057 [-0.175, +0.267]; by stratum it is +0.015 on the 67 future-line cases and +0.483 on the
  180 future-lineage cases (7 clusters). At I2 it is more evenly spread (10 positive, 5 negative lineages;
  skin 59%; equal-lineage mean +0.100 [+0.023, +0.176]).
* **Target-mixture standardisation** to equal lineage weights is shown above; equal stratum weights give
  +0.249 (policy), +0.095 (I2), +0.213 (I1). Source-gate-mixture standardisation gives +0.358
  [-0.087, +0.838] (policy).
* **Unknown outcomes.** Treating unknown as a miss is the registered reading. Unknown per line is
  unchanged (-0.020 [-0.228, +0.172]); the hit rate among known pairs rises by 0.032 [+0.001, +0.062].
  Filling unknown pairs at the pooled hit rate (an optimistic upper bound) gives +0.455 [+0.082, +0.855]
  and availability-weighted nomination +0.267 [-0.075, +0.613].
* **Cost and rounds** are identical (28 wells, 3 rounds per line); arms differ in compute (A 1 s,
  B 2 s, C3 34 s) and in curation (ten authored programs for B and D, none for E, a tuning grid for C).

**Precision.** With 21 clusters the policy-layer interval is about +-0.47, so a gain of +0.36 is neither
confirmed nor excluded, and the smaller attribution contrasts are mostly inconclusive. Absence of
distinction is reported as "not established", never as a null.

## 4. Remaining learnable opportunity (Part 4)

**Not run.** The registered trigger was a primary test with a mean of at least 0.10 and a positive lower
bound. None has one (lower bounds -0.088, -0.026, -0.065). A frozen small-menu hindsight diagnostic, a
nested conventional prediction of useful choices and the four-way classification (insufficient headroom,
insufficient information, unsupported target conditions, algorithm failure) would only restate noise
here, and are not produced. No automatic revision rerun was started.

## 5. What this does not show

* Any independent confirmation: the screen, the lines and the lineages are the ones the earlier study
  opened.
* That revision, stepwise search or an LLM adds anything: none was rerun; the earlier null (editable
  minus fixed library 0.000) stands, with its numbers now on a corrected contract only for the fixed
  library.
* That the seed pairings are biologically correct: a ridge on the same features does equally well, and
  the effect is concentrated in BRAF/NRAS-positive skin lines.
* That programs learned from an empty start fail: the seed-arm ablations do not cover every empty-start
  program.
* Anything about the lower-scoring part of the ranking: the Gaussian score is a ranking score here.

## 6. Decision

* Retain the fixed ten-program seed library as an **optional, scoped component with a labelled
  exploratory effect**: positive point estimates (+0.12 to +0.36), no confirmed lower bound, concentrated
  in BRAF/NRAS-mutant skin lines, harmful on gate-negative lines.
* The strongest simple comparator for any later library claim is a **ridge on the same ten scope-by-gate
  features**, not the strong model alone.
* No further revision, LLM proposal or grammar search on this arena. The development arena's absolute
  numbers are not prospective (section 2); any later study must use `replay.MaskedBench`.
