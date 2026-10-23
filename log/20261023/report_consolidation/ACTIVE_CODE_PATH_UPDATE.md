# Active code path update

Updated active scripts after the raw-source migration plan separated bulky source bodies from durable log records. These edits change path routing only; no code was deleted and no historical report/result was rewritten.

- `research/distribution_health_qualification_20261023/biology_identity_audit.py`, `build_eligibility.py`, `qualify_metadata.py`, and `review_eligibility.py` now read retained raw metadata from `data/external/research_sources/20261023/distribution_health_qualification/source/`. Their audit tables, eligibility TSVs, receipts and derived JSON remain under `log/20261023/distribution_health_qualification/`.
- `fetch.py` and `probe_sqlite.py` now write fetched bodies and schema strings under `data/external/research_sources/...`; their small JSON receipts remain under `log/.../source/`.
- `inspect_schema.py` reads the SQLite prefix from `data/` and keeps `SCHEMA_INSPECTION.json` in `log/`.
- `remote_schema.py` reads/writes SQLite range blocks under `data/`, while `RANGES.json` and `RESULT.json` stay in `log/`. Image-metadata mode likewise reads the schema receipt from `log/remote_schema` and range bodies from `data/remote_schema`.
- `distribution_health_qualification_20261023/verify_records.py` checks log receipts against data bodies/ranges while keeping eligibility records and verification output in `log/`.
- `functional_state_sufficiency_20261023/verify_records.py` now checks each log receipt against its role-matched body under `data/external/research_sources/20261023/functional_state_sufficiency/`; API prompt/usage and review records remain in `log/`.

The path split follows the prepared `DATA_MIGRATION_PLAN.json`: moved `.body`, schema text and range-block files go under `data/external/research_sources`; receipts, `RANGES.json`, small results, `ELIGIBILITY.tsv`, and review outputs remain in `log`. `propose.py` was not changed.

Syntax was checked by parsing the selected Python source files without writing bytecode. The two `verify_records.py` scripts have not been run; their read-only checks are pending the migration's terminal state. No network/API, data fetch, experiment or model fit was run. The prepared migration map—not a terminal post-move check—was the path source for these edits, so runtime verification remains outstanding.

## Root post-migration verification

After DATA_MIGRATION_RECEIPT reached COMPLETE, root executed both retained read-only verify_records.py scripts. Distribution-health20receipt/range checks plus eligibility hashes passed; state-sufficiency8retained receipts, API prompt/usage and report hashes passed. These are path/retained-record checks, not new biological replication or model validation. The earlier pending statement above records the agent handoff state rather than the final state.
