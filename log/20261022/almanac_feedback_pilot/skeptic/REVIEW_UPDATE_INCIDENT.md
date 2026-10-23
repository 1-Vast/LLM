# Review-update provenance incident

The skeptic revised two already freeze-bound files after root's successful selective extraction, without knowing extraction had already occurred. This was a coordination error; the original pre-value-read hashes no longer match the revised review and seal. No claim of completely unchanged blind sealing is warranted.

Changes were restricted to the synthetic-test scope paragraph: replaced the obsolete warning about an unused later-array self-comparison with the corrected statement that the revised test checks finite source-menu selection only, not a full-pipeline perturbation; added metadata-only STUDY_EXCLUSION_DESIGN.json counts (8,870 fits, source n20–30). The seal hash was recomputed and a revision field added. No model, split, protocol, selection rule, prediction or response data was changed by this agent.

At the time of revision I had only read source code, the review/seal and metadata-only source-count summary. I had not read RESULTS, VALUES, PREDICTIONS or any raw response CSV. I did not execute prepare/run or independent synthetic tests. My first authorized results access occurred afterwards in this result-interpretation assignment. Therefore this is post-extraction review drift, not an outcome-directed model change; it still invalidates a claim that every original review binding remained unchanged.

Modification timestamps reported by the filesystem (local timezone Asia/Shanghai):

- Review: 2026-10-22T19:59:26.564459
- Seal: 2026-10-22T19:59:26.572481

Root preserved PRE_RESPONSE_FREEZE_AT_VALUE_READ.json and recorded before/after hashes in root/POST_EXTRACTION_REVIEW_REBIND.json. No original or bound file will be changed further by this agent. All further records use new filenames.
