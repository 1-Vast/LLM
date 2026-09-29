# Dual-core iteration: purchased-measurement context and selection-calibrated risk

**File summary**
- **Path:** `research/dual_core/README.md`
- **Purpose:** block 7 of 2026-09-27. The owner's brief asked to improve both MAESTRO cores through
  literature-grounded implementation and reproducible experiments, to repair the evaluation weaknesses
  first, and to report what the evidence supports.
- **Core points:**
  - **Evaluation repairs done first.** Registered folds are 0-4 (block 6 used 1-5 and missed fold 0);
    a programmatic checker now rejects that and five other failure modes. Every outcome-dependent
    component is refitted inside group-nested inner splits. Both protocols were frozen with code,
    data and split hashes before scoring.
  - **World model (E1): the keep rules pass, and the effect is small.** A quality-weighted
    compound-specific residual (`rrt_q`) beats block 6's `ridge_st` on compound discrimination
    (+0.007 SciPlex3, +0.020 L1000) without losing direction. It does **not** close the gap: plain
    additive transfer still discriminates better on L1000 (-0.071 [-0.113, -0.031]).
  - **Agent (E2): the central negative result.** Wrong-elimination forecasts are 1.6-2.0x too low on
    the actions the planner **selected**, reproducing E-CAL1 with new code. A cross-fitted Platt map
    fixes the aggregate ratio (0.94-1.07) but improves log loss only on L1000 and makes it worse on
    SciPlex3. No abstention threshold transfers across folds: distribution-free certification would
    need about 2,700-3,400 independent units on SciPlex3 (105 available) and about 1.5 million on
    L1000 (229 available).
  - **On selected actions the new world model gives no forecast gain** (every interval contains 0).
    Block 6's gain was measured over all design-planned targets, not over selected ones. This
    qualifies that result.
  - **No synergy claim.** The one positive interaction contrast is an artefact of threshold
    selection, explained in section 6.
  - **Nothing promoted.** No production default, no `src/` file and no earlier record changed.
- **Interfaces / data:** `splits.py`, `transfer.py`, `world2.py`, `ledger.py`, `agent.py`, `e1.py`,
  `e2.py`, `protocol.json`, `protocol_e2.json`, `test_dual_core.py`; outputs under
  `outputs/dual_core_20260927/`
- **Depends on:** `research/protocol_v2/` (v2.1 tasks, sealed view, runner, executor),
  `research/belief_planning/` (planner, reference world), `research/incontext_world/` (block 6 layer
  and metrics), `src/maestro/outcome.py` (evidence admission)

Spend: $0, 0 wells, no downloads. CPU only.

## 1. Literature and prior-art map

Each DOI was resolved through the bioRxiv and Crossref APIs on 2026-09-27; versions and journal
status are as those APIs report them. Repository licences are from the GitHub API.

| Work | DOI | Inspected version | Status found | Adopted / adapted / rejected |
|---|---|---|---|---|
| PRESAGE | 10.1101/2025.06.03.657653 | v1 (2025-06-06), the attached PDF | preprint only; CC-BY-NC-ND; repo `Genentech/PRESAGE`, no declared licence | **Adopted (evaluation):** two-stage effect-size then direction evaluation, centred cosine, phenocopy; attention over knowledge sources with globally fitted weights. **Rejected:** gene-embedding knowledge sources, which target genetic perturbations |
| State | 10.1101/2025.06.26.661135 | v2 (2025-07-10), the attached PDF | **now peer-reviewed: Cell 189(19):5914-5931.e20, 2026-09, doi:10.1016/j.cell.2026.07.052**; repos `ArcInstitute/state` (no declared licence), `cell-eval` (MIT) | **Adapted:** the learned cross-context transition, as a linear ridge map; Cell-Eval's Pearson delta and perturbation discrimination. **Rejected:** the set Transformer and pretrained weights (no local checkpoint of a version whose pretraining overlap with SciPlex3/L1000 we could verify) |
| Tahoe-x1 | 10.1101/2025.10.23.683759 | v1 (2025-10-23), the attached PDF | preprint; CC-BY; repo `tahoebio/tahoe-x1` (Apache-2.0) | **Adopted:** the null, global-mean, context-mean and perturbation-mean delta baselines, and the split-half noise-ceiling idea. **Rejected:** 3B-parameter pretraining (out of budget, and not required by the question) |
| Stack | 10.64898/2026.01.09.698608 | **v2 (2026-06-08)**, the attached PDF | preprint; CC-BY; repo `ArcInstitute/stack` (no declared licence) | **Adopted (as a rule, not an architecture):** measured responses act as an inference-time prompt, and a prompt must be available at query time. MAESTRO's version is stricter: a prompt must be *purchased* (section 4). **Rejected:** tabular attention over cell sets |
| SCALE | 10.64898/2026.03.17.712536 | v1 (2026-03-20) is the attached PDF; **v2 exists (2026-09-03)** and was not inspected | preprint; CC-BY | **Adopted:** its evaluation warnings (protocol parity; control-to-perturbed transport can be easier to optimise than to generalise). **Rejected:** the latent flow model |
| MultiFlow | 10.64898/2026.08.20.746112 | v1 (2026-08-25), the attached PDF | preprint; CC-BY; repo `liuq-lab/MultiFlow` (MIT) | **Rejected for now:** no paired second modality exists in these data. Missing modalities stay missing |

Searches that resolved specific design questions, with verified identifiers:

| Question | Source | What it settled |
|---|---|---|
| Is predicting a drug's profile in a new context from its profile elsewhere novel? | Hodos et al., PSB 2018, doi:10.1142/9789813235533_0004 (L1000, 978 x 2,130 x 71 tensor, 10.5% complete, kNN and tensor completion) | **No.** This is the same task family as A1/A2. Our transfer backbone is adaptation, not novelty; the report says so |
| Are these metrics vulnerable to systematic variation? | Systema, doi:10.1038/s41587-025-02777-8 | Yes; hence centred direction **and** discrimination as co-primary, and effect-size strata |
| How strong are simple baselines? | Ahlmann-Eltze et al., doi:10.1038/s41592-025-02772-6; PerturBench, arXiv:2408.10609 | Strong enough to be the comparison that matters; `additive` indeed still wins on identity (section 5) |
| Why are selected-action forecasts optimistic? | Smith & Winkler, doi:10.1287/mnsc.1050.0451 | The optimizer's curse; the reason E2 scores selected steps separately |
| How to control risk after adaptive selection? | Learn then Test, doi:10.1214/24-AOAS1998; Conformal Risk Control, arXiv:2208.02814 | P3's fixed-sequence Hoeffding-Bentkus construction |
| Can risk control be satisfied trivially? | Selective risk control with coverage floors (arXiv:2608.10893) | Yes: abstain always. Hence the post-hoc coverage floor in section 6 |
| Value of information and design | Rainforth et al., doi:10.1214/23-STS915 | Confirms the planner's expected-value framing; no change needed |
| Agent-side alternatives | IterPert (`Genentech/iterative-perturb-seq`), BioDiscoveryAgent (ICLR 2025), PerTurboAgent (doi:10.1101/2025.05.25.656020) | All select *which perturbation to screen next*; none certifies risk on the actions it selected. That gap is where this block's agent work sits |

Unverified: SCALE v2's changes, and any implementation detail of State, Stack or Tahoe-x1 beyond
their PDFs and repository metadata.

## 2. Data and compute inventory

| Item | Source / accession | Size | Units and controls | Exposure |
|---|---|---|---|---|
| SciPlex3 pseudobulk shifts, 2,473 genes, 16 conditions | Srivatsan et al., doi:10.1126/science.aax6234; prepared in `outputs/dynamic_world_model_20260926/prepared` and `biological_depth_20260926/prepared` | 66 MB prepared (2.4 GB raw h5ad local) | 188 compounds, 185 InChIKey connectivity units, 37 units per fold; split-half replicates; vehicle-well detection null | **Development, exposed** in every block since 2026-09-26, including block 6 on these folds |
| L1000 Level 5 landmark shifts, 978 genes, 8 conditions | GSE92742 (Subramanian et al., doi:10.1016/j.cell.2017.10.049); prepared in `outputs/sequence_audit_20260926/l1000/prepared` | 13 MB prepared (43 GB raw local) | 478 compounds, 335 identity/scaffold components, 67 units per fold; `cc_q75` as quality | **Development, exposed** since 2026-09-26 |
| MSigDB Hallmark v2024.1 | `data/external/msigdb` | 52 KB | 50 sets; those with >= 5 members in each feature space | Gene-set endpoints only |
| GSE70138 | opened in block 2 | - | - | **Not used here.** It was consumed and is not unopened external data |

No new dataset was added. The brief allows one complementary dataset; none was taken, because the
binding limitation found in section 6 is the number of independent units with wrong-elimination
events in the *decision* task, which a new expression dataset does not supply. This is a scope
reduction, disclosed rather than hidden.

**Compute.** 20 physical cores / 28 threads, 15.8 GB RAM (about 2-4 GB free during runs), RTX 4060
Laptop (8 GB) present but the installed PyTorch is a CPU-only build, so every experiment is CPU.
E1: 10 (dataset, fold) jobs, 4 workers, about 9 minutes wall, under 300 MB per worker. E2: 20 tasks,
4 workers, about 11 minutes wall, under 1 GB per worker. Identical grids and inner-CV budgets for
every arm.

## 3. Evaluation repairs (done before any new claim)

| Defect | Repair | Test |
|---|---|---|
| Block 6 used "folds 1-5"; the registered folds are 0-4, so fold 5 was empty and fold 0 was never held out | `splits.check_folds` rejects unregistered identifiers; `check_tasks` rejects an empty intended task; E1/E2 refuse to analyse unless all five folds have records | `test_split_checks_reject_known_failures` |
| Leave-one-unit-out in block 6 removed a reference from the kernel but not from the transition's means or principal components | `world2.StrictInContextWorld.fit_incontext` deals references into 4 inner folds **by independent unit** and refits, per inner fold, the transitions, the projected geometry, the pooled reading frequencies and the class and structural layers | `test_world2_empirical_bayes_is_strictly_nested` (spies on every transition fit and asserts each uses exactly the inner-training folds) |
| Unit versus scaffold conflation | The declared unit is named and checked: SciPlex3 InChIKey connectivity block, L1000 identity/scaffold component. 10 Murcko scaffolds (26 SciPlex3 compounds) span folds and are reported as a sensitivity stratum; no L1000 scaffold spans folds | `splits.manifest`, E1 stratum `scaffold_not_spanning` |
| Coverage and duplicates unchecked | `check_coverage` (each eligible compound held out exactly once) and `duplicated_records` run in every analysis | same test |
| Protocol and exposure | `protocol.json` (22:17:22) and `protocol_e2.json` (22:30:12) hold hypotheses, arms, endpoints, keep rules, grids, seeds and SHA-256 of code, prepared data and the split manifest. Both were written before the scores they govern. Post-hoc analyses are in separate files and labelled | - |
| Estimand | Unit mean is primary; item-weighted sensitivity is reported beside it. Cells, repeated conditions and candidate actions are never treated as replicates | - |

`outputs/dual_core_20260927/split_manifest.json` records fold assignment digests
(`ec6dde3f...`, `eb4b5ba5...`), the seven prepared-file hashes and the cross-fitting roles.

## 4. What was built

**World model.** `transfer.py` separates three information regimes and gives each its own models.

- A0 (no measured response of the query compound): zero, global mean, context mean, chemical
  Tanimoto kernel ridge, chemical kNN. Without a structure the chemical models fall back to the
  context mean.
- A1 (one purchased prompt): prompt copy, additive, `ridge_st` (block 6), and the new
  residual-retaining transfers. The diagnosis behind them: `ridge_st` recovers the shared direction
  and discards what is specific to the compound. So the part of the centred prompt outside the
  transition's subspace is added back, scaled by the prompt's measured replicate quality:

      y_hat = m_c + B (x - m_p) + gamma0 * q * P_perp (x - m_p)

  `gamma0` is fitted by least squares on inner out-of-fold residuals.
- A2 (several prompts): equal weight, the single most reliable prompt, or inverse inner-CV-error
  ("precision") weights.

**Agent.** Three pieces, each independently switchable.

- `ledger.PurchaseLedger` is the only route from a measurement to a prompt. `record` accepts only an
  executor result whose row exists, passed QC and matches this compound and condition, and otherwise
  logs `no_row`, `qc_failed` or `identity_mismatch`. `prompts` serves only conditions already
  executed before the decision point, refusing `target_outcome_leakage`, `future_measurement` and
  `unpurchased`. Each prompt carries compound, dataset, assay, condition, acquisition step, cost in
  days, row, batch, quality, detection and a SHA-256 of the shift.
- `world2.StrictInContextWorld` accepts `Prompt` objects only; a bare array raises. With `kappa = 0`,
  no prompt, or the target offered as its own prompt, it returns the reference world's forecast
  exactly. Forecasts keep `EvidenceKind.MODEL_PREDICTION`.
- `agent.abstaining(arm, threshold)` is the decision-policy change: stop and abstain when the
  chosen action's risk forecast exceeds a threshold. Because abstention only truncates a trajectory,
  a threshold's effect is computable exactly from one unconstrained run; 480 live replays confirmed
  the equivalence (480/480).

Predictions never become evidence: only the runner's `evidence_update` on a real executor result can
eliminate a hypothesis, and a test asserts that a prediction-kind record eliminates nothing.

## 5. E1: predictive validity by information regime

Unit means on detected targets, 95% unit-cluster bootstrap. SciPlex3: 153 units, 11,176 A1 items.
L1000: 109 units, 1,935 A1 items.

| Regime | Metric | Dataset | Best baseline | ridge_st (block 6) | **rrt_q (new)** | rrt_q - ridge_st |
|---|---|---|---|---|---|---|
| A1 | Discrimination | SciPlex3 | 0.075 (additive) | 0.041 | 0.048 | **+0.007 [+0.005, +0.009]** |
| A1 | Discrimination | L1000 | -0.249 (additive) | -0.340 | -0.320 | **+0.020 [+0.014, +0.027]** |
| A1 | Direction | SciPlex3 | 0.195 (prompt) | 0.368 | **0.371** | +0.003 [+0.002, +0.005] |
| A1 | Direction | L1000 | 0.187 (additive) | 0.370 | **0.377** | +0.007 [+0.005, +0.009] |
| A2 | Direction | SciPlex3 | 0.242 (prompt mean) | - | **0.431** (precision) | +0.003 [+0.003, +0.004] vs equal |
| A2 | Direction | L1000 | 0.234 (additive mean) | - | **0.437** (precision) | +0.0002 [0.000, +0.0005] vs equal |
| A0 | Direction | both | 0 (context mean) | - | **0.206 / 0.247** (chem ridge) | +0.206 / +0.247 vs context mean |

- **Both keep rules pass on both datasets**, so `rrt_q` became E2's transfer source and precision
  aggregation its multi-prompt rule.
- **The gains are small, and the identity gap is not closed.** `rrt_q` still loses to plain additive
  transfer on discrimination: -0.027 [-0.066, +0.016] on SciPlex3 (interval spans 0) and
  **-0.071 [-0.113, -0.031] on L1000**, and loses to prompt copying on L1000
  (-0.053 [-0.095, -0.011]). Ridge shrinkage remains the wrong tool for compound identity; the
  residual term recovers only part of it. Fitted `gamma0` medians are 0.12 (SciPlex3) and 0.19
  (L1000), and inner MSE falls by only 0.2-0.8%.
- **Quality weighting helps where quality varies:** `rrt_q - rrt_const` discrimination is
  +0.010 [+0.007, +0.015] on L1000 but +0.001 [-0.000, +0.002] on SciPlex3.
- **Controls behave.** Against `rrt_q`: a shuffled prompt is worse by 0.29-0.37 discrimination and
  0.31-0.44 direction; a wrong-target transition by 0.22-0.24 and 0.20-0.28.
- **Secondary endpoints agree and are tiny:** gene-set Spearman +0.003/+0.004, phenocopy@5
  +0.001/+0.004, MSE -0.00002/-0.028, effect AUROC 0.843/0.852 (best arm both datasets).
- **Where the gain sits.** Larger where the prompt was detected (+0.013 vs +0.001 SciPlex3;
  +0.047 vs +0.013 L1000) and for dose or time transfer rather than across cell lines. It survives
  item weighting (+0.011, +0.029) and restriction to compounds whose Murcko scaffold does not span
  folds (+0.007, +0.020).
- **A0 has no compound identity at all**: every arm's discrimination is negative
  (best -0.073 SciPlex3, -0.514 L1000). Without a purchased response, this model ranks conditions,
  not compounds.

## 6. E2: calibration after action selection

Both planners ran on all 20 protocol-v2.1 tasks through one ledger executor: 6,601 episodes each,
0 audit problems, 0 view violations. **The reference arm reproduced E-DATA1's registered `belief`
action sequences in 6,601 of 6,601 episodes**, so the comparison is anchored to the registered run.

### 6.1 The forecasts are optimistic on selected actions, as E-CAL1 found

| Dataset / planner | Selected steps | Wrong events | Observed / forecast, raw | After cross-fitted Platt | Log loss, calibrated - raw |
|---|---|---|---|---|---|
| SciPlex3 reference | 2,237 | 51 | **1.70 [0.95, 2.52]** | 1.05 [0.57, 1.61] | +0.006 [+0.001, +0.012] |
| SciPlex3 incontext | 2,237 | 44 | **1.57 [0.86, 2.37]** | 1.07 [0.57, 1.68] | +0.007 [+0.001, +0.013] |
| L1000 reference | 4,767 | 31 | **1.96 [0.96, 3.20]** | 0.94 [0.47, 1.53] | **-0.008 [-0.015, -0.002]** |
| L1000 incontext | 4,704 | 30 | **1.95 [0.95, 3.16]** | 0.95 [0.47, 1.52] | **-0.008 [-0.015, -0.002]** |

- E-CAL1's finding reproduces with new code and strict nesting: forecasts are about 1.6-2.0x too low
  on the actions the planner chose.
- **The calibration endpoint passes on L1000 and fails on SciPlex3.** Platt recalibration fixes the
  aggregate ratio everywhere, but sharpness gets worse on SciPlex3, where events are 2x denser.
  The Brier score barely moves (0.019 to 0.020; 0.0064 to 0.0063).
- A ratio near 1 is not calibration: the intervals are wide (0.47-1.68), and per tier the calibrated
  forecast overshoots on L1000 LT (9 observed against 13.7 forecast) while undershooting on T.

### 6.2 The new world model gives no gain on selected actions

Both world models scored the realised reading of each planner's own executed steps, truth branch:

| Dataset / planner | All steps | Steps with at least one prompt |
|---|---|---|
| SciPlex3 | -0.001 [-0.007, +0.005] | +0.001 [-0.022, +0.025] |
| L1000 | -0.003 [-0.009, +0.002] | -0.007 [-0.022, +0.006] |

Every interval contains 0. **This qualifies block 6's result:** its -0.018/-0.008 nat gain was
measured over all design-planned targets, most of which a planner never buys. On the steps a planner
actually selects, the in-context layer adds nothing measurable here.

### 6.3 No abstention policy controls risk on held-out units

| Dataset / planner | Policy | Wrong among decided | Coverage | Abstained | P - P0 wrong among decided |
|---|---|---|---|---|---|
| SciPlex3 reference | P0 | 0.049 [0.027, 0.076] | 0.634 | 0 | - |
| SciPlex3 reference | P2 | 0.050 [0.027, 0.077] | 0.602 | 0.070 | +0.001 [-0.003, +0.003] |
| SciPlex3 incontext | P0 | 0.042 [0.022, 0.067] | 0.625 | 0 | - |
| SciPlex3 incontext | P2 | 0.043 [0.022, 0.067] | 0.624 | 0.013 | +0.000 [0.000, +0.000] |
| L1000 reference | P0 | 0.047 [0.024, 0.079] | 0.141 | 0 | - |
| L1000 reference | P2 | **0.059 [0.029, 0.101]** | 0.099 | 0.126 | +0.012 [-0.003, +0.032] |
| both | P3 (Learn-then-Test) | 0 | **0** | 0.55-0.99 | vacuous |

- **The agent endpoint fails.** No P2 - P0 interval is below 0, and on L1000 the held-out rate rises
  above alpha.
- **P3 is degenerate.** Learn-then-Test certifies only "abstain always", which satisfies risk control
  vacuously (a known failure mode; hence the coverage-floor literature).
- **The trade-off does exist.** The risk-coverage curve (all folds pooled) shows that abstaining at a
  threshold of 0.01 nearly halves the SciPlex3 wrong rate: 0.026 (reference) or 0.024 (incontext) at
  coverage 0.33-0.34, against 0.049/0.042 at full coverage. The registered alpha is 0.05 -- the
  validator's own maximum wrong-elimination rate -- and both planners already satisfy it at full
  coverage, so the frozen policy correctly chose not to abstain.
- **Post hoc, at a binding target it collapses.** At alpha = 0.025 with a 50% coverage floor, the
  selected thresholds fall to near-total abstention and the held-out rate *rises* to 0.058-0.085.
  The threshold does not transfer across folds.
- **Post hoc, the reason is power.** Certifying the best low-risk threshold at delta = 0.1 would need
  about 3,369 units (SciPlex3 reference) or 2,733 (incontext); 105 exist. On L1000, where the rate
  sits exactly at alpha, about 1.5 million units would be needed; 229 exist. The binding limitation
  is the number of independent units carrying wrong-elimination events (44-51 on SciPlex3, 30-31 on
  L1000), not the model.

### 6.4 No synergy claim

The 2x2 (world model x policy) contrast on identical episodes is positive for SciPlex3 coverage:
+0.031 [+0.020, +0.045]. **It is an artefact and is not claimed as synergy.** Its whole mechanism is
that cross-fitted threshold selection picked different thresholds for the two world models (the
in-context arm selected "no abstention" in 4 of 5 folds, the reference arm in 2 of 5), so the
contrast measures threshold instability, not an interaction between the cores. The wrong-elimination
interaction is +0.001 [0.000, +0.004], which is not an improvement either. On L1000 both contrasts
are 0.000. Under the frozen rule, synergy is not established.

Decision outcomes are descriptive only, because E-DATA1's registered failure rule stops
planner-superiority work on these data: SciPlex3 correct 0.600 (reference) against 0.597
(incontext), wrong 0.034 against 0.029, identical measurement cost 1.48.

## 7. Tests

`research/dual_core/test_dual_core.py` (10 tests): split checks including the fold-1-5 regression;
inner folds never split a unit; `rrt` recovers a residual when one exists (gamma about 1.0) and
ignores noise (gamma < 0.2); with q = 0, `rrt_q` is exactly `ridge_st`; chemical models fall back
without a structure; aggregation weights form a distribution; the ledger refuses target, future,
unpurchased, QC-failed and identity-mismatched prompts; `world2` refuses held-out reference
qualities and bare arrays and nests the reference world exactly; the empirical-Bayes fit uses exactly
the inner-training folds; a prediction-kind record eliminates nothing; truncation equals the
abstention rule.

## 8. Contribution statement

| Layer | Claim |
|---|---|
| **Engineering correctness** | Established. The purchased-prompt ledger, strict nested fitting, split integrity checks, prediction-evidence separation and exact abstention-truncation equivalence (480/480) are tested, and the reference arm reproduces the registered run exactly |
| **Predictive improvement** | Small but real on both datasets under strict nesting: discrimination +0.007 / +0.020, direction +0.003 / +0.007, with every control behaving. It does not close the gap to plain additive transfer on compound identity |
| **Calibration improvement** | Partial and dataset-specific. Aggregate ratio corrected on both; log loss improved on L1000, made worse on SciPlex3. The new world model adds nothing on selected actions |
| **Decision improvement** | **None demonstrated.** No abstention policy reduced held-out wrong eliminations; the registered E-DATA1 rule blocks superiority claims; decision outcomes are descriptive |
| **Methodological originality** | Low for the transfer model: Hodos et al. 2018 already predicts a drug's profile in an unmeasured context from its measured ones. The defensible contribution is the evaluation and agent construction: regime separation (A0/A1/A2) with a purchased-measurement ledger, risk evaluated on selected actions with an exact truncation equivalence, and a quantified power requirement for certifying such risk. Honest framing: adaptation and validation, plus a negative result |

## 9. Recommendation

- **Nothing is ready for a default path.** `rrt_q` passes its predictive keep rule, but promotion
  also requires acceptable risk on selected actions, which E2 did not show.
- **Keep as research:** `rrt_q` as the transfer source, precision aggregation for several prompts,
  the ledger, and the abstention policy as an opt-in arm.
- **The next experiment is a power problem, not a modelling one.** Certifying a risk threshold needs
  about 25-30x more independent units carrying wrong-elimination events than these tasks have. Either
  a decision task with far more units, or a target error rate loose enough to certify, would be
  required. Adding another expression dataset does not supply this.
- **If a calibrated risk gate is wanted now,** the only defensible form on this evidence is the
  descriptive risk-coverage curve of section 6.3 with its wide intervals, not a certified threshold.

## 10. Reproduction

```bash
python -m pytest research/dual_core -q -p no:cacheprovider
python -m research.dual_core.splits                      # split manifest and hashes
python -m research.dual_core.e1 run --workers 4          # write-once per (dataset, fold)
python -m research.dual_core.e1 analyse
python -m research.dual_core.e2 run --workers 4          # write-once per task
python -m research.dual_core.e2 analyse
python -m research.dual_core.e2 posthoc                  # post hoc, binding alpha
```

Outputs in `outputs/dual_core_20260927/`: `split_manifest.json`;
`e1/{dataset}_{A0,A1,A2}_fold{n}.parquet`, `e1/{dataset}_fits_fold{n}.json.gz`, `e1/analysis.json`;
`e2/tasks/*.{traces,cross}.jsonl.gz` and `*.json`, `e2/analysis.json`,
`e2/reference_reproduction.json`, `e2/posthoc_binding_alpha.json`, `e2/posthoc_power.json`.

## 11. Deviations and disclosures

- **Both protocols were frozen before the scores they govern.** `protocol_e2.json` was written after
  E1's analysis was read, because E1's keep rules choose E2's world model; it says so, and it was
  written before any E2 score.
- **Execution-only smoke runs** preceded each freeze (L1000 fold 0 for E1; L1000 T fold 1 and
  SciPlex3 A fold 2 for E2). They printed row counts, problem counts, live-check matches and timing.
  No metric was computed or read from them.
- **Post-hoc, in separate files and labelled:** item-weighted sensitivities inside E1's analysis, the
  binding-alpha repeat with a coverage floor, the power calculation, and the fitted-gamma summary.
- **The A2 keep rule passed on L1000 with a difference of +0.0002 [0.0000, +0.0005]**, which is
  statistically above 0 and practically nil. It is reported as such rather than as a benefit.
- **`rrt_q` is not a fix for identity.** Additive transfer still discriminates better on L1000. Any
  future use should include additive as a live candidate, not a baseline.
- **P3's guarantee assumes exchangeable units.** Episodes within a unit are correlated; the unit-level
  losses are the exchangeable objects. This is why every estimate is unit-level.
- **Scope reduction, disclosed:** the population backend of `src/virtual_cell/population_flow.py`
  (the Codex pilot of the same day) was **not** re-evaluated in this block. Its re-evaluation was
  planned, scoped and then dropped for time; the existing pilot's own limits stand unchanged, and
  none of this block's code depends on it.
- **Fold numbering.** Block 6's E-WM1/E-WM2 records for folds 1-4 plus its later fold-0 records are
  preserved unchanged. This block's runs use 0-4 from the start.
- **No `src/`, `tools/`, production default or earlier record was changed.** Nothing was committed.
