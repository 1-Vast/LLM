# DOI paper audit (evidence-bounded)

**Requested model / effort:** `gpt-6-astra / xhigh` (effective model: not exposed).  
**Audit date:** 2026-10-30.  
**Paper:** Yue You et al., “Virtual-cell verification enables self-auditing AI discovery for immune rejuvenation.”  
**DOI:** [10.64898/2026.08.04.742916](https://doi.org/10.64898/2026.08.04.742916).  
**Version located:** bioRxiv v1, posted 2026-08-11; preprint, CC BY.

## Evidence obtained

The DOI, title, date, author list, corresponding author (Luyi Tian, Guangzhou National Laboratory), bioRxiv status, license, and abstract agree across [Crossref](https://api.crossref.org/works/10.64898/2026.08.04.742916), [OpenAlex](https://api.openalex.org/works/https://doi.org/10.64898/2026.08.04.742916), and the [bioRxiv API](https://api.biorxiv.org/details/biorxiv/10.64898/2026.08.04.742916). [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.64898/2026.08.04.742916&format=json) indexes it as PPR1296302, but reports `hasPDF=N`, `inEPMC=N`, and no full text. [Semantic Scholar](https://api.semanticscholar.org/graph/v1/paper/DOI:10.64898/2026.08.04.742916?fields=title,authors,openAccessPdf,url,abstract) supplies the same abstract and only a DOI landing-page OA link.

The abstract is the only paper content that could be read reliably. It reports three verifiers:

1. **PACE (phenotype verifier).** Immune aging is represented by ten directionally scored, cell-type-resolved gene-set modules. The modules were selected for cross-cohort stability across four PBMC cohorts. The abstract says PACE outperformed five established aging clocks in an independent in-house cohort of 434 elderly donors.
2. **CellQ (virtual-cell verifier).** A “multi-modal LLM” compresses each single-cell transcriptome into eight discrete tokens aligned with an LLM vocabulary by residual vector quantization (RVQ). The abstract claims state-of-the-art perturbation prediction and sensitivity to weak module-level shifts that differential-expression recovery misses.
3. **Analyzer–Planner–Auditor agent.** The agent screened 110 compounds in primary human PBMCs. It observed that aged-down modules were more reversible than aged-up modules, changed its objective from an equal-weight mean to a balance-constrained minimum, and reportedly generalized this self-correction to an independent 13-compound T-cell assay.

The last two bullets are abstract-level claims. They should not be treated as a methods read or as a result table: no effect sizes, uncertainty intervals, baselines, or raw observations are present in the abstract.

## CellQ audit: what is and is not established

| Audit item | Evidence available from the abstract/metadata | Unresolved from inaccessible full text |
|---|---|---|
| Input | A single-cell transcriptome is mapped to eight discrete RVQ tokens; the abstract calls the model multimodal. | Raw counts versus normalized expression, gene vocabulary, QC, cell-type/context fields, donor metadata, modalities other than transcriptomics, and whether perturbation identity/dose/time are model inputs. |
| Tokenization/model | RVQ aligns eight discrete tokens to an LLM vocabulary. | Codebook size, residual levels, tokenizer training objective, LLM backbone, decoder, conditioning path, and whether eight tokens is fixed for every cell. |
| Training data | None stated for CellQ. The four PBMC cohorts are explicitly attached to PACE module selection, not explicitly to CellQ training. | Dataset names/accessions, number of cells/donors, perturbation classes, chemical versus genetic perturbations, control construction, preprocessing, train/validation/test split, leakage controls, and training compute. |
| Validation/test | “State-of-the-art perturbation prediction” and recovery of weak module shifts are claimed. | Benchmark identity, held-out perturbations/cell types/donors, comparator set, metrics, numerical results, confidence intervals, and whether the test set is independent. |
| Perturbation type | The agent screen uses 110 compounds in primary human PBMCs; CellQ's perturbation task is not typed in the abstract. | Drug names/targets, genetic perturbations, combinations, concentrations, exposure times, washout, and dose-response design. A chemical screen should not be inferred to be the CellQ training task. |
| Biological readout | Module-level transcriptomic shifts are emphasized; PACE defines the modules. | Any direct protein, viability, cytokine, proliferation, activation, or other cell-function endpoint. Transcriptomic module recovery is not evidence of functional rescue. |
| Replication | The abstract gives counts of 110 and 13 compounds and calls the latter assay independent. | Donor count, biological/technical replicates, plate/randomization design, batch correction, missingness, and whether each compound was tested at more than one dose/time. |
| External cohorts | PACE: four PBMC cohorts for cross-cohort stability and an in-house 434-elderly-donor cohort. Agent: an independent 13-compound T-cell assay. | CellQ-specific cohort boundaries and whether the 13-compound assay is independent of CellQ training/model selection. |

Thus, the defensible statement is: **the abstract specifies an eight-token RVQ interface and reports an agent-level transcriptomic verification/self-correction story; it does not expose enough information to audit CellQ training, generalization, dose/time behavior, replication, or functional validation.**

## How the agent appears to use CellQ (abstract-level reconstruction)

The abstract does not provide a prompt, API, diagram, or algorithm pseudocode. The narrowest reconstruction consistent with the text is:

- **Analyzer:** obtains CellQ's predicted perturbation response and evaluates it in the PACE module space (or uses CellQ to verify predicted weak module shifts), then compares it with measured primary-PBMC screen results.
- **Planner:** proposes or prioritizes compounds/assays for the 110-compound screen under the current score.
- **Auditor:** checks whether the score's behavior agrees with experimental module reversibility and changes the aggregation rule when the equal-weight mean is judged misleading; the revised rule is then tested in the 13-compound T-cell assay.

This role mapping is an interpretation of the abstract, not a full-text finding. It does not establish that the LLM itself chooses doses, generates compounds, calls laboratory instruments, or updates CellQ weights. “Self-auditing” here is supported at the objective/scoring-logic level reported in the abstract; it should not be expanded to autonomous biological or causal self-correction.

## Transfer to “cheap public drug screen + same-target drug pair + cell function” CDI

### What can be borrowed with minimal commitment

The most portable mechanism is a **verifier loop around a fixed, auditable phenotype score**:

1. Represent each compound-treated cell state in a compact latent/token space (an RVQ-LLM tokenizer is optional; a simpler validated perturbation embedding is a valid first implementation).
2. Predict module-level responses for single drugs and same-target pairs, and aggregate them with an explicit CDI score.
3. Reserve a target/pair/lineage holdout. Let an Auditor compare predictions with a small, predeclared cell-function assay and revise the score only under a recorded rule (for example, a balance constraint that prevents one rescued module from hiding a harmed module).
4. Re-test the revised score on an independent pair set and report transcriptomic and function endpoints separately.

This transfers the **separation of prediction verification from objective verification**, not the paper's CellQ performance claim or its biological conclusion.

### Strongest counterexample / failure mode

An equal-weight mean can reward a large improvement in one module while a safety-critical module worsens; a balance-constrained minimum can expose that failure. However, the reverse failure is equally plausible: a minimum over noisy modules can over-penalize a useful pair because of one unstable or poorly measured module. More fundamentally, a transcriptomic shift can be disconnected from cell function, and same-target drugs can differ in off-target activity, exposure, and pharmacology. Therefore, the reported 110-compound PBMC screen plus 13-compound T-cell assay does **not** demonstrate same-target pair synergy, dose-aware transfer, or functional CDI rescue.

### Claims that must not be made for CDI

- Do not claim that CellQ is state-of-the-art for CDI, or that eight-token RVQ is necessary, without its data, code, and a matched benchmark.
- Do not claim that the Analyzer–Planner–Auditor loop generalizes from the paper to same-target drug pairs, a new lineage, or a cell-function endpoint. That requires an independent, predeclared holdout.
- Do not claim causal target mediation, synergy, mechanism, dose optimization, or therapeutic rejuvenation from module-level expression prediction.
- Do not count “110 compounds” and “13 compounds” as replication numbers: the abstract gives compound counts, not donor/technical replicates or power.
- Do not treat the four PACE PBMC cohorts or the 434-donor PACE cohort as CellQ training/validation cohorts; the abstract does not make that linkage.

### Minimum CDI evidence needed before any positive claim

Publish the exact public datasets and preprocessing; freeze target/pair/lineage/donor splits; specify doses and exposure times; report biological and technical replicates; compare against a simple latent/DE baseline and a perturbation model; evaluate per-module predictions and the cell-function assay separately; and log every objective revision with an untouched post-revision test set. A negative or null function result must remain visible even if transcriptomic CDI improves.

## Access and repository record

- `https://www.biorxiv.org/content/10.64898/2026.08.04.742916v1.full.pdf`, the early full-text PDF route, the HTML route, and the JATS XML route returned HTTP **429 Too Many Requests**. A retry after the server's `Retry-After: 64` interval still returned 429. No login or paywall was bypassed.
- `https://syndication.highwire.org/content/doi/10.64898/2026.08.04.742916` returned **403 Forbidden**.
- DOI resolution redirects to bioRxiv and then returned 429. Europe PMC `fullTextXML` returned **500** and its record says no PDF/full text. OpenAlex and Unpaywall expose only the DOI landing page and no PDF URL.
- Public GitHub searches for the exact title/DOI/`CellQ`, plus the corresponding author's [`LuyiTian` repositories](https://api.github.com/users/LuyiTian/repos?per_page=100) and [`TianGzlab` organization repositories](https://api.github.com/orgs/TianGzlab/repos?per_page=100), did not locate a repository identifiable as this paper's CellQ or Analyzer–Planner–Auditor implementation. This is a bounded public-search result, not proof that no private or later repository exists.

No source code under `src/tools` was modified. No scientific experiment or mechanistic adjudication was performed.

