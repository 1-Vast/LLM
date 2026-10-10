# MAESTRO P0.5R exploratory read-only analysis (not an experimental freeze)

All findings are *post hoc*, based exclusively on the uploaded `AXIS_RECOVERY_REPLAY.zip`. No network requests were made. These scripts do not modify scientific source files, do not promote P0.6/P2, and do not supersede frozen certificates.

Unpack the original replay ZIP into a directory, then from this bundle run:

```bash
python check_c44_cached_numeric.py /path/to/unpacked/replay
python recompute_binary_ilp.py /path/to/unpacked/replay
```

The first checks c44 224 old DMSO + 19 newer discovery + 9 already-read holdout expression values against all 62,710 genes; the original 9 holdout rows are not new independent tests. The second solves a binary support set-cover ILP in the retained development index pool; its count-minimizing solution might have different row IDs than the secondary cost-minimizing fixed-count proposal recorded in `EXPLORATORY_REPORT.json`. Both are prospective **index-only** proposals; new RNA values were not fetched. The c45 secondary solution's binary support was also tested independently from the archived index ranges.

The projected 133,564 bytes are expression body bytes only, not network wire bytes or verified total research costs. Any prospective new reads require a separately frozen protocol and budget.
