# Amendment 1 to implementation_identifiability_v1

Post hoc, not preregistered, no independent confirmation. Sources were exposed. v1 files are unchanged (v1 base commit f997c157c1b6b01026652beb0d4fc49879199086; the audit started at the same HEAD).

## Verdict

The public records do not contain a condition-matched, quantitatively interpretable, lineage-qualified unit. Nothing in this audit changes a v1 decision.

| Decision | v1 | After audit 1 |
| --- | --- | --- |
| G0 | QUALIFIED_FOR_LOGIC_TEST | unchanged |
| Research level | ASSET_BLOCKED | unchanged |
| G1 engineering | pass | unchanged (v1 replay rebuilt byte-identically; 10 of 10 mutation checks behave as stated) |
| G1 biology | NOT_ESTABLISHED | unchanged (BIOLOGICAL_DISCRIMINATION_NOT_ESTABLISHED) |
| G2 to G5 | not executed | not executed |

Units by level (U1, U2, U3, C4): Level 1 = 1 (C4), Level 2 = 3 (U1, U2, U3), Level 3 = 0, Level 4 = 0. The audit rules E1 to E6 cannot raise a level, and none did.

## Material read, and not read

Read: the full text of both papers (Europe PMC XML, digests in v1 `records.py`); S1 supplementary information PDF, Supplementary Data Set 3 (IMR5 TMT), Data Set 2 (catalogued only), Supplementary Table 2, Source Data PDFs for Figs 1, 2, 4, 5 and ED 2, 4, 5 (uncropped blot images, no numbers) and the Extended Data figure files (raster images); S2 SI PDF, the Kelly proteomics workbook and the SI csv. All file digests are in `supplement_extracts.json`.

Not read, and why:
- S1 Supplementary Table 1 (BRET EC50 values), Data Set 1 (kinobeads) and Data Set 4 (interactome): neither the Europe PMC bundle nor the PMC route served them; the PMC route returned a script-based interstitial that was not bypassed.
- Numeric Source Data for S1 Fig 6 and ED7 (none is published) and any value read off a bar in a figure image. Figure interpretation is not a measurement.
- S2 Figure S7B pGI50 values (image only) and the blot images in Figures S8, S10 and S11.
- The S2 publisher page (HTTP 403).

Because of this, neither paper is described as fully extracted.

## Source completion

S1 (ED7 and Fig 6, matched conditions, lineage, engagement, activity, genetic loss, rescue controls) and S2 (Fig S7, compound 57, controls, shared endpoint, background and time, lineage) are graded item by item in `SOURCE_COMPLETION_AUDIT.json`. Quantitative data were found only for proximal AURKA abundance (S1 IMR5 TMT; S2 Kelly proteomics) and S2 HiBiT summary statistics. Terminal values for JB170 against JB211 are qualitative (ED7 is a raster image with no Source Data), alisertib has no 72 h arm in S1, and CCT400028 has no inhibitor or genetic terminal comparator in S2. Lineage (cell stock, passage, plate) is not reported by either paper. The IMR5 TMT contrast has one batch and no vehicle channel. Two S2 numbers disagree between files (JB170 HiBiT DC50 39 nM against 28 nM; three SI csv values against SI Table S1).

## JB211 premise status

CRBN-null close analog; AURKA binding is asserted in the source, but direct intracellular engagement and catalytic inhibition remain unresolved in the extracted evidence.

Recorded as six separate fields in `JB211_PREMISE_STATUS.json`: CRBN recruitment (not mediating degradation, per the authors), AURKA occupancy (asserted, not measured in the material read), intracellular exposure (not reported), catalytic activity (not reported; no pT288 or substrate assay anywhere read), protein abundance (JB211 raises AURKA in IMR5 TMT, 18.88 log2 units, three channels, and in an MV4-11 blot; abundance only), terminal phenotype (qualitative). The premise "JB211 inhibits AURKA catalytically" stays unresolved. T217D rescue is limited on-target evidence: wild-type AURKA overexpression also rescues, and the T217D mutant lowers binding of an alisertib analog, so rescue partly reflects expression.

## Compound 57

A CRBN-null matched control for AURKA degradation (no depletion up to 10 uM, 4 and 24 h, Kelly, 2 experiments, blot). No terminal result exists in the text, SI or workbook (`CCT57_TERMINAL_STATUS.json`). Lack of depletion does not establish terminal inactivity, so no inactivity claim is allowed.

## G1 logic re-run

The frozen v1 rules were not changed. The v1 replay rebuilt with per-step output hashes identical to the stored ones. Multiple explanations are preserved. Only legally released observations update state. Hidden evaluator outcomes do not alter the pre-purchase proposal (mutation M01). Under the strict criteria, the extracted action menu declares no uncertainty model, so the step-0 decision is `still_indistinguishable`. As a sensitivity check only, a hypothetical equivalence margin was declared: the two published outcomes (T217D `rescued`, JB211 viability `no_loss`) are graded `reported_qualitatively`, do not update compatibility, and the final compatible set is all four explanations plus `OPEN_OR_UNMODELED_EXPLANATION`. The margin is hypothetical and is not evidence. The retrospective limitation remains: the replay menu was chosen partly by outcome availability. No G2 value is inferred.

The v1 `cost_total` double-counts duplicated bundles (36 against 18 wells in mutation M05); `cost_total_unique` is the corrected audit version. The v1 replay is unaffected.

## Unresolved explanations

EX_PROTEIN_LOSS_SCAFFOLD, EX_CATALYTIC_INHIBITION, EX_CRBN_DEPENDENT_OFFTARGET, EX_WARHEAD_OFFTARGET_BINDING and OPEN_OR_UNMODELED_EXPLANATION all remain compatible. These are study-local fixtures. No probability is attached and no mapping to H_E, H_M, H_C or H_O is made.

## Missing experiments and data

See `MISSING_EVIDENCE_UPDATE.json` (v1 items G01 to G10 with new status, and N01 to N07): JB211 occupancy, exposure and activity as separate measurements; equivalence margins or detection limits for negative terminal readings; a vehicle channel in the IMR5 TMT contrast; a matched inhibitor and genetic terminal comparison for CCT400028 and a terminal result for compound 57; exposure or pharmacodynamic support for dose matching; S1 Supplementary Table 1 and Data Sets 1 and 4 and numeric source values for Fig 6 and ED7; T217D expression and localisation. A second target family is needed before any generalisation.

## Next permitted action

A person with the right to ask (the user or the papers' authors) obtains S1 Supplementary Table 1, Data Sets 1 and 4, and numeric source values for Fig 6 and ED7 with lineage metadata. This audit is then re-run as audit2. No modelling, no G2 to G5, no data purchase and no wet-lab work before that.

## Claims not made

No G2, G3, G4 or G5 result, no Agent-gain, no Virtual-Cell-gain and no autonomous-discovery claim. Software tests and mutation checks are evidence about the code, not about biology.
