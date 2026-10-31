# Target-source evidence handoff

2026-10-31. Investigator; requestedSol/medium, effective configuration unknown. Initial structural questions and exact metadata-only scope were saved in initial_questions.md before any candidate/scout/developer interpretation. The later root message names an IMP scout but no scout draft was read and no candidate is evaluated here. This is targeted acquisition, not a new survey. Shared library/index remain root-owned.

## What changed

An economical official supplementary entrance and original preprint Methods now exist locally. This repairs source access; it does not admit independent biological response observations or establish a new useful intervention learner. The accessible original is the 2023 preprint v3, posted2023-05-20, not the final2026Cell article or2025guide. The latter two remain abstract-level in the inspected shared-library rows. No claim of unchanged final-version methodology is supported.

P001: DOI10.1101/2023.04.19.537364, authenticated Jiang et al. title/author/DOI and CC-BY-NC4.0 footer on main PDFp1; CaltechAUTHORS zpnpe-wnj98. Full main PDF52pp saved as sources/dspin_original_preprint_v3.pdf.hop1,17,889,759B,SHA256bd80396e3b3361fb13f259c6786a82ce2978f73db97899a7b68cd119b5f04b9c. Methods supplement21pp saved as sources/dspin_original_preprint_v3_supplement.pdf.hop1,8,248,041B,SHA25679f7e1cb16e5b585fd9160a1144a1c1c9709d6c2a20b29061a21ef7509151373. Retrieval links:
- https://authors.library.caltech.edu/records/zpnpe-wnj98/files/NIHPP2023-04-19-537364v3.pdf?download=1
- https://authors.library.caltech.edu/records/zpnpe-wnj98/files/NIHPP2023-04-19-537364v3-supplement-1.pdf?download=1

Reading levelP: mainp1-2 identity/abstract,p5-6 formulation/training,p18-19 drug design/single-network construction,p26-27 limits/data-code availability; supplement1.1p7,1.3p9 partial normalization/batching,1.7p13-14 partial fitting details,1.15-1.16p17-18 coherence/phase diagram and2.1-2.4p18-19 experimental methods. Entire52/21pages not read, not F. Text extraction files are searchable aids with original page markers, not new numerical dataset projections.

## Source-native object and ordinary explanations

C001 (mainp5-6,19): D-SPIN is an undirected equilibrium spin/Markov random-field model, P(s|n) proportional exp(sum Jij si sj + sum hi(n)si), with one shared J and condition-specific h(n). Gene programs derive from oNMF and ternary states{-1,0,1}. For drug profiles the source explicitly infers a singleJ plus drug-specific biases. Changed cell-state correlations across conditions do not by themselves prove changed couplings: a fixed interactingJ with changing fields already produces changing marginal distributions/correlations. The coupling object is conditional interaction rather than a correlation matrix.

C002 (supplement1.1p7;1.7p13-14): the fitted response vectors are latent/derived outputs estimated from condition-level empirical means and cross-correlations under inferredJ. They are not independently measured target outcomes. Subtracting controlh is the source's batch-correction scheme. Source fitting uses all Drug Profiling conditions to inferJ; fitting h of other conditions conditional onJ is not a held-out intervention prediction test. Source runtime is not automatically economical here: it reports5x10^7MCMC samples per iteration per condition for30program network inference,10^7for response-vector inference and300-1000iterations. Reusing fitted summaries may be cheap, but cannot remove their source-fit/exposure provenance.

C003 (supplement1.15-1.16p17-18): source-native combination capability already includes program-level coherent/incoherent drug-response analysis and interpolation of combined-dose cell states. For phase diagrams, both dosage experiments are used to fitJ and h. The published design profiles all dose pairs for Dasatinib(0.1,1,10,100,1000nM)xHalcinonide(0.01,0.1,1,10,100,1000nM), and Tacrolimus(0.1,1,10,100,1000nM)xMotolimod(1,10,100,1000,10000nM). A thinplateinterp of fittedh(c1,c2), target-state mean log likelihood and softmax determine the displayed phase diagram. These are published methods/design descriptors, not acquired dataset response values. This passage supports interpolation from a profiled combination grid, not a demonstrated zero-combination training advantage. Mainp26 explicitly says additivity alone cannot accurately predict cell-population structure and asks when additivity holds or breaks. A proposed additivity-boundary question therefore has an explicit source-owned precedent.

C004 (mainp18-19; supplement2.1-2.4p18-19): drug study PBMCs, healthy-donor origin, activation with antiCD3/CD28,24h simultaneous compound exposure and scRNA-seq; resting subset also profiled. Protocol uses200,000PBMCs per well; sample multiplexing tags assign recovered cells to conditions; multiply labelled cells removed. Methods distinguish experimental batches (MULT-6etc), sequencing alignment versions and a30h reverse activation time course. There is no admitted mapping from individual donor, well, condition, batch and replicate to each response-summary row. Generic healthy donors plural plus a schematic human donor singular does not establish multi-donor replication. Cells, tags, batches and independent biological replicates must remain distinct.

C005 (mainp26): equilibrium model does not account for network dynamics and produces undirected graphs. Reported gene-program/function annotations and transcriptional population-state modulation are not measured killing/viability, secreted cytokine output, therapeutic efficacy or biological causal mechanism. No direct drug-discovery functional endpoint was established in the inspected passages. This is a reading limitation, not proof that no auxiliary validation exists anywhere in final2026materials.

Closest ordinary explanations that a future claim must distinguish: fixedJ plus changingh; nonlinear readout/phase thresholds; source-fitted-response interpolation; additive program recruitment with nonadditive population composition; mixtures/selection of cell types; batch-dependent offsets; direct equally informed dose/condition-response regression. These are mechanisms/aliases for comparison, not findings of a new empirical effect. Context-dependent coupling as a label alone has no novelty or benefit evidence.

## Official processed and raw availability

P002 https://data.caltech.edu/records/tbmca-wbj97 , DOI10.22002/tbmca-wbj97, supplementary datasetv2 published2025-05-21,CC-BY4.0, linked to preprint10.1101/2023.04.19.537364. The record lists six XLSX totalling14.7MB: Figure2(255.4kB),Figure3(3.0MB),Figure5(718.8kB),Figure6(10.0MB),Figure7(250.7kB),PerturbSeq_program_DAVID_annotation(388.8kB). It is a different valid route from the large raw record; not automatically an observation dataset. Main paper version vs summary update dates must not be silently equated.

Only Figure5 and Figure7 were acquired under the written exact header/container scope. sources/Data_Figure5_20240312.xlsx.hop1 is718,753B,SHA2568f522a630ed3ad1a3acd9759640d05a8b2ddb496b56010e85f081b88d2ee0201; Figure7 is250,651B,SHA256383413c0150691a41ddff64dd349f79074634b443b692c35b051cb85850e12ab. ZIP/workbook/row1text descriptors are in xlsx_metadata_only.json; no numeric cell values/formula caches/plots/subsequent rows were projected. Row1string labels are explicitly a header proxy: notably 'Drugs in pairwise combination' starts with a drug identity, so row1 is not guaranteed a table header. It is not an independently sampled response record.

Figure5 workbook descriptors:
- Drug library summary A1:G503; headers product_number,library_type,product_name,drug_class,drug_target,target_gene,Information.
- Single-cell sequencing summary A1:J17; Experiment Name,Total barcodes in exp,Filtered single-cells,Machine,Multiplexing,Mean # reads/cell,Total reads,Median # genes/cell,Median # UMIs/cell,Note.
- Cell types A1:G36; Leiden_index,Index,Coarse,Fine_v0,Fine_celltype_name,UMAP color,Markers.
- Gene programs with weights A1:BH699; P1..P30/Weights.
- Regulatory network A1:AE31; P1..P30.
- Response vectors A1:AE1133; Sample_name_with_batch,P1..P30.

Figure7 workbook descriptors:
- Drugs in pairwise combination A1:A12 (row1not guaranteed header).
- Drug interaction on programs A1:AS31 (row1combination text identities;44text entries, dimensions not proof of44or45 independent measured combinations).
- Regulatory network A1:AE31; Response vectors A1:AE91; Phase diagram network A1:AE31; Phase diagram response vectors A1:AE91; program labelsP1..P30.
- Program regulators A1:YH31,657text column labels.

Dimensions describe occupied cell rectangles, not independent observations or exact usable row counts. No header-proven donor/replicate/time/well support identity is supplied. Response vectors and interaction networks are fitted summaries; no first/second moments, uncertainty/cell counts by independent condition, or held-out response likelihood contract is established by these descriptors. Do not train or evaluate on these as independent functional labels.

P003 https://data.caltech.edu/records/2cjss-wgh69 ,DOI10.22002/2cjss-wgh69,CC-BY4.0, recordcreated2023 and updated2026. Technical metadata explicitly says dosesnM and default1,000nM. It lists dosage_combination_raw_counts.h5ad772.6MB and drug_profiling_raw_counts.h5ad5.6GB,total6.4GB. Neither downloaded; no H5AD schema/obs identities/response values inspected. These are raw-count-labelled containers, not a small processed admission route.

Official source code is linked in mainp27 and CaltechAUTHORS metadata: https://github.com/JialongJiang/DSPIN (MATLAB/Python/notebook implementations). No code fetched or executed; current commit, license, final-paper association and exact source schemas unknown. Previous failed GitHubsearch endpoint not retried.

## Residual exact contract before numerical admission

Needed: source-owned metadata-only map from each independent donor/experimental well or replicate to compoundA/B,doseA/B,activation,time,batch and actual measured response support; distinction of measured/control/combined-dose/derived grids; explicit biological replication and sampling unit; a direct functional endpoint if the task requires one, or honest transcriptional-state estimand; source-fit provenance ofJ,h,programs and interpolation; empirical moments/counts or another economical processed measurement likelihood with uncertainty; leakage-safe source-training and held-out support. The two retrieved workbooks alone do not provide this contract. Reading selected author data/schema source text or requesting a metadata-only manifest is the next useful step, not a new coupling model. No protected responses are implicated or admitted by the present entrance.

## Acquisition accounting and limits

12actual HTTP ledger rows,27,330,183known decoded body bytes (26.06MiB),0known partial bytes, no retries. Rows1-2Caltech metadata;3-4Figure5redirect/body;5-6Figure7redirect/body;7CaltechAUTHORS D-SPINquery;8-9mainPDFredirect/body;10-11supplementredirect/body;12guide identifier query. The last exact quoted667326query returned zero hits, not proof of absence. Broad D-SPINquery total27371was not a bounded relevance count: only first authenticated matching record used; remaining unrelated results not surveyed. All errors/redirect bytes included; wire bytes not certified. Budget stops further investigatorHTTP. Old failed original endpoints were inspected as receipts and not retried. No installations, modelAPI calls, author-code execution, simulations, fits, numerical response previews, protected data access or shared-library writes occurred.
