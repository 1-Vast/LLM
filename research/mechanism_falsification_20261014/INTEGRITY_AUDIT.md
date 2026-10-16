# Integrity audit: scientific-decision contracts and evaluation boundaries

Study folder: `research/mechanism_falsification_20261014/`. Status: Phase 1 complete (defects reproduced, fixes
implemented and tested). HEAD at start: `9df96f627552def97f72a2fb472f963aeeba2d1b`, unchanged from the last
externally reviewed HEAD; working tree clean.

Everything below was reproduced on miniature in-memory fixtures by
[reproduce_defects.py](reproduce_defects.py) against the **unchanged historical modules**. No frozen study file,
result artifact or hash was touched. `src/maestro/decision_review.py` is itself under the
`selective_hit_triage_20261013` freeze (`FREEZE.json` line 43), so editing it would have invalidated a frozen
study; every fix is therefore a new, separately versioned module.

## 1. Confirmed defects

| Id | Where | Reproduced behaviour | Severity |
|---|---|---|---|
| D1 | `decision_review.review`, [decision_review.py:206](../../src/maestro/decision_review.py) | `review(..., no_signal=True)` with **zero evidence** returns `NO_GO / NO_SELECTIVE_SIGNAL`. The docstring (line 188) says the flag "must itself come from admitted evidence"; nothing checks it. | P0 |
| D2 | same, [decision_review.py:211](../../src/maestro/decision_review.py) | A progression explanation with predictions `engagement_z <= -2` and `rescue_fraction >= 0.5` returns `GO` when only the first is supported; the second is merely listed as `untested:` in `limitations`. The existing test `test_a_model_prediction_can_neither_falsify_nor_progress_a_candidate` pins this GO as expected behaviour. | P0 |
| D3 | `EvidenceItem`, [decision_review.py:120](../../src/maestro/decision_review.py); `AssayContext`, [hit_triage.py:82](../../src/maestro/hit_triage.py) | A source digest is accepted when `len(...) == 64`. An item naming `nonexistent_file.csv` with digest `"f" * 64` is `admitted`. | P0 |
| D3b | `EvidenceItem.independent`, [decision_review.py:111](../../src/maestro/decision_review.py) | A field that nothing reads. Two items with `independent=True` and different digests for one upstream run both count. | P1 |
| D3c | `DECIDING_KINDS` | `DERIVED_ANALYSIS` is admitted with no named parent. The kind is the caller's word, so a prediction relabelled as an analysis decides. | P0 |
| D4 | `DECIDING_STATUSES`, [decision_review.py:54](../../src/maestro/decision_review.py) | `UNDETECTED` is decisive for **any** observable, with whatever numeric value the caller attaches. | P1 |
| D5 | `_dependence_groups`, [acquisition.py:63](../../src/maestro/acquisition.py) | "Actions without provenance retain the legacy independent-trial assumption": unknown provenance is treated as independent. Unknown should be dependent until shown otherwise. The assumption was named in `assumptions`, not silent. | P1 (**repaired, opt-in**) |
| D6 | no unit field anywhere in `EvidenceItem`; frozen reader [outcomes.py:79](../selective_hit_triage_20261013/outcomes.py) | The percent-or-fraction guess `scale = 100 if max > 2` divided every CTRP viability by 100 once overgrowth reached 2.66. It was corrected after opening (see that study's DEVIATIONS.json). The contract layer has no unit at all. | P0 (evaluator) |
| D7 | `information_tier.admit`, [information_tier.py:82](../../src/maestro/information_tier.py) | Tiers are the caller's declaration. A T1 input declared T0 is admitted unless the caller also passes a registry. Same class as D3. | P1 (**repaired in a new module**) |
| D8 | `endpoint_decision.choose` | `VALIDATED_SCOPE` (GCP histone peptides, 24 h, A375 anchor) is a constant that is never enforced; `abstain_below=None` by default means no abstention. A forecast outside that scope is ranked without refusal. | P1 (**repaired, guarded entry point**) |
| E1-E7 | frozen `knowledge_reality_20261013/confirm.py` | See `research/evaluator_audit_20261013`. The evaluator never ran; findings are converted to tests in section 3. | as audited |

**What was not a defect.** `claim_audit.audit` re-reads artifact bytes and recomputes the digest, so its
authentication is real. `hit_triage.nominate` is order-invariant, and `OutcomeSeal.release` compares the digests of
the bytes it is handed. `decision_review.evaluate_prediction` uses `all()` over admitted items, so duplicating an
item cannot turn a contradiction into support. `exploration_tournament` refuses probability use as documented.
These are left untouched.

## 2. Old versus new behaviour

Historical semantics are preserved for frozen studies (`test_historical_review_semantics_are_unchanged` pins both
D1 and D2 as the old behaviour). The strict policy is `strict-review-1` in
[strict_decision_review.py](../../src/maestro/strict_decision_review.py); it is opt-in and named in every decision
(`StrictDecision.policy_version`).

| Case | `decision_review.review` (historical) | `strict_review` (`strict-review-1`) |
|---|---|---|
| `no_signal=True`, no evidence | NO_GO | cannot be asked: needs `no_signal_receipt` + `no_signal_rule`; an unknown receipt, unregistered rule, wrong context, prediction, tampered bytes or a value that shows signal is refused with `NO_SIGNAL_REFUSED:<reason>` and the review continues |
| 1 of 2 required predictions supported | GO | NEED_MORE_EVIDENCE, `UNTESTED:<key>`, cheapest discriminating experiment |
| Supportive (optional) prediction untested | not distinguished | GO still possible; listed as `supportive_untested:<key>` |
| All required supported, funded | GO | AWAITING_APPROVAL until a named human approval bound to the basis digest; then GO with `APPROVED_BY` |
| Competing explanation never excluded | not considered | NEED_MORE_EVIDENCE `ALTERNATIVE_NOT_EXCLUDED:<id>` (policy `exclude_alternatives`, default on) |
| Unresolved critical limitation | not representable | NEED_MORE_EVIDENCE `CRITICAL_LIMITATION:<id>` |
| 64-char digest, file absent or altered | admitted | refused `SOURCE_MISSING` / `SOURCE_DIGEST_MISMATCH` (bytes re-read on every call) |
| Three copies of one experiment, 2 groups required | GO | NEED_MORE_EVIDENCE: copies collapse to one independence group |
| Prediction relabelled `DERIVED_ANALYSIS` | admitted | `PREDICTION_IN_LINEAGE` / `NO_LINEAGE` |
| Independent measurements disagree | NO_GO | NEED_MORE_EVIDENCE `CONFLICTED:<key>` |
| No discriminating experiment in the menu | `ValueError` | NEED_MORE_EVIDENCE with `NO_DISCRIMINATING_EXPERIMENT_AVAILABLE` |
| Percent vs fraction | not representable | units convert by division to one canonical unit; wrong dimension refused `UNIT_DIMENSION_MISMATCH` |
| Required receipt withdrawn after GO | n/a | `certificate_problems` lists `RECEIPT_WITHDRAWN`; re-review no longer reaches GO |

A strict contradiction is a qualified, authenticated, in-context, in-protocol measurement of a required prediction
whose rule id equals the prediction key. Everything else is context.

## 3. Fixes and where the tests are

| Module | Contract | Tests |
|---|---|---|
| [evidence_registry.py](../../src/maestro/evidence_registry.py) | source registry, receipts, lineage, independence groups, withdrawal, unit canonicalisation | `tests/test_evidence_registry.py` (7) |
| [strict_decision_review.py](../../src/maestro/strict_decision_review.py) | `strict-review-1` policy, approval, certificate | `tests/test_strict_decision_review.py` (20) |
| [evaluation_contract.py](../../src/maestro/evaluation_contract.py) | C1-C7 as functions | `tests/test_evaluation_contract.py` (8) |

Mutation check: the three modules were mutated at 13 points (digest check disabled, prediction-lineage check
disabled, competitor-exclusion check, approver check, support-gap check, group computation, no-signal rule
check, normaliser authorisation, `/100` replaced by `*0.01`, cross-screen collision check, and others).
Three mutants initially survived (competitor exclusion, hand-built automated approval, the `*0.01` product); tests
were added and all 13 are now killed. The mutation harness is a one-off script, not a committed test.

## 4. Later repairs (D5, D7, D8) and findings that remain open

Each repair keeps every existing caller's behaviour and adds a stricter, named entry point, because the three
modules are promoted and relied on by other studies. None of the modules is hash-frozen except
`information_tier`, so that one is left byte-identical and the strict gate is a new file.

| Id | Repair | Where | Test |
|---|---|---|---|
| D5 | `select_expected_coverage(..., unattributed_dependent=True)`: actions with no source ids share one dependent component, the assumption is renamed `unattributed_actions_treated_as_one_dependent_component`. Default unchanged (`False`), so recorded plans do not move. | [acquisition.py](../../src/maestro/acquisition.py) | `test_unattributed_actions_are_independent_trials_only_when_the_legacy_assumption_is_kept`, `test_attributed_independent_sources_stay_independent_under_the_strict_flag` |
| D7 | `tier_gate.strict_admit` (`tier-gate-1`): a registry is mandatory (`REGISTRY_REQUIRED`); every input needs provenance that names a registered source whose bytes still match; a T0 claim must be checked against the observed-response sets (`COLD_START_VIOLATION`, `COLD_START_UNCHECKED`), so a mis-declared tier cannot pass on its own say-so. | [tier_gate.py](../../src/maestro/tier_gate.py) | `tests/test_tier_gate.py` (6) |
| D8 | `endpoint_decision.choose_validated`: refuses a scope other than `VALIDATED_SCOPE` (`SCOPE_NOT_VALIDATED`) and a missing or non-probability abstention threshold (`ABSTENTION_THRESHOLD_REQUIRED`). `choose` is unchanged for development use. | [endpoint_decision.py](../../src/maestro/endpoint_decision.py) | two tests in `tests/test_endpoint_decision.py` |

Still open, with reasons:

* Existing callers of the permissive entry points (`information_tier.admit`, `endpoint_decision.choose`, the default
  `select_expected_coverage`) are not switched over: doing so would change recorded plans and frozen studies. Any new
  reported decision or claim should use the strict entry points; switching the orchestrator is a separate, reviewed change.
* A declaration is still the registrant's assertion. `tier_gate` makes it traceable to verified bytes and consistent
  with the data handed in, not true.
* **The registry proves bytes, not truth.** A receipt whose source bytes match its registered digest is only as
  good as the registration. Registering a wrong file with the right digest authenticates it. The contract binds
  claims to bytes; it does not certify that the bytes measure what the receipt says. QC provenance
  (`qc_reference`) is a required string, not a verified document.
* **Software CI is not research reproduction.** `python -m pytest` exercises code on miniature fixtures. It
  reads no study. `tools/research_validation.py` authenticates frozen bytes only and states
  `ENGINEERING_ONLY`; with no active protocol it prints `BLOCKED/ASSET_MISSING`. This study adds
  [authenticate_assets.py](authenticate_assets.py), which distinguishes `VERIFIED`, `LOCAL_DIGEST_ONLY`, `MISMATCH`
  and `ASSET_MISSING` for external data (all GEO files used here are `VERIFIED` against GEO's own SHA-512 sums,
  see [DATA_FEASIBILITY.md](DATA_FEASIBILITY.md)).

## 5. Test status

Status vocabulary: `PASS`, `FAIL`, `BLOCKED/ASSET_MISSING` and a scientific `NO_GO` are kept apart.

* Default asset-free suite before this work: PASS (all collected tests).
* New tests: 35 for the strict contracts plus 10 for the D5, D7 and D8 repairs, PASS.
* Default suite after: 903 passed ([TESTS_AND_INVARIANTS.md](TESTS_AND_INVARIANTS.md)).
* Research studies were not re-run; `research_validation` authenticates freezes only.
