# Repeat-study maintenance and research entry

This is the current review and maintenance entry. The byte-preserved imported
experiment remains in `../repeat_signal_20261005/`; its final archive report
supersedes the earlier root report, preserved here as `USER_REPORT_ZH.md`.

## Owners and scientific scope

- `REPORT_ZH.md`: this iteration's findings and completed changes.
- `NEXT_EXPERIMENT.md`: one current first-screen research design; not a frozen outcome-access protocol.
- `scientific_review.md`: scientific agent's detailed audit and alternatives.
- `verification_review.md`: independent reconstruction, portability and source limits.
- `maintenance_review.md`: dedicated code/report/asset inventory and preservation decisions.
- `verify_snapshot.py`: the sole maintained saved-result audit; no historical analysis imports.
- `tools/datasets/biological_knowledge.py`: shared read-only feature access; no duplicate research query implementation.

The original fixed code is available for isolated replay, not another active
controller. Two original SQLite files have different permissions: feature
catalog versus measured evidence and candidate predictions. Do not combine them.

## Read-only commands in maestro

Run from the repository root:

```powershell
& D:/anaconda/envs/maestro/python.exe research/astra/repeat_optimization_20261006/verify_snapshot.py
& D:/anaconda/envs/maestro/python.exe -m tools.datasets.biological_knowledge --database research/astra/repeat_signal_20261005/feature_catalog.sqlite repeat_features SIDM00136
& D:/anaconda/envs/maestro/python.exe -m pytest -o addopts= --import-mode=importlib research/astra/repeat_signal_20261005/test_analysis.py research/astra/repeat_signal_20261005/test_biology_recovery.py research/astra/repeat_signal_20261005/test_raw.py research/astra/repeat_signal_20261005/test_rna.py research/astra/repeat_optimization_20261006/test_repeat_features.py -q
```

The imported tests use relative imports without a package initializer, so
explicit importlib mode is required. All four are registered in research scope;
no global import-mode change or copied test suite is needed. Default asset-free
core tests remain `python -m pytest -o addopts= -q`.

The verifier prints JSON by default. Optional `--output NEW_FILE` refuses any
existing destination. Do not rerun original database finalizers or manifest
writers against supplied evidence. Existing receipts are fixed records;
`verification_receipt.json` is the canonical audit receipt. The final rerun
matched it exactly, so no duplicate final-result copy is retained.

## Full replay and source boundary

The package does not include the original ~199 MB fitted Jaaks CSV, ~61 MB raw
ZIP, or ~429 MB DepMap CRISPR source. Their expected paths/hashes are in the
original RUN_MANIFEST.json. Saved score, aggregation and accounting checks do
not require downloading them. Full raw normalization/refitting does.

Follow the imported README acquisition instructions only in an isolated copy.
Verify original hashes before use; do not modify a freeze if bytes differ.
Two external text dependencies have LF/CRLF differences, explicitly recorded
in the new receipt. This is content equivalence, not raw-byte identity.

Feature access needs only the supplied derived catalog. It retains missing
modalities, unknown provenance and biological semantics. Hotspot zero is not
verified wild type; CRISPR dependency is not dose-specific drug inhibition.
Source licenses remain separate and unchanged.

The original knowledge successor README navigation was updated after its run;
its old manifest retains the original README hash. The current tool has also
changed since that run. These are maintained-code changes, not frozen-result
corruption; current hashes are in this iteration's RUN_MANIFEST.json.
