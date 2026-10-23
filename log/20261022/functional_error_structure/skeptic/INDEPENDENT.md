# Fixed descriptive decomposition of ALMANAC functional error

2026-10-22. Independent preparation: read the mandatory full goal and query_teacher_resolution/CONTINUATION.md. No current peer draft read, no network, no biological response array loaded, no model refit. Git HEAD 47a0e2dea5a7dd42379fa17eb3621caf6bd0114c. The full goal remains ACTIVE / NOT_ACHIEVED; current anchor-transport novelty/RSI STOP remains in force.

## Existing evidence and nonduplication

Read the ALMANAC DECISION, DIAGNOSTIC_READER_SCOPE, run.py, diagnostics.py, error_diagnosis.py and skeptic_result_interpretation.py; searched the local phase code and records for centering, affine/scale/offset and decomposition. Prior diagnostics report dose/pair gains, leverage and innovation/error slopes after across-pair centering. They do not report an exact orthogonal decomposition of total surface MSE into a cell-global error, pair-mean contrast error and within-pair dose error. Thus the fixed decomposition below supplies a new descriptive accounting rather than rerunning the stopped innovation-correlation experiment. This search is limited to the identified ALMANAC phase, not a claim to have exhaustively audited every project file.

The established selected-model MSE improvement is ordinary functional feedback adaptation. Study-exclusion mean top89 selection regret worsens despite positive MSE gain. This does not itself imply global calibration caused the gain: saved predictions permit exact accounting, but not biological/assay causality.

## Single analysis agreed with root before response computation

Use only root/PREDICTIONS.npz entries B0-selected, B1-selected, B0-study-exclusion and B1-study-exclusion. Truth is y[30:40, :, :8] from the existing first40-cell VALUES.npz cache. Do not read raw CSV, closed selection/later cells, other reserves, tune predictions or other candidate outputs. NPZ y access physically materializes the already authorized first40 array before slicing; do not claim only development bytes were decoded. No training or correction fitting.

For each development cell, let e[p,d]=prediction[p,d]-truth[p,d], with 887 pairs and eight scored dose positions. Let m=mean_{p,d} e, q[p]=mean_d e[p,d], and r[p,d]=e[p,d]-q[p]. Report exactly three nonnegative terms:

1. Global mean-error term G=m².
2. Across-pair centered pair-mean-error term C=mean_p (q[p]-m)².
3. Within-pair dose-centered-error term D=mean_{p,d} r[p,d]².

Orthogonality gives MSE=G+C+D exactly in real arithmetic. Report per-cell and ten-cell equal-weight means; for each source condition, report signed B0-minus-B1 changes in G/C/D and their sum. Negative component changes are deterioration, and positive ones improvement. No component-fraction promotion threshold, parameter sweep, bootstrap search or new model selection. Verify the numerical identity and consistency with saved RESULT metrics at tolerance 1e-12 absolute (failure stops interpretation).

Root requested this simpler three-term decomposition instead of my initially suggested extra projection onto true pair-mean scale. Accepted: the latter would add an oracle projection and an easy-to-misread relation to ranking. No scale parameter is estimated in this protocol. Therefore the analysis precisely separates mean-shift error from pair-contrast and dose-shape error, but does NOT fully separate multiplicative scale calibration from pair-specific contrast distortion.

## Interpretation and stopping conditions

Adding a constant to every pair score leaves that cell's pair ranking unchanged. Positive global scaling also preserves ordering, but C can include such scale errors; it is not pure rank error. D is orthogonal to the eight-dose pair-average score by construction, so it can improve surface MSE without changing that decision score. These facts make the accounting relevant to the MSE/decision gap; they do not identify why a particular top89 regret changed, prove a repair is available, or establish world-model/agent/RSI need.

The only success condition is a reproducible exact accounting of already observed errors, with explicit retained limitations. If identities or saved metrics disagree, stop and audit indexing rather than reinterpret. If identities pass, report signs and magnitudes without causal labels and finish this diagnostic. Do not use a favorable component to reopen the stopped anchor-transport mechanism, fit a new corrector, open reserve or claim transferable update/RSI value. A later independent mechanism needs its own hypothesis, prior-art evidence and validation contract.

Root will execute the single frozen implementation; this reviewer has not run a parallel data analysis. No research code added by this reviewer because a second competing implementation is unnecessary for this small exact identity. Independent implementation review can follow after root supplies its script, before execution.
