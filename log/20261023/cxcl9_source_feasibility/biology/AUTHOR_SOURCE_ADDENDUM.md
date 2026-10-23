# Independent addendum: pinned author source

The initial Methods-only opinion was sealed before receipt/inspection of these additional files. Read only author README, `01_mechanistic_model/01_preparing_inputs.R`, its `utils.R`, `02_active_learning/optimization.R`, its `utils.R`, and three `data/**/metadata.md` files. Parent reports commit b654a45faf5a80cdb1b514188cc90af8c9565b85; no assay table, saved parameters, predicted outcomes, or peer opinions read. No code executed.

## More precise normalization restriction

The preprocessing code reads AsPC1 E3DA and E3DB, renames Sample1/2 into SampleA1/A2 and SampleB1/B2, and pools bead-event rows for conditionwise IQR cleaning. It subsequently computes arithmetic MFI per cytokine/inhibitor/sample and takes log10 before min-max normalization **within each sample identifier across its entire condition screen**. It then averages these normalized values by condition. The helper uses caret preProcess(method="range"). Thus the actual quantity here is the average of sample-normalized log-MFI, not simply a linearly scaled pooled MFI. Full-screen extrema and samplewise transformations enter before an outcome mask. The earlier Methods-only warning remains correct and is now concrete.

This preprocessing code does not show the complete Caspase correction or the later 0.8 modification; do not claim to have reconstructed that pipeline. A lawful sparse raw-response oracle should preprocess an acquired condition using only its bead events plus any calibration/control conditions explicitly charged and revealed beforehand. Conditionwise pooled IQR across the acquired condition's replicate samples is lawful if those replicate samples are acquired together. It does not require other conditions; the full-screen extrema do. If preserving original sample min/max, report the task as fixed transductive processed-endpoint completion. Do not equate either construction with raw viable-cell-normalized secretion.

## Replicate metadata improves, but does not finish, independence audit

CXCL9 assay metadata identify E3CA/B as BxPC3 at passages P12/P14 and E3DA/B as AsPC1 at P12/P14. Therefore A/B are demonstrably different passage contexts, stronger evidence than anonymous technical duplication. Sample1/2 within each experiment may still be technical or culture replicates; these metadata do not specify wells, experimental dates, randomization, or independent culture preparation. Treat the four sample names as nested within passage/experiment, not four independent biological contexts. Raw rows are explicitly FACS measurements. Bead-event counts cannot justify biological uncertainty estimates.

The active-learning metadata identify AL1A/AL2A as AsPC1 rounds 1/2 and AL1B/AL2B as BxPC3 rounds 1/2. They do not establish that every candidate condition has a measured outcome or that unchosen conditions can be replayed retrospectively.

## Real and synthetic candidate feedback must be separated

AsPC1 metadata describe 24 experimental initial conditions; one 10-condition initial split has a test set described as 73 + (24 - 10), and the all-experimental initial split has 73 test candidates. These counts are metadata, not outcome observations. They must not be interpreted as 97 wet-measured labels. In `02_active_learning/optimization.R`, `CXCL9_values_AsPC1.csv` is read from `synthetic_data`. For each selected candidate, the code unconditionally obtains `synthetic_mean` from that table and writes it into the final-time training row. A comment says “use either experimental value or ... synthetic” but the visible executed source has no experimental-vs-synthetic branch at that point. Its automated multiround replay therefore cannot be treated as a general real wet-feedback oracle without explicit source/data changes and real measurement coverage.

The metadata support initial real-condition completion and selected later wet-measured rounds, subject to raw payload availability. They do not establish a fully observed real candidate pool for comparing counterfactual acquisition choices. A missing unselected candidate response cannot be supplied by the original fitted logic model and then counted as biological validation. Simulated oracle evaluation is useful only with that label and a distinct robustness question.

## Model and agent uncertainty

`calculate_CI` applies a t-test confidence interval to ensemble model predictions. With default non-bootstrap optimization, these predictions are optimization restarts conditional on the same data. The interval is a useful dispersion score, not validated biological measurement or posterior predictive coverage. Calibrated uncertainty would need independent held-out residuals or an explicit observation model; no such calibration has been established here.

The pinned source also loads `initial_parameters.RData` from a previous model before training and warm-starts each corresponding restart in later rounds. Parameter provenance matters for a future strict replay: if the initial parameters were fit to all measured outcomes, restricting the initial label file is insufficient to restore blindness. This is an unresolved audit requirement, not a finding that the saved parameters actually leak. Do not load that protected artifact before its provenance and allowed training scope are declared.

## Revised gate

Maintain REVISE / schema audit. There is a plausible small real-feedback prediction task, and a biologically relevant endpoint. There is not yet evidence for a full real-feedback acquisition benchmark, novel action-update mechanism, cross-task inheritance, or RSI. The source confirms a concrete route to designing a lawful raw-response replay and a concrete reason not to run the supplied multiround synthetic loop as a biological experiment. No new performance claim is made.
