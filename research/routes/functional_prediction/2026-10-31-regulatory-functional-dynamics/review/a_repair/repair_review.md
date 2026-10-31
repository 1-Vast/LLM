# A1 implementation repair review

2026-10-31. **PASS_SYNTHETIC_CALLER_FLOW_AND_STATIC_REPAIR_ONLY** for corrected experiment SHA-256 `7e94ea162d1e1cc46a8f5913da59035ea884d01aa3f1ff62d3644ef5eea922d0` and corrected launcher SHA-256 `6f4c9f0dfb28721edfc67888c0e7759ac3e29e4685fa47a0f15dd99857be0c30`. The coordinator must finish and hash-check the corrected freeze before launch. This review does not launch the reserved repair run or admit a scientific protocol change.

## Independently verified failure

The original preserved stderr reports a dimension mismatch inside `source_features`: its baseline column has size 1 while other feature columns have one row per eligible pair. Original main constructs `b` as the two-culture baseline matrix, then its floor-QC loop assigns `a,b=groups[i],groups[j]`. Python loop assignments remain in the function scope. After the final pair, `b` is the last gene's two-guide index vector; `b[source]` is consequently a scalar. `source_features` broadcasts this scalar into its baseline map and reaches `column_stack` with inconsistent row counts. `predict_source` invokes `source_features` before any estimator fit, consistent with the preserved failure stack.

This is an implementation variable-shadowing error, not unfavorable candidate performance. The first real launch and its artifacts remain failed and visible. No endpoint values, prediction values, training statistics or count values were opened by this reviewer. Only source text, the failure traceback, launch metadata and hashes were read. The traceback exposes an array dimension, not a response measurement. The original `endpoints.tsv` was not opened or decoded.

The previous arithmetic review checked local endpoint helpers but missed the baseline variable's state after the main floor loop. Its original report, code, checker and receipt remain unchanged; this review extends the missing caller-flow coverage without revising the historical PASS record.

## Meaningful synthetic regression

`check_caller_flow.py` extracts the exact original/corrected floor-loop AST from main and executes only that isolated loop on synthetic arrays. It never invokes `load_counts`, `main`, `predict_source`, a launcher or an estimator. The fixture has three genes with two guides each, three unordered pairs, a baseline array of shape `(2,3)` and artificial counts of 100 except four ordered constructs set to zero for one culture.

Hand-computable expected floor flags are `[[True,False,False],[False,False,False]]`: four of eight retained ordered constructs meet the low-count rule for the first pair in the first culture. Both source versions produce exactly these same flags.

The original loop overwrites baseline `b` with `[4,5]`; passing `b[0]` into the original `source_features` reproduces the same ValueError class and size-1 versus pair-count mismatch, using three synthetic pairs. The corrected loop preserves the full `(2,3)` baseline array. For each culture, corrected `source_features` then returns finite features of shape `(3,16)` and a graph of shape `(3,3)`, exactly equal to the original feature helper when supplied the intended uncorrupted baseline. Its added shape assertion rejects the scalar baseline before matrix/SVD construction.

This regression exercises the caller's post-QC state and the feature function together. It addresses the missing coverage rather than merely testing the renamed local variables in isolation.

## Exact repair scope

AST comparisons confirm all original experiment functions other than main and `source_features` are identical. Removing the leading baseline-shape assertion makes the entire feature helper identical. Applying only `a,b` to `ga,gb` within the floor loop and changing the output directory to `a_results_corrected` makes original main identical to corrected main. Endpoint, masks, fold, information inputs, model grid, tuning, seed, graph, metrics, detectability/practical gates and readout sensitivities are unchanged.

Launcher AST comparison confirms only these changes: corrected experiment/freeze/stdout/stderr/receipt names and explicit `matrix_number=2`, `spare_used=True`. The original 1800-second timeout, thread caps, prelaunch hash/admission checks and rerun refusal remain identical. The corrected launcher references `a_freeze_corrected.json`, `a_launch_corrected_receipt.json`, `a_run_corrected_stdout.txt` and `a_run_corrected_stderr.txt`; it does not reuse the original failed outputs or receipt.

All files pinned by original `a_freeze.json` still hash-match, including the original experiment, launcher, reviews, checkers and receipts. No original file was edited. The regression checks corrected source hashes before and after execution. The coordinator's corrected freeze should pin the new experiment, launcher, checker, regression result and repair review, retain the original failure ancestry and permit only the one reserved implementation-repair attempt.

## Disposition and limits

The reproduced failure satisfies the brief's demonstrated implementation/environment-failure condition for considering the globally reserved repair attempt. This is a code-repair assessment, not reviewer execution of that attempt or a replacement scientific endpoint. Corrected-freeze verification is a separate metadata-only final check. No additional network request, real numerical audit, scientific fit or matrix/spare run was performed by this reviewer. The original root launch consumed its original attempt; the reserved repair attempt remains under coordinator control.
