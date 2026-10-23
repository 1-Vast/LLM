# Statistical response after independent cross-review

2026-10-23. Read `PRIMARY_REVIEW.md` and `EVIDENCE_REVIEW.md` after saving `STATISTICAL_REVIEW.md`. This response preserves those independent originals. No numeric response payload or protected/reserve outcome was opened. The new regression checks below use invented decision records and stubbed test results only.

## Capital protection: agreement with a necessary correction

The primary review's distinction is correct. A fixed, self-financing pair of wallets W_t = 0.5 E_base,t + 0.5 E_adapt,t preserves W_t >= 0.5 E_base,t on the same observation path. If both wallets are globally valid, so is their fixed mixture. Portfolio e-BH at alpha then contains the base wallet's alpha/2 discoveries on that same path and hypothesis family. This is not a guarantee against a standalone baseline that would buy different reads.

The existing `replay.gate1_run` is a mixture of next-read factors, not that pair of wallets. Its round-1 PF factor receives weight 1/3 and its round-2 PF factor receives weight 1/2. The direct pathwise lower bound is therefore 3^(-n1) 2^(-n2) E_PF, not 0.5 E_PF. Even a 1/2 base weight at every step would yield only 2^(-n) E_base. None of these algebraic lower bounds supplies base-process validity under the real assay law. A future protected-wallet implementation must also specify self-financing capital allocation when experts are born or replaced; free initial capital cannot be added repeatedly.

## Credit: prediction on selected reads is observable; policy utility is different

All frozen candidate densities/bets can be scored on a purchased observation. That supports a comparison of their prediction scores on the selected-action distribution. A learned expert may be scored on round 1 to choose a future round-2 weight without retrospectively changing round-1 wealth. This is compatible with predictable betting under the necessary conditional base-law contract, but is an in-sample credit score rather than evidence of later improvement.

Allocation policies purchase different actions and cause different subsequent histories. Same-stream scores do not reveal those missing outcomes or identify the resulting alternative adaptive trajectory. A prospective allocation-credit study needs a precisely limited estimand, logged probabilities with positivity, and an estimator with its uncertainty and cost charged. Complete retrospective observations can evaluate predefined policies in a replay; the availability/selection conditions and the difference from prospective evidence must remain explicit. Discovery FDR alone does not certify beneficial editor adoption or recursive improvement.

## Minimum Jaaks diagnostic: supported with bounded interpretation

The evidence review's reduced two-phase experiment is an appropriate next resource test. It avoids the unqualified t certifier and a fitted-simulator oracle. Required conditions are:

1. Freeze eligibility, BARCODE-level scout/final role hashes, the original-score rule, response-independent selection among role plates, rounding, missingness handling and utility before reading responses. Verify BARCODE maps to SIDM consistently. A globally assigned plate role prevents the same plate serving as scout for one unit and final for another.
2. On a common eligible universe, pay scout reads for the original-score top 40%, then nominate 20% for finals. Compare original versus scout ranking within that same scout set. The important net-value control is original-only allocation spending the same planned 60% directly on final reads. Selection and cost accounting must be identical wherever the policies share actions.
3. Report observed positive-final counts per planned seven-well read proxy, together with absolute counts, planned/available reads and missingness. Charge every planned scout and nominated final; missing finals contribute no observed success, retain their charge and receive no outcome-based replacement. Shared controls and plate overhead remain excluded proxy costs. A positive final measurement is not a latent true hit or a certified discovery.
4. Freeze the role of thresholds >0 and >0.10 in the decision rule. One can be primary and the other a robustness diagnostic, or the success rule can require both. Do not pick a favorable threshold after outcomes. One hash is the primary replay; further hashes are sensitivity analyses, not independent experiments.
5. SIDM-cluster resampling is reasonable for a selected-line development population if plate membership is nested within SIDM. If a plate crosses SIDMs, use the larger connected plate/line blocks or explicitly restrict the uncertainty claim. Report cluster counts and recognize that a small selected-line sample gives uncertain generalization. Resampling does not remove selection of the original validation pool.

A gain over the costly fixed-scout policy alone means improved reprioritization after paying for scouts. Beating original-only allocation as well is necessary evidence that feedback paid for itself at this budget. With 20% versus 60% final observations, the adaptive arm needs substantial enrichment; this is a meaningful resource hurdle, not an unfair requirement to remove after failure. A clear loss or inconclusive result should stop this frozen configuration, without rescuing it through thresholds, reserves or new salts.

Even a positive result supports a bounded development decision and the next comparison against direct/ordinary allocation methods. It does not establish world-model, agent, inheritance, joint or improved-improver contributions. The primary-source controls, especially direct prediction plus ordinary evidence-growth allocation, remain necessary before claiming novelty.

## Unresolved inference issues

The three reviews agree that real FDR certification remains unestablished. Unresolved items include full-evidence plug-in nuisance fitting, finite null-grid coverage, pair-difference noise, non-null inactive combinations, plate dependence under the global adaptive filtration, and repeated-reporting rules. Passing the newly hardened label logic or a synthetic numerical check resolves none of those scientific assumptions. Plate-rank diagnostics remain diagnostic until their physical assignment/exchangeability contract is justified.

## Surgical hardening delivered

- `research/certified_discovery_gates_20261023/gate1.py`: decision helper requires all 48 planned pool/bettor/budget/stopping cells and no skipped required pool. Labels are `GATE1_DIAGNOSTIC_PASS`, `_FAIL` or `_INCOMPLETE`; `mathematical_certification` always remains `NOT_ESTABLISHED`. Gate 1b outputs `PLATE_RANK_DIAGNOSTIC_PASS` or `_FAIL`.
- `research/certified_discovery_gates_20261023/test_synthetic.py`: failed or empty test selections return exit code 1; a passing selection returns 0. Removed wording that its finite-grid test establishes validity.
- `research/evidence_portfolio_optimization_20261023/test_gate_hardening.py`: lightweight regressions cover a skipped required pool, one missing planned cell without a skip marker, complete-pass versus failed diagnostics, and subprocess exit codes for passing/failing/empty test selections.

Verification: `D:/anaconda/envs/maestro/python.exe -B -m pytest research/evidence_portfolio_optimization_20261023/test_gate_hardening.py -q -p no:cacheprovider` exited 0; all four tests passed, including subprocess checks of the three exit outcomes. Output is recorded in `GATE_HARDENING_TESTS.txt`. No heavy synthetic gate suite was rerun. These edits change decision reporting and failure propagation only. They do not change response preparation, noise fitting, portfolio factors, thresholds or protected-data boundaries. No code was promoted to `src/` or `tools/`.
