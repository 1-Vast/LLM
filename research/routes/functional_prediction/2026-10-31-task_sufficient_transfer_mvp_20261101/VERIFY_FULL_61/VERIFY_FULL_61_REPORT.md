# Independent full replay report

The replay was run from `replay_full.py` in the `maestro` environment over all 1,403 compounds, all 578 lines, all five folds and all 20 arms. The only data file read was the frozen `dev_pool.npz`; protocol interpretations and ambiguities are recorded in `PROTOCOL_INTERPRETATION.json`.

Raw transfer and ridge reproduce the frozen runner numerically: `raw_k5`, `raw_k20`, and `ridge_raw` have identical NaN masks and maximum finite absolute differences below `1.2e-14`. Fold assignments also match all 1,403 compounds. The independent implementation does not pass the all-arm equality gate: chemistry differs only for zero-fingerprint singleton queries (frozen output is NaN there), and the GAT/PCA/random/full-residual families have substantial value and mask mismatches. This is a concrete diagnostic result, not a scientific PASS.

The dominant unresolved implementation ambiguity is the meaning of “reference principal directions” for per-option GAT residualization; this replay used PCA on flattened reference-centred option states. The protocol does not specify the exact coefficient convention for the global decomposition or the empty-ik14 hash serialization. Therefore the scientific gate remains `NON_CONFIRMATORY`; no innovation or biological claim follows.

The complete machine-readable outputs are `predictions.npz`, `per_query_metrics.csv`, `RESULTS.json`, `environment.json`, and `VERDICT.json` in this directory.
