# Independent metadata-only identity review

2026-10-23. Reviewed complete goal, previous DECISION and frozen reciprocity protocol, original pseudobulk code, exact saved author population notebook/source, final/sharing chosen-guide mappings, original GEO feature IDs/symbols and raw guide-identity strings. No peer report or biological response values were read. Code: research/reciprocity_resolution_20261023/identity/inspect_identity.py. Actual maestro execution exit 0; METADATA_AUDIT.json records hashes, all 103 mappings and access scope.

## Finding: source domains were conflated

Pinned author GI_generate_populations.ipynb, extracted population.source.txt lines 22–23, explicitly states: “This guide lands between RHOXF2 and RHOXF2B but appears to have stronger effect on RHOXF2B”, then replaces RHOXF2 in guide_identity with RHOXF2B. Lines 34–38 put this entry in a mixed-purpose name_replacer with three reference nomenclature changes. This is not evidence that the two genes are synonyms. The original reference has two distinct rows: zero-based 14109 ENSG00000203989 / RHOXF2B, and 14112 ENSG00000131721 / RHOXF2. Relabeling a perturbation's intended biological target does not authorize relabeling both measured readout genes to one coordinate.

Final chosen map contains raw label RHOXF2, guide RHOXF2_+_119292286.23-ENST00000371388.3, protospacer GCATGCGTTGTCCTGTAGAC. Sharing map adds RHOXF2B, guide RHOXF2B_-_119211886.23-ENST00000371402.2, with the exact same protospacer. Author population source lines 152–163 selects guides by protospacer, explicitly drops RHOXF2B and writes the final mapping. This supports one sequence with an ambiguous genomic/biological target interface, not two independent perturbations or evidence that both readout rows should merge. No new alignment or off-target specificity proof was performed.

## Recommended new contract: author-intended target labels, exact readout symbols

SUPPORTED for a metadata identity contract: retain the already-used 103 perturbation labels as created by the pseudobulk procedure, including original RHOXF2 single/control cells labeled RHOXF2B according to the author's intended-target assignment. On the readout axis, select the unique exact reference symbol equal to each canonical target label, without applying any aliases to feature symbols. All 103 have exactly one such symbol in the unchanged 33,694-row GEO reference. Consequently RHOXF2B selects row 14109, while row 14112 remains a separate RHOXF2 readout outside this 103-coordinate submatrix. No target is removed, feature rows are not merged, and no RNA values determine this selection.

This new contract corrects a source-domain mismatch. It is not a retrospective PASS for the old contract, whose explicit alias-on-features rule correctly stopped on a duplicate. Keep the old STOP and protocol unchanged. Save a distinct revised protocol and mapping before numerical access. The new protocol must name the different coordinate definition openly, without presenting it as the originally frozen specification.

The author's stronger-effect judgment was already response-informed in the original work. Reconstructing that existing target assignment now is not new response-based choice by this investigation; it also is not a newly blinded biological discovery or independent validation of that assignment. It gives a defensible operational coordinate specification, not a validated physical force interface.

## Historical raw-label alternative and its limits

A separate source-label coordinate contract could keep RHOXF2's original library label and choose RHOXF2 row 14112, while retaining the other three documented nomenclature mappings. Its 103 coordinates are also unique under this explicitly hybrid rule; all corresponding raw single/control orientation labels exist. But this is a different estimand, does not implement the author's intended-target correction, and cannot be described as proof that the guide acts only or predominantly on RHOXF2. Calling it a fully exact historical raw-label match for all 103 genes would be inaccurate because the other three historical names require reference nomenclature changes. It should not be selected after viewing which result looks more reciprocal, and there is no reason to run both as outcome rescue.

## Physical identifiability remains unestablished

Even the recommended exact-symbol contract does not show that CRISPRa supplies a positive force along one measured logCP10K coordinate. The original source comment explicitly leaves dual-target/off-target activity plausible. Reference symbols/IDs do not resolve sequence mappability, transcript quantification cross-mapping, positive amplitude, composition/normalization, nonlinear endpoint behavior or conjugacy after transformation. Current NCBI/Ensembl annotation would not independently establish those physical assumptions. No additional metadata download is necessary for the bounded operational mapping decision; experimentally validated force semantics would need different evidence.

Therefore a revised necessary-condition diagnostic could examine compatibility of these operational coordinates with the exact stipulated model, while any failure only excludes that saved-number/interface model. It cannot reject general cell potentials, prove a biological violation or support a new world-model/agent/RSI mechanism. No model fitting is justified by identity resolution alone. Primary source supports this domain-specific correction; no innovation, predictive gain or independent-task claim follows.

## Independent recommendation

REVISE_COORDINATE_CONTRACT / OLD_STOP_PRESERVED / PHYSICAL_FORCE_IDENTITY_NOT_ESTABLISHED. Predeclare exact canonical readout matching without feature aliases if the root decides the bounded compatibility diagnostic remains useful. Keep the historical-label variant as a documented alternative, not a second response-selected run. The recommended contract is simpler, source-supported and preserves all existing 103 perturbation groups. Zero RNA-response-array or function-value access occurred in this audit.
