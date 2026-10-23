# Root audit failure and repair

The first final-audit invocation failed with `AttributeError: 'str' object has no attribute 'items'` in `audit.py` while parsing a role seal. Its `sha256` field was a single digest accompanied by a `file` field, rather than a path-to-digest mapping. This was an audit parser failure, not an experimental result.

The parser now explicitly supports the single-file seal and retains dictionary/list seals and plain path-to-hash mappings. Other scalar metadata is not interpreted as a mapping.

The second invocation exposed a separate path-resolution error: constructive's cross seal uses basenames relative to its own directory, while the audit assumed every relative name was workspace-relative. It failed with `FileNotFoundError` for `D:\MAESTRO\INDEPENDENT_SEAL.json`. Basenames now resolve relative to the containing seal; workspace-relative and absolute paths retain their declared locations.

Only the saved-result/continuity audit is rerun; no experiment is rerun or changed. Final audit outcome is stored in `AUDIT.json` and the subsequent phase manifest in `VERIFICATION.json`. Local sealing does not repair historical global provenance drift.
