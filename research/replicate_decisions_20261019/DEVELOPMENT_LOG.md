# Development log (pre-freeze; search block and reference data only)

All entries 2026-10-19, before `FREEZE.json`. The selection and evaluation blocks were not read by any method code.

1. **Pre-protocol descriptive pass (all roles).** Replicate agreement only (see `EVIDENCE_MAP.md`). No method comparison.
2. **Arena construction.** All-label families produced one 509-compound component. A hash-slot assignment gave unbalanced
   roles (evaluation 589 / reference 405); replaced by a balanced deterministic assignment (metadata only). Edge purging
   per block added. Five `AMBIGUOUS_STRUCTURE` refusals; one empty-SMILES parse crash fixed.
3. **First smoke run on the search block** (q = 20, rho = 1, fixed): `rsd` far below `raw` (D1 0.43 vs 0.79; selected
   pairs predicted 1.77 vs 0.35 observed). Diagnosis: the pool-block noise covariance (pairwise-complete estimate) had 25
   negative eigenvalues (min -0.61), so the posterior amplified noise. **Defect fixed** by clipping each pool block's
   eigenvalues at 1e-3 x median noise variance.
4. **After the fix (search block, q in {5, 20, 40, 100, 200}, rho in {0, 1}, inspected):** calibration near nominal (mean z^2
   1.16-1.61); best q = 5, rho = 0 (D1 +0.052, D2 -0.002 vs raw); utility falls as q grows; the pool-noise term (rho = 1)
   is worse at every q. Reference signal geometry: top 20 axes carry 81% of signal variance.
5. **Tuning moved off the query blocks.** Because step 4 inspected query outcomes for several configurations, the
   configuration is no longer chosen on the search block: `inner_select` chooses (q, rho, q_pca) by replicate-split decision
   utility inside the reference set (input A, target T, five cluster folds, edge purged). First inner run on the search
   block's references: q = 2, rho = 0 best (+0.071), pool term worse at every q, PCA below raw at every rank. q = 2 was the
   grid edge, so the grid was extended to q in {0, 1, 2, 3, 5, 10} and q_pca in {2, ..., 80} (reference data only).
6. **Search stage run** (`rsd_run.py search`, code hashes in `search_code_sha256.txt`) -> `SEARCH.json`.
7. **Search-stage readout (first pass, q = 2, rho = 0, prior on):** headroom gate passed (`raw2 - raw` +0.134 D1, +0.140
   D2); `rsd - raw` D1 +0.052 [0.003, 0.113], D2 +0.007 [-0.023, 0.039]; removing the chemistry prior was better (D1
   +0.057); selected-pair calibration near nominal (claimed 0.81 vs observed 0.76); exploit-first escalation beat KG VOI
   (-0.012 [-0.021, -0.005]); posterior-predictive mean z^2 1.06-1.20.
8. **Changes after that readout (disclosed as search-informed):** `use_prior` joined the reference-only inner grid (so the
   reference data, not the search block, decide it); ablations became "flips" of the chosen configuration (prior, pool
   term); a claimed-vs-observed optimism table for D2-selected pairs was added for every arm. The final procedure was run
   once more on the search block (`SEARCH_v2.json`, code hashes in `search2_code_sha256.txt`).
9. Sensitivity analyses (re-selection bootstrap, reference refits) and line-ending-normalised freeze hashes added after the
   search run; they do not change any search-stage number.
10. **Defect:** the shell edit that added `sha256_text` turned the `b"\r\n"` literal into a raw line break, so the first
    `search2` launch crashed on import before reading any data. Fixed (function body only) and relaunched; the code
    hashes in `search2_code_sha256.txt` are those of the relaunch.
11. **Reporting-only additions after the search2 launch (not seen by the search2 run):** the pre-specified verdict rule
    (`rsd_run.verdict`: Holm over H1-D1/H1-D2 and estimate >= delta_D) and a descriptive D1 split by identity tier
    (strict = component-isolated non-giant queries, purged = edge-purged giant queries). Both were smoke-tested on the
    search block (q = 2, rho = 0, 200 bootstrap draws) before the freeze. `test_rsd.py`'s poisoning test was moved
    from the evaluation block to the search block so that no policy output on a reserved block is computed before the
    freeze.

12. **Search2 readout (`SEARCH_v2.json`; final procedure, inner choice q = 3, rho = 0, prior off, q_pca = 80):** `rsd - raw`
    D1 +0.081 [0.035, 0.132], D2 +0.023 [-0.007, 0.057]; cross-run D1 +0.084 [0.040, 0.123] (a second raw read gives
    +0.068 there); selected-pair optimism raw +0.80, pca +0.42, raw2 +0.56, shrink +0.05, rsd -0.04; selected-pair 80%
    coverage 0.71; exploit-first escalation +0.065 over none, KG VOI -0.008 [-0.019, +0.002] vs exploit-first;
    posterior-predictive mean z^2 1.09-1.24.
13. **Baseline defect found in that record and fixed (no change to `rsd` or its ablations):** with the inner choice
    "prior off", `vc_only` became a zero matrix and `fusion` collapsed onto scalar shrinkage (D1 identical to `raw`),
    because both took the chosen VC's (zero) prior. Baselines now keep their own definitions whatever the inner choice:
    `vc_only` and `fusion` use the chemistry prior (with the prior-on VC's reliability), `shrink` uses the reliability of
    the read around zero. The reference refit sensitivity analysis drew cluster-bootstrap resamples with duplicates;
    on the search block the duplicated references filled the kNN neighbour sets and depressed the refit estimates
    (prior-on refits D1 +0.008 to +0.023 against +0.043 for the unresampled fit, same metric), so it now refits on 80%
    cluster subsamples without replacement and reports the primary metrics. Smoke-tested on the search block before the
    freeze.

14. **Test failure diagnosed:** `test_other_blocks_do_not_train_search_block` failed only because the reference line
    mean is NaN for one listed line (ACH-001192, pool P933), which has no HTS002 2.5 uM read for any compound, and
    `np.array_equal` treats NaN as unequal. The comparison is now NaN-aware; the VC fitted with the other blocks replaced
    by noise was otherwise identical. That line's pairs are unknown in every arm (480 informative lines).

What this means for interpretation: the search block is development data that informed the design (steps 3-5); its
numbers are not evidence for the hypotheses. Only the selection gate and the evaluation block are pre-specified tests.
