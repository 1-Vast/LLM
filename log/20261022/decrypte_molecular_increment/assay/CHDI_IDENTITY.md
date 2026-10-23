# CHDI identity discrepancy: metadata-only investigation

2026-10-22. No network request and no molecular numerical values were read. A selective script `research/decrypte_feedback_assay_20261022/chdi_identity.py` decoded only permitted cells A139:F139 of the already archived Table S1 compound-information sheet. The resulting exact cell texts are saved in `CHDI_IDENTITY_CELLS.json`. The saved Shiny landing HTML and processed-file identity metadata were inspected for this name only. The reported internal molecular string is taken from the preserved exposure report, not a new inspection of the molecular body.

## Authenticated identities

| Source | Exact identity evidence |
|---|---|
| Supplement A139 | `CHDI00465983` |
| Supplement B139 | `F-Cyclo` |
| Supplement C139 | `HDAC inhibitor` |
| Supplement D139/E139 | Empty ChEMBL-ID / SMILES identity fields |
| Supplement F139 | `HDAC1, HDAC2, HDAC3, HDAC4, HDAC5, HDAC6, HDAC7, HDAC8, HDAC9, HDAC10, HDAC11` |
| Archived repository file metadata | `f.MSV000093659/other/Dose response data - Jurkat proteome/CHDI00465983/TXTs_Classified/CHDI00465983_ALL.txt` |
| Exposure report's internal drug observation | `CHDI-0046593-0000-003` |

The saved Shiny landing HTML contains no `CHDI` occurrence and contributes no alias resolution. The archived repository metadata authenticates a published folder/filename assignment to CHDI00465983. It does not explain the different internal row drug identifier. The internal string lacks digit 8 relative to the supplemented name after removing punctuation; this is not a punctuation-only normalization. Its suffix is also not explained by the supplement.

## Disposition

**The supplied metadata do not authenticate `CHDI-0046593-0000-003` as a chemical alias of `CHDI00465983` or `F-Cyclo`.** The broad shared HDAC annotation and near-name similarity are insufficient. Do not silently remove punctuation, insert a digit, infer a batch suffix or use edit distance to manufacture agreement. No ChEMBL/SMILES identity bridge is available in this permitted row, and chemistry identity remains unknown as already disclosed in the functional pilot.

Two distinct contracts must not be conflated:

1. **Verified compound/condition pairing:** the current draft requires file metadata and internal row drug identity to agree via documented aliases. This investigation cannot satisfy that requirement for CHDI. Strict preparation under that contract should stop at the mismatch pending explicit disposition; it must not silently claim success.
2. **Published file-assignment analysis:** a separately explicit, scientifically weaker contract could use the dataset author's folder/filename assignment as the association between the functional CHDI label and that assigned molecular file, retaining the discrepant internal string verbatim and flagging provenance uncertainty. That would support only prediction using a published assigned feature file. It cannot authenticate actual same-compound treatment, biochemical mechanism, molecular effect of F-Cyclo, chemical scaffold or specific target identity. A result including that assignment needs this qualification beside the main claim; no result can repair the identity gap by being predictive.

This is not grounds to remove CHDI, repartition drugs, select models from exposed values, or rescue a failed statistical gate. Keep its original development membership and the prior missing-structure handling. Choosing between the strict-stop and explicitly limited file-assignment contract is a scientific protocol decision to record openly before the selective preparation proceeds, including the already disclosed accidental exposure. No additional source was contacted and no author-confirmed alias is asserted.
