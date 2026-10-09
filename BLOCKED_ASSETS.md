# Blocked Assets

These items are not included in a clean release checkout. No values are substituted for missing
assets, and no downloads were performed during release repair.

| Asset | Impact | Status |
|---|---|---|
| `data/virtual_cell/tahoe_c39_x_hvg_feature_names.json` | Named by the STATE readout freeze. It is absent from both this checkout and baseline `540bc85`. | `BLOCKED/ASSET_MISSING` |
| `outputs/paper_01286/state_readout_repair/RESULTS.json` | Generated verifier input, ignored by Git. It may exist in a research workspace but is not shipped. | `BLOCKED/ASSET_MISSING` in a clean checkout |
| `outputs/paper_01286/state_feedback_repair/RESULTS.json` | Generated verifier input, ignored by Git. | `BLOCKED/ASSET_MISSING` in a clean checkout |
| `outputs/decision_value_validation_20261009/RESULTS.json` | Generated verifier input, ignored by Git. | `BLOCKED/ASSET_MISSING` in a clean checkout |
| MAP released checkpoints, compatible source/dependencies and Tahoe metadata | Required for a fresh released-weight/native-forward audit; details and recorded digests are in `research/astra/map_release_test_20261008/ASSET_MANIFEST.json`. | `BLOCKED/ASSET_MISSING` |
| `outputs/viability_contrast_20260928/prepared/` | Local prepared PRISM/DepMap pack required by risk-calibration `run10` verification; not tracked. | `BLOCKED/ASSET_MISSING` in a clean checkout |
| LINCS source files and case-memory pack | Required to build or audit the case-memory scientific pack. | `BLOCKED/ASSET_MISSING` unless supplied by the user |

Run `python -m tools.research_validation --verify` to check current study output files and pinned
inputs before calling the frozen verifiers. It prints `BLOCKED/ASSET_MISSING` and exits nonzero
when any required path or hash is absent or mismatched.
