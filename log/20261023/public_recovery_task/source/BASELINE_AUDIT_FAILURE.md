# Baseline identity audit local failure

2026-10-23. Initial ad-hoc read_text() did not strip the CSV UTF-8 BOM, producing KeyError 'sample' before writing BASELINE_REUSE_AUDIT.json. The subsequent attempted cross-seal consequently failed on that missing file; no seal was written. Corrected retained audit script decodes utf-8-sig, consistent with the already successful independent result audit. No forecast, result or original seal changed.
