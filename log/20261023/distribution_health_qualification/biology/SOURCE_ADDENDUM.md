# Independent identity and endpoint qualification addendum

2026-10-23. Independent original and bilateral review unchanged. Read selected metadata fields from retained official IDR CSV, ES2 plate map, all_metadata and target mapping. Executed research/distribution_health_qualification_20261023/biology_identity_audit.py; output IDENTITY_AUDIT.json records input hashes and scope. No GET, predictive fit, endpoint value decode or API call. CSV parsing necessarily traversed the IDR file, including sequence-bearing records in memory, but only identity fields were selected and no reagent sequence was emitted or used for analysis.

## A real grouping defect caught before outcomes

Official IDR metadata gives **BRAF1-1** and **BRAF-2** the same Gene Identifier **ENSG00000157764**, although Gene Symbol and author gene_name use **BRAF1** versus **BRAF**. ES2 plate mapping confirms those distinct strings. Grouping by gene_name or guide-name prefix alone could place guides targeting the same gene into train and test. My independent earlier shorthand 'whole-gene' must therefore mean canonical verified target grouping, not trusting a string category.

Use official stable gene IDs for grouping after checking that each reagent has one compatible ID across plates/lines. All guides mapping to the same ID must share a source/train/held partition across all lines and plates; any conflicting mapping must be reconciled before fitting. Use connected components if multiple authenticated target IDs occur per guide: never split a shared target edge across partitions. This is grouping metadata, not an extra predictive feature. Do not expose held labels to resolve identity.

Independent counts from selected fields:

- IDR:6912rows,18distinctplate labels,3lines. Source author all_metadata:3456rows,119guide labels,357guide×line conditions,59gene strings. These counts are metadata cardinalities, not biological independence estimates.
-102 source guides have exactly one official nonempty gene ID, spanning **51 canonical IDs**. The only multiple-symbol ID found among these is BRAF/BRAF1.
-6 noncontrol source guides have no official gene ID: **ATP50-1/2, SMARCB1-1/2, XBP-1/2**. Their readable strings do not authorize automatically correcting ATP50 to another gene or XBP to a preferred symbol. Until metadata-only independent resolution, conservatively exclude these guides from BOTH supervised training and held evaluation; retaining them in training could defeat an ostensibly held-gene guarantee if an unknown alias overlaps a resolved target.
-10 source guide labels are declared negative controls. **EMPTY** does not match a named IDR reagent key; official no-reagent rows use blank reagent strings. EMPTY's exact plate/well no-reagent correspondence must be verified rather than asserting absence or fuzzy-name matching. Controls are reference/calibration material, not independent biological targets or held-gene task units.

Excluding unresolved guides is a metadata-based prespecified eligibility restriction, not outcome-based cleanup. If later resolved using authoritative metadata, freeze revised membership before outcomes and record the revision. The raw59gene-string count must not serve as the gene-cluster sample size, inferred biological target count or count of later independent inherited tasks. Actual evaluable cluster count is further restricted by target availability and split, still not numerically inspected.

## Endpoint stronger but not fully qualified

target_mapping.body defines **vb_percent_dead** as 'Fraction of DRAQ7 positive cells', readable death measure, original '% Dead'. **vb_percent_dead_only** is separately described as 'Fraction of caspase negative in dead cells', original '% Dead Only'. They have different stated fractions; neither may silently replace the other. This strengthens exact released-column identity but does not supply a literal all-cells denominator formula or its gating/exclusion details. The latter remains a qualification issue, especially when segmentation may lose detached cells. No numeric target labels were inspected to select between them.

## Remote schema and pseudo-replication limits

Root reports authenticated remote schema with4tables and one inspected plate's image metadata:384wells,3455images. This addendum does not independently reparse remote SQLite pages and does not claim whole-corpus schema verification. One plate, many images,18IDR plate labels or repeated profile rows do not create extra biological line backgrounds. Labels with acquisition suffixes cannot be assumed to be new independently perturbed cell populations or blindly collapsed as duplicate acquisitions; establish the imaging/plate relationship from metadata. The source all_metadata repeats membership and measurement bookkeeping and must not be treated as3456 supervised health-independent observations. The current qualified prediction unit remains guide×line with gene-group dependence.

No held gene/test target labels or protected assets were used in this identity audit. It does not prove global historical provenance, secure test blinding or schema correctness for uninspected plates. It removes a concrete would-be leakage path and identifies6 unresolved reagents before fitting.

**Decision remains GO bounded qualification, NO_FIT_YET.** Canonical groups must be frozen, EMPTY/control mapping checked and endpoint denominator/usable object joins defined. No performance, new mechanism, world/agent/inheritance/joint or recursive gain is established.
