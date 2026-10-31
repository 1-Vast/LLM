# Independent implementation-failure spare admission

Date: 2026-10-31. **Repair admission: `ADMITTED_IMPLEMENTATION_FAILURE_SPARE`.** The previously granted scientific admission, `ADMITTED_NARROW_RAW_ENDPOINT_PROBE`, remains applicable under protocol v2 and the corrected bytes below. This is the single globally reserved implementation-failure spare, not a new scientific experiment, an unfavorable-result retry, or an additional candidate revision. There is no admission for a third matrix or for changing the scientific contract after this spare.

This review is static and repair-specific. No real count/endpoint/performance values were opened, no model was run, and no network request was made. The independent companion arithmetic/access check and complete corrected hash freeze remain the existing launch prerequisites. Original reviews are preserved unchanged.

## Failure evidence

The original `a_launch_receipt.json` records `matrix_number: 1`, `spare_used: false`, `status: FAILED`, and return code1. The original stderr traceback reaches:

`main()` line284 -> `predict_source()` line96 -> `source_features()` line73 -> `numpy.column_stack()` dimension mismatch: baseline length1 versus47,893 pair-feature rows.

Static inspection confirms the cause. `main()` first stores the full two-culture baseline array as `b`. Its floor-QC loop later assigns `a, b = groups[i], groups[j]` in the same function scope. After that loop, `b[source]` is a scalar guide index rather than one culture's baseline vector. This corrupted argument reaches `source_features()` before the first estimator `.fit()` in `predict_source()`. The traceback therefore supports an implementation failure before any estimator fit or predictive performance result. Feature/SVD construction itself was entered with the wrong argument; this was not an unfavorable fitted-model outcome.

The initial static review missed this orchestration-level variable overwrite. This repair review corrects that omission while retaining the original review bytes and failure evidence. The coordinator reports not having inspected endpoint values. Independently, a filename/size-only directory check found only `a_results/endpoints.tsv` (4,533,965 bytes), with no result JSON, prediction TSV or Top100 support TSV. Its contents were not read or hashed by this reviewer.

## Exact minimal code changes

Independent unified diffs show only the following changes in `a_experiment_corrected.py` relative to the original experiment:

1. `source_features()` gains `assert baseline.shape == (len(pairs),)` before feature construction.
2. The output directory changes from `a_results` to `a_results_corrected`, preserving the original partial.
3. The floor-QC local indices change from `a, b` to `ga, gb`; the two corresponding mask/depletion indexing expressions use those new names. The arithmetic of the QC operation is unchanged. This prevents overwriting the baseline array used at the next source-prediction call.

The corrected launcher changes only the freeze filename, launch receipt, stdout/stderr filenames and experiment filename to their separate corrected paths, plus `matrix_number: 2` and `spare_used: true`. It retains the same Python executable,1800second timeout, thread-cap environment, file-hash checks, scientific/arithmetic admission strings and refusal to overwrite an existing corrected launch receipt. It has no automatic retry path.

No source file, eligibility rule, endpoint, mask, fold, feature definition, estimator/grid/default, fit/tuning partition, ranking, precision event, floor threshold, sensitivity readout, scientific gate, resource limit or interpretation boundary changes in these diffs. Protocol v2 is unchanged. The repair restores the intended baseline argument and adds an early contract assertion; it does not select a scientific change using observed performance.

## Independently calculated hashes

| Artifact | SHA256 |
|---|---|
| Corrected experiment: `a_experiment_corrected.py` | `7e94ea162d1e1cc46a8f5913da59035ea884d01aa3f1ff62d3644ef5eea922d0` |
| Corrected launcher: `a_launcher_corrected.py` | `6f4c9f0dfb28721edfc67888c0e7759ac3e29e4685fa47a0f15dd99857be0c30` |
| Original experiment, unchanged | `7530e8888959d0f044ea9b299619cd962924bedbe80083ae5d25f9767d874ce9` |
| Original launcher, unchanged | `20e0c0fb4c1072bb2be10de0ba15d042df4ab892d9b75067e1580b61668cccab` |
| Protocol v2, unchanged | `d7ea7c865bfac661d68309eb5b5c2aec990d08eb85522a69864ae6a53c0800c5` |
| Guide identity TSV, unchanged | `9adbe2671aa6d422f394016677b4f944c9347eacfb8bc6acb07a2b0ba184ea78` |
| Runtime environment, unchanged | `b64e33f5b585fcf0ea4cea8726287d6824e01391825d1801632925972557c308` |
| Original stderr | `757bd6564c364138c192e6162a4948fba928d04a6816b50d678785e46a515ff8` |
| Original failed launch receipt | `af4b5904b5b07bf2580d408dac2c3e4698d3353ebe88014739ab498dd000a343` |
| Initial review, unchanged | `e2497b74b0595eb48e67b43351f92a42af6ab5dd7396838938cd2d84ee406776` |
| Final scientific review, unchanged | `e327111348c14376c7ce2191dc5a8ec13902c5991af3dd71c6c632343df0e445` |

The corrected launcher consumes `a_freeze_corrected.json`; the coordinator must bind it to these reviewed bytes and the companion review rather than reuse the original experiment hash. This reviewer did not write the freeze manifest or alter any original source/review artifact.

## Limits retained

T2, T3 and T5 from the original reviews remain fully active: this is a raw fixed-time abundance endpoint, pseudocount/depletion/shared-control effects are bounded rather than eliminated, and two cultures from a preselected ATR library with dense anchors do not establish biological mechanism, method novelty, sparse assay efficiency or broad transfer. The target-only decisive event and descriptive joint confirmation remain unchanged. A stop/fail of the corrected matrix is terminal under the existing contract.

Additional use for this repair review: zero HTTP attempts, zero model executions, zero real-value access, zero dependency/install/index/commit changes. Requested model/effort remains inherited; effective model identity, tokens and cost are unknown.
