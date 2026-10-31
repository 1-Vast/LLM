# AssayBench resource audit B — 2026-10-30

**Decision: eligible for a small, internal, publication-grouped binary gene-hit ranking pilot.** The downloaded training labels support assay-context prediction and common-essential-gene controls. They do not establish a causal treated-minus-control effect, a mechanistic virtual cell, a new learning principle, or agent benefit. No model was fitted in this audit.

## Observed resource and split boundary

- Official HF revision: `fa2ed4195d2eea1e5ed570d1a67c21e47650962d`; official code revision: `552008a7f3c52c560c60dbdadd2dc0d2f8e928dc`.
- Actual BioGRID parquet has **1,901 entries, 1,565 underlying original screen IDs, 231 publication IDs, 41 columns, 11 row groups** (ten groups of 173 rows and one of 171).
- The HF physical split is named `train` for every row. The real primary split is the **`yearfold0` column: train 1,349, validation 218, test 334**. Calling the HF split `train` is not permission to train on all rows.
- Training is publication year ≤2020; validation is 2021; test is ≥2022 (paper §2.3). The distinct `LaTest` config has 19 recent-publication screens (after September 2025). Thus 1,920 combines historical entries and LaTest; it is not the historical training count.
- No LaTest parquet, existing sealed/protected/confirmation file, or existing local research outcome was opened. Public historical validation/test gene/hit values co-occur in the physical chunks downloaded below; they were masked in Arrow before conversion to Python, census, and output, and were not scored. This mixed-chunk retrieval was explicitly authorized by the coordinator.
- Source acquisition was initially capped at 100 MB, then expanded to 265 MB for the two projected columns. Logged received/saved HTTP response bodies total **252,230,176 bytes**; the gene/hit chunks account for 250,944,990 bytes. The complete 1,092,438,556-byte parquet was not downloaded.

## Usable files and schema

All paths below are under `D:/MAESTRO/data/external/virtual_cell_four_directions_20261030/assaybench/`.

| File | Contents |
|---|---|
| `biogrid_temporal_train_gene_hits_csr.npz` | NumPy-only arrays, 46,887,143 bytes; 1,349 × 23,724 matrix dimensions |
| `biogrid_temporal_train_metadata.json` | All 35 scalar metadata fields for the same ordered 1,349 training tasks, plus original screen IDs and gene/hit counts |
| `biogrid_temporal_train_metadata.csv` | CSV equivalent of that training metadata |
| `biogrid_metadata_only.parquet` | Scalar metadata for all 1,901 historical tasks; contains no outcome arrays |
| `chunks/rg??_genes.bin`, `chunks/rg??_hit.bin` | Exact pinned source byte ranges; mixed historical split bytes, not a training-ready table |
| `ranges/` | Footer and scalar source byte ranges |
| `code/` | Targeted official loader, screen/metric/baseline implementation and notices |
| `paper.html` | Official arXiv HTML; selected methods were read |

The NPZ keys are `genes`, `dataset_names`, `shape`, `measured_indices`, `measured_indptr`, `hit_indices`, and `hit_indptr`. The two CSR matrices have implicit one-valued data. **Unmeasured gene-task pairs are missing, not negative labels.** Gene and task arrays define the column and row order. For example:

```python
import numpy as np
from scipy.sparse import csr_matrix

z = np.load(path, allow_pickle=False)
shape = tuple(z['shape'])
measured = csr_matrix((np.ones(len(z['measured_indices']), dtype=bool),
                       z['measured_indices'], z['measured_indptr']), shape=shape)
hits = csr_matrix((np.ones(len(z['hit_indices']), dtype=bool),
                   z['hit_indices'], z['hit_indptr']), shape=shape)
```

The six original array columns are `relevance_genes` (list of string), `hit` (list of bool), and four list-of-float columns: `relevance_scores`, `combined_scores`, `unmasked_scores`, `raw_scores`. Only genes and hits were retrieved. Each full float column is about 210.3 MB; the gene column alone is 247.6 MB. Full schema and row-group metadata are in `parquet_footer.json`.

The 35 scalar fields include identifiers `dataset_name`, `author`, `source_id`; experimental fields `cell_line`, `cell_type`, `phenotype`, `screen_rationale`, `library_methodology`, `screen_type`, `library_type`, `experimental_setup`, `condition_name`, `condition_dosage`, `duration`, `notes`, `condition_clause`, `significance_criteria`, `ranking_rationale`, `source`, `screen_category`, `cleaned_phenotype`; and the `authorfold*`, `cell_linefold*`, `phenotypefold*`, `randomfold*`, `yearfold0`, `year_match_val_testfold0` assignments.

## Training census

| Quantity | Observed |
|---|---:|
| Tasks / publications / underlying screen IDs | 1,349 / 134 / 1,206 |
| Distinct merged screen-ID tuples | 1,201 |
| Cell-line strings / cell-type strings | 681 / 99 |
| Phenotype descriptions / screen rationales | 343 / 96 |
| Condition names, including `Not specified` | 151 |
| Condition missing or unspecified | 987 / 1,349 (73.2%) |
| Dosage missing or unspecified | 1,044 / 1,349 (77.4%) |
| Measured gene-task pairs / hit pairs | 20,489,712 / 1,498,169 |
| Micro / macro hit prevalence | 7.31% / 8.65% |
| Median genes / hits per task | 17,637 / 1,306 |
| Gene-count range | 32–21,205 |
| Hit-prevalence range | 0.0049%–98.23% |
| Duplicate symbols within tasks / zero-hit tasks | 0 / 0 |

Cell line, cell type, phenotype, rationale, and duration have no empty/`Not specified` training values. Completeness does not imply controlled terminology or distinct biological backgrounds: 490 of the 681 cell-line strings occur in one publication only, while 191 occur in multiple publications; resistant backgrounds can be described only in notes while retaining the same cell-line string.

Training categories are fitness 947 (42 publications), drug/environment response 278 (58), molecular output 48 (12), trafficking 38 (14), infection 38 (23). The actual historical category counts are 1,027 / 579 / 91 / 44 / 160, respectively. The card/paper contain different category subtotals, so use the pinned data census for this episode.

## Endpoint and independence checks

- Training has 1,062 unidirectional, 243 directional/bidirectional-derived, and 44 recovered-bidirectional entries. The last category has generic effect descriptions.
- There are 74 complete `dec`/`inc`/`merged` triplets. In **all 74**, directional binary-hit sets are disjoint and the merged binary-hit set equals their union. An additional 21 decreasing branches have no complete triplet. Related entries must stay together; their repeated gene measurements are not independent screens.
- Paper §§2.2 and A.1 define positive relevance as target-direction significance, zero as non-hit, and negative relevance as opposite-direction significance. The downloaded binary hits support hit prioritization. They do not preserve continuous relevance magnitude or distinguish opposite-direction hits from ordinary non-hits; signed AnDCG/dFDR should not be claimed from this NPZ alone.
- The top two publications are Meyers 2017 (`29083409`, 340 entries) and Behan 2019 (`30971826`, 324): together 49.2% of training. Use publication macro averaging or explicit study weighting; a task-micro average can be dominated by them.
- `source_id` is a PubMed ID and is a useful grouping key. No publication ID or original screen ID crosses the provided temporal split.
- **Merge/exclude provenance-related sources `27260156` and `29083409` before an internal split.** The 33 Aguirre GeCKOv2 rows explicitly say they were reanalysed using CERES in Meyers and use gold-standard essentiality sets tied to other sources. Publication identity alone is not proof of raw-data independence. See the exact note in `census.json`.

## Treatment/control and text quality

There are 246 same-publication/cell-line/library unspecified-versus-treated candidate pairs across 11 studies. Only six match phenotype text, screen type, and duration; all concern PMID `32416067`, SUM149PT, JQ1 versus unspecified conditions. Two unspecified backgrounds differ in resistance state in their notes. No condition name explicitly says untreated/DMSO/vehicle/control. This is insufficient for a broadly replicated causal treatment-control residual endpoint.

One genuine no-drug baseline is task `2374` (PMID `32028983`, HAP-1, 14 days): notes say “in the absence of any drug.” Its 20 drug tasks use positive-selection resistance, while the baseline uses negative-selection viability. They are useful contextual examples but not directly subtractable matched functional effects.

Do not feed `notes`, `ranking_rationale`, `significance_criteria`, author/publication/IDs, or loader-generated `answer` into a new predictor. Notes can disclose outcomes: task `1165` says PARP10 knockout potentiates a drug; tasks `2375` onward name seven compounds that yielded no significant hits; essentiality notes reveal shared gold-standard label construction. The loader creates `answer` directly from top-scoring target genes.

The candidate-safe phenotype/condition/rationale fields contain gene symbols in 48/23/30 rows. Inspected examples identify the assay readout, drug target, or perturbation background (NCOA4 reporter, BRD4/JQ1, BRCA2 knockout), not hit lists. Symbol presence alone is not leakage. This bounded check does not certify every sentence; use a fixed feature allowlist and keep the same information in all comparators.

## Baselines and experimental gate

The official paper's gene-frequency method is already **phenotype-category conditioned**, and attributes much of its strength to recurring fitness dependencies (§§4.3, 5.4). Calling a category-specific frequency model “conditional” does not establish a new method.

Official code implements global observed-hit frequency; screen-type, `screen_rationale`, and `cleaned_phenotype`-stratified frequencies; library-coverage prior; and TF-IDF neighbor hit frequency. The exact TF-IDF comparator concatenates `phenotype`, `condition_clause`, `screen_rationale` excluding `Not specified`; uses 5,000 features, English stop words, 1–2 grams, cosine similarity, 10 nearest training screens; aggregates each gene's unweighted hit count divided by its measured-neighbor count; gives unseen genes zero and randomly breaks ties. The embedding kNN described in the paper is a different comparator.

Frequent hit genes in the training census include TXNL4A (812/1,041), SNRPD1 (814/1,058), RPS11 (844/1,101), PRPF19 (840/1,099), and RPL23 (812/1,071). This is consistent with recurring essentiality dominating many fitness tasks. Frequencies in this descriptive audit include all official historical train rows; **recompute them only from an internal fit partition** for any internal held-out test or low-frequency-gene mask.

A suitable pilot compares a fixed context-feature predictor/residual model with ordinary global, phenotype/type priors, exact TF-IDF KNN, and a regularized direct/kernel predictor on the same features. Group publication/provenance components, keep original-screen branches together, retain the measured-gene mask, account for tasks with fewer than 50 genes/hits, and report study- and category-level results plus a fit-only-defined low-frequency-gene subset. This is an internal methodological comparison. A gain cannot by itself establish new biology, transport to unseen systems, or algorithmic novelty.

## Source access and reading limits

Requests, status/error outcomes, exact URLs, ranges, hashes, and byte totals are in `requests.jsonl`. The supplied lowercase site returned 404; official GitHub metadata identified the functioning case-sensitive site `https://genentech.github.io/AssayBench/`. Several SSL EOFs succeeded on bounded retry. One initial tiny-range SSL failure preceded retry logging and is backfilled with an explicit marker.

Official sources read: pinned HF card/API/tree; official GitHub loader, screen wrapper, metric, baseline implementation and third-party notices; arXiv `2605.10876` §§2.1–2.4, 3.2, 4.3, A.1, C.1 plus targeted statements on frequency/essentiality. Public paper descriptive split metadata was read; official per-gene evaluation labels were not analyzed. No external model API, training, paid bridge, exhaustive novelty search, or LaTest data request occurred. The HF dataset card and official code state MIT; code notices explicitly do not grant rights to third-party datasets, and this audit does not establish upstream BioGRID rights beyond the public distribution.

Reproduction: `inspect_parquet_metadata.py` retrieves scalar projection; `fetch_train_gene_hits.py` retrieves/caches exact gene/hit chunks and emits training CSR; `census.py` validates/counts training labels; `audit_text_and_pairs.py` checks metadata pairing and text flags. `paper_methods_excerpts.md` preserves the selected official methods. Model configuration is inherited; effective model/cost is unknown.
