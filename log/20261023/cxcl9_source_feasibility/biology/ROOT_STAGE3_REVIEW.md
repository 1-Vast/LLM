# Review of parent stage-3 diagnostic proposal

Parent proposal received after independent sealing: acquire only four initial raw files E3CA/CB/DA/DB; no AL1/AL2. Aggregate bead MFI by cell/passage-screen/sample/condition; outlier removal within sample/condition; logMFI minus same-sample blank; optional fixed no-inhibitor IFNG+TNFA anchor; ridge additive, interactions and Hamming-kernel baselines; leave whole inhibitor and leave passage out; diagnose repeatable drug-by-stimulus error only. No functional values inspected for this response.

## Support

This is a reasonable narrow diagnostic. Same-sample fixed calibration avoids full-screen extrema; a complete condition reveal includes its duplicate assay samples. The central test should be passage-held-out reproducibility of within-drug stimulus interactions. It can answer whether an error pattern from one passage helps predict the other better than ordinary pooled/direct condition predictors. Two lines are two biological contexts, not a population of independent tasks.

## Necessary qualifications

- A logMFI-minus-logblank output is a log fluorescence ratio, not calibrated CXCL9 concentration or secretion fold change. Background and sandwich-assay nonlinearities remain. Use a literal endpoint label.
- Confirm blank pairing and matched vehicle exposure. Methods indicate 1% DMSO in inhibitor screens but a raw row named None/None alone does not prove the vehicle match. If ambiguous, flag the claim as limited; do not infer a vehicle-control measurement.
- Optional positive anchors must be predeclared and revealed/charged for each sample. An anchor is not a free held-out measurement. A near-zero/negative log-contrast denominator makes positive-anchor scaling unstable; use a predeclared calibration-quality rule from the assay protocol, or retain the blank-centered endpoint without dividing.
- Per-sample conditionwise IQR filtering differs from the visible author's pooled-condition filtering. It is a reasonable new oracle, not faithful code reproduction. Retain unfiltered-MFI sensitivity to show that filtering does not manufacture transfer. Bead-event variability is analytical precision only.
- With whole-inhibitor holdout, purely categorical additive/interactions cannot learn the held-out inhibitor coefficient and a basic Hamming kernel is equally distant from all unseen identities. This does not constitute a strong test of mechanistic drug extrapolation. Report it as a cold categorical-condition completion stress test unless same-information drug/target descriptors supply a legitimate transfer signal. With five drugs, even descriptor transfer has very limited independent units.
- Distinguish a residual recurring by drug/stimulus from a uniquely action-caused error. A direct interaction model can capture the former. Two passages with the same drug cannot establish complete inhibition, action-map correctness, or internal causal trajectories.

## Explicit stops and decision bounds

STOP raw-oracle construction if sample/passage/condition identifiers cannot be unambiguously paired, blank calibration is missing under the declared endpoint, or the files are not actual assay observations. Preserve all failures and do not fall back silently to normalized/synthetic labels. If positive-anchor QC fails, stop that optional scaling; this need not stop a declared blank-centered endpoint if its own requirements hold.

STOP a persistent-error claim if out-of-passage drug-by-stimulus residual structure does not recur or improvement disappears under direct interaction/kernel baselines, unfiltered sensitivity, or honest held-out grouping. No significance claim based on bead-event n. If an effect is present only within one line or one passage direction, retain it as exploratory, not inherited capability. A positive diagnostic permits defining a candidate update law; it does not itself warrant a world-model, agent, inheritance or RSI claim.

The four files can establish feasibility and repeated-condition prediction at most. Selecting which next experiment would have been best in the enlarged original candidate set remains unsupported until those counterfactual outcomes are known. Preserve AL and all synthetic/saved-fit outputs as untouched at this stage.
