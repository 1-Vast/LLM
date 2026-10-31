# Retained implementation-failure note: exact-count ranking ties

Date: 2026-10-30. Overall goal: ACTIVE / NOT_ACHIEVED.

The coordinator reports that the first authorized development matrix completed once, but the independently frozen arithmetic verifier found that frequency-baseline top-20 genes do not match integer source call counts with the preregistered lexical gene tie rule. The first run is therefore not an accepted scientific comparison. No positive or negative scientific verdict is inferred here, and no held-out outcome is released.

## What the prior static review missed

My static PASS did not catch floating-point tie differences inside the frequency/nearest prediction computation. The existing script remains SHA-256 `1ac2ae94a41b1384179248322a5ef857a408fab2ba0ba02b613cc619fa6e07f7`. A source-only reread confirms that `prediction_weights` constructs floating frequency and nearest-five matrices, and `evaluate` computes both as `matrix @ y` before stable lexical sorting.

Stable sorting preserves lexical order only when the computed scores are exactly tied. Different placements of the same number of binary calls can accumulate the constant floating weights in slightly different ways, so mathematically equal frequencies may differ numerically. The same issue can affect nearest-five profile means. Integer totals used for final model selection, p-value ties and bootstrap gains do not repair the earlier gene-ranking difference.

This note records the missed implementation issue without changing the initial PASS/HOLD records. I have not independently opened the first run's numerical arrays or reproduced its mismatch; the verifier's concrete failure is reported by the coordinator. The source code mechanism is independently confirmed. No initial result magnitude, direction or winning method was inspected or used to choose the correction.

## Permitted correction and rerun boundary

The narrow correction is to compute source gene-call counts as integers and divide once by the number of source compounds; compute nearest-five donor-call counts as integers and divide once by the number of selected donors. Equal integer counts then produce identical floating scores under a common denominator, allowing the existing stable lexical gene order to implement the original tie contract. Integer accumulation must count calls, rather than Boolean matrix multiplication that would lose multiplicity.

This changes the numerical implementation of the frozen means and tie rule, not the scientific model. Ridge, compound/scaffold partitions, representative screens, descriptors, eligibility, all 49 complete-block permutations, RNG ordering, source/validation truth, loss, model-family selection and continuation gate must remain unchanged. The same correction applies to every aligned/null context, never just the observed baseline. No tuning against the initial scores is authorized.

The coordinator will preserve the original scripts, input freeze, raw outputs and failed verification byte-identically and use the one predeclared implementation-failure rerun in a separate `stage1_corrected` output directory. The demonstrable contract violation qualifies for that existing exception; it is not a fresh scientific attempt or an invitation to change thresholds. A further failure must be retained without an automatic third matrix or a replacement candidate.

The modified code requires a bounded static check before that rerun. Check exact integer accumulation/division and gene ties for both means, unchanged Ridge and fixed design, separate output path/replay guards, hard time limit, all frozen inputs, retained checkpoints and independent post-run arithmetic verification. This note does not itself approve a not-yet-inspected modified implementation.

## Access and scientific limits

For this note I read only the unchanged implementation source. No result array, new interaction label, held-out call, biological model output or protected historical asset was opened; no real or synthetic calculation ran. Public traffic: **0 HTTP attempts / 0 completed response-body bytes / 0 known partial bytes**. Prior review artifacts are unchanged.

The original limits remain: one selected processed-call panel, conditional block exchangeability, shared controls, source-selected regimens, unknown preprocessing scope, no identified physical contrast, no prospective label-construction independence, and no established practical/biological/mechanistic/agent/novelty advantage. All 63 held-out outcomes remain outside the authorized numerical boundary. Overall goal remains ACTIVE / NOT_ACHIEVED.
