# Bounded author-GitHub metadata search

2026-10-22. qualification_assay. Root authorized at most three public GitHub metadata requests, no biological values/expressions/IDs, no protected data, no author contact. Executed exactly three requests, all HTTP200. Bodies and SHA256 receipts are retained beside this file; acquisition code is `research/replogle_growth_acquisition_20261022/biology/github_metadata.py`.

1. Repository metadata for thomasmaxwellnorman/Perturbseq_GI: default branch master.
2. Public repository list for josephreplogle (`per_page=100`): returned four repositories. Newly named lead **CRISPRi-dual-sgRNA-screens**, default branch main, https://github.com/josephreplogle/CRISPRi-dual-sgRNA-screens . Other repositories: guide_calling, infercnvpy, target_enrichment. The new lead's description is null; this result alone does not authenticate study year or data coverage.
3. Recursive metadata-only tree for Perturbseq_GI/master: no truncation. Paths include `final_emaps/processed_fitnesses.csv`, `processed_perturbseq_fitnesses.csv`, `single_fitnesses.csv` and replicate phenotype tables, but named neighboring paths identify **CRISPRa K562 epistasis**. These must not silently become the original2022 CRISPRi dual-guide gamma. No file contents were fetched.

## Decision

**EXACT_2022_GROWTH_FILE_NOT_IDENTIFIED.** There is a concrete author-owned repository lead with a promising intervention-class name, but its tree/README has not been read within this three-request budget. Root was promptly informed, with URL/default branch and uncertainty. A next bounded metadata-only tree request to that newly identified repository is defensible if separately allocated; this reviewer does not make it implicitly. Do not download Norman fitness tables merely because a filename contains fitness.

No biological numerical payload, state value or row identifier was downloaded/decoded. The only downloaded bodies were GitHub repository/list/tree metadata. This source search is not a performance experiment, confirmed paired dataset, or global no-data conclusion. Full goal and independent growth join remain unfinished.
