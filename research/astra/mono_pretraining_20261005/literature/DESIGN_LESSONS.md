# Design lessons for the mono-pretraining experiment (agent A, 2026-10-05)

Companion to `RELATED_WORK.md` (IDs `[Rxx]` refer to it and to `related_work_matrix.csv`). Statements marked **(inference)** are my reasoning, not something a source says. Statements marked **(repo note)** come from the repository documents or its memory index and were not re-verified by me. Nothing here read any GDSC2 or Jaaks outcome value.

Reviewed protocol: `research/astra/knowledge_optimization_20261004/PRETRAINING_PROTOCOL.json` (status DESIGN_ONLY_NOT_FROZEN_FOR_OUTCOME_ACCESS, so everything in section (e) can still be adopted before freeze).

---

## (a) Novelty assessment

### What is not new

| Ingredient | Prior work |
|---|---|
| Single-drug supervision shared with a combination head | MARSY multitask [R12] (+6.1% / +5.1% Spearman over single-task, DrugComb); PDSP [R11] (drug-response nodes, fine-tuning to patients); Kim 2021 [R10] (mono+synergy multitask, transfer data-rich to data-poor tissue); DrugCell [R17] (mono model used to nominate combinations) |
| Pretrain on a public screen, adapt on few new samples | TCRP [R31] (k=0-10 shots; gains saturate quickly); RECOVER [R06] (pretrain on O'Neil/ALMANAC, fine-tune by rounds); chemCPA [R27] (bulk L1000 pretraining) |
| Low-rank bilinear drug x context head | comboFM [R16] (rank 25-100 multi-way FM); the linear model G W P^T in Ahlmann-Eltze et al. [R22] |
| Pathway-footprint covariates | PROGENy [R48] |
| Mapping/feature shuffle controls | SynVerse [R05] (10 shuffles per feature set), RECOVER [R06] (identity-shuffled model) |
| Decision-level metrics (top-k yield, enrichment vs random, therapeutic index) | RECOVER [R06], BATCHIE [R07] (retrospective on the same Jaaks/GDSC2 combination data), Kim [R10] |
| Calibrated shortlisting with error control | Jin and Candes [R65, R66]; the repository's own yield/FDR certificates (repo note) |

### What is arguably different (and how much it is worth)

1. **Decision estimand against a strong history-based ranking, not against random.** RECOVER and BATCHIE compare to random acquisition; the repository's earlier campaign shows a development-selected simple ranking is hard to beat (R vs C_mean -5.96% [-13.36, +1.67], repo note). Testing whether mono-pretraining changes confirmed yield *over that ranking* under a frozen screen-then-verify contract is new in kind. Value: real, but it is a better test, not a new model.
2. **Attribution through pretraining-stage permutations with a same-input scratch arm.** SynVerse and RECOVER shuffle inputs of the final model; permuting only the mono pretraining stage separates "pretraining information" from "extra parameters or training steps". Value: real if the permutation null is estimated properly (see (e)); a single fixed permutation is not a null distribution.
3. **Target is a Bliss residual while the pretraining target is a main effect.** The Jaaks call removes the monotherapy-expected effect (R01). A model pretrained on mono labels therefore supplies *coordinates* (where a drug sits in cell-context space), not the *sign or size of the interaction* between two drugs (inference): the product term r x (e_a x e_b) is never trained by mono data. This is both the interesting question and the reason to expect a small effect.
4. **Sparse same-tissue history regime** (n4 history lines per tissue). Related to few-shot work [R31, R10] but not tested for an anchored menu.

### Does it differ from "ordinary transfer learning plus a ranking policy"?

Only in 1-2 above; the model class and training recipe are ordinary. I would not claim methodological novelty. Honest framing: **a pre-registered attribution and decision-level test of a known idea in a regime where it has not been tested**. A null result would be informative and publishable as a negative result; a positive result would still need an independent release.

### What prior work refutes or constrains

- **Features help synergy models:** largely refuted for regression benchmarks. No SynVerse model beat the one-hot MLP and shuffled features matched real ones [R05]; no drug-feature performance in monotherapy DRP [R32]; in AZ-DREAM the identity-only baseline reached 0.32 and only drug-target annotation beat it (p=0.012) [R04].
- **Monotherapy as a feature for synergy:** post-hoc AZ-DREAM analysis found no significant gain, yet monotherapy-resistance biomarkers enrich for synergy [R04]. Mono explains combination *response*: IDACombo Spearman 0.93 in-sample ALMANAC, 0.59-0.65 cross-dataset (ceiling 0.60) [R08]; 59.5% of combination biomarkers are monotherapy biomarkers [R03]; ECB tracks efficacy and PDX response better than synergy [R02].
- **Foundation/perturbation models:** deliberately simple baselines match or beat them [R22-R26]; low heterogeneity makes constant predictors strong [R23]. What worked was matched-assay pretraining of a linear low-rank model [R22], the closest analogue to this design and mildly encouraging.
- **Zero-shot transfer across studies:** poor (RECOVER study-transfer task [R06]; cross-dataset DRP [R33, R34]; AZ-DREAM to ALMANAC [R04]). GDSC2-to-Jaaks is cross-study even though both are Sanger screens (inference: same institution does not guarantee same readout, time point, plate format or curve fitting; I did not verify GDSC2 protocol details).
- **Active-learning/scheduler gains:** acquisition rankings are unstable across datasets, metrics and models [R54]; the repository found no scheduler headroom (repo note).

### Prior probability (inference, subjective)

I expect: mono-pretraining improves held-out mono prediction for a minority of pathway-targeted drugs (PROGENy associations are concentrated on MAPK/EGFR [R48]); a small or null effect on the Bliss-residual ranking over strong simple (more likely below the 5% bar than above it); a larger, more detectable effect on a combination *efficacy* endpoint. This is a judgement from the evidence above, not a result.

---

## (b) Does single-drug sensitivity predict synergy or combination ranking?

### What is established

- Combination *efficacy* is largely mono-driven: independent drug action explains approved combinations (Palmer and Sorger [R39], Plana [R40], additivity 95% of approvals, Hwangbo [R41]); monotherapy predicts in-vitro combination viability (IDACombo [R08]); in Vis 2024, ECB frequency correlates with efficacy r=0.57 (0.48 after removing synergistic responses) [R02].
- Jaaks synergy (Bliss residual, thresholds 8-fold dIC50 or 20% dEmax) is rare (5.2%), mostly in weak-to-moderate single-agent activity, pair-specific (mostly <3 lines per tissue) and anchor-dose specific (only 27.5% of synergistic pairs at both anchor concentrations) [R01]. 76.8% of combination biomarkers relate to only dIC50 or dEmax, not both [R01].
- Biomarker overlap with monotherapy is large for combination response (59.5% [R03]) but this is not the same as predicting the residual **(inference)**.

### Mechanisms by which mono information could help

1. **Headroom.** A Bliss-residual call needs room above the monotherapy expectation. Arithmetic from the Jaaks definition (inference): a dEmax call needs Bliss-expected viability >= 0.20 (observed viability cannot be below 0), so if the product of the two monotherapy viabilities is below 0.20 an efficacy call is impossible; a potency call needs the library drug's IC50 inside the tested range. The synergy rate is therefore an **inverted-U** in monotherapy activity (consistent with the 52-86% / 53-80% viability IQR in R01). Predicted mono sensitivity of the anchor and library drug in the target line is the cleanest way mono data can matter, and it needs a non-monotone transform; a linear head on r x e does not provide it **(inference)**.
2. **Shared pathway dependence.** Two drugs dependent on the same cell-state axis (large r x e_a x e_b) may be redundant (Bliss-additive or antagonistic) or parallel (synergistic); network and pathway work argues for "complementary exposure" [R49] and parallel-pathway logic [R17]. Mono pretraining gives coordinates, but the **sign must be learned from sparse combinations** **(inference)**.
3. **Context-specific resistance.** Mono-resistance biomarkers enrich for synergy in cell lines and PDX [R04].

### Mechanisms by which it could not help (and why the effect may be small)

1. **Label is a residual.** Anything explained by monotherapy is subtracted by construction; the model is rewarded only for the part monotherapy does not explain [R01, R42]. AZ-DREAM saw no significant mono-as-feature gain [R04].
2. **Tissue-level pair history already carries most of the usable signal.** Pair-specific synergy is rare; the earlier campaign found the large gain came from two-orientation history (+13.4% [8.4, 18.8]), not from modelling (repo note). Line-specific deviation from the tissue-level pair rate must come from 14 pathway scores and ~4 history lines per tissue.
3. **Saturation/ceiling.** If either drug is already near-lethal at the anchor or library concentration in a line, efficacy synergy is arithmetically excluded (see above); mono pretraining on LN_IC50 does not report viability at the Jaaks concentration.
4. **Assay mismatch and extrapolated fits.** GDSC2 LN_IC50 comes from different concentration ranges (MIN/MAX_CONC per drug, repo note); the Jaaks anchors are <=10 uM at fixed doses chosen for 50-90% viability [R01]. Out-of-range fitted IC50s are extrapolations of a shared-slope NLME curve [R38], not observed thresholds (the protocol already lists this as a do-not-infer item). Cross-study transfer of mono is only moderate (IDACombo cross-dataset 0.59-0.65 [R08]; DRP cross-dataset drops [R34]).
5. **Coupled measurement noise.** The synergy label is computed from monotherapy in the same experiment, so label and mono errors are correlated; synergy scores also depend on dose range, maximal response and Hill slope [R42, R43] **(inference for the consequence)**.
6. **Pooled-metric optimism.** Gains reported for multitask mono+synergy [R12, R10] are pooled, transductive, and use mono labels from the same experimental blocks as synergy, so they do not transfer to new-line within-menu ranking [R09, R32].

### Corollary: a positive-control endpoint

If mono pretraining works at all, it should rank combination *efficacy* in new lines (viability under anchor+library) better than scratch (IDACombo [R08] shows this is feasible with measured mono). If it fails there, the pipeline is broken or the GDSC2-to-Jaaks bridge fails; if it works there but not for the Bliss-residual call, the mechanism question is answered cleanly. This endpoint costs no new data.

### Tissue vs pair specificity

Jaaks: synergy mostly pair- and line-specific, with 192 combination-tissue pairs (7.8%) synergistic in >=20% of lines [R01]; NCI-ALMANAC: most combinations active in 11-30 of 60 lines, largely independent of histology except leukemia [R20]; Vis: tissue synergy rates concordant with Jaaks (Spearman 0.81-0.90) [R02]. History pooled within tissue estimates the pair rate, the quantity the strong simple ranking already uses.

---

## (c) Leakage and split pitfalls (with citations) and protocol status

| # | Pitfall | Evidence | How it could bite here | Protocol status |
|---|---|---|---|---|
| 1 | Cell-line identity: duplicates, aliases, same-donor lines, strain drift | Ben-David [R44] (>=75% of compounds strongly inhibiting some MCF7 strains inactive in others); Safikhani/Haverty [R45, R46] | GDSC2 lines that are aliases or same-donor relatives of Jaaks lines leak target-line response | Exact SIDM exclusion and alias/COSMIC check; **add same-donor (STR/Cellosaurus) check and flag, not only exact IDs** |
| 2 | Drug-pair/drug identity leakage in random or leave-triplet splits | SynVerse [R05]; Sidorov [R18]; DeepSynergy [R13]; MARSY [R12] | Here pairs recur across lines by design; the claim is "new cell line, known pair", not new pair | Protocol states new-pair claim is not primary. Keep it explicit in the report title and abstract |
| 3 | Shared single-agent measurement between pretraining/feature and label | Label is the Bliss residual of the same experiment's monotherapy [R01]; metric artefacts [R42, R43]; MARSY multitask uses same-block mono [R12]; AZ-DREAM mono mis-annotation [R04] | Target-line Jaaks monotherapy viabilities must not enter any non-oracle arm | "Do not add mono IC50/AUC to synergy" present; **add an explicit test that no Jaaks mono value of the target line enters features** |
| 4 | Fitted-value dependence (NLME pooling) | Vis 2016 [R38]; Vis 2024 methods [R02] | Fitted LN_IC50 are jointly estimated; Jaaks-line curves may have informed pooled parameters of the 838 retained lines | S0 lists "independent vs shared fitting"; **disclose and keep the label "fitted-parameter transfer"** |
| 5 | Replicate, plate and batch structure; cross-study shift | DrugComb [R19] (between-study replicate SD 15.44 vs 4.25/12.02 within); RECOVER [R06]; Jaaks F-score 0.62-0.70 between primary/validation [R01]; cross-dataset DRP [R33, R34] | Caps attainable ranking; GDSC2-to-Jaaks is a cross-study transfer | Plate/batch sensitivity listed; **add a replicate-based noise ceiling for the confirmed-yield endpoint** (Jaaks has 2-18 biological replicates per line [R01]) |
| 6 | Hyperparameter/comparator selection on test; adaptive reuse of an exposed set | Cawley and Talbot [R51]; Varma and Simon [R52]; Dwork et al. [R53]; Kapoor and Narayanan [R50] | Jaaks is already exposed; strong-simple is chosen among six ranks | Nested inner selection; E61 transport-only; selection limit stated. **Keep E61 and the all-125 pooled analysis labelled exploratory; count forking paths** |
| 7 | Preprocessing leakage and unequal access to unlabeled information | [R50] | The pretrained arm sees unlabeled PROGENy of 838 lines; if scratch standardises only on the small combo-training set, gains can reflect standardisation or covariate geometry, not mono labels | Protocol standardises on "allowed mono/combo training covariates"; **give scratch the same unlabeled covariates (standardisation and a covariate-only/PCA pretraining arm)** |
| 8 | Pooled metrics inflate skill; mean predictors look good | Eckhart [R09]; Branson [R32]; Csendes [R23]; AZ-DREAM [R04] | Pooled MSE/AUC across lines/pairs will reward drug-average information | Primary is yield (good); **make within-line metrics the secondary standard, never pooled correlation** |
| 9 | Dependent units | Earlier report: two-way line x pair bootstrap [-22.8, +10.7] vs line-only [-13.4, +1.7] (repo note) | Pairs recur across lines, so line-only intervals are too narrow | "Line x pair sensitivity" listed; **report two-way interval as co-primary uncertainty** |
| 10 | Whole-pipeline false-continue rate untested | [R51, R53] | A multi-condition gate with many looks can pass by chance | Synthetic contract tests; **add a full-gate null simulation (permuted outcomes within tissue; scratch-vs-scratch seed contrast)** |

---

## (d) Calibration, selective prediction, abstention and sequential feedback: what bears on this campaign

Only the following bear on a ranking-and-confirmation campaign; I recommend not importing more machinery into this experiment.

1. **Calibrate on the selected set, not the whole menu.** Calibration degrades under dataset shift for all methods [R61]; temperature-type recalibration is cheap for classifiers [R60]. The optimizer's curse implies the selected top candidates are over-estimated when estimates are noisy [R58]; the repository's own earlier finding was the opposite sign (forecasts on selected actions 1.6-2x low, repo note), which points to shrinkage rather than selection bias **(inference)**. Either way, check reliability on the actions actually purchased, with cross-fitting.
2. **Abstention as "do not override the strong simple ranking".** Selective prediction trades coverage for risk [R62]. Operationally: the pretrained arm overrides the baseline's screen only when its calibrated margin exceeds a threshold fixed before outcomes; evaluate net correct versus wrong swaps. This is the mechanism-level test of whether information, not noise, enters decisions.
3. **Shift between pretraining and target tissues.** The 838 retained lines include many tissues, the targets are breast/colon/pancreas. If any calibrated claim is made, weighted/selective conformal methods give finite-sample guarantees only if the covariate shift is estimable [R63, R65, R66]; with 14 covariates this is plausible but untested here **(inference)**. Minimum: report held-out mono predictability **within the three target tissues** separately from the pooled validation.
4. **Delayed, noisy, failed feedback.** Delays add regret to a non-delayed learner [R55]; batches can be selected with outcomes pending [R57]; failed experiments should be modelled as an unknown constraint, not as missing at random [R56]; the replicate-versus-new-experiment trade-off is unresolved in benchmarks [R54]. For this fixed two-round, stop-allowed contract (repo note) the practical implications are small: keep failed/unexecuted as visible categories, and do not claim a scheduler or feedback gain, because the repository found no headroom there (repo note).
5. **Decision-focused evaluation.** Prediction loss is an imperfect proxy for decision quality [R59]; hence yield and swap analysis, not MSE, are primary.

---

## (e) Concrete recommendations

Priority: **P1 = adopt before freeze**, P2 = strongly advised, P3 = optional.

### Estimands

- **E1 (primary, as now):** paired per-line difference in measured confirmed yield (roles and seeds averaged within line), pretrained minus scratch and pretrained minus strong simple, relative to strong simple. Add the absolute version (hits per 100 lines).
- **E2 (mechanism, P1): swap analysis.** Report the fraction of purchased screens that differ from the baseline, then net confirmed hits among swapped-in versus swapped-out screens, with a line-clustered bootstrap and a sign/binomial test on discordant lines. Fix the reporting order: swap rate before yield difference.
- **E3 (secondary):** within-line concordance of the ranking score with the joint outcome (as in the earlier report, defined on lines with both classes) and within-line AUC; never pooled correlations [R09, R32].
- **E4 (mechanism, P1): dose-response of the gain on mono predictability.** Pre-specify the stratifier from GDSC2 held-out cells (per-drug within-drug rank correlation of mono predictions) and test whether gain increases with predictability. This is stronger than a pooled null and does not replace the menu (the protocol forbids a covered-subgroup replacement; keep it as a pre-specified stratified secondary).
- **E5 (positive control, P1):** same contrasts on a combination efficacy endpoint (viability under anchor+library) derived from the same data [R08, R02].
- **Uncertainty:** report both the line-only and the two-way (line x pair) intervals; the earlier campaign shows they can change the verdict class (repo note).

### Baselines and arms (additions to `arms`)

1. **Two-stage "ordinary transfer" baseline (P1):** per-drug ridge/elastic net mono predictions from the 14 covariates, converted to headroom features (predicted anchor and library viability, inverted-U terms) and fed to the strong-simple ranking or a low-parameter logistic head. If the rank-4 head cannot beat this, the "ordinary transfer plus ranking policy" reading is confirmed.
2. **Headroom-only ranker (P2):** rank by predicted headroom alone.
3. **Main-effects-only pretraining (P1):** rank-0/drug-mean + cell-context main effects, to separate main-effect transfer from rank-4 interaction transfer (diagnostic only; does not violate "no family search" if rank 4 stays primary).
4. **Covariate-only unlabeled pretraining for scratch (P1):** same standardisation/PCA on the 838 lines for the scratch arm.
5. **Compute-matched scratch (P2):** scratch with the same total gradient steps as mono-plus-combo, selected by the same inner-fold rule; and a **scratch-vs-scratch seed contrast** to estimate the noise floor of the "gain" statistic.
6. **Oracle-mono ceiling (P1):** replace predicted mono by the target line's own measured Jaaks mono viabilities (exposed Jaaks, development folds only, access-logged; never a deployable arm). If even perfect mono does not move yield by at least the threshold in (e) "minimum meaningful improvement", stop before pretraining. The mechanical dependence of the label on those mono values (section (b), item 5) makes this an optimistic bound **(inference)**; a null is therefore strong evidence, a positive is not.

### Negative controls

- **K >= 10 permutations per control, not one fixed permutation (P1).** SynVerse used 10 shuffles per feature set [R05]. Report the null distribution of the gain and require pretrained to exceed its upper quantile (for example the 95th) plus the paired-line interval.
- **Stratified permutations (P1):** cell permutation *within tissue* (a cross-tissue permutation is trivially detectable because PROGENy encodes tissue); drug permutation *within target-pathway class* in addition to unrestricted permutation.
- **Label-shuffled mono (P2):** permute response across cells within drug (kills cell-context information, preserves drug means).
- **Non-menu-drug pretraining (P3):** pretrain r on GDSC2 drugs not in the Jaaks menu with menu e_a random, to separate transfer of the cell-context map from transfer of menu-drug coordinates.
- **Placebo contrast:** scratch-vs-scratch (above).

### Minimum meaningful improvement and power (from the repository's own numbers)

- Earlier campaign (n=61 lines): 95% half-width of the relative gain +-5.5%; P(L>0)=0.43 at a true +5%; about 250 lines needed to exclude a 5% effect at 0.95 power (repo note). My arithmetic from those figures: per-line SD about 0.57 hits (SE 0.0735 at n=61); with the yield about 1.9 hits per line, 5% = 0.096 hits per line, so 80% power needs about 280 lines.
- The primary here is the outer-fold HD set (64 lines): SE about 2.7%; for a true +5% gain the chance that L>0 is about 0.45 for one contrast; the gate requires the point estimate >= 5% **and** L>0 **and** two controls **and** two-of-three seeds. A true effect exactly at the threshold passes the point-estimate criterion at most 50% of the time at any sample size, and passing both controls jointly is less likely **(inference, assuming roughly normal estimates)**. The gate is therefore much more likely to return STOP or UNRESOLVED than to find a true 5% gain.
- **Recommendation (P1):** keep tau = 5% as the "worthwhile" label, but pre-register three outcomes in advance: *benefit detected* (L>0, point estimate > 0), *worthwhile* (point >= 5% and L>0), *worthwhile excluded* (U < 5%), with everything else *unresolved*; do not read UNRESOLVED as no effect. Report a pre-freeze power curve at the actual n and swap rate.
- **Cost-equivalence anchor (P2):** 5% of yield is about 0.1 confirmed discovery per line, roughly 1.4-1.8 measurements per line at about 14-18 measurements per hit (derived from 1,563 spent for 110.5 hits and the 1,954 cap, repo note). The earlier +13.4% from adding the confirmation-orientation history is the competing use of resources.
- **More precision for free (P2):** make the pooled all-125-line nested cross-fit a pre-specified exploratory co-analysis; the earlier all-125 sensitivity had half-width about 3.3% (repo note).

### Specific edits to `PRETRAINING_PROTOCOL.json`

| Key | Change |
|---|---|
| `stages` | Insert **S1a mono-transfer preflight gate**: after freeze, GDSC2 only, held-out cells, per-drug within-drug rank correlation vs drug-mean baseline, reported pooled and within breast/colon/pancreas; define the predictable-drug stratifier here. Insert **S1b oracle-mono ceiling**. Stop rules: STOP if mono predictability is no better than the drug-mean baseline for nearly all menu drugs, or if the oracle ceiling is below the threshold |
| `arms` | Add: two-stage mono-feature baseline, main-effects-only pretraining, covariate-only scratch, compute-matched scratch, scratch-vs-scratch; replace the single fixed permutation by K >= 10 stratified permutations per control |
| `continue_gate.required` | Replace "positive attributable advantage over both mono permutations" with "exceeds the 95th percentile of the permuted-pretraining null"; **drop "at least 2 of 3 history seeds positive"** (with three weakly dependent seeds it has no discriminating power; replace by a variance decomposition across seeds and the scratch-vs-scratch floor); add the three-way outcome classification and the two-way (line x pair) interval |
| `metrics.secondary` | Promote swap analysis (E2), stratified dose-response (E4), efficacy positive control (E5), noise ceiling; mark pooled correlation as not reported |
| `model.mono` / `loss` | State how out-of-range fitted IC50 (above MAX_CONC) is handled (censoring-aware loss or flag/clip); add AUC (or viability at the Jaaks anchor/library concentration if derivable from the fit parameters) as a second mono target, because the Jaaks label depends on viability at fixed concentrations, not on IC50 alone **(S0 must confirm which fit parameters exist)** |
| `S0_metadata_before_labels` | Add same-donor/STR near-duplicate check; GDSC1/GDSC2 duplicate compound IDs; disclosure that pooled NLME fits may have used the excluded Jaaks lines |
| `tests` | Add: no Jaaks monotherapy value of the target line enters non-oracle arms; scratch and pretrained use identical unlabeled-covariate standardisation; full-gate null simulation |
| `outcome_scope` | Keep "adaptive exploratory"; state that Vis is not an independent source in the platform sense (same Sanger platform, 49 of 51 combinations overlap Jaaks with 46 same anchors [R02]) and that line overlap with the Jaaks 125 must be checked before any Vis use |

### Things not to do

- Do not add a foundation-model or knowledge-graph embedding arm: the evidence says it will not help and it dilutes the attribution [R22-R26, R05].
- Do not add a scheduler, LLM or feedback arm: no headroom was found (repo note) and acquisition-function rankings are unstable [R54].
- Do not interpret improved mono held-cell error as evidence for the combination claim (already in `not_sufficient`; keep).

### Evidence quality caveat

Most precedents report pooled metrics under transductive splits; none tests the within-menu new-line decision problem. My recommendations rest on the structural arguments above and on the independent benchmarks [R04, R05, R06, R09, R22, R23, R32], not on a direct replication of any of them.
