# Independent non-fit implementation review

2026-10-22. Data/evaluation auditor `/root/functional_auditor`. **GO for the single registered gate after the normal pre-response freeze. No open blocking finding remains in the reviewed implementation.** This is an implementation/design judgment, not an assay qualification or useful-information result.

Final reviewed SHA256:

| Artifact | SHA256 |
| --- | --- |
| research/stack_conditional_information_20261022/gate.py | `bb41a2c67b03b34958f42d7bdd9b5c0dbf57964cc983d7c44e4fb046bd298739` |
| research/stack_conditional_information_20261022/test_gate.py | `8279097f89c46abc618368ea6d2c88570c081d2ac4b3b50ade7d6e2573cb5619` |
| PROTOCOL.md (V4) | `3db9df46dacd7231361341e602fe9785d3767e3f5ecf23255937690561b64c56` |
| data_auditor/NONFIT_SYNTHETIC_TESTS.txt | `03bb689915ba01059d4c49804f39a8011c9c73fd4f5319362517735c3bae6295` |

The V1 independent draft is preserved at SHA256 `2c81355d310b3847c6bc31788c03d3ba3f33deb595d23af6bd8485a96b2e18da`. Later post-result judgments must be new files; this review and CROSS are not to be rewritten after freeze.

## Scope and verification

Read gate.py/test_gate.py, the updated protocol and old identity/header/collision/acquisition-summary metadata only. No raw/XLSX read, real-source file hashing, assay-value access, network/provider call, or model fitting by this auditor. Root reports its complete10-test suite passed. Independently ran eight synthetic tests, excluding the metadata test that hashes real source files and the synthetic Ridge-fit test. All eight passed (1.214s test time; process exit0), with the exact names and output in NONFIT_SYNTHETIC_TESTS.txt. Instantiating estimator objects in the budget test did not fit them.

At the final pre-review check PRE_RESPONSE_FREEZE.json, RUN_START.json and ACCESS_prefix.json did not exist. This corroborates pipeline staging at that check; it is not a cryptographic or global proof that bytes could not be viewed outside the pipeline.

## Blocking findings found and resolved before responses

1. **Cached early formulas could encode future information.** Initial code accepted a selected numeric cached formula and recorded only formula presence. A formula in an early address could reference a future value, defeating address-only temporal isolation. Root adopted prospective V4: every selected formula, prefix **and** target, is `formula_disallowed` before numeric conversion, regardless of cache. The current parser branches on formula before `float`, preserves value=None and follows/evaluates no references. Tests cover cached and uncached formulas plus closed malformed formula cells. This resolves the identified path without a convenient numerical exception. Plain numeric literals still inherit the documented upstream export/provenance limitations.

2. **Bootstrap population must include all frozen test groups.** The initial implementation used only groups appearing in scored rows. Current `bootstrap` receives all frozen test role groups, including zero-complete groups; sums and counts per group/screen preserve row multiplicity. Repeated sampled clusters repeat their original rows; division is by each draw's screen-specific row count, not an equal-group average. The synthetic unequal-size/zero-observation example independently matches explicit row-weight resampling. Empty-screen redraws are now prospectively declared and counted; the qualified real panel has positive coverage in each screen.

3. **Test-target authorization needed prefix-status verification.** The first seal check enforced keys/seven forecast fields but did not itself compare predicted/abstention status with prefix eligibility. Current `read_stage(test_target)` rebuilds eligibility from the already saved ACCESS_prefix data and calls `verify_predictions` with the expected per-key status before any test-target projection. Missing, changed, incomplete, wrong-key or eligibility-inconsistent forecast files fail the guard. The main path already saved all five selected arms and two fixed anchors before that call.

There is no remaining unresolved blocking defect from these findings in the final hashes above. Root performed corrections; this auditor did not change experiment code or protocol.

## Confirmed operational contract

- **Source and cells:** `make_manifest` uses named rows only, binds each source to its previously authenticated expected hash and exact projected sheet path, and `read_stage` verifies the source hash before projecting values. The old metadata names the T98G+DMSO sheet `T98G^N + DMSO Full dataset`, and the other sheets `Full dataset`; “Full” in the protocol is the table designation, not a requirement for a literally named `Full` tab. Only those selected sheet paths are opened. No87identity-error responses, QC sheet, result-side fields or library Counts are included.
- **Time mapping:** T98G SG C:I and live AC:AI; U2OS SG C/E/G/I/K/M/O and live BL/BN/BP/BR/BT/BV/BX. Old metadata independently confirms AU1=72 for both T98G files, CV1=72 for U2OS; U2OS AU1=88 is not mistakenly used as its target. Other U2OS2h frames and all future SG stay closed. Numeric conversion is restricted to authorized addresses; closed payloads/formulas are not inspected for values.
- **Roles:** hash-defined1,832 groups, the named conflict pair sharing one group, and all three screens sharing each name's role are implemented. Manifest checks enforce5,499 distinct screen/name records. The corrected freeze counter counts distinct groups rather than names. Names/rows/groups/metadata never enter model features.
- **Qualification versus panel:** `coverage` separately returns the full-member/all-screen group guard, the dual-prefix mask and the complete-observation row mask. Fitting/scoring uses per-screen complete rows, without deleting otherwise legal members of partly incomplete groups. The synthetic collision-group example keeps602of603 legal rows despite the group no longer qualifying as fully contributing. Coverage denominators include all fixed role×screen entries, with separate live/dual/D-additional/target/complete counts.
- **Exposure and stopping:** train/validation labels alone precede fitting; their failed qualification returns with0fits and no test targets. Test forecasts/abstentions cover every fixed test key, with seven finite predictions for eligible rows and seven nulls otherwise. A saved SHA256 seal precedes test-target projection. Final qualification failure returns before scoring/gain status. There is no smaller-panel rescue or automatic rerun.
- **Features and fitting:** dimensions19/20/20/21/26, log-D-only ablations, joint endpoints nested in history, residual target anchored at observed L24, train-only scaler, and train+validation-only refit match V3/V4. Mean-one weights `N/(3*n_screen)` are recomputed for each fitting set. The14fixed configurations and five-arm loop produce70trials+5refits; HGB has explicit300iterations with early_stopping=False. Validation macro MAE plus lexicographic config name selects the model, with no test decision.
- **Metrics and decision:** row-weighted screen means followed by equal-screen macro averaging; history comparisons against L-only and all three snapshot/endpoint arms; absolute.05, relative10%, and positive each-screen gates are implemented. All targets/predictions on scored keys are recorded. Group bootstrap remains sensitivity conditional on these fitted forecasters and fixed screens, not biological/model-selection uncertainty. Its interval does not alter the predeclared point gates.
- **Freeze:** the final freeze includes all research Python files, protocol, resolved role/source/address manifest, all current subdirectory Markdown reviews (including this one), and final root test/verification receipts. The source hashes are embedded in the frozen role manifest and rechecked during each stage. Later review edits would invalidate the intended frozen record and are unnecessary.

## Minor findings / reporting limits

The header-map unit test checks prefix-label membership rather than explicitly checking the full ordered header list and72target label. Current addresses have been independently matched to the exact immutable metadata above, so this is a test-strength limitation, not a blocker or a request to tune the experiment. Any future source/schema reuse needs its own exact mapping qualification.

The result label DYNAMIC_HISTORY_PASS must retain its registered narrow meaning: extra intermediate SG coordinates helped these finite forecasters beyond the joint endpoints. It does not prove temporal causality, necessity of every frame, true viability, a new world model or actual triage/agent/RSI utility. If point gates pass with a bootstrap interval spanning zero, report both the registered point-pass and directional instability; do not add a new CI gate or call it replicated significance.

No further pre-run change is required by this review. Once the final hashes/reviews/roles/test receipts are frozen, run once under the registered coverage/stopping rules. Any later implementation exception must be preserved and diagnosed, with no automatic rerun or response-driven feature/model/endpoint change.
