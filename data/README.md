# Data

[INVENTORY.md](INVENTORY.md) is the authoritative local inventory; [ASSETS.json](ASSETS.json) records file-level observations and source-path claims. Large data stay ignored by Git. Do not open protected outcomes for maintenance.

Use [DATASET_CATALOG.md](DATASET_CATALOG.md) for route-level dataset classification; use `INVENTORY.md` for file-level identity, exposure, and missing-asset status.

- [raw/](raw/README.md): raw experimental inputs.
- [external/](external/README.md): downloaded external datasets, source documents and retained third-party sources.
- [processed/](processed/README.md): derived datasets, model artifacts and detailed numeric outputs.

Keep key reports and result summaries in [log](../log/README.md), and experimental code and tests in [research](../research/README.md). Record data origin, version, current path and hashes in the corresponding log record. Data must survive routine research-code cleanup.

See the [storage policy](../log/STORAGE_POLICY.md) and [consolidated data locations](../log/README.md). Historical paths may require the migration indexes linked there.
