# Experiment record: 2026-10-08

> - **Path**: `log/20261008/README.md`
> - **Purpose**: Summarize the MAP checkpoint audit and risk-calibration development.
> - **Core points**: Released-weight tensor loading and native forward execution were verified, but the authenticated output gene order and training-time semantics remain unresolved. Fixed-policy risk calibration certified no conditional-risk threshold and failed the registered coverage gate.

## 1. Record control

This record summarizes completed studies. It adds no experiment, model or production behavior.

## 2. Research questions and hypotheses

The MAP audit asked whether the released weights support an authenticated native RNA comparison. The risk study asked whether a fixed policy could certify useful decision risk without using evaluation outcomes.

## 3. Materials, data and computational environment

The MAP audit used the pinned public release and already acquired checkpoint assets. Risk calibration used the frozen development packet and previously exposed fold-0 units.

## 4. Experimental design and controls

The MAP checkpoint was strictly loaded and run through a disclosed compatibility bridge. Risk calibration used one fixed training-only policy, disjoint calibration units, exact binomial bounds and explicit abstention for unsupported classes.

## 5. Experiment register and results

The MAP native forward was finite, but its output order and original attention semantics could not be authenticated. Risk calibration selected no conditional-risk threshold; marginal coverage remained below the 20% gate. The subsequent conditional-feedback repair remains development evidence only.

## 6. Deviations, failures and corrections

No missing gene map, training-time forward or independent unit was inferred. Failed and superseded attempts are omitted from this compact release record; baseline Git history preserves them.

## 7. Interpretation and claim boundaries

These results establish execution and a risk-calibration failure, not native MAP response validity, safe deployment, LLM advantage or biological decision value.

## 8. Reproduction and artifact ledger

- MAP receipt: `MAP_RELEASE_TEST.json`; native-forward diagnostic: `MAP_NATIVE_FORWARD.txt`.
- Risk and feedback receipts: `VIABILITY_CONTRAST_V9.json` and `VIABILITY_CONTRAST_V10_REPAIR.json`.
- Current code and protocols: `research/astra/map_release_test_20261008/` and `research/viability_contrast/`.

## 9. Open items and next experiments

Authenticate the MAP training-time forward and output gene order. Test any risk policy on qualified unused units under a predeclared utility and cost contract.

## 10. Curation provenance

The release retains canonical summaries and receipts. The content manifest is generated with `python -m tools.log_manifest`.
