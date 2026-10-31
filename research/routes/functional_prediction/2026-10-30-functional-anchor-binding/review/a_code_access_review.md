# Independent A implementation and access review

2026-10-30. Reviewed before any new A real-data execution. Scope: the proposed A scripts, amended scientific/operator contract, permitted access paths, numerical edge cases and bounded failure/timeout behavior. The reviewer inherited the current model/effort; effective model/effort values were not independently available and are not asserted.

## Verdict

**ADMIT the inspected implementation, subject to the already required final execution freeze and independent arithmetic-verifier freeze. No remaining blocking scientific/operator defect was identified in the final script hashes below.** This is implementation admission for one bounded retrospective matrix, not evidence of model benefit or permission to read protected outcomes. `a_execution_freeze.json` was not present during this review; final manifest contents, exact input hashes and inclusion of these final scripts must therefore be checked before launch. Its absence prevents executing the current code successfully and must not consume the model matrix or repair reserve.

The mathematical candidate is ordinary joint Ridge-100 followed by a source-response spectral projection. This review does not establish a distinct teacher mechanism, new functional information, algorithmic novelty, non-forgetting, physical sensitization, assay savings, prospective superiority or biological benefit.

## Scientific and operator alignment

- `a.py:29-57` constructs source-standardized linear and RBF operators without outcomes. Linear weights use population SD, replace zero SD by one, center source inputs and add the unpenalized response-mean intercept. Joint alphas are 1/10/100; chemical-only and knowledge-only use 100. The RBF uses the reciprocal number of source-varying standardized columns, the specified fallback, source kernel centering and alpha 1. Query-only annotation columns retain the specified linear/RBF behavior.
- `a.py:60-95` centers raw source response columns without per-gene variance normalization. The teacher sees all source response columns, including source-ineligible genes; rarity restricts recommendations only. Positive eigenmodes use the frozen `1e-10 * max(1, largest_eigenvalue)` tolerance. Rank is at most 32. More than 32 positive modes with a numerically tied 32nd/33rd boundary raises `TIED_RANK_BOUNDARY`, including under every null. Zero numerical rank gives the source mean.
- The candidate row operator is `J + (W_ridge100 - J) U_r U_r'`. For the complete source response matrix this equals `mean(Y) + (direct_prediction - mean(Y)) V_r V_r'`; selecting eligible columns after using the complete source teacher is correct. Clipping occurs after reconstruction. No query response enters normalization, source eligibility, frequency, teacher modes or prediction construction for that query fold.
- Eligibility is exactly integer `count >= 1` and `count * 10 <= n_source`; fewer than 20 eligible genes terminates the matrix. Frequency divides an exact source count once. Stable decreasing-score sorting preserves canonical lexical tie order provided the pinned parent genes are lexical, as required by the input contract. All eight methods use the same source-eligible universe, including queries with zero calls.
- `a.py:158-179` applies each frozen mapping to the entire response matrix before fitting/scoring, so destination row `i` receives response row `mapping[i]` for both source and query truth. Source teachers, frequency, eligibility and response predictions are rebuilt per null; outcome-free feature operators are correctly reused. Exact integer recovered totals select the best of all seven ordinary controls; the aligned winner uses first-listed ties and each null reselects its maximum. The fixed candidate is index 7. Integer gain comparisons and the `/50` p-value match the contract.
- The 2,000-draw bootstrap uses lexical `np.unique` scaffold order, seed 20261031, integer group differences and sampled compound denominators, with NumPy's default linear quantiles. Summary precision, recall, zero-call recall, oracle, mobility and annotated-subset descriptions align with the written contract. Its interval remains conditional on the fixed saved predictions and the selected aligned comparator.

## Access, pinning and bounded execution

The scripts' explicit array reads are confined to the corrected exposed development `labels.npz`, the parent's chemical-feature archive, the current pharmacology-feature archive and the corrected parent's permutation assignments. No protected 63-compound calls, S2 numerical values, HTS031 values, historical sealed/confirmation responses or network clients appear in these paths. Query chemical identities/features and independently admitted pharmacology are permitted inputs; they are not new experimental function.

This is a code-path assessment, not a fresh audit of real label construction, chromosome/identity masks, source annotations, lexical order, fold membership or coherent-map provenance. The code asserts the principal response and mapping shapes and pharmacology row alignment, but relies on the exact pinned admitted parent assets for the other invariants. The final freeze must list only permitted artifacts and bind their hashes: its hash loop reads every listed file. No real arrays or even array headers were opened by this reviewer.

`run_a.py:16-45` permits one launcher journal and uses `subprocess.run(..., timeout=1800)` to kill/wait for its sole Python child on timeout. It does not restart. `a.py` separately refuses an existing `run.json`. The intended invocation must use `D:/anaconda/envs/maestro/python.exe` directly, because the launcher deliberately inherits `sys.executable` rather than asserting a particular interpreter. The child sets the four numerical-thread environment limits before importing NumPy and encloses the model operators/evaluations in `threadpool_limits(limits=4)`.

Ranks are atomically checkpointed after each completed null and the run receipt records the completed count. A killed operation between checkpoints can leave only earlier completed work; this is correctly incomplete and cannot pass the launcher completion check. Top20 arrays and source eigenvalue diagnostics support the declared bounded checks, not an independent audit of every unsaved prediction. Child CPU accounting is available after normal child completion/exception and explicitly reported unavailable after a forced stop rather than invented.

Two failure-record defects identified during this review were repaired by the coordinator before real execution: failure decisions omitted `conditional_interval_above_zero=false`, and launcher failure did not retain a structured exit code or terminal failed child receipt. Final static inspection confirms all boolean gates are false on both failure paths, nonzero exit codes are retained, and launcher failure marks `run.json` failed with launcher elapsed time and a CPU-availability flag. These changes affect failure reporting only. No scientific setting or real-data fit was changed or executed by the reviewer.

## Synthetic checks

Only synthetic numerical functions were executed; neither `a.main()` nor `run_a.main()` was executed. The bundled CLI was run with the required interpreter, `-B`, and `--synthetic`. A separate in-memory synthetic fixture imported definitions with a non-main run name and compared them to independently constructed primal Ridge, full right-singular-vector projection and centered-kernel calculations.

| Check | Result |
|---|---|
| Bundled projected-Ridge identity | PASS; maximum absolute error `9.71445146547012e-16` |
| Bundled exact-count tie order | PASS |
| Independent primal Ridge and rank-32 full-panel projection, nonzero response mean and zero-variance feature | PASS; maximum projection error `2.6645352591003757e-15` |
| Independently centered RBF/intercept calculation | PASS; maximum error `1.8041124150158794e-16` |
| Zero-rank teacher | PASS; returns zero modes and source-mean prediction |
| Numerically tied rank-32 boundary | PASS; raises `TIED_RANK_BOUNDARY` |
| Synthetic full-panel projection followed by clipping and stable Top20 | PASS |
| Saved synthetic indices versus independently counted integer recovered calls | PASS |

The final changes were confined to failure-record fields and were checked statically after these synthetic checks. No runtime failure or timeout test was performed because the review explicitly excluded main execution. No performance outcomes were read.

## Inspected SHA-256 identities

Paths are relative to `research/routes/functional_prediction/2026-10-30-functional-anchor-binding`. These final hashes were obtained after the coordinator's failure-reporting fixes.

| File | SHA-256 |
|---|---|
| `brief.md` | `16a01753825ce5a170b2fab2ab441e0eacef1574e44918cc838b7ff1fce5d6cd` |
| `protocol_a.md` | `1a5c7704141656330d6fd3c64bc5ba55c3b198526002296d37187f37960ffc63` |
| `protocol_a_v1_1.md` | `991bc330bd8b61564390a60c740d2db22824e6846db2b791d6f74ee7a5dbbd4c` |
| `a_numerical_amendment.md` | `39245e90c793c5d1e27c934390907fe85843cf7064870f24f11252ac412b071d` |
| `output_contract_a.md` | `a5712ff5927b6cfb74563c2d949c12799785cddbcbadf7dfdb05e481bab534c4` |
| `a.py` | `74d6732a7f2386b629177e232911af3ca2f68ff1a086b4134d58b067be53e701` |
| `run_a.py` | `57b5594d8e19db00c1e83322a59899410e9c0daabf71949a24c8adac462bffba` |
| `review/a_protocol_initial.md` | `cc4f09e3212ecf313766cfebbc68277abc3646582b4c77d2b732a9e25145ee08` |
| `review/a_amendment_check.md` | `6cadd179bb966b822728eb8d6bb3032886ca8690cc77946819b76d257859b1f6` |

Access/budget: **0 HTTP requests, 0 completed decoded body bytes, 0 known partial bytes; 0 real-data fits, 0 real-array/header reads, 0 model-outcome reads, 0 installations and 0 code edits by the reviewer.** Only this review is written. No independent agent was spawned. The final execution manifest and real-data saved-rank arithmetic remain separate coordinator/verifier work.
