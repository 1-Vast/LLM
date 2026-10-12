# Evidence qualification for discrepancy P0

Date: 2026-10-12, Asia/Shanghai. This audit covers three original sources and small methods/metadata retrievals. It does not fit a policy, open new outcome matrices, or establish superiority of the dual-core framework. `SOURCES.json`, `SOURCE_READ_RECEIPTS.json`, and `RETRIEVAL_RECEIPTS.json` distinguish reused sources, new retrievals, and failed content validation.

## Dated CXCL9 correction

The original [CXCL9 paper](https://doi.org/10.1038/s44320-026-00221-w) measures **24-hour culture-supernatant CXCL9** with a LEGENDplex capture-bead sandwich immunoassay, read by FACS Symphony A3. Flow events are capture beads; they are not intracellular protein measurements or independent single cells. Earlier packet wording describing intracellular/single-cell CXCL9 is superseded by this correction. Historical packets and receipt hashes are preserved.

Figure 1 reports two independent biological screenings with technical duplicates. The pinned repository maps E3CA/E3CB to BxPC3 passages P12/P14 and E3DA/E3DB to AsPC1 P12/P14; preprocessing preserves run/duplicate distinctions as SampleA1/A2 and SampleB1/B2 before aggregation. This supports a screening/run hierarchy, but bead events and technical duplicates must not inflate biological sample size. Culture-start provenance and exact pairing remain unresolved. Active-learning files use a different naming rule: AL1A/AL2A are AsPC1 rounds 1/2; AL1B/AL2B are BxPC3 rounds 1/2. A/B is not a biological-replicate label in those files.

AsPC1 and BxPC3 receive different cytokine doses (10 and 1 ng/mL). Their contrast combines cell context and stimulus dose. The six-point MIDAS model-input grid is not observed temporal evidence, and constrained model nodes are not measured proteins.

The paper separately measures Caspase-3 activity with EnzChek/Z-DEVD-R110 after cell lysis. This is a promising orthogonal apoptosis readout. The stated correction adds normalized CXCL9 and Cas3 and rescales; it does not validate secretion per live cell. A negative CXCL9/Cas3 association alone cannot distinguish reduced secretion, apoptosis, altered growth, or assay interference.

The official Fig. 5 source archive is a reproducible candidate path. A bounded attempt to save it sealed and inspect names/schema returned an HTML reCAPTCHA response rather than a ZIP; the publisher mirror failed TLS. Both attempts are receipted. BioStudies metadata routes returned 404 and the paper-linked landing page returned a generic application shell. These failures leave same-well or sister-culture pairing **unresolved**, rather than proving it absent. No outcome values or archive members were read.

## Functional candidates and justified units

| Source | Qualified evidence | Unit supported by original methods | Still unresolved |
| --- | --- | --- | --- |
| CXCL9 | Secreted-protein response to cytokines/inhibitors; separate apoptosis-assay protocol | Two biological screenings with technical duplicates for initial screening; specific raw-file mapping is a candidate hierarchy | Culture starts, orthogonal-channel pairing, active-learning repeat hierarchy, live-cell counts, held-out intervention plan |
| [PRISM Repurposing](https://doi.org/10.1038/s43018-019-0018-6) | Five-day relative barcoded pooled-cell-line viability; primary 2.5 micromolar and secondary eight-dose response | Three independently treated assay plates; one to three retained after QC | Separate thaw/culture starts, raw replicate outcomes for a new functional validation, matched molecular/functional exposure, actual cost |
| [BATCHIE](https://doi.org/10.1038/s41467-024-55287-7) | Prospective adaptive combination screening with Alamar Blue readout after 72-hour exposure plus 24-hour reagent incubation | Physical plates and adaptive rounds; rounds 1-10 singly, 11-15 in duplicate | Biological culture-start independence, prospective outcome schema, temporal holdout access, actual plate cost |

PRISM original Extended Data Figure 1 caption explicitly states: “Up to 3 independently treated plates (range 1–3 based QC filtering) in one screen are median-collapsed.” This qualifies assay repeats even without a literal `culture_id` column. The README provides `screen_id`, `compound_plate`, `detection_plate`, `well`, `pool_id`, and `minipool_id`; the primary treatment schema also includes a detection timestamp. Detection beads, cell lines in the same pool, and technical MTS010 redos are not independent culture replications. Repeated measurements can qualify measurement reliability without qualifying a new held-out model-validation unit. Validation units must follow the generalization claim and dependency structure.

PRISM metadata annotations identify drug mechanism/targets; they are not experimentally verified mechanism labels for each response. Shared compound/cell IDs with L1000 do not establish matched dose, exposure, culture, or a causal state-to-function bridge. The original PRISM paper's selected gene knockout/rescue follow-ups are stronger causal evidence, but they are a separate targeted experiment, not labels attached to the complete screening matrix.

BATCHIE's retrospective “plates” are constructed replay groups with averaged replicates. They must not be substituted for its prospective physical-plate design. Its public Zenodo manifest advertises a 24,695,289-byte pair screen and a 6,725,455-byte triplet screen, not small metadata tables. Neither outcome file was downloaded. Supplementary Data 1/2 describe cell culture and drug metadata; original paper paths are recorded for possible later qualification.

## Consequences for the dual-core design

The immediate contract between Agent and world model should preserve endpoint, intervention, dose, time, context, experimental-unit hierarchy, and provenance. A discrepancy should enter as an observation with a residual and uncertainty. An explanation remains a competing hypothesis until a matched discriminating observation is available. Missing fields alone are not grounds for rejecting a design when original methods support the relevant units; methods cannot manufacture unavailable outcomes or prove a stronger level of independence.

A qualified distinct channel could test whether the system recognizes and resolves disagreement: for example, secretion plus matched apoptosis/live-cell readouts, followed by an intervention that yields different predictions under competing explanations. The study would need a frozen intervention menu, explicit repeat/cost units, a holdout of independently justified experiments, and an abstention path when hypotheses remain observationally equivalent. Paired Cas3 by itself would improve discrepancy characterization, but would not establish every mechanistic origin.

For current P0, archived PRISM predictions can support descriptive selection-error and measurement-provenance diagnosis. They do not support learned compensation/stress/platform-cause labels, new superiority tests, or promotion to `src`/`tools`. A further study should be either (1) a qualified new orthogonal evidence channel in a matched task, or (2) an independently justified functional task with a newly frozen protocol. Using another unaligned screen merely as more outcome data does not establish the interface design's effectiveness.

The scientific contribution remains a candidate until a controlled comparison shows improved held-out decisions at a declared budget and calibrated abstention, with failures retained. The closest original works already combine adaptive selection with mechanistic models or Bayesian response prediction; combining those components alone does not establish novelty. A stronger contribution would demonstrate that an explicit, evidence-qualified disagreement interface changes experimental choices and resolves testable hypotheses beyond those existing approaches.

Efficiency should be assessed with actual assay/plate units and measured runtime. Existing scenario read-equivalent prices are not established wet-lab prices. Preserve screen/plate constraints, reuse cached metadata, and acquire new outcomes only after the evidence channel and evaluation protocol have qualified.
