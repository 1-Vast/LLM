# ASO Atlas admission and closest-prior audit

Date: 2026-10-31 (Asia/Shanghai); original acquisition UTC timestamps are in `http_receipts.jsonl`. Requested worker model/effort: gpt-6.1-sol / medium; effective telemetry, tokens and cost: unknown.

## Decision

**NOT ADMITTED for a numerical transferable local sequence/chemistry-edit pilot in this round.** Public processed-data structural candidates exist, but a matched measurement/source contract has not been certified. No outcome magnitudes, rankings, fitted models or numerical performance were computed from the acquired tables. Only the effect column validity bitmap was accessed to establish measurement presence. Already-public prior-paper effect/performance passages were encountered while identifying methods; those are not pristine or independent evidence for this episode.

The admission question is whether a small whole-gene/source-held public-data pilot is defensible. For ordinary direct activity prediction, conditionally yes after freezing a source-family contract and treating the task as replication. For a controlled local-edit functional relationship, **not yet**: current metadata establish candidate comparability, not actual controlled edits. A source-table identifier is only a proxy for a common assay. No model is selected here and no threshold was chosen using effects.

## Official sources and pinned identity

- Dataset: https://huggingface.co/datasets/barneyhill/aso-atlas-2 ; API response `sources/hf_metadata.json`; pinned revision **b947db330a3bf1e194ac190d0f188f7693660852**. Exact card: https://huggingface.co/datasets/barneyhill/aso-atlas-2/raw/b947db330a3bf1e194ac190d0f188f7693660852/README.md . Card and release manifest were read in full. Dataset license CC BY 4.0; dataset DOI 10.57967/hf/8687.
- Code: https://github.com/barneyhill/aso-atlas-2 ; pinned **38987cb1bd61b25aac82af9a553d03d3a138e8bb** from the official commit API. Tree, README, original LICENSE, cleaning-code slice and outcome-blind family-matcher slice are preserved. Downloaded code was inspected as text, never executed. Original LICENSE explicitly identifies CC BY 4.0 and attribution requirement; GitHub API reports NOASSERTION rather than a standard detected SPDX license.
- Public processed table: https://huggingface.co/datasets/barneyhill/aso-atlas-2/resolve/b947db330a3bf1e194ac190d0f188f7693660852/in_vitro_inhibition.parquet . The one redirect is separately counted. Final body `sources/hf_in_vitro.parquet.hop1`.
- Genomic metadata: https://raw.githubusercontent.com/barneyhill/aso-atlas-2/38987cb1bd61b25aac82af9a553d03d3a138e8bb/data/oligostack/processed/in_vitro_inhibition_processed_with_genomic_data.parquet . Source body `sources/in_vitro_genomic.parquet`. This has **178,403 rows**, not the release's 174,459, and cannot silently be substituted for the release. Exact source-ID/table/compound/HELM/target joins match 123,680 release rows without ambiguous metadata joins; 106,255 have a unique canonical-transcript interval. This is partial metadata reuse, not complete revision reconciliation.

## Provenance and extraction uncertainty

The official card describes LLM extraction from public USPTO patent tables, HELM chemistry resolution, manual gene normalization, cell-line enrichment, filtering and deduplication. All filings originate from **one organisation (Ionis)**; applicants' own selectively reported experiments are not independent laboratory replication. Dose, cell line, time and delivery vary. Missing chemistry remains unresolved. DepMap 25Q3 contributes only derived cell-line identifiers, not response data. Dataset publication does not authorize practising patented inventions.

The release lacks a formal patent-family ID, source-protocol equivalence ID, assay assay-method/normalization identifier, biological/technical replicate identity, plate/batch and uncertainty estimates. `USPTO ID` + `Table Number` groups source tables, not independent families or demonstrably identical assays. Official `family_matcher.py` explicitly states that legal family membership alone is insufficient: matching also requires an adjudicated table-equivalence class. No such class map was authenticated here. Hence legal-family counts and certified protocol-class counts remain **unknown**, not 482 independent experiments.

Genomic coordinates are enrichment attached to canonical transcripts. Their transcript-version/reference-strand semantics and original patent target accession agreement were not authenticated. The genomic table's partial join and differing row count are material limitations. Same named gene never qualifies as a local edit by itself.

## Audited structural counts

All counts below are computed by `structural_audit.py`; exact results are in `audit_counts.json`. Outcome values are never converted to pandas, printed, ranked or analysed. Measurement presence reads only validity through Arrow. Metadata and chemistry tokens are eligible inputs only.

| Structural level | Audited count |
|---|---:|
| Official release in-vitro rows / measured-presence rows | 174,459 / 174,459 |
| Source patent IDs | 482 |
| Non-null raw target labels | 390 distinct; not 390 verified genes |
| Resolved HELM / parseable HELM rows | 173,286 / 173,272 |
| Known cell line / dose / treatment time rows | 162,898 / 144,112 / 160,470 |
| Known species / delivery / cells-per-well rows | 173,432 / 145,128 / 143,747 |
| Unique canonical-transcript-region rows after exact source join | 106,255 |
| Complete strict context, deduplicated structure rows | 96,303 |
| Strict-context patent IDs / target labels | 92 / 49 |
| Single-token chemistry candidate pairs | 240, across 13 patent IDs and 9 target labels |
| One-base tiling candidate pairs | 14,586, across 64 patent IDs and 39 target labels |
| Certified controlled base-substitution pairs | 0 authenticated |
| Certified controlled chemistry-edit pairs | 0 authenticated |
| Verified legal families / independent source protocols | unknown / unknown |

Strict context requires nonmissing source patent/table, target label, cell line/species, dose, treatment time, delivery and cells per well, both measured, parseable chemistry and a unique canonical-transcript interval. Exact structure duplicates within context are removed without examining effects. Chemistry candidates additionally require identical base identities and interval, equal length and exactly one changed HELM monomer token (sugar/base/backbone tuple; base held equal). These candidates are saved in `chemistry_candidate_pairs.csv`. A token edit is not necessarily one chemically elementary perturbation, and positional stereochemistry is not certified.

Tiling candidates require the same canonical transcript, same length and sugar/backbone pattern, with both interval boundaries shifted exactly one nucleotide. They are saved separately in `tiling_candidate_pairs.csv`. These are window shifts that change target context as well as sequence; they are **not controlled base substitutions**. Pair counts share compounds and regions and are not independent sample sizes. Lack of authenticated families prevents a credible family-level holdout count. The 390 raw labels differ from the card's 389 named genes; unnormalized labels and viral targets must not be marketed as confirmed gene units.

## Closest priors and exact reading boundaries

### OligoAI and original ASO Atlas

Authenticated published article: Hill et al., *Accurately modeling RNase H-mediated antisense oligonucleotide efficacy*, Molecular Therapy Nucleic Acids 37(3), 103004 (2026), DOI **10.1016/j.omtn.2026.103004**, PMID 42542598, PMCID PMC13427547. Official full text acquired from https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13427547/fullTextXML ; preserved as `sources/oligoai_fulltext.xml`, extracted paragraphs in `oligoai_passages.txt`. Reading level: source XML and targeted abstract/method/result/prior passages, not a page-by-page figure audit.

The abstract states that OligoAI jointly models “RNA target context, ASO sequence, sugar and backbone chemistries, and dosage to predict in vitro efficacy.” The introduction explicitly describes learning how sequence and chemical modifications influence efficacy. The source also examines chemistry-dependent position-specific nucleotide effects and dense local tiling. These are close adverse priors for a claimed transferable RNA-context/chemistry representation. Direct predictions evaluated as differences are an equal-information baseline already implied by this model, even though a dedicated pair-difference loss was not authenticated.

Official code is linked in the paper: https://github.com/barneyhill/OligoAI ; pinned commit **487e96177e8e2d736654de5b52b39a34401fd0a5**. The pinned README was read; it already specifies pretrained RiNALMo weights and RNA-language-model finetuning. Thus a RiNALMo-plus-context-plus-chemistry ASO predictor is not a new principle. No code license was authenticated for OligoAI, no model weights acquired and no code executed.

The original ASO Atlas accompanies this OligoAI article (188,521 sequences / 334 genes are the paper's historical scope, not this release's audited eligible pairs). Atlas 2.0 repository README identifies *ASO Atlas 2.0: Evaluating antisense oligonucleotide prediction across the preclinical pipeline*, Hill/Whiffin/Rinaldi/Sanders, submitted to NeurIPS 2026. The repository `typst` is a submodule pointing to `barneyhill/paper2`; its public tree returned 404. The repository file `nLorem_paper.pdf` is an unrelated clinical n-Lorem article, **not the Atlas 2 manuscript**; it is preserved with this identification and not used as Atlas evidence. Full Atlas 2 paper authentication therefore remains unresolved. Its public README/card are source-level documentation, not substitutes for unseen manuscript details.

### ASO-RASAR

Authenticated metadata and original abstract: Hwang et al., *ASO-RASAR: A Read-Across Framework for Predicting Antisense Oligonucleotide Gapmer Activity Across Target Genes*, J Chem Inf Model 66(13), 7462–7475 (2026), DOI **10.1021/acs.jcim.6c01314**, PMID 42364111. Official publisher URL https://pubs.acs.org/doi/10.1021/acs.jcim.6c01314 returned **403**; no retry, proxy or access bypass. Original abstract is preserved through Europe PMC's indexed core record: https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:42364111%20AND%20SRC:MED&format=json&resultType=core . Reading level: authenticated abstract only; full methods/code not accessed.

The abstract explicitly benchmarks gene-specific and leave-one-gene-out activity prediction with sequence and target-context descriptors, reports difficulty generalizing across genes, and proposes read-across transfer from data-rich to data-poor genes. This already covers an ordinary cross-target information-transfer proposal and is an adverse prior for broad transferable-ASO claims. It does **not**, at abstract reading level, authenticate a controlled local pair-difference objective. That absence is not proof of novelty. A new pair loss must still beat both direct activity prediction differenced afterward and read-across/conditional-interaction rivals with equal information and legally related source tables kept together.

## Potential future freeze, not authorization or pilot execution

If this entrance is revisited, first authenticate original patent table/protocol passages for the 240 candidates, reconcile canonical target-coordinate versions and group formal families plus adjudicated duplicate/equivalent source tables. Freeze all edit eligibility without effects. Hold out whole target genes **and** independent source-family groups, and compute independent counts before defining a numerical task. Compare direct activity predictions differenced after prediction, simple chemistry/sequence features and conditional interactions; a pair representation is an ordinary statistical alternative. Effect magnitude thresholds, local windows and retention criteria must not be tuned on held effects. No such pilot has been run or frozen here.

## Acquisition and data boundary receipt

All 22 HTTP attempts used the shared `fetch_source.fetch(..., role="aso")`; no alternate network route, automatic retries, weights, installs or access bypass. Total acquired decoded bytes including redirect/error bodies: **27,696,297** (26.41 MiB). Ceiling: 22 attempts / 128 MiB. Wire-byte totals cannot be certified. Full per-call URLs/status/timestamps/body SHA-256 are in `http_receipts.jsonl`; summary and processed-file hashes in `usage.json`.

- `sources/hf_in_vitro.parquet.hop1`: 9,024,462 bytes; SHA-256 `447426f598d3c1763efd0eb31786cc8fdf3daecbcf594c5aa96a95964c367e7f`.
- `sources/in_vitro_genomic.parquet`: 14,889,056 bytes; SHA-256 `e64a7d3aa3632141ea9c69e59944cecf90e38da5cb22c78c7e0602a81db6306c`.

No protected CGI/S2/HTS031 outcomes, shared library/index, production source/tool, global configuration, commits, external messages or model fits were accessed/changed. No further delegation occurred.
