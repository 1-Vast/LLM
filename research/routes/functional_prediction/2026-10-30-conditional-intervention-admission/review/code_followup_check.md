# Follow-up static check of Stage 1 implementation corrections

Date: 2026-10-30. Overall goal: ACTIVE / NOT_ACHIEVED.

Reviewed script SHA-256 `222941928b8b465e928a6ae7a9761a830b3dc0acb763d01f06d9d001b583d165`, launcher SHA-256 `5b4a51ee6d4ed3a528458acdde33edec74443837bb0c4f50e217d523c6547969`, input-freeze SHA-256 `f6cfc29d36f3871dc8b123af849e7e514b120c73761352d7463b36d8c1350670`, preserved v1.1 SHA-256 `f0ac8bdc5e0e219c5ae4b9a8abf8474c9fbceb2c201f80486b24f447a2b2b480`, and the actual `stage1_implementation_amendment.md`. The prior `code_check.md`, initial protocol review and amendment review are unchanged.

## Disposition at this checkpoint

**HOLD for the remaining extraction-failure part of C2.** C1, the completed-analysis/checkpoint portion of C2, C3 and C5 are resolved in the reviewed code. C4 is substantially resolved, with the minor shape-receipt completion noted below. No scientific endpoint, model, null, RNG order, threshold or held-out boundary change is needed.

## Resolved items

- **C1:** All 19 pinned code/protocol/source/metadata inputs are hashed and compared before `extract_labels`. A mismatch raises and produces a false information gate. I independently recomputed all 19 hashes; every one matches. The input freeze binds the exact code, launcher, split, descriptors, gene roster, source manifest and original S1 workbook, among other provenance inputs. Preflight success and the feature hash are recorded.
- **C2, completed analyses:** Labels and all 49 assignments are retained before the initial eligibility stop. Aligned rankings and every completed full null context are checkpointed with atomic replacement. A later support/runtime failure preserves the previous complete checkpoint and failed status rather than silently dropping completed contexts or skipping a draw. Complete ranks are promoted only on the completion path.
- **C3:** `run_stage1.py` runs the child under a hard 1,800-second `subprocess.run` timeout that includes child imports and numerical access. Python kills and waits for a timed-out direct child before the failure handler reads its atomic receipt. Launcher or normal child failure sets complete status to failed and forces a false information gate, while retaining files. The launcher also requires child `run.json` status complete before declaring success. Use this launcher, not direct `stage1.py`, for the authorized run. Both launcher and child retain replay guards.
- **C4, most fields:** The receipt now records the feature hash, fixed methods/settings/seeds, progress and actual label/feature/index/assignment shapes. The aligned-score and null-score shapes are not separately listed, although these are statically created with the corresponding index shapes and retained in the NPZ. Adding these two shape fields would complete the literal promised shape receipt; this is a minor bookkeeping item rather than a scientific blocker.
- **C5:** Per-compound recovered counts are reconstructed as integers, selected-minus-frequency differences are grouped and resampled as integers, and division by `20 * sampled_member_count` occurs before the same NumPy quantile. Thus exact-zero sampled totals stay zero. The RNG order, group draws and interval estimand are unchanged. Exact integer model selection and tie-inclusive null comparisons remain in place.

The static XML filter, HGNC lookup, source-only eligibility, KNN/Ridge weights, coherent block reassignment and selected-model family remain unchanged from the prior checks. No new scientific calculation was introduced by these corrections.

## Remaining C2 issue: extraction failure still loses its access receipt

`extract_labels` still writes `authorized_calls.csv` and `call_access_receipt.json` only after the complete XML loop succeeds. A normal exception after one or more authorized development score/FDR conversions exits before those writes. The outer handler records a failure string but does not retain `development_rows`, `excluded_identity_rows`, the retained sensitizer rows already accumulated, or an extraction-status/access receipt. This is the specific extraction-failure path requested in C2 of the preserved initial static review; it was not fixed by model-context checkpoints.

Wrap the authorized extraction path so that a normal extraction failure records a failed/partial access receipt and the known counts/authorized rows already decoded, then re-raises. Keep the same screen-before-gene-before-numeric boundary. Do not attempt a continuation, add rows from another partition, rerun the scientific matrix or infer a passed gate from incomplete labels. If a hard kill occurs before a parser checkpoint can be written, explicitly retain/report unknown partial exposure rather than asserting a completed extraction or zero exposure. No new real-data test is required to correct or statically verify this path.

## Verification and limits

Both current Python files passed AST parsing without import/execution. All 19 frozen-byte checks passed. The output directory did not exist at this check; no output or label array was opened. No additional synthetic case, workbook outcome conversion, candidate run, model refit, new source retrieval or network traffic occurred. Public traffic remains **0 HTTP attempts / 0 completed response-body bytes / 0 known partial bytes** for this review.

The scientific limits are unchanged: fixed processed-call association in one selected panel, conditional block exchangeability, source-regimen selection, unknown author correction scope, limited chemical generalization, no physical-effect/independent-biology/practical-benefit claim. A successful future development gate does not release the 63 held-out outcomes. Overall goal remains ACTIVE / NOT_ACHIEVED.
