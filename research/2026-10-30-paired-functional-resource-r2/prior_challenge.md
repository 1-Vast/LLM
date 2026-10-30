# Closest-prior challenge: proxy assays, independent function, and agent-selected experiments

Date: 2026-10-30. This is a bounded review of recent primary methods and counterexamples, not an exhaustive novelty search. No author code was run, no sealed outcomes were opened, and no experiment was performed.

## Decision

The broad loop of using an inexpensive molecular proxy, receiving phenotype feedback, and updating ranking or experiment choice already has direct precedents. DrugReflector paired transcriptomics with phenotype feedback and reported improved hit rates in later compound selection. Model Discovery Agent combines LLM-proposed mechanisms, predictive-failure checks, posterior updating, and value-of-information experiment selection. BATCHIE selects batches from posterior uncertainty in real drug-combination screens. These components cannot individually support a novelty claim.

CellQ/PACE is the closest reviewed combination of virtual-cell state, external functional readout, and rule revision. Its reported PBMC feedback changed an aggregate scoring rule, but this review did not verify a preregistered cost decision between measuring function and updating a local state model, nor equal-budget functional hit-rate results on untouched compounds or backgrounds. The study is a preprint; its complete supplement, code, weights, and agent logs were not verified. The OMIX017117 snapshot was controlled access and its 1.69 GB H5AD was unavailable.

The current I304/local-reuse proposal should remain a conditional information audit. Hierarchical measurement-error models, latent error-source variables, posterior predictive checks, and ordinary cost-aware value of information are required baselines. Retain an agent-specific claim only if matched proxy/function data show an advantage over those baselines on whole-drug and whole-background holdouts, including fewer costly functional measurements at equal budget.

## Closest precedents

| Work | Reported operation | Overlap | Remaining gap |
|---|---|---|---|
| DrugReflector, *Science* 2025, DOI `10.1126/science.adi8577` | CMap transcriptomic signatures ranked compounds; CD34+ megakaryocyte/erythroid phenotypes were screened and confirmed across donors. Early scRNA from 12 hits and 8 non-hits was paired with day-7 phenotype to revise a signature; later top-100 hit rate was reported to increase about twofold. | Direct precedent for inexpensive omics proxy, independent phenotype feedback, ranking revision, and follow-up compounds. | Supplementary pairing, per-candidate cost policy, and complete blind split were not verified. No explicit strategy comparison of measuring function versus updating only local virtual state was found in the reviewed paper. |
| BATCHIE, *Nature Communications* 2025, DOI `10.1038/s41467-024-55287-7`, PMCID `PMC11696745` | Bayesian tensor factorization with posterior-simulation batch acquisition; prospective screen covered 206 drugs by 16 cancer cell lines. Authors report prediction of unmeasured combinations after exploring about 4% of 1.4M combinations and follow-up of top Ewing sarcoma combinations. | Strong ordinary baseline for uncertainty-driven measurements and external validation. | Endpoint is viability/therapeutic index and combination synergy, not an independent function endpoint or single-agent virtual-state update. |
| Model Discovery Agent, arXiv:2608.09696v1 (2026 preprint) | LLM proposes mechanisms; SMC/SBI maintains structural and parameter posteriors; failed out-of-sample checks expand the hypothesis class; value of information selects experiments. Biological example is single-neuron electrophysiology, with physics and chemistry benchmarks. | Precedent for agent model proposals, failure-triggered expansion, posterior maintenance, and experiment selection. | No drug-screen evidence joining proxy efficacy to independent function; no measured benefit for choosing direct function assays versus local virtual-state updates. |
| CellQ/PACE, bioRxiv v1 (2026-08-11), DOI `10.64898/2026.08.04.742916` | CellQ compresses scRNA into eight RVQ tokens and predicts drug-induced modules; PACE uses ten directional cell-type modules. The paper reports reducing about 5,000 candidates to 110 PBMC compounds. Analyzer--Planner--Auditor feedback changed `(D+U)/2` to `min(D,U)`; 13 compounds were associated with T-cell flow, senescence, and cytokine readouts. | Closest reviewed combination of virtual-cell state, external function, and agent/rule update. | Preprint details and data are not fully accessible. The changed aggregate score does not establish identifiable local response-model updating or equal-budget transfer to unseen drugs/backgrounds. |
| MultiVCDiff, *Cell Reports Methods* 2026, DOI `10.1016/j.crmeth.2026.101459` | CPgenes assigns perturbation-level averaged L1000 expression to morphology samples; examples use static 24 h endpoints rather than continuous dose/time dynamics. | Recent multimodal virtual-cell representation. | Perturbation-identity joins do not establish matched cell, drug, dose, time, preparation, replicate, and RNA/function covariance; no agent acquisition benefit is shown. |
| Context-response systems comparison, *Science Advances* 2026, DOI `10.1126/sciadv.aed3414` | Separates basal/shared/perturbation/non-additive/context-specific residuals and discusses conserved versus rewired responses, batch/protocol, controls, replicates, perturbation efficiency, destructive scRNA, and sparse time points. | Covers several local-residual and context-transfer diagnostics. | Not a drug agent-selection loop with independent functional endpoints. Renaming residuals or adding a natural-language agent does not establish new capability. |
| Active learning with mechanistic logic-ODE, *Signal Transduction and Targeted Therapy* 2026, DOI `10.1038/s44320-026-00221-w` | Two PDAC lines, cytokines/inhibitors, 24 h CXCL9 bead-FACS, and logic-ODE coupled to greedy, uncertainty, and GU acquisition; two screens and technical replicates, with authors describing n=2 biological replicates and mainly qualitative statistics. | Strong nearby baseline for functional readout, mechanistic model, and uncertainty acquisition. | No independent endpoint loop for an agent virtual cell or demonstrated cross-background/compound agent advantage; CXCL9 secretion is not tumor killing. |

## Resource eligibility

| Resource | Current status | Eligible use |
|---|---|---|
| PRISM 19Q4 / 24Q2 | 19Q4 viability has already been exposed during development; 24Q2 review is limited to metadata/README. | Viability-only baseline or action-cost design; not proxy/function attribution by itself. |
| Perturb-seq / scPerturbBench | Public RNA perturbations, often fixed dose/time, with pooling or response-selection concerns. | Molecular proxy only until matched function and independent replicates are established. |
| BATCHIE ALMANAC/GDSC2/MERCK | Paper and data entry points are identifiable. | Reproduce Bayesian adaptive viability selection as an ordinary strong baseline. |
| CellQ/PACE OMIX017117 | Reported virtual-cell/function workflow; controlled-access dataset. | Borrow directional panels, revision ledger, and interface concepts; not a reproducible local evaluation set. |
| DrugReflector campaign | Paper reports paired scRNA/phenotype and follow-up hit-rate gains; local review covered selected PDF content only. | Closest biological precedent, not a verified downloadable validation set. |
| CAF/LPC | Two-assay criterion is relevant; workbook recovery was incomplete. | Precedent only, not a row-level reanalysis resource. |

## Minimum falsification and acceptance gates

1. Demonstrate matching keys for drug, background, physical dose, exposure time, vehicle, preparation/plate, biological replicate, proxy, and independent function. A drug-name or perturbation-identity join is insufficient.
2. Freeze whole-drug and whole-background holdouts before model/agent choices. Keep exploratory development, post-selection readout, and independent confirmation separate.
3. Compare against random selection, uncertainty-only selection, ordinary hierarchical measurement-error modeling, and cost-aware value of information under equal measurement budgets.
4. Report functional outcomes and actual assay counts/costs. Prediction or ranking gains alone do not prove savings or causal mechanism learning.
5. Treat missing or inaccessible resources as unavailable for this evaluation, not proof that they do not exist. Preserve controlled-access and sealed-data boundaries.

## Evidence boundary

Findings are limited to the listed papers, reviewed source excerpts, and local resource audits. Reported results are author claims unless independently reproduced. The complete original-language audit and underlying citations remain in the user's `D:\MAESTRO` workspace; they were not altered by this publication repair.
