# Dependency Review

## Baseline and method

Reviewed commit: `540bc85801fa78a3a58780b37b81b4197449d107`. The deletion manifest was generated before the first tracked deletion and contains the filesystem SHA-256, baseline Git blob, byte count, reason, scientific conclusion and recovery commit/path for every planned removal.

The closure review covered static imports in `src/`, `tools/` and the retained current studies; `tools/registry.yaml`; every tool `manifest.json`; frozen source lists; verifier `Path`/`np.load` references; `git grep` path matches; current core tests; and local fixture references. Files not assigned to the explicit release closure are in `CLEANUP_MANIFEST.json`. Hash-pinned or verifier-read files remain even when they belong to earlier methodological stages.

## Retained closure

- Production packages: `src/agent/`, `src/maestro/`, `src/virtual_cell/`; all current registered tools and their entrypoints/manifests; `tools/registry.yaml`; core fixtures.
- Canonical research: `research/astra/state_readout_repair_20261009/`, `research/astra/state_feedback_repair_20261009/`, `research/decision_value/`, `research/astra/map_knowledge_pilot_20261008/`, `research/astra/map_release_test_20261008/`.
- Boundary inputs: `research/astra/boundary_acquisition_20261007/packet2/`, its `PROTOCOL.json`, `FREEZE.json`, `method.py`, `execute.py`, and compact `run1` replay receipts. Current STATE verifiers load the packet directly; `run.py` and `verify.py` also check input hashes.
- Boundary replay helper: `research/astra/decision_opportunity_20261007/verify_affordable_replay.py` is retained because the boundary verifier imports its network and path guards.
- Viability risk closure: `run10.py`, `verify10.py`, `conditional_world.py`, `freeze10.json`, `protocol10.json`, package initializer, and every file pinned by `freeze10.json`. The current modules import `prepare`, `run6`, `run8`, `run9`, `world5b`, `qualify`, `qualify2`, and `run7`; these are historical-stage source files but remain necessary for the frozen current reproduction. `freeze10.json` also pins `run3`, `run4`, `run5`, `run5b`, `prepare3`, `prepare5`, tests and other source identities. They are retained to preserve that verifier contract.
- Case storage: `src/agent/case_store.py` remains the only `CaseStore` implementation. `src/agent/memory.py` continues to import it for compatibility.

## Removed scope

The deletion manifest removes historical study trees and result copies outside the named current closure, `tools/datasets/audit_results/`, pre-2026-10-08 dated logs, old report copies, the redundant root innovation/task prose, the old test suites, and tracked generated outputs for superseded case-memory integration. The current scientific record is compressed to the eight canonical rows in `research/EVIDENCE.md` and the four required sections in `research/REPORT.md`.

## Required local assets and blocked states

The three STATE decision studies use the tracked packet2 archive. Fresh verifier runs create outputs under ignored `outputs/`; the output is not treated as an input truth source. MAP's pretrained weights, original source, Tahoe metadata and compatibility packages remain external requirements described by its asset manifest. The viability risk reproduction depends on the prepared PRISM/DepMap pack under ignored `outputs/viability_contrast_20260928/prepared`; absence must report `BLOCKED/ASSET_MISSING`.

The canonical STATE packet2 inputs and frozen outputs for the three current studies are present in this checkout. The MAP release audit still lacks clean-checkout inputs listed in `research/astra/map_release_test_20261008/ASSET_MANIFEST.json`: pretrained weights, compatible dependency bundle, official source checkout, and Tahoe metadata. Those external inputs are `BLOCKED/ASSET_MISSING`; no download was performed. The risk-calibration reproduction's prepared pack is present locally under ignored `outputs/`, but it is not part of a clean checkout and must be reported `BLOCKED/ASSET_MISSING` there. Large local `data/` assets outside the verifier closure were not deleted; they are enumerated as `REVIEW_REQUIRED` because they have no baseline Git blob.

## Limits

Static import and path search cannot prove the absence of every reflective or user-invoked dependency. Untracked packet and run artifacts explicitly outside the release closure were separately hashed and removed; current verifier inputs remain. Any item not confidently removable remains in the release and is identified by the manifest's review list.
