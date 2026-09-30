# Independent post-fix review (2026-10-01)

All six original offline reproductions now satisfy their declared contracts under the source hashes recorded in `independent_validation.json` and `final_audit_validation.json`. Original reports, reproducer and receipts remain unchanged. This reviewing agent performed no repair, provider call, fitting or production mutation.

- Null/array/malformed JSON and invalid UTF-8 become DeepSeek protocol errors or Jev refused evaluations.
- The unusable-text response retains its reported 10-token usage and one received response. This is reported usage, not an inferred bill.
- Same-round duplicate suppression works with one or two workers, including an actual concurrent batch of two distinct inputs plus a duplicate. Across-round reuse disabled gives two inferences per round; enabled gives two inferences in the first round and zero additional inferences in the second. Duplicate request IDs are rebound and duplicate compute cost is zero.
- Abstaining results are deduplicated within each round, keep their refusal reason and are recomputed in the next round. No persistent abstention cache was introduced.
- Mixed served-model or state identities produce refusals without judgments/findings or changes to either judgment/stability ledger. Same-identity repetition still records one repeated judgment.
- Nonfinite history is rejected before cache/backend access. Different history/outcome/mode identities remain distinct cache keys. The default log directory follows the execution date.

The dedicated `ModelAuditAgent` remains report-only: valid and defective proposal checks leave caller inputs and reviewer state unchanged, outputs contain no replacement action/repair, and its imports contain no provider, tool, executor, memory or repair dependency. Forecast text does not satisfy prerequisites or authorize terminal decisions.

Review discovered incomplete containment in the new auditor for unhashable inputs, oversized integers and unpaired Unicode. The implementation owner corrected those cases. Final independent checks return `invalid_task_contract` for NaN/oversized budget, Unicode-encoding failure and nonobject cards, and `malformed_proposal` for set-valued proposal metadata. Unavailable hashes are explicitly null; a serializable but inadmissibly large numeric value retains its hash. No hash is fabricated.

The first post-fix receipt's `new_open_cases` field tracks candidates raised during review. Its recorded results already returned `ModelAuditReport` because the owner's first containment correction landed before execution. The final receipt independently verifies exact finding codes and the later numeric/Unicode corrections; that historical receipt has not been rewritten.

The focused existing-plus-new contract suite passed **161 tests in 14.28 seconds**, including the final numeric/Unicode regression nodes. Reusable commands and input/code/environment/output hashes are recorded in `test_execution.json`, the two validation JSON receipts and `artifact_hashes.json`. Scope is offline engineering correctness; no biological superiority, model calibration or live API performance conclusion follows from these checks. No remaining defect was established in this verified scope.
