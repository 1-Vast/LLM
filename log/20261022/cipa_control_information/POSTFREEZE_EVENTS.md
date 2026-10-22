# Retained postfreeze observations

- During first-outer-fold execution, a read-only progress command tried reading FIT_TRANSCRIPT.txt before Tee-Object had received any stdout and created it. PowerShell reported the absent transcript. The actual Python PID31268 was confirmed live, and the same exec session57909 was polled again. No model process was restarted and no frozen artifact was changed. The pipeline creates the transcript on its first completed-outer-fold message.

- The same fit session completed all five outer folds and exited 0. Separate Maestro scoring completed and wrote SCORE_SEAL.json before the independent auditor was authorized to read results. Primary gate false; no configuration rescue or reserve opening.

- Independent auditor execution initially failed twice on constant-column decimal/float reconstruction. Both transcripts remain sealed. Only the unfrozen auditor was corrected. Final audit exits 0, max score discrepancy 5e-14. One imputed constant column has tiny nonzero floating std and a large held-out standardized input; all response-valid training subsets have exactly zero centered contribution. Coefficients were not saved; no predictive solver was rerun. See POSTRUN_REVIEW.md and detailed SCORE_INDEPENDENT_AUDIT.json for the bounded interpretation.

- Closing predecessor preservation passed all 6,195 inventory entries. No production src/ or tools/ edit was made in this phase. New mechanism/data scouting uses separate research/log directories, without changing this experiment's stopped configuration.
