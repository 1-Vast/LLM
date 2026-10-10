# Phenotype-anchored dual core (block P1, 2026-10-10)

Status: **draft protocol**. Section 9 lists everything already seen. `FREEZE.json` hashes this
file, the analysis code and the reference-line gate receipt before any held-out phenotype, held-out
treated RNA, held-out STATE forecast or LLM answer exists.

## 1. Question

Earlier MAESTRO studies found that frozen STATE improves zero-shot RNA prediction on held-out
lines. That never became a decision gain, for two recorded reasons. First, the 39-gene RNA proxy
tasks had almost no headroom: the panel prior was already near the oracle. Second, every
functional endpoint was refused because RNA and viability came from different assays, doses
and times, so no authenticated bridge existed.

Tahoe-100M measures RNA and phenotype in the **same spheroid** ("cell village" of all 50 lines,
24 h). The same well therefore gives two phenotypes, the ones the Tahoe Cell (2026) paper also
reports: relative survival (cell counts versus DMSO) and cell-cycle shift. This study asks:

> For checkpoint-held-out cell lines, do frozen STATE zero-shot transcriptional forecasts, read
> through a phenotype bridge fitted on same-well reference data, predict and select the drugs
> that **selectively** reduce a line's survival, beyond basal-similarity transfer, lineage,
> driver-target knowledge and an LLM knowledge prior?

## 2. Endpoints

All phenotypes are keyed by (line, drug-dose label, plate) and computed from obs codes in
`phenotypes.py`.

* **Relative survival** `S = log2(n_line / D_well) - log2(n_line,DMSO / D_DMSO)`, using the same
  plate's DMSO spheroids and pseudocount 0.5. `D` is the summed count of the 40 count-qualified
  reference lines in that well, so no held-out line enters any denominator. Absolute survival is
  not identifiable: well totals do not replicate (development check, r = -0.12).
* **Phase log-odds shift**
  `G1 = logit(p_G1 | treated) - logit(p_G1 | same-plate DMSO)`, with S and G2M defined likewise.
* **Selectivity target** `T(L,d) = S(L,d) - mean over reference lines of S(ref,d)`. Where a label
  sits on two plates, the plate mean is used. Evaluation is within line, so line offsets cancel.

**Primary endpoint E1**: survival selectivity at 5 uM. **Secondary**: E2, G1 selectivity at
5 uM; E3, survival selectivity at 0.5 uM.

**Menu**: every 5 uM label in the STATE one-hot map that is measured for the line. A missing
label is refused by name (`LABEL_UNMEASURED`, `LABEL_NOT_IN_CHECKPOINT`) and never imputed.

**Count qualification**: a line whose median treated-well count is below 200 is refused with
`CONTEXT_UNDERCOUNTED`. Five reference lines are refused this way (NCI-H596, NCI-H2122,
SW 1088, NCI-H661, SW 1271). All five held-out lines pass, with medians of 894-2,782 computed
from census aggregates.

## 3. Units and splits

* Reference: the 40 count-qualified lines that are in STATE pretraining. All fitting and
  hyperparameter choice uses leave-one-reference-line-out (LOO).
* Held-out: c12 Hs 766T, c20 PANC-1, c26 C32, c27 HepG2/C3A and c31 HOP62. These are STATE's
  documented zero-shot contexts. All five are used once, for evaluation only; no held-out value
  selects anything.
* Generalization rests on n = 5 lines. Drug intervals do not add line replication.

## 4. Arms (predict T for an unseen line)

| Arm | Information | Construction |
|---|---|---|
| Z | none | T-hat = 0 (generic drug ranking; mandatory zero arm) |
| O | organ label | mean T over same-organ reference lines; 0 if none (`NO_SAME_ORGAN_REFERENCE`) |
| B | basal RNA | kernel transfer of reference T, with weights from basal-profile correlation |
| K | driver genes + drug targets | indicator: a drug target equals a gain-of-function or oncogene driver of the line |
| S | basal RNA + frozen STATE | the primary STATE readout chosen by the gate (below) |
| S_bridge | basal RNA + frozen STATE | bridge(STATE forecast minus reference-panel mean deviation) |
| S_kernel | basal RNA + frozen STATE | kernel transfer of reference T, weighted by similarity between the STATE-predicted response profile (all 5 uM labels) and each reference line's observed profile |
| SB | B + S | equal-weight mean of z-scored B and S predictions |
| S-perm | wrong basal + STATE | S built from another held-out line's basal set (cyclic) |
| L | LLM knowledge | DeepSeek ranks the menu from organ, drivers, drug targets and MoA (secondary) |
| R_bridge, R_kernel | observed same-well RNA | the same two readouts on observed deviations; ceilings, not deployable |
| S_cells (E2 only) | frozen STATE cells | predicted-cell G1 shift (phase classifier) as a z-score minus the z-scored reference G1 panel mean |

Bridge: PCA plus ridge, fitted on reference lines from the context-specific observed deviation
(treated mean minus same-plate DMSO mean, minus the reference-panel mean for that label) to T.
The grids are n_pc in {20, 50, 100}, alpha in {1, 10, 100, 1e3, 1e4} and training doses in
{5 uM, all}. Each is chosen by LOO mean within-line r on E1.

B uses tau in {0.02, 0.05, 0.1} and top-m in {3, 5, 10, 40}, chosen by the same LOO.

The STATE forecast replicates the 2026-10-07 native path: 256 full-QC same-plate DMSO cells,
seeded by file and plate, native `predict_step` per set, and the paired delta (forecast minus
the forecast for DMSO on the identical tensor). For E2, a multinomial phase classifier is fitted
on reference DMSO cells (X_hvg to obs phase) and applied to every predicted cell. The predicted
G1 shift is logit(G1 fraction | label) minus logit(G1 fraction | DMSO) on the identical tensor.

## 5. Gate: world-model value ceiling (computed on references before freeze)

Arms R_bridge and R_kernel on reference lines (LOO) estimate what a perfect RNA world model could
deliver through each readout. **Primary readout**: whichever of the two has the higher reference
LOO r on E1; the other is secondary. **Gate**: evaluate S on held-out lines as a candidate
decision input only if `max(r_R_bridge, r_R_kernel) - max(r_B, r_O) >= 0.05`. Otherwise S is
still run and reported, but the decision arm is refused with `WM_CEILING_BELOW_MUB`. The gate is
recorded in `GATE.json` before freeze. Gate scores use each arm's best grid point, without
nesting. The resulting selection optimism applies to B and to the oracles alike. It does not
reach the held-out evaluation, whose hyperparameters are fixed before access. On held-out lines, the observed-RNA oracle of the primary
readout is compared with B (`gate_check`), which tests whether the gate's reference judgement
transferred.

## 6. Hypotheses and decision rules

Minimum useful benefit (MUB): delta r = 0.05. This is about one standard error of a
within-line r over roughly 379 drugs, and about 8% of the single-well noise ceiling (0.63).

* **H1 (primary, prediction)**: mean over held-out lines of within-line Pearson
  r(T-hat_S, T_obs) on E1 exceeds the same quantity for B. Success requires both:
  * the 95% drug-cluster bootstrap CI of the difference excludes 0 (clusters = Tahoe
    `moa-fine`; 2,000 resamples shared across lines; seed 20261010);
  * r_S > r_B in at least 4 of 5 lines.

  Reported together: r_S versus 0, O, K and S-perm.
* **H2 (co-primary, decision)**: rank-and-commit the top 10 drugs per line by each arm.
  Utility U = -mean T_obs of the committed drugs. S must beat B and Z by the H1 rule (CI plus
  4 of 5 lines). Outcomes never enter selection, so U on the same well is unbiased.
* **H3 (complementarity)**: SB versus B and versus S, same rule.
* **H4 (secondary, distribution readout)**: STATE predicted-cell G1 shift versus observed G1
  selectivity (E2), r compared with B.
* **H5 (secondary, agent knowledge)**: L versus K and O on E1 and on top-10 utility.
* **D2 (secondary, screening)**: on 5 uM labels with two plates, an 8-purchase screen
  (plate-A well) then a 5-commit choice, scored on the plate-B well. Policies are no-screen
  and fixed top-8 screen, crossed with priors {Z, O, B, S, SB}. The screen commits the five
  screened labels with the most negative plate-A selectivity; no posterior model is fitted.
  Credits: 8 A plus 5 B, against 5 B for no-screen.

A failed H1 or H2 is reported as a null with its intervals. Neither the protocol nor the
threshold is revised after held-out access.

## 7. Costs and resources

Laboratory units (simulated replay of public wells): one well equals one credit. Shared DMSO
is counted once per plate. API spend, tokens, GPU seconds and downloaded bytes are reported
separately and never mixed with credits.

## 8. Named refusals

`CONTEXT_UNDERCOUNTED`, `LABEL_UNMEASURED`, `LABEL_NOT_IN_CHECKPOINT`, `NO_SAME_ORGAN_REFERENCE`,
`NO_SAME_PLATE_BASAL`, `WM_CEILING_BELOW_MUB`, `LLM_UNPARSEABLE`, `LLM_SPEND_CEILING`.

## 9. Disclosure of prior exposure (before freeze)

1. Per-(label, plate) cell counts for all 50 lines have been on disk since the 2026-10-07
   census (`research/astra/zeroshot_context_20261007/census/`) and were used only for sampling
   plans. A repository grep finds no study that computed abundance or survival from them. In
   this study, before freeze, only each held-out line's median treated-well count was computed
   (section 2).
2. Held-out treated RNA for the 146 two-plate labels was opened by the 2026-10-07 to 10-09
   studies (39-gene score, RNA error). Cell-cycle phase and cell counts were never analyzed as
   phenotypes for any held-out line.
3. Reference-line development analyses run today, before this protocol:
   * replicate and cross-dose reproducibility (survival interaction r 0.40 / 0.35; G1 0.30 /
     0.43);
   * well totals do not replicate;
   * same-well phase shifts explain about 0% of the survival interaction;
   * same-organ priors give r about 0.07-0.13 and driver-target priors about 0.

   Scripts are in `development/`.
4. Two further reference-only development checks were run after the first draft of this protocol.
   * `development/growth_confound.py`: the survival interaction is low-rank (top three components
     30%, 18%, 12%). The leading line factor does not track DMSO cycling fraction (r = 0.10). After
     removing the rank-1 term, the residual still replicates (r 0.46 vs 0.49). Raw selectivity is
     therefore kept as E1.
   * A debugging dry run of `gate.py` on the first 10 extracted reference lines, with a
     single-point grid, gave LOO r of about 0.41 for B and about 0.17 for the bridge oracle.
     **The S_kernel / R_kernel readout was added after this dry run**, because it suggested that
     transfer between lines carries the predictable structure. The gate's readout choice protects
     the held-out comparison against this ordering: it uses references only.
5. The STATE checkpoint files and the arc-state 0.11.3 source (commit `9bbfe78a`) were absent
   from `data/` and were re-staged hash-identical (`STATE_STAGING.json`).
6. The exact Tahoe Cell (2026) phenotype formulas could not be read (publisher 403, bioRxiv
   429). The definitions above are this study's adaptation, not a reproduction.
