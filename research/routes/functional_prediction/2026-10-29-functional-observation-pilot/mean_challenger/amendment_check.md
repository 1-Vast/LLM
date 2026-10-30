# H_MEAN.v1.1 pre-access amendment check

2026-10-29. Read-only scientific/implementation follow-up after the preserved initial review. Read protocol_v1_1.md, protocol_receipt_v1_1.json, amended run_mean_gate.py and launch_primary.py. Computed hashes and inspected the bootstrap NPY header only. No Python program, scientific calculation or raw HTS/count source was executed or accessed.

All nine files bound by protocol_receipt_v1_1.json match their recorded SHA256. The original v1 protocol, design, metadata and original receipt retain the exact hashes recorded in initial_review.md. The amended receipt itself has SHA256 `682b8392597dbc9a06788369f679382deacba7eaac6f583e5068035cc94ec332`.

The bounded calculation can proceed under the retained limits. No material unresolved implementation ambiguity remains in the requested repairs:

- The amendment explicitly takes precedence for the sign rule; the program requires original Delta and the corresponding bootstrap tail to have the same strict sign. Zero and conflicting signs become INCONCLUSIVE.
- Before parsing counts, the program checks all frozen input/script hashes and loads the draw array with pickle disabled, then checks shape `(500,7,2,7)`, dtype `int64` and range 0–6. The actual frozen NPY header independently displays that shape and little-endian 64-bit integer type.
- The parser checks control status, pre72 time, zero concentration, unit, cell/plate/well identity and exact eligible grid membership before response-field conversion. The attempted-access counter now increments immediately before that field access/conversion. Missing or duplicate coordinates prevent successful completion.
- Raw predictions/parameters, normalized and raw training SSEs, losses, plate scores and aggregated outputs have explicit finite-value guards; final JSON disallows NaN. Original solver status/message/nfev and library identity/version are retained, with bootstrap status summaries and no dropped fits.
- CPU checks use total process CPU time, including imports. Internal wall timing starts immediately after importing time. The separately frozen launcher supplies a 180-second child-process timeout covering launch/import/output, captures return code and records timeout termination. Checks cover original fitting, every bootstrap draw, classification and output. CPU/memory limits remain cooperative rather than OS hard limits.

Operational qualification retained: successful adoption requires the completion receipt and successful outer-process record, not merely the existence of primary_result.json. A late resource failure can leave that file alongside an inconclusive exception receipt. On an outer kill the exact partial count exposure may be unavailable; the saved started/timeout records must not be interpreted as zero exposure or permission to replay. This follows the existing no-replay/failure contract and does not request another scientific or code revision.

The original scientific limits T-MEAN-02–05 remain unchanged. This review permits the specified conditional predictor comparison only; it supplies no numerical outcome, equivalence claim, latent-rate validation, biological benefit or novelty conclusion.
