# PTPC/S8 Efficacy experimental-definition audit

**Conclusion: the accessible primary evidence does not authenticate PTPC/S8 Efficacy dose, response duration, assay technology or numerical decision threshold.** It authenticates molecular sampling at 6 and 24 hours and the released Efficacy field. The earlier HCT116-only gate confirms that background's actual Y/N encoding, not the underlying experimental contract. This audit did not open any new label, 24h protein value, other-background abundance or reserved outcome.

## Direct S8 evidence

Sun et al., *An operational perturbation proteomics-based virtual cell model*, Nature (2026), DOI [10.1038/s41586-026-11001-9](https://doi.org/10.1038/s41586-026-11001-9). The saved supplementary text is `tmp/ptv1_src/si.txt`; exact quotations with source hashes and line positions are in TEXT_EVIDENCE.json.

SI S8A, printed page 4, text lines 158–165:

> “Sample-level metadata for the PTPC dataset, an independent perturbation proteomics dataset generated across five cancer cell lines (A375, HCT116, NCI-H1975, NCI-H2170 and Panc 10.05). Proteomic profiles were collected at 6 h and 24 h after treatment, with control samples assigned a perturbation time of 0 h.”

This defines the **proteomic** collection times. It does not say that the Efficacy assay was measured at either time. Actual S8 DrawingML Legend has the same wording; the previously authenticated A_metadata instead puts every record, including controls, at 6 or 24h. There is no authenticated measured 0h row. Preserve that discrepancy; do not reinterpret controls as same-culture pretreatment baselines.

SI S8B, printed page 4, lines 167–171:

> “Compound information for the 716 perturbation identifiers used in PTPC, corresponding to 708 unique compound names. All compounds were purchased from TargetMol. Information includes perturbation ID, catalog number, compound name, CAS number, SMILES, molecular formula, pathway annotations, indication, solvent, target annotations and compound type.”

Neither this list nor the authenticated S8 A/B headers has a dose field. TargetMol product identity is not an administered dose. No default concentration can be inferred from catalog number or SMILES.

SI S8C, printed page 4, lines 173–176:

> “Matched protein abundance matrix for the same 2217 non-pooled sample records.”

This supports matched state records. It does not establish a matched functional-assay aliquot, functional acquisition time, dose-response measurement or independence of repeated function assays. No S8 Legend sentence explicitly explains the Efficacy column's experimental provenance or numerical cutoff.

## Nearby definitions that must not be transplanted

| Source | Original wording or explicit scope | What it establishes | What it does not establish for S8 |
|---|---|---|---|
| SI S1C, printed p1, lines 32–36 | “cell viability assays … based on the 24 h response”; “resistant (N) or sensitive (Y)”; “efficacy criteria described in the Methods”; “three biological replicates” | Viability-based labels for the original study table/cohort; the numerical rule is deferred to main Methods | PTPC dose, a PTPC-specific 24h label horizon, numerical threshold or assay instrument |
| SI S7B, printed p4, lines 142–147 | “compound efficacy based on the 24 h response”; “three biological replicates”; “resistant (N; negative class) or sensitive (Y; positive class) according to the efficacy criteria described in the Methods” | Direct PTNC label semantics, class polarity and biological-replicate count | A direct PTPC/S8 assay contract; S7 names a different dataset |
| SI S7B, lines 145–147 | “Cell-line-compound combinations with inconsistent labels across repeated experiments were removed” | PTNC filtering policy | Evidence that PTPC underwent the same filtering or that its repeated rows are independent functional assays |
| SI S9A, printed pp4–5, lines 181–187 | “At the default classification threshold of 0.5, the scFM baselines classified nearly all samples as the negative majority class” | A prediction-score classification threshold in a PTPC model-performance narrative | A 50% viability threshold, dose, outcome-acquisition time or biological decision criterion |
| Supplementary Methods, printed p13, lines 600–617 | “Luminescence values were normalized to the untreated control wells”; “viability values were first converted to relative inhibition by subtracting them from one”; “IC values were estimated from the fitted curves” | A stated normalization and dose-response fitting procedure | General S8 Efficacy coding; the paragraph explicitly concerns “Figures 5G-I”, with replicate curves in “SI Figure 4” |

The dose-response paragraph additionally says “For each concentration, three independent biological replicates were collected” and describes cisplatin comparisons by likelihood-ratio tests. That specific validation experiment cannot supply an unreported PTPC concentration grid, assay horizon or binary efficacy threshold. A significance cutoff such as P < 0.05 there is also not an Efficacy classification threshold.

S1 and S7 provide contextual support that this study used viability-derived Y/N labels in some cohorts. That makes a shared protocol plausible, but plausibility is not direct PTPC evidence. Even a complete generic Methods efficacy rule would need its scope checked before asserting that it was applied identically to PTPC.

## Main-text access and bounded public source search

The saved publisher main article (`tmp/ptv1_src/art.txt` and art.html) explicitly says:

> “This is a preview of subscription content, access via your institution”

It contains the abstract, availability statements, references and extended-data captions, rather than the full original Methods body. References containing the word “Methods” are not a Methods section. Therefore this audit cannot honestly report that the complete main paper omits the efficacy rule; the rule may be in currently inaccessible main Methods, as S1/S7 explicitly indicate.

Two exact-DOI public metadata GETs were performed once each, without retry or access application. Both returned HTTP 200 and the exact matching title:

- Crossref returned the publisher version-of-record HTML/PDF text-mining links and no related-manuscript relation. The saved HTML is already a subscription preview; a metadata link is not proof of open full-text access.
- OpenAlex returned `is_oa=false`, `oa_status=closed`, `oa_url=null`, `any_repository_has_fulltext=false`, `best_oa_location=null`; its locations were the publisher DOI and PubMed. No open author/institutional full-text URL was returned.

Raw responses, receipts and PUBLIC_FULLTEXT_LOCATIONS.json preserve these results. This is a bounded search failure to locate public Methods, not proof that no public copy exists anywhere. No guessed mirror, restricted-access bypass, author contact or access application was attempted. The already-downloaded publisher archive was not reopened; its previously extracted exact Legend was sufficient, and no new table or matrix values were read.

## Consequences for the research task

The defensible target remains **prediction of the author-released HCT116 Efficacy annotation**. Its label type is usable for the authorized development experiment. Unknown original assay details do not invalidate that narrow retrospective task or require stopping all research.

Keep the following claims unestablished: fixed-dose drug utility; calibrated IC50; clinical sensitivity; a verified 24h viability outcome; independent function measurements for every molecular timepoint or Rep row; and a prospective 6h intervention decision before label availability. The fact that HCT116 has consistent condition labels across molecular times does not date the function assay or make 6/24h independent targets.

A later comparison using 6h versus 6h+24h observed state can be described as retrospective value of additional measured information for the released annotation. Until assay timing and workflow availability are authenticated, it cannot establish pre-outcome acquisition, prospective turnaround advantage or freedom from future-information concerns for an earlier real decision. Same-observation direct comparators and stated measurement costs remain necessary.

To upgrade the claim, obtain an original Methods passage or author-released protocol explicitly linking PTPC/the five lines to the administered dose or per-compound concentration design, function-assay timing and technology, normalization/control rule, exact binary decision rule, replicate aggregation and repeated-experiment filtering. Do not fill those fields with S7, the model's 0.5 threshold or unrelated Fig5 dose-response methods.

No mechanism, functional improvement, numerical-performance or RSI conclusion follows from this source audit.
