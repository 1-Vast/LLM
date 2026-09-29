# Experiment record, 2026-09-28

> - **Path**: `log/20260928/README.md`
> - **Purpose**: Record block 1 (09:42-11:45), dual-core v2. The owner's brief (drafted by the Codex session that wrote `outputs/diagnosis_20260928/` at 08:22-09:39) asked to verify that diagnosis independently and repair the confirmed defects in both MAESTRO cores: the conditional virtual-cell world model and the evidence-driven agent. It also asked to recompute what the defects affected, test the smallest justified improvements, evaluate the deferred population backend and decide what to keep. The full report is `research/dual_core_v2/README.md` and the issue matrix `research/dual_core_v2/ISSUES.md`.
> - **Core points**: Two defects confirmed and repaired with failing-first regression tests. First, block 7's Learn-then-Test (P3) never tested a nonzero threshold: it broke on the untestable threshold 0 and fell back to it. Second, block 7's calibration for a test fold used traces from models trained on that fold. A third, smaller one: `fit_pair` scored gamma on its own fitting residuals. The repairs change what the verdicts mean, not the verdicts. On block 7's traces and on 40 new nested jobs with exact lineage (0 audit problems, 640/640 reproduction anchors), nothing is certified at alpha = 0.05; the outcome is "no candidate certified" with undefined conditional risk, not "abstain-always certified, error 0". Forecasts of wrong elimination are 1.9-3.1x too low on selected actions. Block 7's "Platt helps L1000 and hurts SciPlex3" does not survive correct lineage. No abstention threshold transfers; the apparent split-design gain comes from abstaining a whole fold. Risk-aware re-selection (the planner's own `wrong_risk_cap`) sits on the same risk-coverage frontier as stopping. The v2 world model (additive and a magnitude-keeping kernel as training-selected sources, a strict prompt contract, quality-aware caches) changes no decision. The bottleneck is localised: perfect response knowledge through the same interface sharpens SciPlex3 reading forecasts by 0.086 nats yet moves correct decisions by +0.008 [-0.004, +0.021], so the task, not the response model, binds decisions. Population backend: observed single-cell distributions add no mechanism signal beyond pseudobulk; the flow ties the mean-shift baseline (MMD -0.0006 [-0.0019, +0.0007]) and stays experimental. Block 7's "25-30x more units" is an artefact of the Hoeffding-Bentkus bound; where the risk sits at alpha no sample size certifies. Nothing promoted; `src/`, production defaults and block 7's files unchanged; $0, 0 wells, no download.

## 1. Record control

- **Tree as found (09:42).** `c3d2345` on `main` with the uncommitted work listed in the session's git status
  (Codex reorganisation of 2026-09-27, blocks 5-7 of 2026-09-27, all untracked or modified, none reverted).
- **Other sessions.** Codex rollout `01a0e152` wrote the diagnosis (08:22-09:39) and this brief (09:39-09:41),
  then went idle; no file changed between the diagnosis and the start of this block. No other actor wrote to
  the tree during the block.
- **Block 7 integrity.** Every file hashed in `research/dual_core/protocol_e2.json` matched the disk, except
  `e2.py`, which differs by block 7's own disclosed post-hoc addition (23:15). No block 7 file was edited here.
- **Pre-registration.** `research/dual_core_v2/freeze.json` (2026-09-28 10:18:21 +0800, 32 files: protocol,
  code, dependencies, prepared data, split manifest) and `freeze_population.json` (10:29:21, the population
  protocol and post-freeze analysis code). Copies in `0928/`.
- **Later block, same day.** The viability_contrast block (v1-v4 frozen 07:37-08:08Z; v5 frozen 10:28Z,
  gate FAILED, reformulation registered as the next direction) is recorded in
  `log/20260928/VIABILITY_CONTRAST_V5.md` and `research/viability_contrast/README.md` section 3.6.

## 2. Research questions and hypotheses

Taken from the brief and the diagnosis, treated as hypotheses:
1. Does block 7's P3 fail by control flow before it examines nonzero thresholds? (diagnosis section 6)
2. Does calibration for test fold f depend on fold f through the models that produced it? (section 7)
3. Is `fit_pair`'s residual-model error in-sample, and do A2 weights or conclusions change with an honest error? (section 2)
4. Where between predicted RNA response and decision does information disappear? (sections 3-4)
5. Does comparing safer actions before stopping beat stopping? (section 5)
6. Does a training-selected world model (additive, magnitude kernel) change decisions?
7. Does single-cell population information add decision signal beyond pseudobulk, and does the flow predict it?
8. What limits certification: the model, the risk ranking, the task, power or the bound?

## 3. Materials, data and computational environment

- **Data.** SciPlex3 pseudobulk (2,473 genes, 16 conditions, 185 units) and the raw h5ad for single cells
  (sha256 `bde2420c...`); L1000 Level 5 landmarks (978 genes, 8 conditions, 335 units); the 20
  protocol-v2.1 development tasks. All exposed since 2026-09-26. No download.
- **Environment.** Tests: `maestro` conda env (Python 3.11.16). Experiments: `C:/Python314` (Python 3.14.4),
  the interpreter that wrote block 7's outputs (pyarrow 24.0.0), and `maestro` for population part 2 as the
  Codex pilot did. 20 cores, 3 workers because 0.3-1.6 GB of RAM was free. GPU (RTX 4060; the `maestro` env has
  a CUDA PyTorch) unused.
- **Literature.** Six starting DOIs re-resolved through the bioRxiv and Crossref APIs (State published in *Cell*;
  SCALE has an uninspected v2 with an unchanged abstract); targeted searches on risk control, betting tests,
  feedback covariate shift, metric choice for unseen chemistry and agent evaluation.

## 4. Experimental design and controls

- **Designs** (`research/dual_core_v2/protocol.json`). `split`, the primary: for test fold f, one model trained
  on three folds, calibrated on fold f+1 and tested on f. `nested_crossfit`, descriptive: four models that
  exclude f. `block7_crossfit`, before only.
- **Repaired risk control.** Nonzero candidates; union null (risk > alpha or coverage < 0.5 x P0); Holm;
  explicit abstain-all; betting (primary) and Hoeffding-Bentkus p-values; alpha 0.05, delta 0.1, unchanged.
- **Arms per nested job.** P0 with reference, v1 and v2 world models. The five split jobs add risk-select (world
  in {reference, v2} x {point, conservative} x three outcome-blind caps) and a diagnostic oracle arm reading
  true shifts. A per-step ablation of every world variant runs at identical executed steps.
- **Controls.** Reproduction anchor against block 2's planner; lineage checks before every job; shuffled and
  tempered controls for the post-hoc population fusion; vehicle and oracle-mean anchors in population part 2.
- **Estimands.** Unit-level throughout (SciPlex3 InChIKey connectivity block, L1000 identity/scaffold
  component), with a 10,000-draw unit bootstrap; conditional risk undefined when nothing is decided.

## 5. Experiment register and results

| Question | Result |
|---|---|
| 1. P3 control flow | Confirmed: P3 = 0 in all 20 fold x arm cells, reported as "0 [0, 0]" at coverage 0. Repaired; on the same traces the repaired procedure certifies nothing |
| 2. Calibration lineage | Confirmed (a test spies on the fitting inputs). Under exact lineage: raw observed/forecast 1.88 [1.04, 2.85] SciPlex3 and 2.84 [1.31, 5.26] L1000; Platt log-loss change -0.008 [-0.021, +0.002] and -0.005 [-0.015, +0.002] (block 7: +0.006 and -0.008, both "significant") |
| 3. Honest residual error | Confirmed optimism: `rrt_q` beats `ridge_st` in 69.5% of SciPlex3 pairs honestly (97.9% in-sample); A2 weights about 0.5 either way; no A2 conclusion changes. Rank grid k <= 128 lowers honest L1000 error 1.4% (training only) |
| 4. Information loss | v2 changes forecasts at 33-41% of steps and decisions in 10 of 1,056 / 6 of 1,895 episodes. The oracle sharpens SciPlex3 forecasts by 0.086 [0.039, 0.135] nats but moves correct decisions by +0.008 [-0.004, +0.021] |
| 5. Risk-select vs stop-only | Same frontier at matched coverage in every SciPlex3 cell; one suggestive L1000 cell (-0.037 [-0.103, +0.001], about three events); no certificate |
| 6. World model v2 | v2 - reference under P0: correct -0.001 [-0.005, +0.002] (SciPlex3), +0.001 [-0.004, +0.009] (L1000); 2% fewer measurements on L1000; v2 - v1 forecast log loss +0.001 [-0.002, +0.005] |
| 7. Population | Part 1 (registered): distribution features worsen log loss (+0.033 [+0.002, +0.065]); post hoc, fusion is only tempering. Part 2: flow - mean shift MMD -0.0006 [-0.0019, +0.0007]; better variance ratios only |
| 8. What binds | L1000: an uninformative task (85% of readings undetected). SciPlex3: few units per class (median 3.5), events in about 20 units. Unconstrained risk at alpha: no sample size certifies it. At the one point where abstention helps, a betting test needs about 400-1,600 units (HB about 3,200) |

## 6. Deviations, failures and corrections

- **Own error, corrected in-block.** The first draft of `horizon_headroom.py` swapped correct and wrong
  eliminations; the session briefly reported "170 of 202 wrong" before the corrected numbers (18/4, 95/31, 60/4
  correct/wrong). Only the corrected table is recorded.
- **Post-freeze changes, disclosed.** Tests added to `test_dual_core_v2.py`; `analysis.load_runs` tags ablation
  rows with the job's model (11:06, no statistic changed).
- **Choice made after seeing historical HB p-values.** The betting p-value was chosen as primary after the
  diagnosis's all-threshold HB p-values on block 7's traces were known; both are reported and give the same
  verdicts everywhere.
- **Post hoc, labelled.** The population fusion check and its controls.
- **Environment.** Block 7's environment of record was not stated in its notes; it was `C:/Python314`.

## 7. Interpretation and claim boundaries

- Every result is on exposed development data; E-DATA1's failure rule still forbids planner-superiority claims.
- No finite-sample risk guarantee is claimed. None was earned, and the nested cross-fit design would not give one.
- The oracle arm reads outcomes; it bounds, it is never a policy.
- Population statements hold for 24 h, 10 uM, 128 cells per condition and one mechanism-class task.
- No mechanism or efficacy claim; mechanism labels are reference annotations.

## 8. Reproduction and artifact ledger

- **Code:** `research/dual_core_v2/` (`risk_control.py`, `nested.py`, `world3.py`, `arms.py`, `run.py`,
  `analysis.py`, `report.py`, `transfer_honest.py`, `e1_honest.py`, `data_audit.py`, `horizon_headroom.py`,
  `block7_repaired.py`, `population_eval.py`, `freeze.py`, `protocol.json`, `protocol_population.json`,
  `test_dual_core_v2.py`, `README.md`, `ISSUES.md`).
- **Outputs:** `outputs/dual_core_v2_20260928/` (74 MB).
- **Tests:** `python -m pytest research/dual_core_v2 research/dual_core -q -p no:cacheprovider -o addopts=` gives 39
  passed; the repository suite gives 1,369 passed (this block changed no file under `src/` or `tests/`).
- **Copies in `0928/`:** `dual_core_v2_run_notes.md`, `dual_core_v2_analysis.json`,
  `dual_core_v2_e1_honest_analysis.json`, `dual_core_v2_population_part1.json`,
  `dual_core_v2_population_part1_posthoc.json`, `dual_core_v2_population_part2.json`,
  `dual_core_v2_horizon_headroom.json`, `dual_core_v2_data_audit.json`, `dual_core_v2_block7_repaired_ltt.json`,
  `dual_core_v2_freeze.json`, `dual_core_v2_freeze_population.json`.
- **Commands:** section 15 of `research/dual_core_v2/README.md`.

## 9. Open items and next experiments

Owner decisions first:
1. Whether to define a separately specified three-measurement task on SciPlex3 B (oracle headroom about 95
   correct decisions in 467 undecided episodes, at 6 more assay days each). Nothing here recommends it yet.
2. Whether to pursue more independent units per mechanism class at detectable conditions (the one data change
   that would help), rather than more rows or cells.
3. Open technical items: the extended rank grid scored only on training data; honest inner re-selection of
   (s, k, e); conditional-on-selection risk control (SCoRE) and cross-experiment e-values (POPPER); SCALE v2 full text.

## 10. Curation provenance

Written by the Claude Code session of 2026-09-28 (block 1). Its sources are the files under `research/dual_core_v2/`
and `outputs/dual_core_v2_20260928/`, whose SHA-256 digests for the frozen parts are in the two freeze records.
Numbers are copied from `analysis.json`, `e1_honest/analysis.json`, `population/part1.json`, `part2.json` and
`diagnostics/*.json`. Nothing in `log/20260927/` was edited.
