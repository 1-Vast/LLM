# RSD protocol: replicate-identified Virtual Cell posterior for noise-aware research decisions

Status: written after the search stage and frozen (see `FREEZE.json`) before the selection and evaluation blocks were read.
Development-grade study on exposed data; it cannot be an independent confirmation.

## 1. Question and hypotheses

Can a Virtual Cell posterior whose signal and noise geometry is identified from replicate plates of reference compounds
improve one-read research decisions on new compound classes, graded on a replicate plate that no policy can read?

| ID | Contrast (evaluation block, graded on read T) | Role |
|---|---|---|
| H1-D1 | `rsd - raw` for context selection (top 10 lines per compound) | primary |
| H1-D2 | `rsd - raw` for candidate progression (top 16 compounds per line) | primary |
| H2 | `rsd - pca` and `rsd - rsd_totalgeom` (replicate identification vs total-covariance geometry) | secondary |
| H3 | `rsd - rsd_priorflip` (chemistry prior of the VC switched relative to the inner choice) | secondary |
| H4 | D3 escalation at +25% reads: `voi_kg - exploit_first`, `voi_kg - none`, `exploit_first - raw_exploit_first` | secondary |
| H5 | Calibration: 80% predictive coverage and mean z on D2-selected pairs; claimed-minus-observed value of selected pairs for every arm (selected-candidate optimism) | secondary |
| H6 | Cross-run check: H1 contrasts graded on the primary-screen run (different compound plate and run) | secondary |
| -- | Fusion, scalar shrinkage, VC-only, pool-term flip and tier ablations, `rsd2 - raw2`; H1-D1 split by identity tier (strict / purged) | descriptive |

**Primary success (per decision):** Holm-adjusted one-sided p < 0.05 over {H1-D1, H1-D2} (cluster bootstrap) **and** point
estimate >= the practical threshold delta_D. delta_D = 0.5 x (value of a second raw read, `raw2 - raw`) measured on the
search block and frozen as a number in `FREEZE.json`: a method below it saves less than half a read (10 wells) per
compound. A decision with a positive lower bound but an estimate below delta_D is reported as `SIGNIFICANT_BELOW_PRACTICAL`.
The rule is implemented in `rsd_run.verdict` (labels `SUPPORTED`, `SIGNIFICANT_BELOW_PRACTICAL`, `NOT_SUPPORTED`); the
one-sided p is the percentile-bootstrap tail (number of draws <= 0, plus 1) / (draws + 1).

## 2. Data, identity and roles

* PRISM 19Q4 secondary, screen HTS002, dose 2.5 uM (atol 0.01), experimental treatments; one column triple per Broad core
  (first `(broad_id, compound_plate, well)` with all three detection plates X1-X3). 1,288 cores have a triple.
* Identity audit (`rsd_data.parents`): parent = largest fragment; 5 cores whose parents differ beyond stereochemistry are
  refused `AMBIGUOUS_STRUCTURE`; 24 stereo-only variants kept on the non-isomeric parent. 1,283 compounds.
* Lines: secondary lines passing STR profiling with an HTS002 pool: 481 lines in 20 pools. One (ACH-001192) has no HTS002
  2.5 uM read for any compound; its pairs are unknown in every arm (480 informative lines).
* Families: union of any shared MoA label (secondary and primary metadata, all labels), shared name, ECFP4 Tanimoto >= 0.5.
  All labels join 509 compounds (most oncology classes) into one component ("giant").
* Clusters: non-giant family, or giant compounds sharing a first MoA label. Roles by balanced deterministic assignment in
  salted-hash order: reference 424, search 215, selection 221, evaluation 423 (163 giant).
* Per block, references with a direct edge (label, name, Tanimoto >= 0.5) to any query are purged (search 48, selection 47,
  evaluation 68). Non-giant queries are component-isolated ("strict"); giant queries are edge-purged ("purged").
* Replicate roles per compound by salted hash permutation of (X1, X2, X3): A = screening read bought for every query, B =
  escalation read, T = truth read. The primary-screen HTS read (replicate-collapsed, separate run) is a second truth.

## 3. Stage roles and isolation

| Stage | Data used for fitting | Outcomes read | Purpose |
|---|---|---|---|
| Reference | reads A, B, T of the block's purged references | all three (historical data) | covariance identification, chemistry prior, inner selection of (q, rho, use_prior, q_pca) by replicate-split decision utility (input A, target T, 5 cluster folds; grid q in {0,1,2,3,5,10}, rho in {0,1}, prior on/off; q_pca in {2,5,10,20,40,80}) |
| Search (215) | reference only | A, B, T of search queries | headroom gate, behaviour of the full procedure, delta_D; debugging (see `DEVELOPMENT_LOG.md`) |
| Selection (221) | reference only | A, B, T of selection queries, once | go/no-go: `rsd - raw` estimate > 0 for D1 or D2, else stop before evaluation |
| Evaluation (423) | reference only | A, B (purchased), T and primary run, once | all hypotheses |

Queries of one block never train another block (`test_rsd.py::test_other_blocks_do_not_train_search_block`). Policies
read only A and purchased B through `Acquisition`; T and the primary run live only in `Evaluator`
(`test_truth_poisoning_leaves_policies_unchanged`). Family/role construction reads no outcome file
(`test_arena_reads_no_outcomes`).

## 4. Endpoints

Selective response of a read: `s = y - rowmean(y) - g`, g = reference line mean of row-centred reference profiles.
Killing = -s. D1: mean of -s_T over the 10 lines chosen per compound, averaged over compounds. D2: for each of 481 lines,
mean of -s_T over the 16 compounds chosen from the block; pairs pooled. Hits: -s_T >= 1. False progression: s_T > 0
among chosen pairs. Pairs with unknown T are excluded and counted (never inactive). D3: D2 after the agent buys B for
25% of the block's compounds.

## 5. Arms (information and budget)

One read per compound (20 wells): `raw`, `shrink` (read scaled by its per-tier replicate reliability around zero), `fusion`
(reliability-weighted read and chemistry prior), `pca` (projection on top q_pca axes of single reference reads; q_pca
chosen by the same inner procedure), `rsd` and its ablations (`priorflip`, `poolflip`, `notier`, `totalgeom`). Zero reads:
`vc_only` (chemistry prior). Baselines keep these definitions whatever the inner choice for `rsd`. Two reads (40
wells): `raw2`, `rsd2` (cost-ceiling references). D3 (1.25 reads, 25 wells per compound): `none` (1 read), `random`,
`exploit_first`, `uncertainty`, `voi_kg` on the rsd posterior, and `raw_exploit_first` (conventional workflow).
Logical action = one compound read across the full panel; physical cost = 20 pool wells per read; no monetary price is
authenticated; compute seconds are logged; no LLM or paid call.

## 6. Statistics

Cluster bootstrap (4,000 draws) over evaluation clusters; per-decision contrasts computed on fixed decisions (intervals
condition on the fitted reference model and on the chosen pairs). Sensitivity: (a) D2 re-selection bootstrap (1,000
draws; pools rebuilt and top-16 re-chosen), (b) training variability from 10 VC refits on 80% subsamples of reference clusters
(without replacement). Holm over H1-D1/H1-D2; secondary contrasts reported with unadjusted intervals and labelled secondary.

## 7. Stopping rules

1. Search headroom gate: if neither D1 nor D2 `raw2 - raw` has a positive lower bound -> `STOP_NO_REPLICATE_HEADROOM`.
2. Selection gate: `rsd - raw` estimate <= 0 for both decisions -> `STOP_SELECTION_NONPOSITIVE`; evaluation not run.
3. After evaluation: if H1 fails, diagnose (headroom, geometry transfer, calibration, power, defect). Fallback B (audit
   risk) is run only if the posterior is calibrated on selected pairs (80% coverage in [0.70, 0.90]); otherwise retire.
No retuning on the selection or evaluation blocks.

## 8. Versions

Code and data hashes, environment versions and the inner-selection grid are in `FREEZE.json`.
