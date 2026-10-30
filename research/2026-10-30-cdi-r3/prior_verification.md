# Closest-prior review for CDI (2026-10-30)

## Scope and candidate definition

This review used publisher pages/full text where available, publisher PDFs, author repositories, and Crossref metadata. It did not use user-pasted summaries. The CDI candidate takes same-target drug pair A/B, molecular relative affinity difference `Delta a` (measured Kd/pChEMBL or frozen PBCNet2.0 prediction), and matched drug-by-cell-by-dose/time functional readout `y`. It estimates `D = [y(A,C1)-y(B,C1)] - [y(A,C2)-y(B,C2)]` and asks whether the affinity-to-function relation depends on target and cell background. The virtual cell models this conditional relation; an agent selects drug/cell pairs to distinguish structural-model error, weak target dependence, cell pharmacology, and experimental mismatch under equal budget.

## Findings by paper

### AdaMBind, *Nature Communications* 2026

DOI `10.1038/s41467-026-70554-5`. The paper organizes DTA data by unique protein target, inputs molecule graph and protein sequence, and predicts binding affinity. It reports MAML and adaptive task modules, support-set adaptation for unseen targets, BindingDB/KIBA/Davis and LIT-PCBA evaluation, and comparisons with DeepDTA, HiSIF-DTA, ColdDTA, Co-VAE, PSICHIC, CML, MetaDTA, and ZeroBind. Its FLT3 example used ten inhibitors to form a support set, queried DrugBank, and reports ADP-Glo validation for Staurosporine against FLT3-WT/FLT3-ITD at n=3.

This occupies target-organized tasks, few-shot affinity prediction, and unseen-target adaptation. The FLT3 validation is a single candidate's enzyme assay, not same-target A/B comparisons across C1/C2 backgrounds or the CDI difference-in-differences `D`. The review did not rerun benchmarks or independently verify the biology; results remain author-reported internal evaluation.

### PBCNet2.0, *Nature Chemical Biology* 2026

DOI `10.1038/s41589-026-02241-x`. The publisher preview reports a Cartesian tensor Siamese network for relative protein-ligand affinity trained on 8.6 million pairs; zero-shot performance near physical simulation, retrospective optimization 7.18-fold more efficient with 41% fewer resources, and prospective residue identification on ENPP1 and ALDH1B1 with five of six selected residues identified correctly. The author repository contains weights, model code, reproduction code, test data, Zenodo data links, SDF/PDB examples, and an FEP fine-tuning script.

PBCNet2.0 could provide the molecular `Delta a` feature and already occupies same-target relative affinity and pocket-residue sensitivity. The reviewed paper/repository did not show matched cellular `y`, cross-background `D`, cell pharmacology, experimental mismatch modeling, or equal-budget agent selection. Full-text details could not be checked. Publisher and repository point to different Zenodo record IDs (`18299525` and `15656365`), which were not reconciled.

### Robin, *Nature* 2026

DOI `10.1038/s41586-026-10652-y`. Robin combines Crow/Falcon literature and candidate agents with Finch assay-data analysis. Crow forms disease and in-vitro-model reports; an LLM judge ranks candidate mechanisms/models. Robin proposes 30 drugs, Falcon prepares evidence/limitation reports, and human reviewers select and execute human-written protocols. Finch analyzes FCS or RNA-seq counts using eight independent analysis trajectories and consensus, and may propose follow-up assays. The dAMD case includes ARPE-19 screening, RPE-SC validation, ripasudil/KL001 candidates, and Y-27632 RNA-seq/ABCA1 clues. The workflow is lab-in-the-loop, with human experimental execution and validation.

The paper reports about US$10.76 average cost for a configured run, approximately 551 papers analyzed, and task-specific Finch expert rubric scores of 100% for flow and 86% for RNA-seq (n=3 each); performance on 170 BixBench problems was 22.8% +/- 1.7%. These are author-reported results. Robin occupies literature-driven candidate generation, human-run experiments, functional/RNA-seq analysis, multi-trajectory consensus, and feedback-driven follow-up. It does not report same-target A/B affinity input, matched C1/C2 dose/time contrasts, CDI `D`, or equal-budget mechanism-discriminating selection. Candidate and protocol execution include human choices.

## Novelty boundary

Already covered and not novel alone:

1. Protein-ligand relative affinity and pocket-residue sensitivity (PBCNet2.0).
2. Target-organized tasks, few-shot adaptation, unseen-target transfer, and task weighting (AdaMBind).
3. Literature-driven candidate generation, LLM ranking, human experiments, flow/RNA-seq analysis, consensus, and follow-up (Robin).
4. Single functional assay validation of candidates or follow-up transcriptomics (AdaMBind and Robin).

Potentially distinguishable, but only with experiments:

1. A reproducible relation between same-target pair `Delta a` and background-dependent `Delta y/D`.
2. Matched A/B and C1/C2 conditions for cell, dose, time, assay, and replicate.
3. An agent selection rule that discriminates the four competing error sources under a fixed budget, compared with random, affinity-greedy, and single-background baselines.
4. Whole-drug and whole-background generalization without near-duplicate leakage.
5. A frozen affinity source, agent-selected pair, blinded test of `D`, and independent cell/dose/time validation; do not feed post-selection outcomes back into the same rule.

## Unknowns and limits

- PBCNet2.0 is behind a publisher subscription preview; full data splits, ablations, residue-selection details, and replicate counts were not verified. Its two Zenodo IDs remain unresolved.
- AdaMBind results are author-reported benchmarks, virtual screening, and one FLT3 in-vitro case; no rerun or independent causal validation was performed.
- Robin is a dAMD lab-in-the-loop case. Cost/time are estimates, and human choices remain in protocol, cell substitution, and execution. Task-specific Finch results do not establish general bioinformatics reliability.
- The reviewed sources did not reveal one paper reporting the entire CDI combination. This is bounded to the accessible sources above, not an exhaustive claim about all 2026 literature.

## Primary entry points

- AdaMBind: DOI `10.1038/s41467-026-70554-5`; [Nature article](https://www.nature.com/articles/s41467-026-70554-5).
- PBCNet2.0: DOI `10.1038/s41589-026-02241-x`; [Nature preview](https://www.nature.com/articles/s41589-026-02241-x); [author code/data](https://github.com/YuJie-0202/PBCNet2.0); [publisher-linked Zenodo record](https://zenodo.org/records/18299525).
- Robin: DOI `10.1038/s41586-026-10652-y`; [Nature article](https://www.nature.com/articles/s41586-026-10652-y).
