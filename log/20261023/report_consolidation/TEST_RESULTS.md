# Consolidation verification

Environment: D:/anaconda/envs/maestro/python.exe, bytecode disabled. HEAD9c6fc0e5aceb3eb1d5485e38abca49d808bfc1fc. No model fitting, new dataset analysis or network/API call in these checks.

- `python -B -m pytest tests/test_repository_shape.py -q -p no:cacheprovider`: exit0, all collected repository-layout tests passed. Includes registered-study shape and runtime/tool dependency boundaries. It does not reproduce the scientific studies.
- `python -B research/distribution_health_qualification_20261023/verify_records.py`: exit0;20retained receipt/range checks and membership hashes passed after raw inputs moved to data/.
- `python -B research/functional_state_sufficiency_20261023/verify_records.py`: exit0;8retained source receipts, API prompt/usage and reviewer-record hashes passed after source relocation.
- `python -B research/report_consolidation_20261023/finalize.py`: final exit0. All1641 archived record/data entries remain available; no614protected source-file hashes changed; all1412retired research paths are absent; all5174data relocations have destination files and no old log copy; active entry-point links resolve.

The first finalization found four broken active-summary links: three references to one result JSON moved into data/, and a malformed mechanism-gap relative link. It exited1; its result remains in FINAL_VERIFICATION_initial_links.json. LINK_REPAIRS.json records the fixes. The final run passed. No assay metric or statistical gate was changed.
