# Corrections before any new matrix access

The predictor's source metadata field was corrected from identity_QC_cells to the actual identity_qc_cells before execution. A pre-access test passed pair-swap symmetry, mean-of-products construction and heldout-label NaN poisoning for every fit model.

Independent prior review found that the draft protocol's shorthand SHA256 modulo5 omitted the predictor's first8-byte big-endian convention. Protocol now explicitly matches the original code; no split or model was changed after outcomes. The previously reviewed protocol bytes are preserved as STATE_PROTOCOL_PREFIT_SNAPSHOT.md; the constructive preliminary review seal refers to that version. Do not falsely report that the old protocol path is unchanged. Final freeze binds the corrected protocol.

Added actual per-fit timing/count logging (expected600calls for the fixed recipe), and streaming hash checks in extractor/predictor to verify the final freeze without materializing the1.44GB compressed matrix merely for hashing. These do not alter model outputs. No extraction or prediction started before these corrections. Scientific recipes have different regularization geometry/costs and are not claimed to be parameter-matched. Final exact conventional envelope includes additive,mean,q_ridge,linear_ridge,bilinear_ridge,fixed_mixture.
