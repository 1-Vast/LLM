# Fixed-seed attribution: contract repair, access trace and a bounded value-and-transport study

Study: `research/seed_attribution_20261017`. Written 2026-10-17 before the attribution run and frozen by
`FREEZE.json`. Local only. No sealed outcome tier is opened. Nothing in `program_revision_20261017`,
`feedback_attribution_20261017` or `context_transfer_20261017` is edited.

## 1. Questions

1. Is the evaluation contract of `program_revision_20261017` one contract, and what does repairing it do to
   the decisions it reported?
2. Which development-query outcomes enter the fits, residuals, thresholds, proposals and selections of the
   development bench, and what do the cost units actually count?
3. What explains the benefit of the fixed ten-program seed library: its biological correspondence, extra
   capacity, per-drug calibration, shared structure, or uncertainty estimation?

Scope limit: these are questions about a fixed library on PRISM 19Q4. They say nothing about autonomous
revision, which `program_revision_20261017` did not support, and this study does not rerun it.

## 2. Contract (`contract.py`, one implementation)

- Aggregate: m = mean of the available confirmation replicates X2, X3 (at least one). X1 is the probe
  readout and never enters the endpoint.
- Status: a pair is known iff at least one replicate exists. Unknown is never inactive and never a hit.
- Reference: the median of m over the known pairs of the drug on the reference lines. One-replicate pairs
  are known pairs and enter. Reference lines are source lines only; a target line's outcome never enters.
- Threshold: thr = min(-1, median - 1). A drug with no known source pair has an undefined reference; it is
  refused by name (`UNDEFINED_REFERENCE`), receives no score and is never nominated.
- Hit: known, every available replicate < 0, m <= thr.
- Score: `crossing_probability` = P(N(mean, var) <= thr). It is the probability that a latent mean crosses
  the threshold. It is **not** a calibrated probability of the complete qualified-hit event, because the
  sign condition, single-replicate noise and the X1-X3 versus X2-X3 target mismatch are not modelled.
- Corrected predictor (`corrected.py`): this contract for labels and thresholds; fit cache keyed by the
  data; predictive variance of the complete corrected predictor measured out of sample (inner cross-fit of
  the correction). The frozen implementation is reproduced only as a parity check.

Parity requirement (stop condition): in frozen mode (frozen thresholds, in-sample library variance) the
runner must reproduce the mean hits and unknown nominations of `program_revision_20261017/RESULTS.json`
for strong and seed at I1, I2 and the exploit-first campaign to 1e-9. Otherwise the run stops with
`PARITY_FAILED` and nothing is written.

## 3. Data and access

- PRISM Repurposing 19Q4 secondary screen, HTS002, 2.5 uM. 966 source drugs, 231 source lines, 247 target
  lines (67 future-line, 180 future-lineage; 21 lineages). Training = source lines only.
- The target strata were opened by `program_revision_20261017` (its `ACCESS.json`). They are **exposed**:
  this study is attribution on exposed data, not confirmation, and a same-screen stratum is not an
  independent domain. The 247 lines are 21 lineage clusters; every interval resamples lineages.
- Part 1 (`AUDIT_CONTRACT.json`) already computed strong-versus-seed decisions at the I1 and I2 component
  layers on these lines under several repair variants, before this protocol. The primary tests P2 and P3
  below therefore are not blind. The policy-layer contrasts under the corrected contract (P1) and every
  attribution contrast (null libraries, shared-only, conventional predictors, variance decomposition) were
  not computed before the freeze. Smoke runs on 12 lines (no inference) checked the code only.
- No PRISM 24Q2 or other sealed tier is read. Public-metadata checks are separate from this study.

## 4. Information and cost units (separate accounts)

Defined in `COST_UNITS.json` and `AUDIT_ACCESS.json`. This study reports, separately: shared historical
data (source screen, identical for every arm), incremental research data (none: no arm buys development
outcomes), deployment wells and assay units (28 wells per line; DNA panel one assay unit per line), rounds
(turnaround), compute seconds, LLM spend (zero) and curation (ten authored programs for B and D; a
permutation rule for E; a fixed tuning grid for C), and logical replay queries (one confirmation = one
query = two wells; not a plate count). The frozen development bench is not used here; its access paths
are traced in `AUDIT_ACCESS.json` and any new replay must use `replay.MaskedBench`.

## 5. Arms

All arms share the strong model S (rank 20), the fold, the inner cross-fitted residuals, the probe design
and the threshold. They differ only in the correction layer.

| Arm | Correction | Question it answers |
|---|---|---|
| A_S | none | baseline |
| B_seed | the complete ten-program seed library (hierarchical per-drug loadings, tau 20) | the object under study |
| D_shared_only | the same ten programs, one shared loading per program, no per-drug term | per-drug calibration versus shared structure |
| E00..E19 | `NULLS.json`: 20 permutations of the seed gates over the seed scopes | biological correspondence at equal capacity |
| C0_additive | ridge on the same scope flags and gate flags, no products | same inputs, no interaction |
| C1_global_ridge | ridge on the ten scope x gate products, one coefficient each | conventional counterpart on the same seed features |
| C1x_global_ridge_cross | ridge on all 8 scopes x 8 gates (72 products) | can a conventional model learn the pairing |
| C2_per_drug_ridge | per-drug ridge on the 8 gate genes, no scope | per-drug calibration without scopes |
| C3_pooled_gbm | boosted trees on scope flags and gate flags | nonlinear same-input predictor |

Null libraries (`nulls.py`): permutation of the seed gates over the seed scope slots; no seed pair reappears;
no pair repeats; every program passes the structural rules the development bench applies to an added
program; the observed scope x gate-positive cell support, summed over the library, is within +-20% of the
seed's; the first 20 admissible permutations in draw order (seed 20261017, 3,992 draws) are kept and never
reduced or reordered. No sign flips: the loading of every program is learned. The accepted nulls carry 4-20%
**more** observed cell support than the seed, so a seed advantage over them is not a support advantage.
A permuted pair can be biologically informative by accident; that would understate the value of
correspondence and is stated in the report.

Tuning: ridge strengths by inner cross-validation over {1, 10, 100, 1e3, 1e4, 1e5} on training residuals;
per-drug ridge by closed-form leave-one-out over the same grid; boosted trees with fixed depth 3,
learning rate 0.05, early stopping on 15% of training pairs, seed 0. Nothing is tuned on a target line.

## 6. Layers

- `policy` (primary): exploit-first feedback campaign, 28 wells per line, confirmation batches 5+5+4, on the
  I2 fold (the layer of the frozen headline contrast); nominations are confirmed pairs; feedback updates the
  line state. Predictive variance of every corrector arm is the out-of-sample variance of its complete
  predictor.
- `I2`, `I1` (component layers): top-10 nominations from the committed single-shot prediction with 8 probe
  readouts (I2) or the DNA panel only (I1).
- Secondary: the exploit-first campaign on the I1 fold (A, B only).
- Variants (component layers): variance decomposition of B, D, C1 and C3 (mean only; variance only, out of
  sample; full with frozen in-sample variance; for B also variance only, in sample); availability-weighted
  nomination (score x training-line availability) for A and B at every layer.

## 7. Outcome and hypotheses

Outcome: known qualified hits per line (unknown is a non-hit). Paired difference over lines, lineage-cluster
bootstrap 95% interval, one-sided sign-flip p over cluster means (frozen `common.paired`), Holm within a
family. MIN_EFFECT = 0.10 hits per line.

- Primary family (Holm over three): P1 policy B-A; P2 I2 B-A; P3 I1 B-A. `CONFIRMED` iff mean >= 0.10, lower
  bound > 0 and Holm p < 0.05; `HARMFUL` iff the upper bound < 0. **The seed signal survives iff P1 is
  CONFIRMED.** A meaningful signal remains iff any primary test has mean >= 0.10 and lower bound > 0
  (unadjusted); only then is Part 4 (opportunity diagnostic) run.
- Decomposition family per layer (Holm over four): B minus mean(E); B minus D; D minus A; mean(E) minus A.
  Plus the exact permutation rank of the seed among the 20 null means, p = (1 + #nulls >= seed) / 21.
- Conventional family per layer (Holm over five): B minus each C arm; each C arm minus A is reported.
- Reading rules (verdicts X_BETTER / Y_BETTER / EQUIVALENT_WITHIN_MARGIN / NOT_DISTINGUISHABLE as in
  `analyse.py`): correspondence is supported only if B minus mean(E) is X_BETTER **and** B exceeds every
  null; capacity alone gains iff mean(E) minus A is X_BETTER; per-drug loadings help iff B minus D is
  X_BETTER; shared structure gains iff D minus A is X_BETTER; uncertainty estimation can carry a gain iff
  variance-only minus A is X_BETTER. Anything else is "not established", not "absent".
- Precision statement: with 21 clusters the frozen policy-layer interval was +-0.42 hits per line. This
  study can establish a policy-layer difference of about 0.4 hits per line or more; smaller attribution
  contrasts will mostly be inconclusive. That is reported as inconclusive, never as a null.

## 8. Required reports (all in RESULTS.json)

Per layer: gate-positive versus gate-negative line utility and per-gene cells; nomination disagreements
between A and B (counts, hits per differing nomination, unknowns, net hits equal to the contrast);
lineage support (per-lineage contrast, positives and negatives, leave-one-lineage-out range, largest
lineage share, both strata); scaffold support (distinct structure groups among B-only hits, largest group
share); target-mixture-standardised contrasts (equal lineage weights, equal stratum weights, source gate
mixture) where each cell has at least 10 lines, otherwise `UNSUPPORTED`; unknown-outcome sensitivity
(unknown per line, hit rate among known, unknown as miss versus at the pooled hit rate, availability
weighted); costs (wells, rounds, compute seconds); the contract parity record.

## 9. Consequences (pre-registered)

- P1 CONFIRMED and correspondence supported: retain the seed library as a fixed, scoped component; any
  claim stays "exposed data, same screen".
- P1 not CONFIRMED: the seed signal does not survive the corrected contract at the complete-policy layer.
  Report the layer-dependent estimates; do not start a revision study; Part 4 runs only if a signal remains
  at some layer.
- Whatever the result, no LLM proposal, no unrestricted grammar search and no new revision campaign.

## 10. Files hashed by `FREEZE.json`

`PROTOCOL.md`, `contract.py`, `corrected.py`, `replay.py`, `nulls.py`, `NULLS.json`, `run.py`,
`analyse.py`, `test_science.py`. Not hashed: `DEVIATIONS.json` (a freeze must not hash its own deviations
log), `seal.py`, `verify.py`, the audit and cost scripts and their JSON outputs (written before the freeze
and read-only afterwards), and run outputs.
