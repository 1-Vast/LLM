# Related work: mono-pretraining for combination ranking (agent A, 2026-10-05)

Scope: literature relevant to `research/astra/mono_pretraining_20261005/` (pretrain a rank-4 drug x cell-context interaction head on public GDSC2 single-drug fitted LN_IC50, fine-tune a combination-residual head on sparse same-tissue combination history, judge by action ranking and confirmed discovery yield). Machine-readable rows: `related_work_matrix.csv` (same IDs). Design consequences: `DESIGN_LESSONS.md`.

## 0. How to read the evidence column

I retrieved most papers as full text through Europe PMC XML or arXiv PDF and read them by targeted section search (abstract, methods on splits and baselines, results, limitations), not line by line. Where that was not possible the level is lower. Nature.com and PMC HTML pages block the fetch tool, so several papers are known only through abstracts or a tool-generated page summary.

| Code | Meaning |
|---|---|
| FT | full text retrieved and read by targeted search |
| FT-skim | full text retrieved, only abstract and a few passages checked |
| PAGE | page fetched and summarised by the fetch tool; I did not read it line by line (numbers copied from that summary) |
| ABS | abstract only |
| SNIP | search-result snippet only |
| BIB | bibliographic record verified (Crossref/Europe PMC); content is background knowledge and is marked as such |

All DOIs/volumes/pages in the CSV were checked against Crossref or Europe PMC records except where the venue string says "not verified". Counts of authors, titles and years are therefore reliable; interpretive statements are mine and are marked as inference where they go beyond the source.

Tiers: A = directly relevant (14), B = supporting (27), C = peripheral/methodological (25). 66 rows in total, more than the 25-45 requested, because many are one-line methodological references; the 14 tier-A rows are the ones to read first.

## 1. Bottom line (one paragraph)

Pretrain-then-fine-tune with single-drug supervision is not new in drug combination modelling (PDSP, MARSY, Kim 2021, RECOVER, TCRP, chemCPA and the perturbation-model work of Ahlmann-Eltze et al. all do a version of it), and nothing I found tests it with the design proposed here: a new cell line, a fixed menu, sparse same-tissue history, a Bliss-residual combination label, a decision-level estimand (confirmed discovery yield under a fixed screen-and-verify budget), and mapping-permuted pretraining as the attribution control. The nearest precedents report gains on pooled regression metrics under transductive splits where mono and combination labels come from the same experiments, and the strongest independent benchmarks (SynVerse, AZ-DREAM, Branson 2025, RECOVER) find that identity-only or drug-average baselines are hard to beat and that feature shuffles change nothing. Evidence that monotherapy information predicts combination efficacy is solid (IDACombo, Vis 2024, Bashi 2024), but evidence that it predicts the Bliss residual that defines the Jaaks Synergy call is thin and partly negative (Menden 2019: no significant gain from monotherapy as a feature; but monotherapy-resistance biomarkers enrich synergy). The contribution is best framed as a rigorous attribution and decision-level test, not as a new method.

## 2. Does anyone already do the proposed thing? (claim-by-claim)

| Claim in the proposal | Closest prior work (ID) | Verdict |
|---|---|---|
| Supervise a drug x cell-context head with single-drug data, then fit a combination head | PDSP [R11], MARSY [R12], Kim 2021 [R10], DrugCell [R17], TCRP [R31] | Done, but with mono labels from the same experiments (MARSY), tiny adaptation sets (PDSP), or different targets. Not new |
| Pretraining on a related public screen improves a low-rank bilinear model for a new cell line | Ahlmann-Eltze 2025 [R22]; chemCPA [R27] | Supported in perturbation transcriptomics; the only consistent winner there was a linear model with a perturbation embedding pretrained on another cell line. Different assay |
| Mapping-permuted/shuffled controls to attribute benefit | SynVerse [R05] (feature shuffling x10, rewiring); RECOVER [R06] (identity-shuffled model) | Standard practice in the better benchmarks; neither shuffles a pretraining stage |
| Same-input scratch control with matched architecture | RECOVER ablations [R06]; Ahlmann-Eltze baselines [R22] | Partly covered |
| Decision-level yield rather than regression error | RECOVER [R06] (enrichment vs random), BATCHIE [R07] (top-20 therapeutic index; used the same GDSC2/Jaaks combination data retrospectively), Kim [R10] (top-20 hit rate), Elmachtoub-Grigas [R59] (theory) | Done for random-baseline enrichment; not done against a strong history-based ranking under a confirm stage |
| New cell line, same menu, sparse same-tissue history | Kim [R10] (data-poor tissues), TCRP [R31] (few-shot), Eckhart [R09] (unseen lines) | Related regimes; none uses an anchored Jaaks menu or Bliss-residual calls |
| Mono pretraining cannot be the whole story because the label is a Bliss residual | Jaaks [R01], MuSyC [R42], Vlot [R43] (label construction); Menden [R04] (mono not helpful as a feature) | Supports expecting a small effect |

## 2b. Narrative by topic

**Context-dependent drug response.** The dominant finding across independent re-analyses is that most reported skill comes from identity and target values, not features. Branson et al. [R32] show that no performance comes from drug features and that drug-average baselines explain much of it, and recommend metrics stratified by drug and by cell line. Eckhart et al. [R09] show that pooled correlations are inflated by drug means (even mean predictors exceed 0.13) and that per-drug correlations are far lower (0.1 for CMax-viability reconstruction on unseen lines). For this project the line-stratified metric is the within-line ranking of the menu, which is exactly where the drug-average analogue (the pair prior from history) is strong. PROGENy [R48] (11 pathways in the original paper; the repo uses 14) associated pathway scores with GDSC IC50 mainly for pathway-targeted drugs (MAPK/EGFR with MAPK-targeting drugs; 178 significant associations among 265 drugs x 805 lines), which predicts that any transfer from a 14-covariate cell state will be concentrated in a minority of drugs.

**Single-to-combination transfer.** IDACombo [R08] shows monotherapy predicts combination efficacy (Spearman 0.93 in-sample ALMANAC; 0.59-0.65 when monotherapy comes from CTRPv2/GDSC, close to the 0.60 cross-assay agreement ceiling), Vis 2024 [R02] that efficacious combination benefit tracks efficacy (r=0.57, still 0.48 without synergistic responses) and tracks PDX response better than synergy, and Bashi 2024 [R03] that 59.5% of combination biomarkers are also monotherapy biomarkers. In contrast the Jaaks label is the Bliss residual. Jaaks [R01] report that synergy sits mostly on weak-to-moderate single-agent activity (anchor-high viability IQR 52-86%), is pair-specific (mostly <3 lines per tissue), and that only 27.5% of synergistic pairs are seen at both anchor concentrations. Menden [R04] found monotherapy added no significant gain as a feature but monotherapy-resistance biomarkers enrich for synergy. Together: mono information should help predict the main effects and headroom; whether it adds anything to the residual beyond tissue-level pair history is an open and probably small effect.

**Foundation and perturbation models and their negative controls.** Ahlmann-Eltze et al. [R22], Csendes et al. [R23], Kernfeld et al. [R24], PertEval-scFM [R25] and Kedzierska et al. [R26] converge: deliberately simple baselines (additive, no-change, training mean, linear low-rank, random forest on GO features) match or beat foundation models, benchmark heterogeneity can make constant predictors look good [R23], and embeddings from big models add nothing inside a linear model [R22]. What did help in [R22] was a perturbation embedding pretrained on a closely matched assay in another cell line, and in chemCPA [R27] pretraining on bulk L1000 helped unseen-drug generalisation modestly. Lesson: task-matched pretraining on measured data is plausible; generic or knowledge-graph embeddings are not; always include the additive/mean null.

**Knowledge-informed representations.** Network proximity [R49] is informative for approved disease combinations at disease level; AZ-DREAM [R04] found drug-target annotation helps beyond identity labels (p=0.012) but identity-only baselines already reached 0.32; SynVerse [R05] found biologically meaningful drug and cell-line features did not drive performance and shuffled features matched real ones. This agrees with the earlier network/target-transfer nulls in this repository.

**Active learning and experimental design under budget.** BATCHIE [R07] and RECOVER [R06] both report decision-level gains over random selection, BATCHIE on three public screens including the Jaaks GDSC2 combination dataset (126 lines, 66 drugs) and prospectively on sarcoma lines; RECOVER notes DeepSynergy is worse than random on novel combinations, that identity-shuffled models are at chance for unseen drugs, and that cross-study batch effects break zero-shot transfer. GeneDisco [R54] warns that acquisition-function rankings depend on metric, dataset, model class and hyperparameters and that label noise and the replicate-versus-new-experiment trade-off are not captured. Random is the wrong comparator for this project; the relevant comparator is a strong history-based ranking, which the earlier campaign already showed hard to beat.

**Sequential decisions with delayed, noisy or failed feedback; calibration; selective prediction; domain shift.** Only the parts that bear on a ranking-and-confirmation campaign are listed: delays add regret to a non-delayed learner [R55], batches can be chosen while results are pending [R57], failed experiments are an unknown constraint, not missing at random [R56], calibration degrades under shift [R61] and is cheaply repaired post hoc for classifiers [R60], selective prediction trades coverage for risk [R62], and weighted/selective conformal methods give finite-sample guarantees for shortlisting under covariate shift when the shift is estimable [R63, R65, R66]. The optimizer's curse [R58] implies selected candidates are over-estimated, which is the opposite sign of the repository's earlier finding (per its memory notes, not re-verified) that forecasts on selected actions were 1.6-2x too low; the likely explanation is shrinkage, so calibration must be assessed on the selected set. See `DESIGN_LESSONS.md` section (d).

**Leakage and generalisation in cell-line and combination benchmarks.** SynVerse [R05] (four splits; the leave-triplet split is the most leakage-prone; leave-drug and leave-cell-line are poor), Sidorov [R18] (random splits overestimate because both drugs recur with other partners; LODO), DeepSynergy [R13] (leave-combination-out but drugs and lines shared), MARSY [R12] (transductive splits), cross-study analyses [R33, R34] (within-study CV optimistic; substantial drop on unseen datasets), RECOVER [R06] and DrugComb [R19] (between-study replicate SD 15.44 vs within-study 4.25 and 12.02), Ben-David [R44] (strain drift: at least 75% of compounds that strongly inhibited some MCF7 strains were inactive in others), and the general taxonomy [R50, R51, R52, R53].

## 3. Tier A sources (directly relevant)

**[R01] Jaaks 2022** - Effective drug combinations in breast, colon and pancreatic cancer cells. Jaaks P, Coker EA, Vis DJ et al.; Nature 603:166-173 (2022); doi:10.1038/s41586-022-04437-2; PMC8891012. Evidence: FT.
- Task / data: Anchored screen: 2,025 two-drug combinations x 125 lines (51 breast, 45 colon, 29 pancreas), 65 drugs, 108,259 combination-line pairs; synergy and biomarkers. Anchor drug at two fixed concentrations (<=10 uM, chosen for 50-90% viability) x library drug at 7 concentrations over 1,000-fold; 2-18 biological replicates per line.
- Evaluation split / baselines: Primary vs validation datasets: r=0.69-0.84, synergy-call F-score 0.62-0.70; replicates r>0.6; 3,106 plates, >70% passed QC. Baselines: Bliss expectation; synergy = combination IC50 reduced >=8-fold or Emax >=20% viability below Bliss.
- Useful idea: Synergy rare (5.2% of pairs) and pair-specific (mostly <3 lines per tissue; 7.8% of combination-tissue pairs synergistic in >=20% of lines); synergy mostly sits on weak-to-moderate single-agent activity (IQR viability 52-86% anchor-high, 69-92% anchor-low, 53-80% library); only 27.5% of synergistic pairs seen at both anchor concentrations (label is anchor-dose specific); 76.8% of combination biomarkers tied to only one of dIC50/dEmax; combination biomarkers often not explained by single-agent activity.
- Limits / leakage risks: Label is a residual from Bliss computed from monotherapy measured in the same experiment (coupled noise); dose-specific; the dataset is exposed (adaptively used) in this repository.
- Already addresses the proposed contribution? No (data source). Defines the headroom that any mono-transfer must exploit.

**[R02] Vis 2024** - A pan-cancer screen identifies drug combination benefit in cancer cell lines at the individual and population level. Vis DJ, Jaaks P, Aben N et al.; Cell Rep Med 5(8):101687 (2024); doi:10.1016/j.xcrm.2024.101687; PMC11384948. Evidence: FT.
- Task / data: 757 lines (21 tissues) x 51 two-drug combinations (29 drugs), anchored design, NLME curve fits; defines efficacious combination benefit (ECB) = synergy, Bliss additivity or independent drug action (IDA). 4.5 M measurements; 49 of 51 combinations overlap Jaaks 2022, 46 with identical anchor concentrations (same platform).
- Evaluation split / baselines: Vs Jaaks (breast/colon/pancreas): synergy-frequency Spearman 0.81/0.89/0.90, ECB-rate 0.89/0.80/0.90; PDX comparison on 7 shared combinations. Baselines: Bliss, highest single agent (HSA), IDA.
- Useful idea: ECB frequency correlates with overall efficacy (r=0.57; 0.48 after removing synergistic responses); ECB, not synergy alone, tracks PDX hazard ratios (p=0.0011 vs 0.19); 12% of responses synergy, 31% Bliss, 54% HSA.
- Limits / leakage risks: Same lab/platform as Jaaks, so not independent in the platform sense; whether its lines overlap the Jaaks 125 was not checked by me; repo notes cite 730 lines / 19 combinations for a 'qualified' subset, which I could not reconcile with 757 / 51 / 49-overlap in the paper.
- Already addresses the proposed contribution? No. Evidence that efficacy (mono-driven) and synergy are different endpoints.

**[R04] Menden 2019 (AZ-DREAM)** - Community assessment to advance computational prediction of cancer drug combinations in a pharmacogenomic screen. Menden MP, Wang D, Mason MJ et al.(AZ-Sanger DREAM Consortium); Nat Commun 10:2674 (2019); doi:10.1038/s41467-019-09799-2; PMC6572829. Evidence: FT.
- Task / data: 11,576 experiments, 910 combinations, 85 lines; SC1 predict synergy for combinations with training data; SC2 binary synergy for unseen combinations. Baseline mutation/CNV/expression/methylation, drug targets; 160 teams.
- Evaluation split / baselines: Held-out experiments (SC1) and held-out combinations (SC2); external O'Neil and NCI-ALMANAC. Baselines: Label-only baseline (NAD: drug and cell-line identity only) reached weighted Pearson 0.32; mean team r=0.24; winner 0.48 (SC1A).
- Useful idea: Identity-only baseline is hard to beat; drug-target annotation is the one feature type that beat identity labels (p=0.012); accuracy matches replicates for >60% of combinations but ~20% poorly predicted by all; post-hoc, monotherapy as a feature gave no significant gain to good models, yet monotherapy-resistance biomarkers enrich synergy (cell lines and PDX).
- Limits / leakage risks: Mono-feature analysis was incomplete (annotation error); pooled weighted Pearson, not within-line action ranking; weak transfer to ALMANAC.
- Already addresses the proposed contribution? Partly. Closest evidence on whether monotherapy information helps synergy models: little as a direct feature.

**[R05] SynVerse 2025** - SynVerse: a modular framework for building and evaluating deep learning-based drug synergy prediction models. Tasnina N, Haghani H, Murali TM; Brief Bioinform 26(6):bbaf676 (2025); doi:10.1093/bib/bbaf676; PMC12753315. Evidence: FT.
- Task / data: 16 synergy models (8 drug/cell-line feature sets, 5 preprocessors, 2 encoders) on DrugComb (S-mean). DrugComb triplets; four splits: leave-triplet, leave-drug-pair, leave-drug, leave-cell-line.
- Evaluation split / baselines: Leave drug pair: PCC 0.78-0.94; leave drug and leave cell line: 'poor'; leave-triplet reported as most leakage-prone. Baselines: One-hot drug + one-hot cell-line MLP (DeepSynergy architecture): no model significantly beat it; shuffled drug/cell-line features performed the same as real ones (10 shuffles per set); network-rewiring ablation shows reliance on per-drug synergy strength shortcuts.
- Useful idea: Template for negative controls (identity features, feature shuffling x10, strength-preserving rewiring) and for stating which split is claimed; random splits let the same drug pair, drugs and cell lines recur.
- Limits / leakage risks: DrugComb S-score mixes many studies and protocols; pooled metrics; no sequential-decision endpoint.
- Already addresses the proposed contribution? Refutes much of 'knowledge features help' for the synergy-regression task; directly motivates mapping-permuted controls.

**[R06] RECOVER 2023** - RECOVER identifies synergistic drug combinations in vitro through sequential model optimization. Bertin P, Rector-Brooks J, Sharma D et al.; Cell Rep Methods 3:100599 (2023); read arXiv:2202.04202v3; doi:10.1016/j.crmeth.2023.100599; arXiv:2202.04202. Evidence: FT (arXiv version; published version not read).
- Task / data: Sequential model optimisation to find synergistic pairs in MCF7, pretrained on public combination data (O'Neil, NCI-ALMANAC) then fine-tuned by rounds. NCI-ALMANAC for in-silico backtests; prospective wet-lab 6x6 matrices on MCF7 (about 5% of search space), 3 rounds + 2 reproducibility rounds.
- Evaluation split / baselines: Tasks: seen/one-unseen/two-unseen drugs; study-transfer (O'Neil to ALMANAC); sequential backtest. Baselines: Random selection; DeepSynergy; SVM; boosted trees; RECOVER with shuffled drug/cell identities.
- Useful idea: Decision-level metric (enrichment of highly synergistic pairs vs random): 5-10x with sequential rounds, >3x for one-shot pretrained selection; DeepSynergy was worse than random on novel combinations; shuffled-identity model fails with one unseen drug and is at chance with two; severe cross-study batch effects (O'Neil vs ALMANAC) break zero-shot transfer but pretrain+fine-tune still helps; advises that at least one drug of a pair be seen.
- Limits / leakage risks: Single cell line; pretraining is on combination data, not monotherapy; synergy score (not Bliss-residual calls with confirmation); small prospective n.
- Already addresses the proposed contribution? Closest precedent for pretrain/fine-tune evaluated on selection enrichment with an identity-shuffle control. Not new-cell-line, not mono pretraining.

**[R07] BATCHIE 2025** - A Bayesian active learning platform for scalable combination drug screens. Tosh C, Tec M, White JB, Quinn JF et al.; Nat Commun 16:156 (2025); doi:10.1038/s41467-024-55287-7; PMC11696745. Evidence: FT.
- Task / data: Batch active design (PDBAL criterion) for dose-level viability models; retrospective on NCI-ALMANAC, GDSC2 combination screen (Jaaks: 126 lines, 66 drugs) and Merck; prospective Ewing/pediatric sarcoma screen. 15 rounds observe 1.7-20.4% of data; prospective ~54 K measurements, 4% of 1.4 M possible experiments.
- Evaluation split / baselines: Random holdout plates; top-20 therapeutic-index (TI) hits; prospective random unseen plates (rho=0.91) and 10/10 validated top combinations. Baselines: Random acquisition; EIG; posterior-variance acquisition.
- Useful idea: Evaluates discovery (average TI at top-20, top-hit AUC) not only R2; models within 5-7% of full-data R2 after 15 batches; synergy-only variant given all single-drug data up front; 13 of 3,465 random combinations had Bliss>0.25.
- Limits / leakage risks: No external mono pretraining described in the sections read; TI and viability endpoints differ from author Synergy confirmation; retrospective Jaaks use means the dataset is already exploited by others.
- Already addresses the proposed contribution? Not the pretraining question. Shows (a) the same dataset was used for retrospective design studies, (b) decision-level metrics are accepted practice.

**[R08] IDACombo 2020** - Computationally predicting clinical drug combination efficacy with cancer cell line screens and independent drug action. Ling A, Huang RS; Nat Commun 11:5848 (2020); doi:10.1038/s41467-020-19563-6; PMC7673995. Evidence: FT.
- Task / data: Predict combination viability/efficacy from monotherapy screens under independent drug action (IDA), no synergy term. NCI-ALMANAC (in-sample), CTRPv2 and GDSC monotherapy; 54 clinical trials.
- Evaluation split / baselines: Cross-dataset: CTRPv2/GDSC monotherapy to ALMANAC combinations. Baselines: Bliss independence (worse for clinical prediction).
- Useful idea: Monotherapy alone predicts combination efficacy: Pearson 0.932/Spearman 0.929 in ALMANAC in-sample; 0.59 (CTRPv2) and 0.65 (GDSC) cross-dataset, near the ceiling imposed by cross-assay agreement (0.60); 84.6% trial-power classification.
- Limits / leakage risks: Predicts efficacy (average viability), not Bliss-residual synergy; cross-dataset ceiling is itself only ~0.6.
- Already addresses the proposed contribution? Gives the positive control: mono information should predict combination efficacy, not necessarily synergy.

**[R09] Eckhart 2025** - How to predict effective drug combinations - moving beyond synergy scores. Eckhart L, Lenhof K, Herrmann L, Rolli L-M, Lenhof H-P; iScience 28(6):112622 (2025); doi:10.1016/j.isci.2025.112622; PMC12152377. Evidence: FT.
- Task / data: Dose-specific relative-inhibition prediction for unseen cell lines (mono and combination), reconstructing sensitivity and prioritisation. Drug-combination panel (DrugComb-style) with disjoint cell lines in train and test; MACCS or physico-chemical features.
- Evaluation split / baselines: Cell-line-disjoint; per-drug and per-combination correlations reported. Baselines: Training-mean (MAE 24.2) and per-drug/per-combination mean (19.74).
- Useful idea: Pooled correlation is inflated by drug/combination means (even mean predictors score >0.13); within-drug PCC 0.58 (mono) and 0.56 (per combination); for CMax-viability reconstruction overall PCC 0.58 but per-drug 0.1; argues synergy scores are poor treatment-prioritisation targets.
- Limits / leakage risks: Not Jaaks; different endpoint.
- Already addresses the proposed contribution? Supports evaluating within-line/within-drug ranking and strong mean baselines.

**[R10] Kim 2021** - Anticancer drug synergy prediction in understudied tissues using transfer learning. Kim Y, Zheng S, Tang J, Zheng WJ, Li Z, Jiang X; J Am Med Inform Assoc 28(1):42-51 (2021); doi:10.1093/jamia/ocaa212; PMC7810460. Evidence: PAGE + ABS.
- Task / data: Multi-task DNN (synergy + monotherapy sensitivity) pretrained on data-rich tissues, transferred to data-poor tissues (bone, prostate). DrugComb: 4,150 drugs, 112 lines, ~710 K monotherapy and ~466 K combination records.
- Evaluation split / baselines: Cell lines disjoint between tissues (drugs overlap); external validation on separate databases. Baselines: DeepSynergy; XGBoost (ALMANAC); no-transfer model.
- Useful idea: Transfer raised AUROC bone 0.665 to 0.802 and prostate 0.651 to 0.854; top-20 hit rates 25% (bone), 100% (prostate); authors admit weak external accuracy because of protocol heterogeneity.
- Limits / leakage risks: Tiny data-poor sets; AUROC, not within-line action ranking; Bliss-residual not isolated; numbers come from the fetch summary.
- Already addresses the proposed contribution? Partly (transfer to data-poor context with mono tasks), but not mono-only pretraining nor controls.

**[R11] PDSP 2024** - From cell lines to cancer patients: personalized drug synergy prediction. Kuru HI, Cicek AE, Tastan O; Bioinformatics 40(5):btae134 (2024); doi:10.1093/bioinformatics/btae134; PMC11215552. Evidence: PAGE (full text retrieved, not read in full).
- Task / data: Pretrain synergy model with drug-response nodes on cell lines, fine-tune with patient single-drug sensitivity. DrugComb 330,103 combinations, 3,068 drugs, 81 lines; 3 leukemia patients (654 sensitivities, 20 synergies).
- Evaluation split / baselines: Leave-drug-combination-out 60/20/20 on cell lines. Baselines: MatchMaker, DeepSynergy, TreeCombo, DeepDDS, RF.
- Useful idea: Explicit single-to-combination fine-tuning path; per-patient fine-tuning 70% vs 40% accuracy.
- Limits / leakage risks: Three patients; leave-combination split shares drugs and cell lines; no negative-control pretraining.
- Already addresses the proposed contribution? Partly: same idea (mono-response supervision then adaptation) in a different regime.

**[R22] Ahlmann-Eltze 2025** - Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines. Ahlmann-Eltze C, Huber W, Anders S; Nat Methods 22:1657-1661 (2025); doi:10.1038/s41592-025-02772-6; PMC12328236. Evidence: FT.
- Task / data: Double-perturbation (Norman) and unseen single-perturbation (Replogle K562/RPE1, Adamson) expression prediction. scGPT, scFoundation, GEARS, CPA, Geneformer, scBERT, UCE vs baselines.
- Evaluation split / baselines: Fine-tune on all singles + half of doubles (5 random partitions); two splits for unseen singles. Baselines: 'No change', 'additive', training-mean, and a bilinear linear model G W P^T (PCA gene factors, ridge).
- Useful idea: No deep model beat additive/no-change/mean; embeddings from foundation models gave no gain inside the linear model; the only consistent winner was the linear model whose perturbation embedding P was pretrained on the other cell line (Replogle K562 to RPE1/Adamson): pretraining helps when the pretraining task matches the target measurement.
- Limits / leakage risks: Gene-perturbation transcriptomics, not viability or synergy; one benchmark family.
- Already addresses the proposed contribution? Supports the logic of task-matched pretraining of a low-rank bilinear head and of using an additive/mean null; does not test synergy.

**[R32] Branson 2025** - Understanding the sources of performance in deep drug response models reveals insights and improvements. Branson N, Cutillas PR, Bessant C; Bioinformatics 41(Suppl 1):i142-i149 (2025); doi:10.1093/bioinformatics/btaf255; PMC12261491. Evidence: FT.
- Task / data: Ablate published drug-response models (tCNNS, DeepTTA, GraphDRP) under mixed-set, cancer-blind and drug-blind testing. Public cell-line screens.
- Evaluation split / baselines: Mixed-set / cancer-blind / drug-blind; metrics stratified by drug and by cell line. Baselines: Drug-average, cell-line-average, identity (marker) baselines.
- Useful idea: No performance came from drug features; performance came from transcriptomics, and much of reported performance is a property of the training target values (drug-average baseline).
- Limits / leakage risks: Monotherapy response, continuous and binary.
- Already addresses the proposed contribution? Supports strong simple baselines and line-stratified evaluation.

**[R38] Vis 2016 (NLME)** - Multilevel models improve precision and speed of IC50 estimates. Vis DJ, Bombardelli L, Lightfoot H, Iorio F, Garnett MJ, Wessels LFA; Pharmacogenomics 17(7):691-700 (2016); doi:10.2217/pgs.16.15; PMC6455999. Evidence: PAGE.
- Task / data: Non-linear mixed-effects (NLME) fit of IC50 with cell-line-level slope and shared information across lines and drugs; applied to 79,903 GDSC series (707 lines, 145 drugs). GDSC.
- Evaluation split / baselines: Compared with an earlier Bayesian fit (median r=0.91). Baselines: Bayesian per-curve fit.
- Useful idea: Fitted IC50s are shrunk, jointly estimated quantities (borrowing across lines and drugs), with lower CV and ~100x speed.
- Limits / leakage risks: Whether GDSC2 release 8.5 NLME_* columns used this exact model is inferred from the column names and Vis 2024 methods, not verified here.
- Already addresses the proposed contribution? Relevant to 'fitted-label independence' in the S0 contract.

**[R48] PROGENy 2018** - Perturbation-response genes reveal signaling footprints in cancer gene expression. Schubert M, Klinger B, Klunemann M et al.; Nat Commun 9:20 (2018); doi:10.1038/s41467-017-02391-6; PMC5750219. Evidence: FT.
- Task / data: Pathway activity from perturbation-response footprints (11 pathways in this paper); association with GDSC IC50. 208 perturbation experiments; GDSC 265 drugs x 805 lines.
- Evaluation split / baselines: Leave-one-out for the footprint models. Baselines: Other pathway tools (GSEA etc.).
- Useful idea: 178 significant PROGENy-IC50 associations at 10% FDR, dominated by MAPK/EGFR activity vs MAPK-targeting drugs (oncogene addiction): pathway covariates carry drug-class-specific, not global, information.
- Limits / leakage risks: The repo uses 14 pathways; the 14-pathway version is a later extension that I did not verify; scores are RNA-inferred, not measured activity.
- Already addresses the proposed contribution? Sets expectations: transfer concentrated in a minority of pathway-targeted drugs.

## 4. Tier B sources (supporting)

**[R03] Bashi 2024** - Large-scale Pan-cancer Cell Line Screening Identifies Actionable and Effective Drug Combinations. Bashi AC, Coker EA, Bulusu KC et al.(37 authors); Cancer Discov 14:846-865 (2024); doi:10.1158/2159-8290.CD-23-0388; PMC11061612. Evidence: PAGE (full text retrieved, skimmed).
- Task / data: 755 lines x 109 combinations (37 AstraZeneca compounds), Bliss excess and HSA excess; biomarker discovery. ~68,000 combination:line pairs; 7 lines in technical triplicate on 6 occasions as QC.
- Evaluation split / baselines: No predictive model; association statistics only (5.4 M tests). Baselines: HSA vs Bliss.
- Useful idea: 59.5% (6,911/11,611) of combination biomarkers are also biomarkers of >=1 constituent monotherapy; 'emergent' biomarkers only ~14%; Bliss excess correlates with HSA excess r=0.924; Emax poorly tracks synergy (activity is often single-agent driven).
- Limits / leakage risks: Biomarkers are of combination response, not necessarily of the Bliss residual; AZ-portfolio drugs.
- Already addresses the proposed contribution? No. Supports 'single-agent biology explains much of combination response', less so the residual.

**[R12] MARSY 2023** - MARSY: a multitask deep-learning framework for prediction of drug combination synergy scores. El Khili MR, Memon SA, Emad A; Bioinformatics 39(4):btad177 (2023); doi:10.1093/bioinformatics/btad177; PMC10359108. Evidence: FT.
- Task / data: DrugComb ZIP and S-mean synergy with auxiliary single-drug relative-inhibition outputs; CCLE expression, LINCS signatures. DrugComb triples with LINCS signature and CCLE expression.
- Evaluation split / baselines: 5-fold leave-triple-out and leave-pair-out (transductive: cell lines and drugs shared). Baselines: LASSO, ElasticNet, SVM, RF, MLP, DeepSynergy, TreeCombo, others.
- Useful idea: Multitask head vs single-task: +6.1% (leave-triple) / +5.1% (leave-pair) Spearman; PCC 0.886/0.875 pooled.
- Limits / leakage risks: Mono labels come from the same experimental blocks as synergy (coupled); pooled metrics; transductive.
- Already addresses the proposed contribution? Evidence that mono supervision helps within DrugComb, with the above leakage caveats.

**[R13] DeepSynergy 2018** - DeepSynergy: predicting anti-cancer drug synergy with Deep Learning. Preuer K, Lewis RPI, Hochreiter S, Bender A, Bulusu KC, Klambauer G; Bioinformatics 34(9):1538-1546 (2018); doi:10.1093/bioinformatics/btx806; PMC5925774. Evidence: FT.
- Task / data: Regression of Loewe synergy for 583 combinations x 39 lines (38 drugs; Merck screen), chemical + expression inputs. Merck O'Neil screen.
- Evaluation split / baselines: Stratified nested CV leaving out drug combinations (drugs and cell lines still shared); grid-search hyperparameters inside. Baselines: Median polish (drug and cell-line medians), elastic net, SVM, RF, GBM.
- Useful idea: 7.2% MSE gain vs second-best; explicit median-polish baseline; nested CV.
- Limits / leakage risks: Authors state they are not aiming at novel drugs; later work (RECOVER, SynVerse) finds it at or below random/one-hot for new combinations.
- Already addresses the proposed contribution? No.

**[R16] comboFM 2020** - Leveraging multi-way interactions for systematic prediction of pre-clinical drug combination effects. Julkunen H, Cichonska A, Gautam P et al.; Nat Commun 11:6136 (2020); doi:10.1038/s41467-020-19950-z; PMC7708835. Evidence: FT.
- Task / data: Factorization-machine prediction of dose-response matrices (new entries, new matrices, new combinations). Random 50-drug subset of NCI-ALMANAC (60 lines); 16 in-house validation triplets.
- Evaluation split / baselines: 10x5 nested CV with scenario-specific folds. Baselines: Random forest; lower-order FMs.
- Useful idea: Low-rank multi-way (rank 25-100) interaction structure; shows predictive accuracy depends on which components train and test share; assumes monotherapy known.
- Limits / leakage risks: Monotherapy of test combination assumed available; subset sampling.
- Already addresses the proposed contribution? Partly (low-rank structure) but with monotherapy given.

**[R17] DrugCell 2020** - Predicting Drug Response and Synergy Using a Deep Learning Model of Human Cancer Cells. Kuenzi BM, Park J, Fong SH et al.; Cancer Cell 38(5):672-684 (2020); doi:10.1016/j.ccell.2020.09.014; PMC7737474. Evidence: PAGE.
- Task / data: Interpretable visible NN trained on mutations (CTRP+GDSC, 509,294 pairs, 684 drugs, 1,235 lines); combinations nominated by pathway logic. CTRPv2 + GDSC monotherapy.
- Evaluation split / baselines: Five-fold CV; synergy check on DeepSynergy data (583 combos, 39 lines). Baselines: Elastic net.
- Useful idea: Monotherapy model repurposed for synergy by subsystem logic; nominated pairs enriched for synergy (per fetch summary: no fine-tuning on synergy).
- Limits / leakage risks: Summary-level reading only; mutation-only inputs.
- Already addresses the proposed contribution? Partly (mono model informing combination choice).

**[R18] Sidorov 2019** - Predicting Synergism of Cancer Drug Combinations Using NCI-ALMANAC Data. Sidorov P, Naulaerts S, Ariey-Bonnet J, Pasquier E, Ballester PJ; Front Chem 7:509 (2019); doi:10.3389/fchem.2019.00509; PMC6646421. Evidence: FT.
- Task / data: Per-cell-line RF/XGBoost for ComboScore from structure. NCI-ALMANAC, 60 lines.
- Evaluation split / baselines: Random 90/10 vs leave-one-drug-out (LODO). Baselines: Cell-line models; tree-SD reliability.
- Useful idea: Authors note random splits overestimate performance because both drugs appear in train with other partners; median Rp 0.641 (90/10) vs LODO: Rp>=0.3 for 75% and >=0.5 for 50% of left-out drugs.
- Limits / leakage risks: One dataset, structure features only.
- Already addresses the proposed contribution? No.

**[R19] DrugComb 2019** - DrugComb: an integrative cancer drug combination data portal. Zagidullin B, Aldahdooh J, Zheng S et al.; Nucleic Acids Res 47(W1):W43-W51 (2019); doi:10.1093/nar/gkz337; PMC6602441. Evidence: FT.
- Task / data: Harmonised combination screening data (2,276 drugs, 437,932 combinations, 93 lines in this release). O'Neil, ALMANAC, others.
- Evaluation split / baselines: Reproducibility: replicate SD of CSS. Baselines: Additive model for CSS prediction.
- Useful idea: Within-study replicate SD 4.25 (O'Neil) and 12.02 (ALMANAC) vs between-study SD 15.44 (604 replicated pairs); batch effects flagged.
- Limits / leakage risks: Replicates there use different concentrations; synergy scores are method-dependent.
- Already addresses the proposed contribution? No (label-noise ceiling).

**[R20] NCI-ALMANAC 2017** - The National Cancer Institute ALMANAC: A Comprehensive Screening Resource for the Detection of Anticancer Drug Pairs with Enhanced Therapeutic Activity. Holbeck SL, Camalier R, Crowell JA et al.; Cancer Res 77(13):3564-3576 (2017); doi:10.1158/0008-5472.CAN-17-0489; PMC5499996. Evidence: PAGE.
- Task / data: 5,232 drug pairs (104 approved drugs) x NCI-60, ComboScore. 304,549 experiments.
- Evaluation split / baselines: Xenograft follow-up (48% of novel pairs better than single agents). Baselines: Single-agent responses.
- Useful idea: Most combinations active in 11-30 of 60 lines; sensitivity largely independent of histology except leukemia.
- Limits / leakage risks: Different assay (SRB growth), cell lines, concentrations; ComboScore not Bliss-call.
- Already addresses the proposed contribution? No.

**[R23] Csendes 2025** - Benchmarking foundation cell models for post-perturbation RNA-seq prediction. Csendes G, Sanz G, Szalay KZ, Szalai B; BMC Genomics 26:393 (2025); doi:10.1186/s12864-025-11600-2; PMC12016270. Evidence: FT.
- Task / data: scGPT and scFoundation vs Train-Mean, RF with GO features, ElasticNet, kNN on four Perturb-seq datasets. Adamson, Norman, Replogle K562/RPE1.
- Evaluation split / baselines: Held-out perturbations. Baselines: Train Mean.
- Useful idea: Train Mean beat both foundation models in differential-expression space; RF with GO features beat them by a large margin; low heterogeneity between perturbations (and raw-space Pearson >0.95) makes benchmarks easy for constant predictors.
- Limits / leakage risks: Same domain caveat.
- Already addresses the proposed contribution? Control design: always include the constant/mean predictor and check dataset heterogeneity.

**[R27] chemCPA 2022** - Predicting Cellular Responses to Novel Drug Perturbations at a Single-Cell Resolution. Hetzel L, Boehm S, Kilbertus N, Guennemann S, Lotfollahi M, Theis F; NeurIPS 35:26711-26722 (2022); doi:10.52202/068431-1937; arXiv:2204.13545. Evidence: FT.
- Task / data: Encoder-decoder with drug embeddings for unseen drugs in single-cell (sci-Plex); pretraining on bulk L1000 (LINCS). sci-Plex + LINCS L1000.
- Evaluation split / baselines: Unseen drug-covariate combinations at 1 and 10 uM. Baselines: Baseline, scGen, CPA, chemCPA from scratch.
- Useful idea: Transfer from existing bulk HTS improves unseen-drug generalisation (1 uM: E[r2] on DEGs 0.60 to 0.68 with pretraining; baseline 0.51).
- Limits / leakage risks: Baseline definition not read; single-cell with dose-specific unseen combos; no permutation control for pretraining.
- Already addresses the proposed contribution? Partly (pretraining on a cheaper related assay improves held-out drugs).

**[R31] TCRP 2021** - Few-shot learning creates predictive models of drug response that translate from high-throughput screens to individual patients. Ma J, Fong SH, Luo Y et al.; Nat Cancer 2:233-244 (2021); doi:10.1038/s43018-020-00169-2; PMC8248912. Evidence: PAGE.
- Task / data: Pretrain on cell-line screens (GDSC1000 1,001 lines; DepMap), few-shot adapt (k=0-10) in a new tissue/PDTC/PDX. GDSC, DepMap.
- Evaluation split / baselines: Nested CV; few-shot sample selection repeated 20 times. Baselines: RF, NN, kNN, linear.
- Useful idea: Pretrain-then-adapt with 5-10 samples helps (PDTC r=0.35 at 10 shots vs <0.10 baselines); gains saturate quickly.
- Limits / leakage risks: Summary-level reading; tissue-transfer setting.
- Already addresses the proposed contribution? Partly (sparse same-context adaptation after pretraining).

**[R33] Xia 2022** - A cross-study analysis of drug response prediction in cancer cell lines. Xia F, Allen J, Balaprakash P et al.; Brief Bioinform 23(1):bbab356 (2022); doi:10.1093/bib/bbab356; PMC8769697. Evidence: ABS.
- Task / data: Cross-study DRP across NCI-60, CTRP, GDSC, CCLE, gCSI. -.
- Evaluation split / baselines: Cross-study. Baselines: Multiple ML.
- Useful idea: Within-study CV is optimistic; assay differences limit transfer; drug diversity matters more than line count (abstract).
- Limits / leakage risks: Abstract only.
- Already addresses the proposed contribution? No.

**[R34] Partin 2026** - Benchmarking community drug response prediction models: datasets, models, tools, and metrics for cross-dataset generalization analysis. Partin A, Vasanthakumari P, Narykov O et al.; Brief Bioinform 27(1):bbaf667 (2026); doi:10.1093/bib/bbaf667; PMC12794626. Evidence: FT-skim.
- Task / data: Seven DRP models x five screens (CCLE, CTRPv2, gCSI, GDSCv1, GDSCv2). -.
- Evaluation split / baselines: Source-target matrix, 10 splits per source. Baselines: LightGBM.
- Useful idea: Substantial drop on unseen datasets; no model wins everywhere; CTRPv2 best source.
- Limits / leakage risks: Mono responses.
- Already addresses the proposed contribution? Quantifies assay-shift risk for GDSC2-to-Jaaks transfer.

**[R39] Palmer & Sorger 2017** - Combination Cancer Therapy Can Confer Benefit via Patient-to-Patient Variability without Drug Additivity or Synergy. Palmer AC, Sorger PK; Cell 171(7):1678-1691 (2017); doi:10.1016/j.cell.2017.11.009; PMC5741091. Evidence: ABS (search-result abstract).
- Task / data: Model of independent drug action with patient variability. Clinical trials, PDX.
- Evaluation split / baselines: -. Baselines: Additivity/synergy models.
- Useful idea: Patient/line variability plus independent action explains many approved combinations without interaction.
- Limits / leakage risks: Full text not read.
- Already addresses the proposed contribution? No.

**[R40] Plana 2022** - Independent Drug Action in Combination Therapy: Implications for Precision Oncology. Plana D, Palmer AC, Sorger PK; Cancer Discov 12(3):606-624 (2022); doi:10.1158/2159-8290.CD-21-0212; PMC8904281. Evidence: FT-skim.
- Task / data: Review of independent action, additivity and synergy. -.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: Defines Bliss (efficacy), Loewe (potency) and Frei independence; argues design by single-agent activity in the target population.
- Limits / leakage risks: Review; clinical emphasis.
- Already addresses the proposed contribution? No.

**[R42] MuSyC 2019** - Quantifying Drug Combination Synergy along Potency and Efficacy Axes. Meyer CT, Wooten DJ, Paudel BB et al.; Cell Syst 8(2):97-108 (2019); doi:10.1016/j.cels.2019.01.003; PMC6675406. Evidence: PAGE.
- Task / data: Two-axis (potency alpha, efficacy beta) synergy formalism. -.
- Evaluation split / baselines: -. Baselines: Bliss, Loewe, HSA, ZIP, CI.
- Useful idea: Existing metrics conflate potency and efficacy and correlate with single-drug parameters (e.g. Loewe vs Hill slope); Loewe undefined beyond the weaker drug's maximal effect.
- Limits / leakage risks: Per fetch summary.
- Already addresses the proposed contribution? No.

**[R44] Ben-David 2018** - Genetic and transcriptional evolution alters cancer cell line drug response. Ben-David U, Siranosian B, Ha G et al.; Nature 560:325-330 (2018); doi:10.1038/s41586-018-0409-3; PMC6522222. Evidence: ABS (full text retrieved).
- Task / data: Strain-level variation across 106 lines and 27 MCF7 strains; drug response of strains. 321 compounds on 27 MCF7 strains.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: At least 75% of compounds strongly inhibiting some MCF7 strains were inactive in others.
- Limits / leakage risks: Abstract-level reading.
- Already addresses the proposed contribution? No (identity/batch risk when matching GDSC2 and Jaaks lines).

**[R50] Kapoor & Narayanan 2023** - Leakage and the reproducibility crisis in machine-learning-based science. Kapoor S, Narayanan A; Patterns 4(9):100804 (2023); doi:10.1016/j.patter.2023.100804; PMC10499856. Evidence: FT-skim.
- Task / data: Survey of leakage across 17 fields (294 papers); taxonomy of eight leakage types; model info sheets. -.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: Checklist to justify absence of leakage (preprocessing on train+test, duplicates, non-independence, test used in model selection).
- Limits / leakage risks: General ML.
- Already addresses the proposed contribution? No.

**[R51] Cawley & Talbot 2010** - On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. Cawley GC, Talbot NLC; J Mach Learn Res 11:2079-2107 (2010); https://www.jmlr.org/papers/v11/cawley10a.html. Evidence: SNIP.
- Task / data: Over-fitting of the selection criterion. -.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: Selection-induced bias is often comparable to differences between learners (from the search-result summary).
- Limits / leakage risks: Not opened.
- Already addresses the proposed contribution? No.

**[R54] GeneDisco 2021** - GeneDisco: A Benchmark for Experimental Design in Drug Discovery. Mehrjou A, Soleymani A, Jesson A, Notin P, Gal Y, Bauer S, Schwab P; arXiv:2110.11875 (ICLR 2022); arXiv:2110.11875. Evidence: FT.
- Task / data: Batch active learning for genetic interventions (hit ratio, MSE) on 4 CRISPR datasets. 9 acquisition functions, 6 batch sizes, 5 seeds.
- Evaluation split / baselines: -. Baselines: Random acquisition.
- Useful idea: Acquisition-function ranking depends on metric, dataset, model class and hyperparameters; label noise and the replicate-versus-new-experiment budget trade-off are not captured.
- Limits / leakage risks: Genetic screens.
- Already addresses the proposed contribution? No (caution against over-claiming scheduler gains).

**[R58] Smith & Winkler 2006** - The Optimizer's Curse: Skepticism and Postdecision Surprise in Decision Analysis. Smith JE, Winkler RL; Management Science 52(3):311-322 (2006); doi:10.1287/mnsc.1050.0451. Evidence: BIB.
- Task / data: Selecting the best of noisy estimates. -.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: Selected options' estimated value is biased upward (background knowledge); bias grows with candidates and noise.
- Limits / leakage risks: Not read.
- Already addresses the proposed contribution? No.

**[R59] Elmachtoub & Grigas 2022** - Smart 'Predict, then Optimize'. Elmachtoub AN, Grigas P; Management Science 68(1):9-26 (2022); doi:10.1287/mnsc.2020.3922; arXiv:1710.08005. Evidence: FT-skim.
- Task / data: Train prediction models with the downstream decision loss. -.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: Squared prediction error can be a poor proxy for decision quality.
- Limits / leakage risks: Linear-objective settings.
- Already addresses the proposed contribution? Supports decision-level estimands.

**[R60] Guo 2017** - On Calibration of Modern Neural Networks. Guo C, Pleiss G, Sun Y, Weinberger KQ; ICML 2017 (arXiv:1706.04599); arXiv:1706.04599. Evidence: FT-skim.
- Task / data: Calibration of deep classifiers. -.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: Modern nets are miscalibrated; temperature scaling is a cheap, effective post-hoc fix.
- Limits / leakage risks: Image/text classifiers.
- Already addresses the proposed contribution? No.

**[R61] Ovadia 2019** - Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift. Ovadia Y, Fertig E, Ren J et al.; NeurIPS 2019 (arXiv:1906.02530); arXiv:1906.02530. Evidence: FT-skim.
- Task / data: Benchmark of uncertainty methods under dataset shift. -.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: Uncertainty quality degrades under shift for all methods (abstract-level reading).
- Limits / leakage risks: Vision/text.
- Already addresses the proposed contribution? No.

**[R62] Geifman & El-Yaniv 2017** - Selective Classification for Deep Neural Networks. Geifman Y, El-Yaniv R; NeurIPS 2017 (arXiv:1705.08500); arXiv:1705.08500. Evidence: FT-skim.
- Task / data: Reject option with a user-set risk. -.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: Risk-coverage trade-off with guaranteed risk level.
- Limits / leakage risks: Classification.
- Already addresses the proposed contribution? No.

**[R63] Tibshirani 2019** - Conformal Prediction Under Covariate Shift. Tibshirani RJ, Barber RF, Candes EJ, Ramdas A; NeurIPS 2019 (arXiv:1904.06019); arXiv:1904.06019. Evidence: FT-skim.
- Task / data: Weighted conformal intervals when covariate distributions differ. -.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: Distribution-free coverage under shift if the likelihood ratio is known or estimable.
- Limits / leakage risks: Needs shift to be covariate-only.
- Already addresses the proposed contribution? No.

**[R65] Jin & Candes 2023** - Selection by Prediction with Conformal p-values. Jin Y, Candes EJ; arXiv:2210.01408 (JMLR 2023, not verified); arXiv:2210.01408. Evidence: FT-skim.
- Task / data: Select candidates whose true outcome exceeds a threshold with FDR control from model predictions (drug-discovery motivation). -.
- Evaluation split / baselines: -. Baselines: -.
- Useful idea: Conformal p-values give finite-sample FDR control for model-based shortlisting.
- Limits / leakage risks: Exchangeability between calibration and test candidates.
- Already addresses the proposed contribution? No.

## 5. Tier C sources (peripheral, bibliographic or abstract-level)

| ID | Source | Evidence | What it is used for |
|---|---|---|---|
| R14 | MatchMaker 2022 (doi:10.1109/TCBB.2021.3086702) | ABS | Up to ~15% correlation and ~33% MSE improvement over next best method (abstract claim) |
| R15 | DeepDDS 2022 (doi:10.1093/bib/bbab390) | ABS | Claims >16% precision gain on an independent AZ set (abstract) |
| R21 | O'Neil 2016 (doi:10.1158/1535-7163.MCT-15-0843) | BIB | Source of DeepSynergy/RECOVER training data |
| R24 | Kernfeld 2025 (doi:10.1186/s13059-025-03840-y; PMC12621394) | ABS | Uncommon for methods to outperform simple baselines (abstract) |
| R25 | PertEval-scFM 2024 (doi:10.1101/2024.10.02.616248) | ABS | No consistent improvement over baselines, especially under distribution shift (abstract) |
| R26 | Kedzierska 2025 (doi:10.1186/s13059-025-03574-x; PMC12007350) | FT-skim | Pretraining-corpus overlap analysis and a randomly initialised control model: template for 'is it the pretraining or the architecture' |
| R28 | scGPT 2024 (doi:10.1038/s41592-024-02201-0) | BIB | Object of the critiques R22-R26 |
| R29 | Geneformer 2023 (doi:10.1038/s41586-023-06139-9; PMC10949956) | BIB | Object of the critiques R22, R25, R26 |
| R30 | GEARS 2024 (doi:10.1038/s41587-023-01905-6; PMC11180609) | BIB | Knowledge-informed representation; beaten by linear/mean baselines in R22 |
| R35 | Costello 2014 (doi:10.1038/nbt.2877; PMC4547623) | ABS | Best methods modelled non-linearity and pathway information; multi-task Bayesian MKL won (abstract) |
| R36 | PRISM 2020 (doi:10.1038/s43018-019-0018-6; PMC7328899) | ABS | Alternative public mono source (not used by the protocol) |
| R37 | CTRP 2015 (doi:10.1158/2159-8290.CD-15-0235) | BIB | Alternative public mono source |
| R41 | Hwangbo 2023 (doi:10.1038/s43018-023-00667-z) | ABS | 95% of approved combinations additive or less; additivity 100% sensitive / 78% specific for trial success (abstract) |
| R43 | Vlot 2019 (doi:10.1016/j.drudis.2019.09.002) | ABS | Only moderate concordance (Pearson >0.32, Spearman >0.34) with strong disagreements driven by tested concentrations, maximal response and EC50 |
| R45 | Safikhani 2016/17 (doi:10.12688/f1000research.9611.3; PMC5580432) | FT-skim | Consistency depends on metric (Pearson/Spearman/Dxy, discretisation) and assay noise |
| R46 | Haverty 2016 (doi:10.1038/nature17987) | ABS | Consistency achievable with good lab and analysis practice (abstract) |
| R47 | Iorio 2016 (doi:10.1016/j.cell.2016.06.017; PMC4967469) | FT-skim | Source description of GDSC mono panel |
| R49 | Cheng 2019 (doi:10.1038/s41467-019-09186-x; PMC6416394) | FT | Only 'complementary exposure' (targets hit the disease module, different neighbourhoods) correlates with approved efficacy |
| R52 | Varma & Simon 2006 (doi:10.1186/1471-2105-7-91; PMC1397873) | BIB | Standard reference for nested CV (content from background knowledge) |
| R53 | Dwork 2015 (doi:10.1126/science.aaa9375) | BIB | Repeated adaptive use of a holdout invalidates it (background knowledge); relevant to the exposed Jaaks lines |
| R55 | Joulani 2013 (arXiv:1306.0686) | FT-skim | Delays add a cost to regret of the non-delayed learner (abstract-level reading) |
| R56 | Gelbart 2014 (arXiv:1403.5607) | FT-skim | Treat failed/invalid experiments as an unknown constraint, not as missing-at-random |
| R57 | Desautels 2012/14 (arXiv:1206.6402) | FT-skim | Batch selection under pending outcomes |
| R64 | Angelopoulos & Bates 2023 (doi:10.1561/2200000101; arXiv:2107.07511) | FT-skim | Practical split-conformal and risk-control recipes |
| R66 | Jin & Candes 2025 (doi:10.1093/biomet/asaf066; arXiv:2307.09291) | FT-skim | Weighted version of R65 for test lines whose covariates differ from calibration lines |

## 6. What I could not verify, and open uncertainties

- **Full-text access.** Nature.com articles (Jaaks full page, Hwangbo, Wright 2025) and PMC HTML pages return redirects or captcha to the fetch tool. Jaaks, Vis, Bashi and others were read through Europe PMC XML, which worked; Palmer-Sorger 2017, Hwangbo 2023, Costello 2014, Corsello 2020, Vlot 2019, Haverty 2016, Ben-David 2018 and Xia 2022 are abstract-level only; DrugCell, TCRP, Kim, PDSP, Holbeck, MuSyC and Vis 2016 rest on a fetch-tool page summary.
- **No source found that does the exact proposed experiment.** I searched for mono-pretraining on GDSC-type fitted IC50 followed by fine-tuning on Bliss-residual calls in an anchored screen with a decision-level yield endpoint and found none; absence of evidence from a bounded web search, not proof of absence. PRISM-based pretraining for combinations (mentioned in the brief) surfaced only the PRISM resource paper [R36], not a combination-transfer study.
- **Vis 2024 numbers vs repository notes.** The paper reports 757 lines / 51 combinations / 49 overlapping Jaaks with 46 identical anchor concentrations; repository notes cite 730 lines / 19 ordered combinations as a qualified subset. I could not reconcile these. Whether Vis lines overlap the Jaaks 125 was not checked.
- **PROGENy version.** The original paper has 11 pathways; the 14-pathway score table used here is a later extension that I did not verify.
- **GDSC2 fit provenance.** That GDSC2 release 8.5 fitted values come from the NLME model of Vis 2016 [R38] is inferred from the NLME_* column names and from the Vis 2024 methods, not from a GDSC2 release document I read.
- **Claims about repository results** (for example forecasts being 1.6-2x low on selected actions) come from the memory index, not from re-reading those reports.
- **Evidence strength** of benefits claimed by the pretrain/multitask papers is weakened by pooled metrics and transductive splits; I have not re-analysed any of their numbers.
