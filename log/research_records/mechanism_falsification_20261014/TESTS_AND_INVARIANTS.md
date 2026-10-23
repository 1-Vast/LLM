# Tests and invariants

New test files (all listed in `pyproject.toml` `testpaths`; D5, D7 and D8 are covered in `tests/test_tier_gate.py` (6) and additions to `tests/test_acquisition.py` (2) and `tests/test_endpoint_decision.py` (2)): `tests/test_evidence_registry.py` (7),
`tests/test_strict_decision_review.py` (20), `tests/test_evaluation_contract.py` (8); fixture helper
`tests/fixtures/strict_evidence.py`. All write temporary files under `tmp_path`, read no study data and call no provider.

## Status vocabulary

`PASS` and `FAIL` describe software behaviour on miniature fixtures. `BLOCKED/ASSET_MISSING` means a replay needs an
asset that is absent or unauthenticated. A scientific `NO_GO` is a result about a hypothesis. They are reported
separately and never folded into one count.

## Contract tests (what each pins)

| Test | Pins |
|---|---|
| `test_a_well_formed_digest_does_not_authenticate_missing_or_altered_bytes` | D3: a 64-hex digest is not evidence of bytes |
| `test_receipt_digest_must_equal_the_registered_digest` | receipt and registry cannot disagree |
| `test_only_measured_kinds_with_a_measured_root_and_no_prediction_ancestor_are_admitted` | D3c, prediction taint |
| `test_status_context_and_protocol_gate_admission` | QC status, context and protocol version |
| `test_independence_is_computed_from_upstream_groups_not_declared` | D3b; unknown provenance is one shared group |
| `test_withdrawal_and_broken_parents_invalidate_dependants` | withdrawal propagates |
| `test_units_convert_by_division_so_boundaries_classify_alike` | D6; exact `[0.29, 0.33, 0.57, 0.58]` |
| `test_historical_review_semantics_are_unchanged` | frozen behaviour preserved |
| `test_a_boolean_or_unknown_receipt_cannot_authorize_no_go` | D1 |
| `test_no_go_needs_an_authenticated_in_context_receipt_that_satisfies_the_registered_rule` | D1: rule, receipt, context, prediction, value |
| `test_undetected_status_is_admitted_only_for_a_registered_no_signal_rule` | D4 |
| `test_one_supported_prediction_is_not_enough_for_go` | D2 |
| `test_optional_predictions_may_stay_untested_but_required_ones_may_not` | required versus supportive |
| `test_go_needs_a_human_approval_bound_to_the_evidence_basis` | approval binds to the digest |
| `test_unfunded_and_unresolved_critical_limitations_block_go` | limitations |
| `test_a_model_prediction_alone_cannot_certify_engagement_or_replace_a_missing_assay` | predictions never certify |
| `test_measured_contradiction_of_a_required_prediction_is_a_named_no_go` | NO_GO route (a) |
| `test_conflicting_independent_measurements_are_not_a_go_and_not_a_no_go` | CONFLICTED |
| `test_no_feasible_experiment_is_a_named_state_not_an_exception` | unidentifiable is a state |
| `test_policy_refuses_a_progression_explanation_with_no_required_prediction` | vacuous GO |
| `test_a_competing_explanation_must_be_excluded...` | strong inference; waiver explicit |
| `test_an_approval_naming_an_automated_actor_is_refused_even_if_built_by_hand` | self-approval |
| `test_the_alternative_waiver_is_part_of_the_basis_an_approval_binds_to` | a waiver changes the digest |
| `test_c1` ... `test_c7`, `test_viability_units_...` | evaluator contract C1-C7 |

## Metamorphic and invariance tests

* **Reordering** the source records over 12 permutations leaves the decision unchanged
  (`test_reordering_source_records_does_not_change_the_decision`).
* **Duplication**: three copies of one upstream experiment never raise the independent-group count
  (`test_duplicating_upstream_evidence_does_not_create_independent_support`).
* **Unit conversion**: declaring 50 percent instead of 0.5 fraction leaves the classification unchanged
  (`test_declared_unit_conversion_preserves_the_scientific_classification`).
* **Withdrawal / alteration**: invalidates the GO certificate and any re-review
  (`test_withdrawing_or_altering_a_required_receipt_invalidates_the_go_certificate`).
* **Outcome invariance of nomination**: changing hidden outcomes, including missingness, cannot change the nominated
  wells (C2).
* **Row locality** of hit labels: removing another test compound cannot change a row's label (C4).

## Mutation check

13 mutants across the three modules (digest check off, lineage check off, competitor-exclusion check off, approver
check off, support-gap check off, group computation changed, no-signal rule check off, normaliser authorisation off,
`/100` replaced by `*0.01`, cross-screen collision check off, and others). Three survived on the first pass
(competitor exclusion, a hand-built automated approval, the `*0.01` product); tests were added and **all 13 are now
killed**. The harness was a one-off script and is not committed; a mutant that survives is a missing test, not a
passing one.

## Gates of the replay

| Check | Command | Result |
|---|---|---|
| Study verification | `python research/mechanism_falsification_20261014/verify.py` | PASS |
| Repository shape (study registered, protocol and verifier present) | `pytest tests/test_repository_shape.py` | PASS |
| Default asset-free suite | `python -m pytest` | PASS, 903 tests |
| Frozen files unchanged | `git diff --name-only` | only `pyproject.toml` and `research/STUDIES.json` (plus `research/REPORT.md` and `research/EVIDENCE.md` if the report entry below is made) |

`tools/research_validation.py` authenticates frozen bytes and states `ENGINEERING_ONLY`; with no active protocol it
prints `BLOCKED/ASSET_MISSING`. A green software suite is not a reproduction of any study.

## Final default-suite result

`python -m pytest` (default asset-free suite, including the 45 new tests): **903 passed in 79.2 s** on 2026-10-14,
run after the last source and test edit. The suite reads no study data; it is not a reproduction of any study.
