# Independent pre-fit code review

2026-10-23. Reviewed research/depmap_state_increment_20261023/run.py by static reading against PROTOCOL_DRAFT.md and PROTOCOL_RESOLUTION.md. No biological preparation, numeric data reads, fitting, network or synthetic execution by this reviewer. Root owns synthetic tests before freeze. This review does not modify earlier sealed opinions. Initial reviewed code SHA256 is recorded in CODE_REVIEW_SEAL.json.

## Mathematical implementation

No predictive leakage defect found in the inspected implementation. Each all_grid invocation recomputes source gene means and residuals using its supplied training rows; nested passes only inner training rows. Linear centering/scale, QC mean/SD and RBF bandwidth likewise use that partition. Global Gram construction from allowed observed state does not introduce labels or cross-query feature fitting: source blocks and source cross-Gram centering reconstruct the declared source-only operations. Within-line full-panel context is lawful declared transduction. Heldout function only enters outer metrics; source validation labels enter selection losses. Simultaneously selecting lambda and menu program on inner validation creates selection opportunity but outer heldout prediction remains honest.

C uses per-target source feature centering before target gating and preserves zero cross-target terms. Unseen-source target cross-kernel is zero, so its unspecified global-context fallback is algebraically irrelevant; gene prior falls back to global source label mean. H uses uncentered Gaussian context distances computed from all source context pairs, with same-target gating after exponentiation. F uses uncentered relative-state Gaussian. D/E use globally source-centered normalized linear Gram matrices; B uses source-zscored QC. Gaussian source diagonal is one, making the omitted explicit divide-by-one harmless. Eigh-based ridge implements the n*lambda scaling; tiny negative eigenvalues are clipped consistently with PSD numerical roundoff. This is not a different fitted model in exact PSD arithmetic.

Inner deterministic sorted-group modulo-three splitting is as resolved. Each validation objective weights lines equally; batch outer summary also weights lines equally. Program order, tie selection, independently tuned C/E mixture, full/restricted menu, primary gain, strict line wins and top10 regret rules match. Padding only accepts allmissing transcript rows across a given line's targets; mixed missingness, infinities, negative and noninteger counts fail. This implements documented sparse-union semantics and must not be advertised as generic missing-value imputation.

## Concrete changes before final freeze

1. Preserve all inner out-of-fold grid predictions, not only the selected lambda for each program. The protocol explicitly promises all inner predictions. Current nested returns selected only and run saves these arrays; all five candidate predictions are otherwise lost. Retain validation[name] matrices, store their row identities and lambda grid, and record selected C/E/G outputs separately. This permits independent reconstruction of both lambda and program selection without refitting.
2. Record by-gene finite coverage, dropped nonfinite pair identifiers, line-to-batch mapping/group counts and inner source-gene fallback occurrences. Current PREPARED summary reports only by-line coverage and final source fallback counts. These additions are evidence bookkeeping, not new filtering. Count and preserve original 1593 identifiers, finite subset and padding masks/counts so audit can reconstruct selection.
3. Record scipy and threadpoolctl versions alongside numpy/pandas, and record total fit/selection runtime plus conceptual mixture selection opportunity. Existing counters correctly count 6 elementary models times 5 lambdas per all_grid; G reuses component fits but independently picks two lambdas, so its opportunity is not another single five-lambda model. Do not falsely count a 25-pair grid as evaluated: the algorithm independently selects two component choices and forms one mixture, although there are 25 possible pairs. Explicitly say zero extra kernel fits for G.

These should be resolved before freeze, then root synthetic tests must pass. They do not justify adding new biological models or reading heldout values before finalization.

## Suggested synthetic/code checks

Assert expected source-only gene means in an inner split; mutate outer query labels without changing predictions or choices; translation invariance of centered linear kernels; zero-kernel correction equals gene prior; C/H off-target blocks exactly zero; genuine allidentical RBF fallback; finite outputs with missing source target and nonempty query. Verify all five inner arrays exist and can reproduce each selected lambda and program. Use synthetic inputs only until freeze. Raw output snapshots are more useful than a boolean test alone.

## Scope

Conditional GO_FOR_FREEZE after bookkeeping fixes and passing synthetic verification. No biological result exists yet. Neither this review nor a positive component result proves a novel update mechanism, target-specific information necessity, world-model/agent contribution or RSI. Fixed-menu positive findings still leave nonlinear QC and context-conditioned low-rank alternatives unresolved. Full objective stays active.
