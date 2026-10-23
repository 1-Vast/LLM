# Public raw lineage joins: updated qualification

2026-10-23. Supplements ROOT_SOURCE_REVIEW; preserves earlier sealed peer opinions. No new biological outcome fits or raw lineage record exports.

## Material positive evidence

Official sample-level GEO SOFT GSE289454 was acquired (3,761,697 bytes, SHA256 8545602f3dd82e41836e7a8e34d7a8cbb82e6a5c715d3321eb68b4f15174e9c3). AML_SAMPLE_INDEX.json projects sample titles and declared URLs. Some entries say NONE for sample-level supplements: this is not a claim that the series has no processed matrices. Series-level matrix declarations and sample-level lineage supplements are different scopes.

GSM8791699 is multiplexed human HL60/TF1/OCI-AML3 pre-AraC GEX; GSM8791701 is multiplexed human HL60/TF1 control/treated post-AraC GEX. GSM8791700/1702 are corresponding MULTIseq libraries. GSM8791698 declares founder/clone tags associated with both sample2 mouse endpoint blood/marrow and sample3 human baseline; GSM8791703 declares post-AraC sample4 founder/clone tags. Therefore a lab-local processed annotation CSV missing from the pinned repository does not establish absence of reconstructable public lineage data.

One bounded Range GET each authenticated the exact pre-associated and post-associated founder-tag sources (HTTP206). Both have the SingleCellLineage readName/UMI/mergedRead/mergedReadRef/target1..8 schema. Full compressed source sizes are 1,177,391,535 and 1,324,422,863 bytes. Only the first decompressed line was exported and compressed prefixes retained; no records exported. No physical non-decoding guarantee is claimed. The shared sample2+3 file must not be called a pure human-baseline table.

## Exact author extraction contract found

Three text-only downloads from author repository commit 3d5ef9070a259fb902feccbc5948f10e6a9d44ae have Git blob SHA1 matching the previously acquired complete tree:

| Source | Git blob SHA1 |
|---|---|
| 1_LineagePreprocessing.py | 9b76606a5c96a8c6d74eba1ed7bfb0bf723f5613 |
| 2_TagClustering.py | 9729ebc5735d7e9f5d81347378da447a4e03bea7 |
| AML_lineage_utilities.py | 77e6e8160b4d082ce70c36513dccb7cd231d3623 |

extractReadInfo splits readName on underscores into seven named fields. R1, the second field, supplies cellBC=R1[0:16], UMI=R1[16:28]; readCount comes from the third field. This is an authenticated code contract, not yet an empirical verification that these exact public files obey it. getBC locates the degenerate reference motif in mergedReadRef and extracts the corresponding aligned segment from mergedRead. Founder and clone tags have distinct motifs; C1498 and HL60 clone-tag constructs differ.

Preprocessing filters PASS reads, joins lineage cellBC to whitelist.FB_bc and carries whitelist.GEX_bc. The required whitelist is an external input; equal character lengths do not prove GEX and feature barcodes are interchangeable. It performs UMI/read-count filtering and Starcode correction. Missing variables, lab-local executable paths and inconsistent variable names mean the scripts are methodological source, not a turnkey reproducible pipeline. No author code was executed or imported.

HL60 founder assignment lacks the C1498 known-founder whitelist. It clusters tag co-occurrences, then removes ambiguous associations and assigns display names by founder/clone cell abundance. These display names are not immutable molecular identifiers. Baseline and endpoint cannot be joined by independently recomputing H1/H2 abundance rankings. Cells must be namespaced by library/sample before cross-library merges; raw 16-base cellBC alone is insufficient.

## Unresolved and falsifiable qualification gate

Current status: public sources available; extraction and sample assignment remain unverified. This is a local qualification limit, not a global blocker or a numerical result.

Before any phenotype/expression fitting, authenticate chemistry/FB-to-GEX translation and MULTIseq tag-to-flask/time definitions from declared sources. Establish that human baseline can be separated from mouse endpoint material in the shared stats library using lawful library identity and GEX/MULTIseq membership, rather than endpoint responses. Define handling of cross-library barcode collisions, ambiguous tags and doublets in advance.

A possible prospective alternative is to learn tag error-correction/reference sets from baseline only, freeze them, and assign later cells with explicit unmatched/ambiguous categories. This is a different estimand from the author's all-observation clusters. It may lose rare/unsampled baseline clones; disappearance is not proof of cell death and unseen is not zero. It must not silently reuse endpoint-informed tag clusters, trees, modules, abundance ranks or QC tuning as starting-state predictors. Post-treatment molecular tags may be used in a predeclared outcome-label measurement pipeline, with that role separated from predictor construction and with sensitivity to label ambiguity.

Only after identity validation can a new numerical contract specify the endpoint, culture-level partitions, untreated-growth controls, actual sampling times, feedback/compute cost and a measurement-grounded success threshold. Treated midpoint day36 and control midpoint day43 are different times. Clone fractions alone measure relative representation, not absolute viable outgrowth or pharmacological sensitivity. Few shared-origin flasks limit independent validation; cells and tags do not create later RSI task generations.

STOP this particular proposed comparison if molecular/sample identities cannot be authenticated, treatment-specific function is not estimable, or independent held-out units are inadequate for its stated scope. Do not rescue it by inferentially matching responses, changing old thresholds or opening Emerald reserve. No new update law, world-model necessity, agent benefit, inheritance, joint benefit or improved-improver effect follows from these acquisitions.

## Actual post-seal opposing review

Constructive and critic independently sealed their source/contract reviews, then exchanged the baseline-only dictionary proposal and strongest objections. Both accept that the target population becomes baseline-detectable/reliably assignable founders, rather than all founders. Freeze eligibility and its denominator before endpoint assignment; do not condition inclusion on later retention or silently renormalize missing cells. Multi-integration/shared tags require a frozen tag-set identity and ambiguity rejection rule. If distinguishing founders requires endpoint co-occurrence reclustering or retuning thresholds, STOP that proposed baseline-identifiable estimand. This actual exchange is separately sealed in constructive/JOIN_CONTRACT_CROSS_ADDENDUM.md, constructive/JOIN_MULTITAG_REPLY.md and critic/AML_JOIN_CROSS.md. No new records, network requests or performance fits were needed for this exchange.
