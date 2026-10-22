# Advocate actual protocol and implementation cross-review

2026-10-22. This review follows the independent draft and the opposing discussion recorded in `ADVOCATE_CROSS_PENDING.md`. I read the revised complete `MEASURED_PROTOCOL.md`, complete `driver.py`, the model/metric implementations and the source-only selected-row and assembly logic in `prepare.py`. I did not open real DATA/CSV/ZIP response values, run a biological fit, or run the measured driver.

Snapshot hashes at this review checkpoint (subsequent targeted changes require corresponding confirmation):

- `MEASURED_PROTOCOL.md`: `4dc3216a1239227a5efb2e278d2ea2dad9275c9b241fadb45a286056bb2d30c2`.
- `driver.py`: `1ec1d9a0f496ed03dcbc6834f49439f1082fe2cfaac34364e3d259849029a067`.
- `metrics.py`: `19cc673a3f61e531a736759d5a55b3bab07f42c3af827a0206b9d4fbfd3468b7`.

## Evidence supporting the bounded ordinary experiment

The revised protocol resolves the previous MAE-only optimization concern: all 48 selected-fit validation prediction arrays are reused for endpoint-specific base configuration and offset-eta selection. Effect receives the same endpoint-specific optimization. Mixture uses each endpoint's own selected effect and direct-offset policies. The validation enumerator searches the registered completed policy menu; final refits cache unique base-arm/configuration pairs and are capped at 14. This is an ordinary finite menu, with all component costs disclosed.

Static driver tracing supports the intended isolation. `role_score` slices to the requested role before scoring, so prediction NaNs in other roles do not enter metrics. Fitted prediction arrays have finite values on the requested valid-input mask; other rows remain NaN. Mixture endpoints operate on finite rows inside that mask; outside-mask NaNs are sliced away or explicitly abstain. Nominal test actions are formed from test-role predictions and paid effects, translated from role-array positions to original global indices, then saved before target conversion. Evaluation translates the sealed original indices back into the same role-array positions. Ascending `flatnonzero` preserves the original global tie order. No target-finite reselection occurs.

The metrics implementation now returns both nested diagnostics and compatible top-level endpoint fields. It explicitly separates forecast finite-row panels from full-target-matrix recommendation panels, keeps nominal denominators, detects zero assigned-MASTER contributors, rejects nonfinite predictions on valid-input rows, and produces aligned MASTER vectors. Nine meaningful synthetic tests passed, including 95% boundary coverage, hidden target missingness, fixed actions, episode-to-MASTER aggregation, and paired 10000-resample bootstrap. Model tests separately passed with correct residual, weighting and input permissions. Synthetic results are engineering checks, not biological evidence.

`prepare.scan_csv` checks every selected matrix against frozen nominal row counts, positions and design dose support. `assemble` retains every nominal target row, uses constant per-episode validity, leaves test y unobserved, and excludes reserves. Thus deriving assigned MASTERs from current nominal rows is equivalent in the intended path, although a direct frozen-list invariant is preferable as noted below.

## Remaining corrections and report obligations

1. Root/data have identified that a paid witness can cover the target drug's monotherapy doses while all observations for some partner-drug dose are missing. Its offset summary then has no usable residual. The shared paid-input interface must either mark this as a common abstention under the stated complete paid encoding or implement a separately preregistered ordinary missing-offset rule. Do not silently discard offset calibration, switch witness, or give a special candidate-only panel. Data agent owns the correction and poison test. This review does not certify the correction before reading its resulting code/test.

2. Add a low-cost load invariant comparing each role's nominal MASTER set with `DESIGN.role_cells`, and ideally its frozen counts. Passing `assigned_masters=sorted(set(cells[idx]))` alone cannot detect an earlier erroneously deleted MASTER, even though the present preparation path preserves them. The metric API already supports an explicit full assigned list and rejects zero contributors. Scientific_skeptic independently agrees this invariant is appropriate.

3. The revised protocol promises paired effect-versus-dose and full-direct-versus-combo-direct attribution, support-rectangle and dose/effect plateau diagnostics, and missingness by role/cell/pair and input/target reason. These were not present in the driver I read. Implement these deterministic reports and relevant synthetic checks before freezing the complete analysis code. They must retain all primary rows/panels and cannot become a favorable subgroup search. The stored MASTER vectors support attribution without extra fits. Scientific_skeptic agrees these are existing reporting obligations, not new success gates.

## Resolved opposing positions and remaining scientific limits

Full nominal matrix finiteness is sufficient for the combined utility/oracle-regret report, not mathematically necessary for fixed-top-five mean utility alone. Both reviewers accept it as the simpler registered common-panel rule. Coverage above 95% does not prove ignorable missingness, and complete-case conditioning must be stated. No extra MCAR qualification gate is proposed.

Endpoint-specific optimal configurations can establish the effect family's performance on two separately optimized tasks, not that one fixed-parameter model wins both. Equal episode mass during fitting is not equal cell mass; the shared fitting convention and separate equal-cell evaluation are explicit. Ordinary mixtures containing the effect endpoint may match it, so a primary gate pass cannot be called a win over equal-menu program search. No component is by itself a new operator, a cellular dynamics world model, a scientific agent, inheritance, joint benefit, or RSI.

## Decision

Conditional GO for this one bounded **ordinary structural opportunity** experiment after the identified paid-input correction, explicit role invariant, complete registered reporting code, full synthetic driver tests, and final freeze are confirmed. No objection remains to the revised selection, nominal-action sealing or common-panel primary estimands as designed. This is not an unconditional authorization based on uninspected future code. Preserve the existing useful-effect thresholds and exact-configuration STOP; a failure must not trigger retuning the exposed test, a new favorable panel, or added complex modules. A pass warrants later novelty review on still-unopened reserved tasks and does not complete the user's new-core/world/agent/RSI goal.

## Final recheck and decision: GO for the registered ordinary gate

I subsequently reread the final driver, its synthetic integration tests and `DRIVER_SYNTHETIC_03.txt`, plus the corrected paid-summary/input-validity code and the relevant preparation synthetic tests. No real response file was opened or measured run executed by this reviewer.

The three previous implementation items are resolved:

- `load` now compares every role's nominal MASTER set directly with frozen `DESIGN.role_cells`, checks episode metadata index order, and rejects a nominal episode with no rows. The synthetic integration test deliberately adds a missing assigned MASTER and verifies rejection. It also poisons an input test target and verifies rejection.
- `paid_summary` collects every nominal paid drug-dose requirement and records whether each has at least one finite observed monotherapy. Episode validity requires this for both paid witnesses, including their other partner drugs. Thus valid episodes have the local offset's own monotherapy references; the whole episode commonly abstains otherwise. `test_common_whole_episode_abstention_with_no_retarget` covers `mono`, `partner_mono`, and `combination` failures. `PREPARE_SYNTHETIC_TESTS_04.txt` reports nine tests OK.
- Evaluation now writes every registered effect-versus-policy paired comparison, direct-versus-combo attribution, support-rectangle summaries, nominal-input-defined plateau pair counts with separately counted finite/missing response pairs, per-episode role/cell/pair/input-reason/target-finiteness records, and full fitting/evaluation stage elapsed costs. These are descriptive reports and preserve the original primary panel. `DRIVER_SYNTHETIC_03.txt` reports six tests OK, with the integration path producing 48 selection fits plus four cached final fake-model refits, sealed nominal actions before test labels, seal-tampering rejection, and complete evaluation/report execution. These are synthetic pipeline checks; the fake-model numbers have no biological meaning.

An additional opposing scientific point is resolved without adding modules or another gate. For a fixed base configuration, the local offset is an episode-constant shift `eta*c_e`. It therefore leaves the ordering of `Yhat_i-max(u_i,v_i)` unchanged within that episode. In a mixture, its contribution is the same constant `(1-w)*eta*c_e`, also leaving ranking unchanged. Offset is forecast calibration, not a recommendation adaptation mechanism. The unified registered grid can remain; in exact arithmetic its U policy is equivalent to its corresponding base and stable ties select the first eta/configuration. Any finite-precision near-tie action difference must be reported as a numerical tie effect, not agent or adaptation evidence. Scientific_skeptic and I independently agree; root will state this interpretation in the protocol/report.

Final checked hashes:

- `driver.py`: `f6de7623f8f138505bd08a223cd857741a74a1d9f4bb6f051134678cfa6f1d97`.
- `test_driver_synthetic.py`: `32be8c88a44b6c4744263ccc467df3d0bad6514031551bbe409325bb7a11aef9`.
- `prepare.py`: `a4d8c84bf66700c9778252dc371cad21ff0c5207a3cbff6f7ade953635b5024e`.
- `DRIVER_SYNTHETIC_03.txt`: `72131fa5912acc88d8db2f000fedcdd4796230d6c1a53eb5ee32e649c782efa4`.

**Final decision: GO to freeze and perform this one registered ordinary paid-reference gate.** I have no remaining blocking scientific-design or implementation objection in the reviewed scope. Preserve the existing freeze, one-run seal sequence, coverage/usefulness/headroom thresholds, all reserve exclusions, full positive/negative reporting, and exact-configuration STOP. This GO is not evidence that any useful structural effect, new mechanism, world-model contribution, agent contribution, inheritance, joint benefit or RSI has been demonstrated. A negative gate remains a negative result and cannot be rescued by reinterpretation or tuning this exposed test.
