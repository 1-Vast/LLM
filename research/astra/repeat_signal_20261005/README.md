# Repeat signal and cheap biological information

Read REPORT_ZH.md; review.ipynb contains executed result checks and figures. Exploratory extension of repository commit 0f7a99928857dbbc93e2aebb85ecca6c95517389. The unpushed Windows mono-pretraining artifacts were unavailable. No production source or Vis outcomes were changed/read.

- results/: strict repeats, matched orientation, third event and technical repeats.
- raw_results/: plate-local no-fit endpoint, 4424 actions; 95 composite interventions excluded only here.
- rna_results/: continuous-target RNA experiment.
- recovered_biology_results/: actual binary-target hotspot/dependency/RNA, destructive controls and post hoc zero-feature static control. Includes all candidate scores and selected actions.
- feature_catalog.sqlite: no combination outcome labels; drug targets, basal RNA, hotspots and CRISPR dependency.
- experimental_evidence.sqlite: assay conditions, events and 54228 ranking predictions, including unselected candidates. Do not load this outcome database as model features.
- verification_recovery.json: scalar action reconstruction and 14 targeted tests; same executor, no independent-agent review.
- RECOVERY_PLAN.md: snapshot interruption and known-outcome rerun, not a new untouched evaluation.
- RUN_MANIFEST.json: exact shipped hashes, dependencies and execution scope.

## Reproduce

Use a separate checkout of the pinned commit and unpack at research/astra/repeat_signal_20261005. Requirements: numpy, pandas, scipy; review plots also need matplotlib. Versions are in the manifest.

The supplied outputs and small DepMap inputs are immediately usable. prepare_inputs downloads the original fitted Jaaks CSV (~199 MB) if absent and restores the small RNA snapshot. The repository supplies the plate hierarchy. It never downloads Vis. To rerun raw_endpoint, also fetch public file https://ndownloader.figshare.com/files/34010816 to assets/original_raw.zip and require SHA256 51550262aed5440d3c5f54997cc940f429ff5dcb55e6970179d3500ba7c5f61e before execution. The 429 MB CRISPR source need not be downloaded because the derived input is included.

```bash
PYTHONPATH=src:. python -m research.astra.repeat_signal_20261005.prepare_inputs
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 python -m research.astra.repeat_signal_20261005.recover_biology
```

The model runner refuses an existing recovered_biology_results directory: preserve supplied output under another name first, in the separate checkout. Surviving earlier runners analyze, matched_comparison, rna_test and raw_endpoint likewise refuse existing output directories. Never alter frozen hashes to bypass mismatches. Exact result-byte equality may require the recorded software versions. Reruns append outcome-access logs and need a fresh run manifest if repackaged.

finalize_evidence verifies results and extends existing evidence databases once; do not run it against the already-enriched supplied databases. To rebuild databases, preserve both supplied SQLite files, run build_evidence then acquire_mutation_features before finalize_evidence. Do not treat a database rebuild as a new biological validation.

review.ipynb cells were executed top-to-bottom by a plain Python runner and saved with text/PNG outputs; no networked Jupyter kernel was used. It only reads saved outputs, not retraining. The notebook is standard nbformat 4 and can be rerun from its study directory with the dependencies above. Production-loadable coefficient artifacts and an agent bridge are not supplied.
