# Independent verification of generic_axis_transfer_20261031

Written by the independent verifier, a fresh-context agent that never saw the run code. It was saved verbatim by
the principal because the harness blocks subagents from writing report files. The machine-readable record is
`VERIFICATION.json`.

**Verdict: PASS.** 139 of 139 checks pass: the 120 required by section 9 and the brief, plus 19 extras. Every reported number reproduces. The study's results reproduce: H1 CONFIRMED, H3 CONFIRMED, leakage control valid in both sets, promote_C1 true. One input discrepancy, which changes no reported number, is listed below. All code is the verifier's own; no run code, development material or run log was opened.

**Checks.**
1. *Statistics.* The verifier re-derived the observed and generic profiles; the saved arrays match them to 4.4e-16. Largest differences: per-compound r 6.7e-16, hit precision exact, means 5.6e-17, contrast mean/t/p 2.0e-15. Holm decisions, leakage control, verdicts and promotion all match. The verifier's own bootstrap (10,000 resamples) agrees within 0.0016.
2. *Arms.* B0 and C1 re-implemented for NCI-60 (10 folds) match the saved predictions to 1.1e-15 and 8.0e-15, with identical missing-value patterns. B1, B2 and L on NCI-60, and all five arms on 24Q2, also reproduce (largest difference 8.4e-15).
3. *NCI-60 inputs.* Keys (419), folds (SHA-256 of the key as an integer, mod 10), killed-line counts and actives (293) reproduce exactly; profiles to 4.4e-16.
4. *24Q2 inputs.* The MD5 matches. Queries (101), parsed rows (101), lines (568), profiles (1e-16) and actives (32) reproduce. No query matches the development pool by InChIKey block, name or Broad ID. The development pool equals its block N and block M sources.
5. *Freeze.* 6 study files, 13 built inputs and 22 sources match FREEZE.json; nothing changed after 04:53:24Z. The 24Q2 matrix was written 24.6 s after the freeze.

**Discrepancy (input construction).** Matching on the InChIKey block, as the run does, 102 sealed compounds are eligible; the run used 101. The missing compound is BRD-K57796080 (3,5-DHPG-(S)), which shares its block with query BRD-A20589515. `keys_24q2.tsv` keeps one Broad ID per block. PROTOCOL.md does not describe this, though its census count of 101 matches it. The file was built at 04:20Z, before the freeze and the 24Q2 download. Its effect is unknown because the sealed row was not read. The enantiomer is inactive (17 of 568 lines killed; 29 needed). A sign flip would need a paired difference below −0.467 (H1) or −0.584 (H3); the observed ranges are −0.154 to +0.134 (H1) and −0.133 to +0.183 (H3).

**Ambiguities.** For each: the reading used, then the effect of the alternative.
1. *Hit count.* Nearest integer, ties to even, over lines where both residuals are defined: reproduces exactly. Rounding down, up, or halves up does not (up to 0.33 on NCI-60, 0.036 on 24Q2); rounding down gives secondary NCI-60 contrasts of +0.0069 and +0.0105 instead of +0.0088 and +0.0152. This reading was chosen after rounding down failed 16 checks. No decision uses this endpoint.
2. *24Q2 activity denominator.* All 568 lines gives 32 actives. Lines with a value gives 33; H1 +0.0147 (p 0.104), H3 +0.0208 (p 0.028); verdicts unchanged.
3. *24Q2 lines.* Exact IDs give 568. Adding the four `_FAILED_STR` lines gives 572; H1 +0.0146 (p 0.111), H3 +0.0186 (p 0.044); verdicts unchanged.
4. *Kill threshold.* 5.60 as written. Using 5.602 changes 32 killed-line cells and no activity flag.
5. *"10 µM".* The nominal LINCS dose label is used; signature counts reproduce for all 1,675 keys. The exact dose of 10 would drop 7 NCI-60 keys and 2 queries; testing that needs the 23 GB gctx.
6. *24Q2 L1000 identity.* Not stated for 24Q2. InChIKey block gives 101 (102 without de-duplication); Broad ID gives 77; the union gives 104.
7. *B2 multi-NSC fingerprint.* The first NSC's SMILES is used; a union would differ for 6 keys.
8. *L permutation.* Resolved: one `default_rng(20261031)`, references permuted fold by fold.
9. *Bootstrap.* The study's draws are not reproducible; intervals agree within 0.0016.

**Notes.**
- C1 centres the query on the reference mean; without that, predictions differ by up to 1.03.
- L's hit precision on actives (0.121 and 0.120) exceeds the 0.10 zero arm (one-sided p 0.003 and 0.004), so 0.10 understates chance for the secondary endpoint.
- RESULTS.json omits arm-vs-Z and the secondary context contrasts; they are computed in check1_stats.json.
- Only the 101 query rows of the 24Q2 matrix were parsed.
- To re-run: v02 first (about 3.5 min), then v03 to v15, then v13_assemble.
