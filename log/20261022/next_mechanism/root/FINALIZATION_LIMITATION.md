# Historical response drift discovered during finalization

2026-10-22. The prepared finalizer was attempted after source and cross-review writes ended. Its predecessor preservation gate failed. A second diagnostic attempt recorded the three exact failures in FINALIZATION_PRESERVATION_FAILURE.json; no scientific experiment was rerun. The other 7,002 of 7,005 predecessor entries passed the recorded comparisons, but full predecessor preservation does not pass.

Affected paths:

- log/20261022/tggates_rna_feedback_pilot/api_reviews/mechanism_advocate/RESPONSE.md
- log/20261022/tggates_rna_feedback_pilot/api_reviews/method_skeptic/RESPONSE.md
- log/20261022/contrast_mechanism_scout/api/RESPONSE.md

All three currently contain the same 52-byte text, `No response was captured before this review closed.` SHA256 `2102b939bbaFe0525bcd4cfc932942f940fa3e31a1c699a33e07cd5cb08b42e4` (case-insensitive hexadecimal). Their observed modification timestamps are 2026-10-22T08:46:04Z, earlier than the new proposal review's direct primary requests at 08:55Z. This timestamp is not proof of authorship or the reason for change. The current root did not write or restore these historical responses. Original inventory expectations are retained unchanged; do not overwrite them or fabricate missing reviews to make verification pass.

The finalizer stopped before writing FINAL_INTEGRITY, PREDECESSOR_PRESERVATION or FINAL_FILE_INVENTORY for next_mechanism. Thus no final-pass claim is made for this phase. The source originals and their seals, current decision, completed opposing reviews and exact falsifiers remain separately inspectable. This is a provenance limitation, not an additional biological experiment result and not a reason to repeat stopped scientific configurations. The external RSI proposal review has its own narrowly scoped evidence bindings and does not certify all predecessor bytes.
