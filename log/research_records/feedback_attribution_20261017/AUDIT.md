# Phase 1 audit of the context-transfer implementation and evidence

* **Audited state.** Commit `10b848d2591e1c362f9e8cbd59c54d102fe12573` (clean working tree at the
  start), study `research/context_transfer_20261017`.
* **Frozen files.** None was edited. `verify.py` there still prints VERIFIED after every change
  below.
* **Data.** Numbers marked *diagnostic* come from development runs on exposed Beat AML data
  (`COHERENCE.json`, `DECOMPOSITION.json`). The others come from the frozen records or from design
  columns.

## A1. Claim mapping and decision thresholds

**Finding.**

* `confirm.py` decides C3 "agent adaptivity" by P5, non-inferiority to the best fixed procedure in
  hindsight. It passes C4 "agent beats fixed pipelines" if any of P1, P2 or P6 passes.
* The selector chose exploit-first in 5/5 folds, and P2 is exactly 0. P6 beat a comparator
  (`lookahead_v1`) that has a defect.
* `verdict()` returns SUPPORTED on Holm p < α with a positive lower bound. `min_useful = 0.05`
  only separates NOT_SUPPORTED from INCONCLUSIVE. P1's lower bound is 0.025.

**Recorded.** `context_transfer_20261017/CLAIMS.json` (`claims.py`):

* CONFIRMED is kept as the protocol-execution label.
* Seven scientific claims carry their own status.
* Every contrast is reported at three levels: positive, above the minimum useful effect, and net
  of round cost.
* The defective-comparator contrasts are flagged.

The REPORT.md, README.md and research/EVIDENCE.md entries point to it. This study's
`attribution.py` reports the three levels for every contrast.

## A2. Resource units

**Finding.** A "well" in the frozen study is one archived probit AUC, one 7-dose profile. The
assay design is confirmed from the source (Tyner et al. 2018 Methods) and from the raw file:

* every run in the 520 x 165 domain has 7 dose points;
* 15% of measured pairs carry more than one 7-well profile, and the mean is 8.7 treatment wells
  per measured pair.

Sixteen queries stand for 112 treatment wells before controls, at one replicate, or about
1.1 million cells per sample. A bridged arm adds a round of about 72 h with banked cells, and the
replay cannot test whether a banked sample keeps its response state.

**Recorded.**

* `COST_UNITS.json` holds the action → data → cost mapping and a per-arm table.
* Docstrings in `src/virtual_cell/bridged_transfer.py`, `src/agent/bridge_design.py` and
  `tools/evaluation/bridge_replay.py` now say "query", and `VALIDATED_SCOPE` now reads
  `..._16_auc_queries_...`.
* Paired comparisons at equal query counts are unaffected.

## A3. Archive coverage versus experimental feasibility

**Finding.** `measured_rate` (q_i) is historical marginal archive coverage. Of the 32,229 missing
domain pairs:

* 30,361 (94%) were never scheduled;
* 1,868 were on a panel the sample ran but have no QC-passed record;
* none have a fit lost to identifier mismatch, and none have raw wells without a fit.

The release contains only QC-passed wells, so QC removals, too few cells and failed runs cannot be
told apart.

| Predictor of the measured mask | Median per-inhibitor AUROC |
|---|---|
| Panels run (the schedule) | 0.945 |
| Panels plus basal PCs | 0.931 |
| Basal PCs alone | 0.593 |

The PC association runs through the schedule, plausibly through batch effects of the collection
era.

*Diagnostic:* lost profiles come from samples that are more sensitive overall (G z −0.63 against
recorded samples, in 95% of 135 inhibitors). Assay failure is therefore not at random with
respect to overall sensitivity.

**Recorded.** `MISSINGNESS.json`. This study runs three tasks:

* `archive`: the frozen rules;
* `design`: the menu is the sample's scheduled panel, and a historical failure is a failed assay,
  with no imputation;
* `panel80`: 93 inhibitors scheduled for at least 80% of samples.

The 29% → 89% rise in measured bridge queries after the lookahead repair is described as an
evaluability effect, not as stronger reasoning.

## A4. Event probability is not coherent

**Finding.**

* `BridgedTransferModel.thresholds` puts `median(predicted mean)` into
  `t_d = a_d + b_d * median(mean) + med_d − 3 * MAD_d`.
* `event_prob` then scores `Phi((t_d − mean_d) / sd(Y_d))`. The threshold moves with the
  prediction, but the variance ignores the uncertainty in G (the coherent variance is
  Var(Y_d − b_d G)).
* `_lookahead` computes `t` once, before its fantasy readouts, so the planned and executed scores
  target different events.

**Reproduced.** The one-factor, three-item counterexample: the prior score is 0.16340, and after
one readout it is 0.000178 for every observed value from −4 to 4. The expected change is −0.163,
where coherence requires 0 (`test_science.py`, `COHERENCE.json`).

*Diagnostic on Beat AML.* Held-out samples, rank 20, exploit bridge:

* **Martingale gap.** The promoted score drops in expectation by 0.0026 (all unprobed items) and
  by 0.0067 (top 50 items). Mean prior probability is 0.028.
* **Coherent scorer.** Its gap is 1.6e-5 (all unprobed) and 6.6e-5 (top 50), which is zero within
  Monte Carlo error.
* **Decisions.** The two scores share 74% of their top-16 choices.

**Calibration** on realised events: coherence does not fix it.

| Score | Mean predicted (observed 0.021) | Log loss | Pooled AUROC |
|---|---|---|---|
| Promoted | 0.028 | 0.0975 | 0.729 |
| Coherent | 0.018 | 0.0988 | 0.740 |
| Monte Carlo, exact endpoint | 0.015 | 0.1065 | 0.737 |

* The model's own exact-endpoint probability is too low, which means its Gaussian tails are too
  thin for a z ≤ −3 event.
* The promoted score's inflated variance partly offsets that.
* The coherent score ranks slightly better before and after readouts (0.763 against 0.756 after).

A coherent and calibrated score needs a heavier-tailed residual or an empirical tail calibration.
That is not done here.

**Recorded.**

* `coherent.py`: a development scorer with a fixed event, G = g0 + g'f + η fitted on source
  factors, and one function for the prior, the fantasies and the posterior.
* `planner.py`: a joint Monte Carlo two-stage reference. It samples readouts and whether they
  return, updates only on returned readouts, uses the same terminal score as execution, and
  splits EVSI, opportunity cost and round cost.
* Properties are tested on synthetic data: coherence, no information and no covariance change
  when nothing returns, the terms add up, and opportunity cost ≥ 0.
* The promoted modules are unchanged, so the confirmed records reproduce. Their docstrings now
  state the approximation.

## A5. Inner procedure selection

**Finding** (`src/agent/procedure_selection.py`).

* `_paired` computes the inner SE over sample rows, so a patient's samples count as independent.
* The z > 1.645 threshold is applied after the rank is chosen among four and after the larger of
  two bridge z values is taken. It is a heuristic, not a post-selection guarantee.
* Every procedure reuses vc0's rank, although exploit's best inner rank differed in some folds
  (fold 0: vc0 40, exploit 10).
* The outer analysis already clusters by patient.

**Recorded.**

* The docstring states these limits, and `SELECTION_STATUS` marks the corrected-lookahead
  selector as development.
* `tuned.py` gives every procedure its own rank and adds a generate-then-calibrate selector on
  disjoint patient halves. It uses patient-level units, a Bonferroni lower bound and a declared
  round cost.
* The attribution groups use one fixed common rank.

## A6. Corrected code and confirmation status

**Finding.** The corrected `lookahead` became the default name in `src/agent/bridge_design.py`
after the confirmation.

**Recorded.** `RULE_STATUS`:

* `exploit`: confirmed under the archive replay;
* `lookahead_v1`: frozen and rejected;
* `lookahead`: development, post hoc, not confirmed.

A test (`tests/test_bridged_transfer.py`) pins these grades.

## A7. Workflow versus knowledge transfer

**Finding.** `replay.py` refits drug means, loadings, the expression map, thresholds, rank and
procedure on Beat AML source patients in every outer fold. The confirmation therefore shows an
algorithm developed on PRISM applied within Beat AML. It does not show biological knowledge
carried from PRISM.

**Recorded.** CLAIMS.json `transfer_type`, the src docstrings and research/EVIDENCE.md.

## A8. Descriptive count

**Finding.** Post-run prose said 166 inhibitors; the analysed matrix has 165. The census's 166
includes one inhibitor measured only in samples without RNA-seq.

**Recorded.** `context_transfer_20261017/DEVIATIONS.json` entry 3; the prose is corrected and the
frozen PROTOCOL.md is left as written. No result is affected.

## A9. Endpoint content (diagnostic)

**Variance split.** The frozen residualisation splits AUC variance over measured pairs into:

* inhibitor mean: 41.7%;
* sample-wide sensitivity (b_d G): 15.2%;
* residual (the endpoint's quantity): 43.0%.

**Inside the residual.**

* Within-run replicate noise accounts for about 41% of it. This is a lower bound on noise, because
  between-run and specimen noise are not included.
* A ridge on 30 basal PCs predicts 9.8% of it out of fold.

**What each state predicts** on held-out patients:

| State | G (r) | Residual (mean within-inhibitor r) |
|---|---|---|
| RNA prior | 0.37 | 0.25 |
| RNA, after four readouts | 0.51 | 0.30 |
| Population, after four readouts | 0.42 | 0.18 |

So the RNA prior does predict part of the drug-by-state interaction, and the four readouts mostly
sharpen G. Whether that translates into hits is the attribution study's question (H3, H2).

## A10. Independent confirmation data (Phase 4): blocked

**What is known.** The PRISM 24Q2 REP.1M census (`research/knowledge_reality_20261013/SEALED_CENSUS.json`,
metadata only):

* 1,278 compounds, of which 49 match 19Q4 by name, core or connectivity; 1,229 are eligible;
* 545 panel lines with CCLE expression, of which 285 lie outside the 19Q4 panel.

**What blocks the check.** Whether REP.1M wells were re-screened or carried over from intermediate
releases is not answered by that census. The release README and metadata files (figshare article
25917643) are no longer on disk.

**Missing dependency.** Those small metadata files (README.txt, Repurposing_Public_24Q2_Readme.txt
and the cell-line, treatment and compound tables). Downloading them needs authorisation, and the
72.5 MB outcome matrix stays sealed.

**A design limit.** A model with inhibitor-specific loadings cannot score the 1,229 new compounds.
Confirming on them needs inductive compound features, or a within-release fit on source lines,
which would again be workflow transfer.
