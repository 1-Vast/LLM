# Blocked Assets

These assets are absent from a clean release checkout or remain scientifically
unqualified. Local retained files do not establish clean-checkout reproducibility;
missing inputs are not substituted. The P0.5R-Extension separately records its
133,564-byte acquisition and offline repair.

| Asset | Impact | Status |
|---|---|---|
| `data/virtual_cell/tahoe_c39_x_hvg_feature_names.json` | Named by the STATE readout freeze. It is absent from both this checkout and baseline `540bc85`. | `BLOCKED/ASSET_MISSING` |
| `research/astra/state_readout_repair_20261009/PROTOCOL.json` and `FREEZE.json` | Both existing file digests differ from the canonical verifier pins. Baseline comparison confirms the mismatch predates this consolidation; frozen files and pins remain unchanged. | `BLOCKED/SHA256_MISMATCH` |
| `outputs/paper_01286/state_readout_repair/RESULTS.json` | Generated verifier input, ignored by Git. It may exist in a research workspace but is not shipped. | `BLOCKED/ASSET_MISSING` in a clean checkout |
| `outputs/paper_01286/state_feedback_repair/RESULTS.json` | Generated verifier input, ignored by Git. | `BLOCKED/ASSET_MISSING` in a clean checkout |
| `outputs/decision_value_validation_20261009/RESULTS.json` | Generated verifier input, ignored by Git. | `BLOCKED/ASSET_MISSING` in a clean checkout |
| MAP released checkpoints, compatible source/dependencies and Tahoe metadata | Required for a fresh released-weight/native-forward audit; details and recorded digests are in `research/astra/map_release_test_20261008/ASSET_MANIFEST.json`. | `BLOCKED/ASSET_MISSING` |
| `outputs/viability_contrast_20260928/prepared/` | Local prepared PRISM/DepMap pack required by risk-calibration `run10` verification; not tracked. | `BLOCKED/ASSET_MISSING` in a clean checkout |
| P0.5R-Extension retained source ranges and standalone replay ZIP | Local numerical verification qualifies c44/c45's specified 39 coordinates; raw ranges and `outputs/decision_value/P05R_EXTENSION_REPLAY.zip` are ignored assets. | Locally verified; `BLOCKED/ASSET_MISSING` in a clean checkout without the listed replay assets |
| Complete 2,000-gene data axis and STATE checkpoint output order | The 39-coordinate data-file certificate does not authenticate either full axis. | `BLOCKED/AXIS_UNCERTIFIED` |
| New P0.6 execution protocol, control allocation, reference weights and byte budget | P0.6's c44/c45 data-axis prerequisite is satisfied, but no new execution freeze exists. The old c40/c44 noise plan remains blocked because c40 is not qualified. | `BLOCKED/PROTOCOL_UNFROZEN`; P2 and production remain closed |
| LINCS source files and case-memory pack | Required to build or audit the case-memory scientific pack. | `BLOCKED/ASSET_MISSING` unless supplied by the user |

Run `python -m tools.research_validation --verify` to check current study output files and pinned
inputs before calling the frozen verifiers. It prints `BLOCKED/ASSET_MISSING` and exits nonzero
when any required path or hash is absent or mismatched.

The authoritative local qualification is
[QUALIFIED_CERTIFICATE.json](research/decision_value/axis_extension_20261010/QUALIFIED_CERTIFICATE.json).
[P06_READINESS.md](research/decision_value/axis_extension_20261010/P06_READINESS.md)
separates its satisfied coordinate prerequisite from the remaining measurement and
execution gates. Neither record changes the old readout freeze or its missing
feature-name asset or its preexisting protocol/freeze hash mismatches. The current
verification output is retained in
`outputs/research_consolidation_20261010/RESEARCH_VERIFIERS.txt`; the new extension
certificate does not release the canonical readout verifier.
