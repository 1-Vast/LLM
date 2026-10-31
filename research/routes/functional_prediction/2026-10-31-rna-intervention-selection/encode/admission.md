# ENCODE/ENCORE admission: PARK

2026-10-31. Metadata association is verified; a numerical RBP-knockdown splicing task is not admitted. The missing item is an audited mapping from released processed rMATS files to experiments, controls, biological replicates, assembly and event coordinates. No model was fitted and no event-level treatment-effect values were inspected.

## What was counted

Complete official ENCODE compact responses `sources/kd_compact.json` and `sources/eclip_compact.json` establish:

| Unit | Count |
|---|---:|
| Released shRNA RNA-seq experiments, K562 / HepG2 | 263 / 259 |
| Total experiments | 522 |
| Unique target-label/cell pairs / target labels | 453 / 256 |
| Experiments advertising biological replicate numbers 1 and 2 | 522 |
| Experiments with one possible_control / none | 460 / 62 |
| Distinct referenced possible_controls | 58 |
| Released eCLIP experiments / target-label-cell pairs | 250 / 244 |
| KD/eCLIP target-label-cell intersection, K562 / HepG2 | 102 / 85 |
| Intersection total | 187 |
| Target labels with intersecting assays in both cells | 57 |

These query-defined counts are not counts of independent functional tasks. They use literal target labels, not a validated protein-identity crosswalk, and include all returned shRNA targets rather than a curated RBP-only panel. Multiple experiments share a target/cell or control. All human identities, perturbation efficiency, replicate sample identities and actual control matching still require file/biosample crosswalks. An advertised replicate number does not verify independent cultures. eCLIP and KD on the same protein/cell are different experiments, not paired cultures or measured binding changes after KD. The metadata table is `metadata_units.tsv`.

The individual file inventory for AQR/HepG2 `ENCSR431SXF` contains 22 returned files: GRCh38 alignment/quantification tracks and reads, with no rMATS/event output. This does not establish absence across ENCODE. A global `output_type=differential splicing` query returned HTTP404, so this vocabulary/query failure is not a zero-result biological claim. Four earlier oversized responses are explicitly partial, excluded from certified totals, and retained with receipts.

## Original processed-data route

Van Nostrand et al., Nature 2020, DOI `10.1038/s41586-020-2077-3`, authenticated Europe PMC `PMC7410833`, **Data Availability Statement**, identifies publication file set `ENCSR413YAF` for secondary DEseq/rMATS/MISO/CUFFDIFF outputs and `ENCSR870OLK` for batch-corrected expression/splicing. KD filesets are HepG2 `ENCSR369TWP`, K562 `ENCSR795JHH`. These exact routes were found at the end of the worker slice and handed to the coordinator; their contents were not fetched by this worker. This is the decisive next metadata check, not proof of usable files.

The paper's Methods establish rMATS 3.2.1.beta, five event types (SE/MXE/A3SS/A5SS/RI), knockdown replicate BAMs against control replicate BAMs and GENCODE19. All manuscript analyses used GRCh37/hg19 and GENCODE19; GRCh38/GENCODE24 alignments were also deposited. Therefore contemporary GRCh38 portal tracks cannot silently be joined to original hg19 event coordinates. Event headers, coordinate conventions, junction-only versus junction-plus-exon counts, replicate order, PSI definitions/sign and presence-only event intersection remain **unknown** here. Certified rMATS-eligible intersection: **not established**, not zero.

## Feasible functional test, conditional on admission

A useful new test would ask whether a regulatory rule learned for an RBP transfers its direction of exon inclusion change to the other cell context, after accounting for pre-KD inclusion and expression, on genes not used for fitting. Split units must include gene/event families, RBP identity, experiment/control batch and cell/source; event rows are dependent observations. First define eligible events from coordinates and pretreatment coverage without choosing them by treatment significance. Binding-only labels cannot substitute for this endpoint. Cross-cell transfer already has material prior art (KATMAP); a gain alone would not establish a new learning principle. This worker does not favor a model and does not certify that this test is presently executable.

No treatment matrix or performance was computed. Published aggregate figure-caption counts and significance statements were inadvertently exposed while extracting original-paper methods; further KATMAP split-method reading also exposed published aggregate validation descriptions. They are disclosed in `evidence_notes.md`; no pristine-evidence claim is made.
