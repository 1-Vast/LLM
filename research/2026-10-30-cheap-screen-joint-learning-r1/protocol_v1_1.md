# E001: conditional-gain pilot v1.1 (clarified before target decoding)

2026-10-30. Status: exploratory; independent initial design review completed; interpretation/provenance clarified before target decoding. Candidate I301.v1 is an empirical assay-readout restriction, not a new algorithm or completed Agent mechanism. Source article directions are exposed. No P14-guided tuning, favorable inhibitor selection or population significance claims.

## Question and provenance

Does TNF change the background-corrected IFN-gamma MFI response by a common multiplicative gain across five pharmacological interventions, within a declared cell line, cytokine dose and preparation? The changed premise is the acquired crossed cytokine/inhibitor/technical-well data in the official CXCL9 repository at b654a45faf5a80cdb1b514188cc90af8c9565b85. Two cell lines have different cytokine concentrations and remain separate. Raw events are capture beads measuring secreted CXCL9, not cells. The tested quantity is background-corrected fluorescence MFI, not per-cell secretion, apoptosis-adjusted output or tumor benefit.

Primary source DOI10.1038/s44320-026-00221-w, saved evidence/active_mechanistic.body: Par18, Par57–61. Owning source already studies inhibitor-specific cytokine synergy and directly couples logic-ODE models to active combination acquisition. Common-gain is ordinary rank-one response structure; no algorithm novelty is claimed. Earlier functional-abstraction and MuSyC-equivalence negatives are relevant ancestry; a changed qualified resource does not reset those conclusions.

## Frozen observations and processing

Use only evidence/cxcl9_raw_E3CA.body, E3CB, E3DA and E3DB, plus literal source metadata. All five inhibitors are retained: momelotinib, BMS-345541, salirasib, trametinib, taselisib; no-inhibitor controls are used for calibration. Stimuli are 00=None,10=IFNG,01=TNFA,11=IFNG_TNFA. E3CA/B are BxPC3/P12/P14; E3DA/B are AsPC1/P12/P14. Use all Sample1/2 wells in each file. No later AL, synthetic, GDSC, Cas3, protected/sealed or confirmation outcomes.

For each file×Sample×Condition (technical well), apply source Par60's 1.5IQR rule to the exported PE values (presumed capture-bead-selected from the source processing; exact APC gate provenance cannot be reconstructed or independently verified from this PE-only export): NumPy default linear quartiles; keep values within closed [Q1−1.5IQR,Q3+1.5IQR]; arithmetic mean of retained events. Capture-bead gate cannot be newly reconstructed from the single PE channel. Retain event counts before/after trimming and two well means. Average well means equally; do not pool event numbers or treat beads as biological replicates. Do not use all-condition minmax normalization, target-informed preprocessing choices, standard curves or apoptosis correction. All operations are declared before decoding.

For no-inhibitor controls, let m00,m10,m01,m11 be the means of two well means, D0=m10−m00, N0=m11−m01, S0=m11−m00. Technical envelopes use min/max of the two control well means, not statistical confidence intervals. Numeric calibration gate: Dlow=min(w10)−max(w00)>0, Nlow=min(w11)−max(w01)>0, and S0>0. Report failures without substituting a baseline or selecting drugs. No target fluorescence is converted before the control-only checkpoint and independent review allow evaluation.

## Models and targets

For every qualified preparation, kappa=N0/D0 is fixed from four no-drug control conditions only. For each inhibitor d, reveal its three calibration means y00d,y10d,y01d; keep y11d out of fitting/selection. Predict:

- H_gain: yhat11d=y01d+kappa*(y10d−y00d).
- B_add: yhat11d=y10d+y01d−y00d (no cytokine interaction).
- B_const: yhat11d=y10d+y01d−y00d+I0, where I0=m11−m10−m01+m00 (fixed untreated interaction).
- B_control: yhat11d=m11 (no inhibitor effect).

The H_gain/B_const difference is I0*((y10d−y00d)/D0−1); it is not informative when I0 or the inhibitor's IFNG-effect change is negligible. Report this distinguishing contrast for all targets; do not select a subgroup after seeing it. No free parameters, training, hyperparameter search or model-selection bootstrap.

Report signed residual and absolute prediction error divided by S0 for all five drugs in each of four preparations, and the mean within each preparation/model. Also report inhibitor ordering and exact gain-minus-comparator differences descriptively. A/B are two independent preparations per line, not four independent cell types. All four have local control calibration, so this is calibration-conditioned target holdout, not wholly unseen-preparation transfer.

For a nonstatistical sensitivity check, form the range of kappa from control-well envelopes (all endpoint ratios with positive denominator), then interval-propagate the inhibitor well ranges through H_gain. Report whether its prediction interval overlaps the observed y11d technical-well range. This checks the observed technical envelope only; no CI, p-value, biological noise guarantee or population-falsification claim.

## Decision and cost

This pilot can support or limit a conditional response restriction under these four assays. It cannot establish a new biological mechanism, broad transfer, target specificity, clinical benefit or an Agent acquisition advantage. Three drug calibration conditions to avoid one target are more expensive than measuring that target directly. An economical sequential capability would require a separate multi-target reuse question and a comparison including all calibration/feedback costs. Do not build an Agent wrapper to bypass this objection.

If calibration fails, park that preparation as unqualified rather than contradicting the law. If gain errors/departures persist across A/B, stop the invariant-gain line under those conditions; do not fit drug-specific gains and call that validation. If gain is useful, retain it as exploratory; independent recalculation is computational verification, and future evidence must separately establish biological transfer, novelty and practical acquisition value. Do not promote anything to src/ or tools/.

Bound: one main numeric pilot with a control-only checkpoint; at most30 CPU-minutes cumulative across independent implementations, no new model API calls for science. A native independent reviewer checks protocol/sources before numeric evaluation, then a separate implementation recalculates results. DeepSeek may perform a second, explicitly formula-bound arithmetic support task; it does not choose a metric or scientific verdict.

## Independent-review clarifications (same hypothesis, targets and numeric rules)

Original protocol_v1.md and review/initial_assessment.md are preserved. These are interpretation/provenance clarifications, not a revised fitted model or scientific success. A common nonlinear assay mapping can create or violate the observed MFI restriction despite ordinary concentration-level biology. No standard curve is available here; source's0.8 logic-state cap is not proof of physical assay dynamic range. Success/failure cannot identify or refute a concentration-level law. NumPy linear quantiles are a reproducible explicit convention, not source-certified implementation detail.

H_gain is exactly ordinary proportional response/rank-one: D0*N_d−N0*D_d=0, with D_d=y10d−y00d and N_d=y11d−y01d. No division by a drug-specific D_d is needed. This ordinary alternative is the hypothesis, not a separate mechanism that model success defeats. B_const is the essential distinct comparator; beating additive alone does not favor common gain.

All20target errors, gain-minus-comparator errors and gain-minus-constant prediction contrasts must be retained by drug/preparation. Small comparator contrasts relative to technical prediction envelopes leave discrimination uninformative; no favorable subgroup/new threshold is selected. Report full control denominator and kappa envelopes, including broad intervals. Interval multiplication uses all endpoint combinations, including negative/crossing drug effects. All4local-control calibrations mean target-condition holdout. Exposed source results are prior directions, not extra validation. Between-line differences cannot be attributed to cell identity because cytokine doses differ.

The control-only run used the unchanged numeric rules in initial v1 before target values were decoded, and all4preparations passed its gates. That is an arithmetic calibration condition, not validation of the hypothesis. Its original protocol SHA and numeric checkpoint are retained locally but omitted from this publication; target evaluation binds this final v1.1 SHA. The coordinator's execution decision is scientific admission within the user's prior authorization, not a new user approval requirement.

## Source-code processing boundary discovered after the primary run

The pinned source file `sources/cxcl9_prepare.body` was read after E001. Its R implementation pools the two labeled samples within each cytokine×inhibitor group (and, in its original experiment setup, combines the two preparation files) before strict `>`/`<` IQR trimming. E001 instead trims each preparation×condition×technical sample separately, then averages the two surviving well means. This was a deliberate preparation-holdout analysis convention in the frozen protocol, but it is not an exact reproduction of the paper's preprocessing. The primary and independent results remain labeled E001 under this convention. A separate source-like sensitivity check is recorded as post hoc diagnostic only; it cannot be used to select a favorable result or to claim source-code reproduction.
