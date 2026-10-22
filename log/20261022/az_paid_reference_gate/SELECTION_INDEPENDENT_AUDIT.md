# Independent validation selection audit

Status: **PASS**. No fits, test-target reads, reselection or parameter changes.

Recomputed all 228 candidate score records from 48 saved base predictions, training-only paid priors and legal validation outcomes. Compared 123996 numerical fields; maximum absolute difference 0.

| Endpoint | Ordinary comparator | Enumerator | Mixture effect weight |
|---|---|---|---|
| mae | direct | direct | 0.0 |
| utility | combo_direct | combo_direct | 0.0 |

Deduplication yields 5 base/config final refits, within the frozen maximum 14. Actual completion of refits is outside this validation-only audit.

MAE and U have separately selected policies. The MAE-optimal and U-optimal settings must not be portrayed as one parameter choice that wins both endpoints. Offset eta ties in U retain the first candidate (eta=0); exact ties use stored order, never an approximate tolerance.

All five mixture weights were independently scored per endpoint. The ordinary set excludes the effect candidate, its offset and the mixture; the enumerator includes all reported policies in fixed order.

Historical prediction scores were only checked for consistent use in comparator/enumerator selection; regenerating them would require additional training outcomes/dose fields outside this audit contract.

One pre-script schema inspection displayed a test-role paid-query summary value. It was already paid information, was not a test target, and was not used by this audit; the formal calculation filters training summaries before reading their values. Root confirmed this distinction. No protected target or forbidden feature arrays were read.

Costs are independent verification compute, with zero experiment-search fits. All source inputs remained unchanged; details, tie indices, candidate mixtures and hashes are in SELECTION_INDEPENDENT_AUDIT.json.
