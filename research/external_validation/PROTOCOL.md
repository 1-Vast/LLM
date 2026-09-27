# External-validation protocol

**Registered:** 2026-09-27, before any arm new to this block was run on real data. The
machine-readable version is [`protocol.json`](protocol.json); `freeze.json` records the digests of
this file, the code, the data and the manifests at the moment of registration.

## 1. The claim under test

On a completely unseen study, with frozen policies, thresholds, prompts, retrieval libraries,
calibration and baselines, MAESTRO reaches better terminal decisions at equal or lower experimental
cost, within a pre-registered wrong-elimination risk limit.

Decision quality is the primary endpoint. Profile cosine, MSE, correlation, Brier score and ECE
are diagnostics. A predictor that improves them but does not change actions for the better has no
acquisition value.

## 2. What data can and cannot show

| Study | Role | Why |
|---|---|---|
| SciPlex3, tiers A and B | development | every acquisition policy since block 2 of 2026-09-26 was diagnosed or designed on it |
| L1000 Phase I (`subset48`), tiers LT and T | development | it validated the block-4 fallback, then informed the sparse-value design |
| external study | none registered | [`manifests/external_candidates.json`](manifests/external_candidates.json) |

Every result in this block is therefore an **internal replay**. It can reject a policy, rank it
against simple baselines, and fix the comparator and thresholds for a later external test. It can
never pass gate G5 (external replication).

## 3. The firewall

- **Sealed policy view.** Each fold's arms see a copy of the data from which every held-out
  compound's profiles, QC fields, detection flags and mechanism annotations have been removed. The
  training reference tables, the validator calibration and the virtual cell are built from training
  rows only.
- **Executor.** The executor keeps the real data. It returns the registered reading of the bought
  measurement to the runner, and its profile to the episode's visible-evidence store, nothing else.
- **Vault.** An external study's outcomes live in a `Vault` that opens once, only when every frozen
  digest verifies and the study's manifest digest is registered in the freeze. After it opens, any
  function marked as a fitting step (reference-model construction, ridge fitting, preparation)
  refuses to run in that process. Everything that is fitted must be prepared before the vault opens.
- **Manifests.** Dataset manifests (source digests, study version, licence, compounds with canonical
  structures, groups, scaffolds, contexts, and plate, batch and replicate clusters; never labels),
  split manifests (folds and boundary reports) and episode manifests (menu, budget, QC rule,
  episodes; never truth) are schema-checked.
- **Hypothesis ontology.** External contrasts come only from the development-frozen
  [`hypothesis_ontology.json`](manifests/hypothesis_ontology.json). The external metadata manifest
  cannot add, remove or relabel hypotheses, and its episode builder accepts no truth or mechanism
  field. The evaluator may join the held-out label only after an arm has returned.
- **Boundaries.** The external boundary must share no compound, group, scaffold or batch. Internal
  folds must share no compound or group. They do share plates and batches (nuclear hashing and
  L1000 plating put many compounds on one plate), which is recorded rather than hidden.

## 4. Shared rules

All arms run through `sequence_audit.policies.run_matched`:
- at most two measurements;
- exposure time never earlier than any executed action, failed ones included;
- no repeated action;
- a 16 assay-day budget (SciPlex3) or 12 (L1000);
- a QC failure is charged and read as no evidence, and the episode continues;
- the episode stops at the first elimination.

Every record carries the menus the arm was offered, and they are checked against the legal menu
recomputed from the executed steps.

## 5. Arms

| Rung | Arm | Definition |
|---|---|---|
| 1 | `defer_floor` | never measures |
| 2 | `random_legal` | uniform legal choice, seeded per episode and step |
| 3 | `fixed` | the registered early-to-late sequence, then stop |
| 4 | `cost_only` | budgeted selector without priorities |
| 5 | `marginal_only` | sparse-value planner without conditional response distributions, price 0.02 |
| 6 | `retrieval` | forecasts from the five training references per hypothesis nearest the measured profile; one-step value |
| 7 | `magnitude` | budgeted selector with the virtual cell's predicted magnitude as priority |
| 7c | `magnitude_permuted` | priorities from another held-out compound (control) |
| 8 | `ridge` | structure-to-profile ridge; the predicted profile read by the registered validator |
| 9 | `info_gain` | maximum mutual information between hypothesis and reading |
| 10 | `myopic_edv` | one-step expected decision value, P(correct) − 2 P(wrong) − price; **mandatory comparator** |
| 11 | `maestro_masked` | the runtime opt-in selector (`select_discriminating_action`), virtual-cell channel masked |
| 12 | `maestro_vc` | the same selector with the virtual cell's priorities: **primary candidate** |
| 12c | `maestro_vc_permuted` | priorities from another held-out compound (control) |
| 13 | `maestro_vc_jev` | registered, not executed: `provider_arm_reserved_for_external_study` |
| 14 | `oracle` | reads hidden results; upper bound only |
| R | `production_default` | the shipped power-aware expected-coverage selector |
| R | `sparse_two_step` | the sparse-value two-step planner, price 0.02 |

`myopic_edv` and `sparse_two_step` are also run at prices 0, 0.005, 0.01, 0.05, 0.1 and 0.2, for the
cost curves. The virtual cell is the frozen structure-kNN rule: the five nearest training compounds
by Tanimoto, a weighted mean of their measured profiles, 24 h conditions only.

**Why the Jev arm is not run here.** Block 2 already measured Jev's choices on these SciPlex3
episodes: it follows the top card, and defers without cards. A full development replay would need
about 10^4 provider calls. On an external study it runs on a pre-registered random sample of 200
episodes under the provider ceiling.

## 6. Endpoints and thresholds

The scientific decision uses separate endpoints, never the utility scalar alone:

| Endpoint | Definition |
|---|---|
| Effectiveness | correct-decision rate per episode |
| Safety | wrong-risk: wrong-elimination rate per episode |
| Cost | measurements and assay-days per episode |

**Secondary endpoints:**
- coverage, selective risk and deferral;
- wells, compute seconds and provider USD;
- the +1/−2 utility, used as an internal objective only;
- risk–coverage, correct–cost and wrong–cost curves;
- the Pareto frontier.

| Threshold | Value |
|---|---|
| wrong-risk cap (upper 95% bound) | 0.05 |
| wrong-risk non-inferiority margin | 0.005 |
| minimum practically important effect, correct rate | 0.02 |
| correct-rate non-inferiority margin | 0.01 |
| cost non-inferiority margin | 0.10 measurements, 0.5 assay-days |
| cost superiority | 0.10 measurements fewer |

**Derivation of the thresholds:**
- The wrong-risk margin is a quarter of the minimum effect. The worst admissible net gain is then
  0.02 − 2 × 0.005 = 0.01 utility.
- The cap sits just below the highest wrong rate of any accepted development arm: SciPlex3 tier-A
  fixed, 0.057.

## 7. Comparator, inference and multiplicity

- **Strongest baseline.** Over rungs 1–10, the arm with the highest correct rate among those whose
  wrong rate is at most the cap. Ties go to fewer measurements, then to the name.
  - Internally it is selected on the same data. That is optimistic for the baseline, so
    conservative for MAESTRO.
  - For an external study it is frozen from these development results in `baseline_selection.json`.
- **Intervals.** 2,000 paired cluster-bootstrap draws (seed 20260927), resampling independent units:
  the SciPlex3 skeleton and the L1000 component.
  - Sensitivity clusters: compound, Murcko scaffold and plate cohort (SciPlex3); identity and
    batch cohort (L1000).
- **Multiplicity:**
  - **Primary:** `maestro_vc` against the strongest baseline per tier. The gates are tested in a
    fixed order, each at two-sided 95%.
  - **Secondary candidates:** `production_default`, `maestro_masked` and `sparse_two_step`, each
    against the same comparator with Bonferroni 98.75% intervals.
  - **Ladder:** every other comparison is descriptive.

## 8. Gates and status

| Gate | Passes when |
|---|---|
| G1 integrity | the freeze verifies; zero rule violations; identical offered menus; a clean sealed view; no compound or group crossing a fold |
| G2 safety | the candidate's wrong-risk upper bound ≤ 0.05, and the upper bound of its difference from the comparator ≤ 0.005 |
| G3 effectiveness | the lower bound of the correct-rate difference > −0.01; *superior* when the lower bound > 0 and the point estimate ≥ 0.02 |
| G4 benefit | superior with no higher cost (measurements ≤ +0.10, assay-days ≤ +0.5), or cheaper (upper bound < 0 and point ≤ −0.10) while non-inferior |
| G5 external replication | G1–G4 on an `external_test` study under a verified freeze and a single vault opening |
| G6 virtual cell | `maestro_vc` beats `maestro_masked` and `maestro_vc_permuted` on correct rate (lower bound > 0) without more than 0.005 extra wrong-risk |
| G7 prospective | new measurements confirm G2–G4; only then may a policy become a default candidate |

| Status | When |
|---|---|
| REJECTED | G1 fails; or the wrong-risk lower bound > cap; or the wrong-difference lower bound > 0.005; or the correct-difference upper bound < −0.01 |
| INCONCLUSIVE | no reject condition holds, but G2, G3 or G4 does not pass |
| SHADOW | G1–G4 pass on development data only (opt-in, logged, not default) |
| DEFAULT_CANDIDATE | G1–G6 pass, including G5; G7 is still required before any default changes |

The overall status is the worst across the four tiers. No status is ever raised by a secondary
metric, a prediction metric or calibration alone.

## 9. Virtual-cell ablation and calibration audit

**Ablation pairs:**
- `maestro_vc` against `maestro_masked` and against `maestro_vc_permuted`;
- `magnitude` against `cost_only` (the same selector with the channel masked) and against
  `magnitude_permuted`.

**Reported for each pair:**
- first-step and any-step switch rates;
- correct, wrong, measurement and assay-day differences on the switched episodes and overall.

**Prediction diagnostics** (profile cosine and magnitude of the virtual cell and the ridge, each
against the training-target mean) are computed outside the policy path and reported as
diagnostics.

**Calibration** is reported for the forecasts at chosen actions:
- the sparse-value model (`myopic_edv`, `sparse_two_step`);
- the reference cards (`maestro_vc`).

It is stratified by:
- cell context;
- action;
- support;
- scaffold novelty;
- batch or plate cohort;
- response magnitude;
- forecast basis.

Metrics:
- calibration intercept and slope;
- Brier score and log loss;
- ECE and reliability bins;
- Wilson bounds on realized wrong readings.

These are diagnostics. No threshold is chosen from them.

## 10. Procedure when an external study arrives

1. The owner approves the download (see the candidate audit for files and sizes); SHA-512 sums
   are verified.
2. Dataset and split manifests are written from metadata alone. Compounds and scaffolds in the
   development reference library are excluded, and the batch boundary is checked.
3. Any representation change is pre-registered and applied to development first; the ladder is
   re-run on development, and `baseline_selection.json` and every digest are frozen.
4. All fitted components are prepared, then the vault opens once. The locked replay runs with role
   `external_test`, and the Jev arm runs on its pre-registered sample.
5. The gates are applied as written. Nothing is re-tuned afterwards.

## 11. Disclosure

**What had been seen before registration:**
- Outcomes on these data had already been seen for:
  - fixed, cost_only, magnitude and production_default on SciPlex3;
  - fixed and production_default on L1000;
  - marginal_only and sparse_two_step on both;
  - maestro_vc on SciPlex3 (block 4's conditioned `da` arm carried the magnitude priorities there);
  - maestro_masked on L1000 (block 4's `da` arm had no virtual cell there).
- The other arms had never been run on real data.
- Of the local Tahoe subset, only its metadata was read, never its expression.

**Addendum, registration day, before the freeze.** Two mechanics checks executed arms on real
data before `freeze.json` was written:
- `locked_replay --smoke` ran three episodes each of SciPlex3 A fold 0 and L1000 T fold 0 through
  every arm. It printed record and violation counts only (87 records each, 0 violations).
- The contract tests ran two to four episodes of the same folds. They assert structure and
  equality and print no rate.

No outcome rate, correct count or wrong count was displayed by either check.
