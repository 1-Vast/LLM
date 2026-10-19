# Evidence Register

2026-10-19: [Kinobeads substitution test](kinobeads_substitution_20261019/REPORT.md), **NOT_SUPPORTED** (the action-substitution study's Level M falsifier; Klaeger 2017
kinobeads Kd from ChEMBL CHEMBL3991601, downloaded 2026-10-19 with approval; exposed Jaaks 2022 interaction endpoint; protocol frozen before any binding correlation; run once;
`verify.py` VERIFY OK). 31 of 64 Jaaks drugs map; 20 of the 27 phase-2 implementations have a binding profile (Dactolisib has none). A B5-form kernel on kinobeads correlation
is worse than the functional kernel (MSE_B5 - MSE_K -0.000059 [-0.000115, -0.000010]) though better than sibling copy (+0.000197 [+0.000027, +0.000404]); binding similarity
does not rank substitution failures (AUROC 0.635 [0.476, 0.738]) and is no better than Jaccard (-0.024) or functional similarity (-0.041). It recovers the motivating EGFR/HER2
(0.51-0.61) vs Sorafenib/Dasatinib (0.15-0.19) contrast but not other families (mTOR 0.07 rarely fails; IGF1R 0.31 fails half the time; Alisertib/Tozasertib asymmetric). Profiles
are thin (median ~15 measured binders). Level M branch closed; action substitution stays NARROW. Development evidence only.

2026-10-19: [Conditional pharmacological action units](action_substitution_20261019/REPORT.md), **NARROW** (programme as briefed STOP; exposed Jaaks 2022 GDSC anchored
combination screen, downloaded 2026-10-19 with approval; gate plan written before responses were read, phase 2 and phase 3 frozen before prediction; `verify.py` ALL OK).
Gate CONDITIONALLY QUALIFIED: same-target swap contrasts reproduce across seeding dates (interaction r 0.31 [0.23, 0.51]), but the reproducible variance is partner-specific
(0.00052) not partner x line (0.00007, CI crosses 0; share 0.08 < 0.25); interaction swaps are not potency (R^2 0.015), efficacy swaps mostly are (0.49). Phase 2, leave one
implementation out (27 drugs, 1,950 partner units): interaction NOT_BEYOND_BASELINE (learned substitution model -49% vs functional-similarity kernel; partner features nil);
efficacy INCONCLUSIVE (+11.5% [-15%, +30%] vs cold-start ridge; potency matching AUROC 0.85). Post hoc: same-target sibling copy is beaten by the functional kernel
(+0.00025 [+0.00011, +0.00042]) and ties the identity-free partner mean; it is best only in tight families (EGFR/HER2), worst in multi-kinase ones. Phase 3: one same-partner
counterexample cuts interaction error 17% (PARTNER_SPECIFIC_REFINEMENT; a different-partner probe hurts) but moves no equivalence decision at epsilon 0.03, even with every unit
probed, so agent value is bounded at zero; efficacy refinement adds nothing beyond potency matching. Independent confirmation BLOCKED. Development evidence only.

2026-10-19: [Heavy-tail RSD](heavy_tail_rsd_20261019/REPORT.md), **HEAVY_TAIL_DOES_NOT_FIX_D2** (test of RSD's REVISE; exposed PRISM 19Q4 HTS002 compounds, 0.625 and 10 uM reads
opened once after the freeze; development on the exposed 2.5 uM reads only; `verify.py` VERIFY OK). Student-t noise (pair-level or compound-level multivariate t; scale ML-fitted
on reference replicate differences, (level, nu) chosen by RSD's reference-only replicate-split utility) on the frozen RSD signal geometry. Pooled 1,715 compound-doses, 250 clusters:
`ht - raw` D2 +0.015 [-0.014, +0.046] (delta 0.080); `ht - rsd` D2 -0.007 [-0.011, -0.003]; `ht - raw` D1 +0.043 [+0.003, +0.076], Holm p 0.060; D1 non-inferior to rsd
(-0.015); selected-pair 80% coverage 0.690 (rsd 0.698). The reference utility preferred the Gaussian over every heavy-tail candidate in all 6 test units and all 3 development blocks.
Compound-level noise alone restores selected-pair coverage (0.749) and optimism (-0.003) but costs D2 -0.048. Secondary: frozen RSD D1 gain replicates in sign at both doses (+0.057
[+0.026, +0.085]), about half its 2.5 uM size and below half a second read (0.078); a second read gives +0.16 on both decisions. Development evidence only.

2026-10-19: [Replicate-identified VC decisions (RSD)](replicate_decisions_20261019/REPORT.md), **REVISE** (exposed PRISM 19Q4 secondary HTS002 2.5 uM, 1,283 audited
compounds x 480 informative lines; all-label/name/Tanimoto families, edge-purged references; replicate plates assigned A = screening read, B = purchasable,
T = sealed truth, plus the primary-screen run; search/freeze/selection/evaluation once; `verify.py` VERIFY OK). Evaluation (423 compounds, 130 clusters):
H1-D1 context selection `rsd - raw` +0.118 [+0.084, +0.157], Holm p 0.0005, above delta 0.067 (SUPPORTED); equals two raw reads at half the wells (-0.023 [-0.071,
+0.021]); cross-run +0.090 [+0.062, +0.116]; false progression 0.251 -> 0.170. H1-D2 progression -0.008 [-0.037, +0.025] (NOT_SUPPORTED; never above delta in
any block). Selected-candidate optimism +0.07 (raw +1.08, two raw reads +0.80) but selected-pair 80% coverage 0.675. Chemistry prior hurts new classes (-0.050);
PCA denoising below raw; KG escalation = exploit-first (+0.001) and the posterior adds nothing to the raw re-read rule (-0.006). Exploratory diagnosis: heavy-tailed
pair-level noise (kurtosis 3.2) dominates the extreme pairs D2 picks; geometry transfer is not the bottleneck. Development evidence only.

2026-10-19 maintenance: [FAR working entry point](maestro_far_20261019/README.md). Removed duplicate discarded-run files and redundant non-frozen driver code;
verification is now read-only and stage/model writers refuse existing outputs before data access. Seven regression tests pass; all 118 contrasts and 54 replay combinations
still match in the original environment. Frozen core, models, decision gates and original study results are unchanged; FAR_NOT_SUPPORTED remains the scoped verdict.

2026-10-19 audit: [FAR reproduction and design audit](maestro_far_20261019/audit_20261019/REPORT.md).
All 118 saved contrasts recompute; select/test records and atlases reproduce exactly in the original base environment. `maestro` has model/version incompatibilities.
Keep FAR_NOT_SUPPORTED, with corrected scope: search uses select outcomes as references, test folds train on each other, and four slices are not exactly equal drug-count cost.
These are exposed-data cross-validation results; the audit does not establish strictly isolated search/select/test or independent future-task headroom. Original frozen files/results preserved.

2026-10-19: [MAESTRO-FAR dev arena](maestro_far_20261019/REPORT.md), **FAR NOT SUPPORTED** (exposed PRISM 19Q4 x L1000 x ECFP4, 848 dev drugs, 242 families, 5 family
folds; search/select/freeze/test once; reused-vault check is not independent; `verify.py` VERIFIED). Failure signatures AUROC 0.47-0.52 in select, test and vault (0 of 3
above 0.60). FAR - exploit-first: test +0.006 [-0.003, +0.018], select -0.013 [-0.028, -0.004]; FAR-v2 (benefit model) test -0.000 [-0.007, +0.006]; threshold 0.010 not met.
Assay + gate repair - no assay: test +0.039 [+0.009, +0.085], vault +0.047 [+0.009, +0.095] (not FAR-specific). Line-agnostic hindsight slice choice - random: test +0.059
[+0.015, +0.113] (reproducible slice value that no pre-assay feature predicts). Agent, 2x2, transfer, EG-RPT and external phases not run (frozen rule).

2026-10-18: [Observable-state bets](observable_state_20261018/REPORT_OBS.md), **AGENT CLAIM WITHDRAWN** (exposed PRISM 19Q4, internal development
assessment; freezes FREEZE0/1, `verify.py` VERIFIED). 136 MoA families, within-family chemical split, 7 held-out lineages; one typed edit per family per arm.
Confirmation rate: random 0.051 (test calibrated), enumerator 0.059, target-gene rule 0.088, agent 0.081, masked agent 0.059. Agent - enumerator +0.022
[-0.022, +0.074] (upper bound < +0.10); agent - target-gene rule -0.007; agent - random +0.029 [-0.005, +0.069]. Exploratory: target-gene rule - random +0.037
[+0.003, +0.075], unadjusted. Stated probabilities ~5x overconfident. Not tested: decision utility, other edit primitives, independent data.


2026-10-17: [Program revision](program_revision_20261017/REPORT.md), **METHOD NOT SUPPORTED**
(pre-registered on PRISM 19Q4 HTS002; freeze 12:55:48Z; future strata opened once at 13:09:54Z;
`verify.py` VERIFIED). Not an independent confirmation: the future strata come from the same screen.
* Design.
  * 966 source and 322 novel drugs (held-out structure groups); 231 source lines (10 development
    projects, support 128 / query 103), 67 future lines, 180 future-lineage lines.
  * Decision: nominate 10 drugs per line; utility is qualified confirmed hits (mean(X2,X3) <= -1 and
    <= drug source median - 1, every available replicate < 0; unknowns counted separately).
  * Strong model: rank-20 ALS with feature-ridge line prior and Bayesian probe updating; beats a
    drug-specific ridge by +0.33 [0.12, 0.52] at I2.
  * Program language: scope (MoA/target) x observable state; loadings fitted on cross-fitted
    residuals; capacity 12 programs, 3 atoms.
* Registered primary (I2, 8 probe wells, Holm).
  * H1 maestro_llm - strong: +0.211 [0.097, 0.340], p 0.004 (CONFIRMED, entirely the seed library).
  * H2 vs stepwise search: +0.008. H3 LLM vs enumeration: +0.004. H4 editable vs fixed: 0.000.
* Secondary.
  * Seed at zero observation: +0.445 [0.084, 0.921]. Empty-start revision: enum +0.057
    [0.022, 0.104], LLM +0.045 [0.000, 0.114].
  * Ablation: MDM x TP53 +0.077 [0.025, 0.128], RAF x BRAF +0.057, PI3K x PIK3CA +0.028;
    revision-added programs -0.004 to -0.008.
  * Novel drug groups: libraries +0.02 to -0.04 (no transfer); strong model beats potency control
    except future lines at I1.
  * AFA vs fixed design +0.223 [0.104, 0.400]; library on AFA -0.012.
* Stage C (28 wells/line). Seed + exploit-first 5.26 vs strong + exploit-first 4.83 (+0.437
  [0.041, 0.889]); fixed probes vs exploit-first -0.381 (HARMFUL); feedback vs one-shot +0.166;
  AFA vs fixed +0.198 at 10 rounds. Revision wells (about 4,300 per arm) are never repaid.
* Diagnosis (post hoc, development data only): the frozen rule would accept 2/10 seed programs on
  the development arena; BRAF/PIK3CA gates are rare there (6 and 12 query lines vs 37 and 30 in
  future lineages). LLM: 62-73% insufficient evidence, 20-23% wrong committed direction.
* Cost: 0 purchased wells, deepseek-flash 0.287 USD (90 calls; 0.088 pre-freeze smoke).

2026-10-17: [Seed attribution](seed_attribution_20261017/REPORT.md), **DEVELOPMENT** on the exposed
PRISM 19Q4 strata; contract repair of the program-revision evaluation.
* Defects: score reference `(X2+X3)/2` (NaN for one replicate) against labels on the available-replicate
  mean; 100 source drugs without a frozen threshold (24 remain undefined, refused by name); thresholds
  differ for 527 of 866 drugs; fit cache ignored the data; the Gaussian crossing score ranks (AUROC 0.834)
  but is not a calibrated probability of the qualified-hit event.
* The frozen development bench trained every fold on 74-101 of the 103 reserved query lines. Seed-library
  query hits at I2: 4.41/line frozen vs 3.87 masked. The masked bench is exactly invariant.
* Seed minus strong (247 lines, 21 lineage clusters): policy +0.356 [-0.088, +0.856] (frozen +0.437
  [0.041, 0.889]), I2 +0.117 [-0.026, +0.248] (frozen +0.211 [0.097, 0.340]), I1 +0.283 [-0.065, +0.699]
  (frozen +0.445). Primary family NOT_CONFIRMED (Holm p 0.29-0.31).
* Attribution (policy / I2 / I1): B vs 20 matched permutations +0.348 / +0.140 / +0.311 (seed above all 20
  nulls everywhere; matched contrast supported at I2 only, lower bound +0.001); capacity +0.009 / -0.023 /
  -0.027; shared-only vs strong +0.324 / +0.093 / +0.146; per-drug loadings +0.032 / +0.024 / +0.138;
  variance-only +0.012 (I2), +0.004 (I1); global ridge on the ten features matches B (-0.004, +0.008,
  +0.166); ridge on all 72 products +0.093 / +0.032 / +0.008.
* Skin carries 82% of the policy gain; gate-negative lines lose 0.32 hits/line; equal-lineage mean +0.057
  [-0.206, +0.355] (corrected 2026-10-18: the saved [-0.175, +0.267] dropped lineage multiplicity in the bootstrap; see
  [seed_attribution_20261017/ERRATUM_20261018.md](seed_attribution_20261017/ERRATUM_20261018.md); primary tests unchanged). Part 4 not run. Cost 0 wells, $0.

2026-10-18: [Acquisition programs](acquisition_program_20261018/REPORT.md), **DEVELOPMENT** (exposed PRISM 19Q4; two-stage freeze; `verify.py`
VERIFIED). Whole-pool target set; second-pool choice; 3 pools per compound.
* Clarification: predecessor `D_hindsight` selected by squared error; campaign-level best of ridge/R1 lists = 131 vs R1 100 (ridge 95).
* Development (20 cells): fixed 305, lookahead 337, agent incumbent 343, hindsight ceiling 410. Searches (12 proposals each): conventional 0
  accepted; agent 1 accepted, 1 no-op, 10 rejected.
* Held-out (30 cells, per 64 compounds): fixed 1.822, lookahead 1.717 (−0.106 [−0.262, +0.022]), conventional = lookahead, agent 1.725
  (−0.097 [−0.232, +0.026] vs fixed; +0.008 [−0.033, +0.054] vs lookahead); R1 1.922, gated 2.083, prior 0.931; hindsight ceiling 704 vs 656.
* Decision: no acquisition program improves on the fixed design here; no project-wide stop is inferred. Cost 0 wells; DeepSeek flash 34k tokens.

2026-10-18: [Feedback propagation](feedback_propagation_20261018/REPORT.md), **DEVELOPMENT** (exposed
PRISM 19Q4 folds 2-4; freeze before the comparison; `verify.py` VERIFIED). Corrected audit: the old
indication-triage hits (395, 293) are 99.7% / 100% on pairs the arm probed.
* Utility: events among nominated unmeasured pairs per 64 compounds, B = 3 pool reads (hypothetical units),
  2,398 compounds, 36 complete campaigns; delta* = 0.1875 from the cost of one more pool for the baseline
  (minimum detectable gain about 0.7-0.9).
* Prior 1.58, ridge-plus-feedback 2.64, kNN10 2.69, R1 (kNN-analogue prior plus ridge residual) 2.78, gated
  3.06, mixture mean 2.67, empirical covariance 2.61, forest 2.39; oracle 32.
* P1 R1 - ridge +0.139 [-0.579, +0.870] (Holm 0.75; development +0.81); P2 R1 - kNN10 +0.083 [-0.279,
  +0.437]; P3 gated - R1 +0.278 [-0.165, +0.775]. Ridge - prior +1.056 [+0.626, +1.526]; at 16 logical
  lines +0.167 [-0.108, +0.451]. Item-specific (own vs deranged histories +2.361). Second noise draw: R1 -
  ridge +0.861 [0.000, +1.690].
* Closed loops (3 pools): loop-R1 2.25, loop-ridge 1.33, below the fixed design (2.78 / 2.64).
* Decision: STOP at P1; no program search. Cost 0 wells, $0.

2026-10-17: [Beat AML gate G1](beataml_g1_20261017/REPORT.md), **DEVELOPMENT** (exposed Beat AML, frozen
before the run). Total hits over 16 queries per sample, 520 samples, 479 patients.
* A_item 0.785, S_ridge 0.835, C0 (low-rank prior) 0.808, E (confirmed engine) 0.854, RF (ridge plus
  feedback) 0.917, CAND (frozen candidate) 0.933; fixed k = 4/8/12 candidate 0.900/0.965/0.908.
* Gate CAND - S_ridge +0.098 [+0.045, +0.153]; net lower bound -0.005 (< 0.05): FAILED. CAND - RF +0.015
  [-0.036, +0.066]; CAND - C0 +0.125 [+0.074, +0.180]; RF - S_ridge +0.083 [+0.042, +0.127]; C0 - S_ridge
  -0.027 [-0.065, +0.011]; CAND - E +0.079 [+0.032, +0.127]; E - S_ridge +0.019 [-0.033, +0.073].
* Decision: stop the low-rank state-model branch. Cost 0 wells, $0, 43 s.

2026-10-17: [Feedback attribution](feedback_attribution_20261017/REPORT.md), **DEVELOPMENT**
(pre-registered; freeze 06:45:10Z; `verify.py` VERIFIED). This is not a confirmation: Beat AML
was already exposed. The Phase 1 audit is in [AUDIT.md](feedback_attribution_20261017/AUDIT.md).
* Design.
  * Same domain, folds and model as the confirmation.
  * All groups share four probes chosen by the population item prior. Fixed rank 20.
  * Outcome: hits among the twelve follow-up queries per sample (520 samples, 479 patients).
  * Parity: with vc0's probes, D and C reproduce the confirmed `b_exploit` and `vc0` exactly
    (297 samples, rank-20 folds).
* Registered (Holm, one-sided 0.025). All positive; none clears 0.05 at its lower bound.
  * H1 population + update vs population state: +0.096 [+0.047, +0.155].
  * H2 RNA + update vs population + update: +0.065 [+0.030, +0.105].
  * H3 RNA prior vs population state: +0.073 [+0.033, +0.113].
  * H4 low-rank vs overall-sensitivity update: +0.081 [+0.033, +0.131].
  * The same holds at ranks 10 and 40, with vc0's probes, in the scheduled-panel `design` task and
    on the 93-inhibitor `panel80` task.
* Weak comparator.
  * The model's population state under the promoted score is 0.090 below the empirical item
    prior, because the promoted event score is incoherent.
  * RNA prior vs item prior: -0.017 [-0.073, +0.042].
  * A drug-specific ridge on the same 30 PCs beats the RNA prior: +0.065 [+0.023, +0.109].
  * Post hoc: the confirmed two-round engine vs that one-round ridge is +0.023 [-0.029, +0.077].
  * The registered label RNA_PRIOR_HAS_INDEPENDENT_VALUE is therefore not a scientific claim.
* Readouts carry item-specific information.
  * Deranged control: D - F +0.115 [+0.061, +0.177].
  * An overall-sensitivity update gives +0.008 [-0.008, +0.024]. It is close to rank-neutral on
    this G-residualised endpoint.
* Coherent event score: +0.04 to +0.08 per group, and martingale gap about 0. It is not
  calibrated (mean predicted 0.018 vs observed 0.021).
* Probes.
  * 8 coherent probes vs none: +0.158 [+0.103, +0.216]. This is the only registered contrast
    clearing 0.05 at its lower bound, net of 0.05 per round.
  * 8 probes vs 4: +0.065.
  * The joint-Monte-Carlo planner chose 8 for 519-520/520 samples, with no per-sample adaptivity.
    Its EVSI understates the realised gain 1.5-1.9x.
* Tuned procedures (Q3). Exploit-first at its own rank gives 0.871 total hits, against:
  * corrected lookahead 0.860;
  * hybrid selector 0.840;
  * calibrated selector 0.806 (bridged 2/5 folds).

  Exploit-first stays the default.
* Diagnostics.
  * AUC variance: inhibitor mean 42%, overall sensitivity 15%, residual 43%.
  * Replicate noise is at least 41% of the residual, and basal PCs predict about 10% of it.
  * Scheduled profiles without a record come from more sensitive samples (G z -0.63), so failed
    assays are informative.
* Cost: 0 wells, 0 USD, no downloads.
* Independent confirmation is blocked: no unexposed domain is local, and PRISM 24Q2 independence
  is unverified (its metadata is not on disk).

2026-10-17: [Context transfer with verified bridges](context_transfer_20261017/REPORT.md),
**CONFIRMED** under the frozen claims C1-C4 (one shot; freeze 04:43:08Z; `verify.py` VERIFIED).
That label records protocol execution. The claims amendment
([CLAIMS.json](context_transfer_20261017/CLAIMS.json)) supports only the functional-feedback gain
(under the replay). The cell-state prior beyond the item prior, procedure selection, the LLM,
the repaired planner and any cost advantage are not established, and C3/C4 as frozen do not test
adaptivity or superiority. This is workflow transfer within Beat AML, not biological knowledge
carried from PRISM.
* Domain: Beat AML 2.0, its first MAESTRO use.
  * 520 primary AML RNA-seq samples from 479 patients x 165 analysed inhibitors (166 in the
    release census).
  * Probit-AUC selective events (no absolute gate, at least 100 measured samples).
  * 16 archived AUC queries per sample (the frozen files call them wells; 112 treatment wells if
    run), 5 patient-disjoint folds.
  * Development was on exposed PRISM 19Q4.
* Choice: the source-verified agent chose exploit-first bridging (4 of 16 queries) in 5/5 folds.
* Hits per sample: `maestro` 0.850 against
  * `vc0` 0.777 (+0.073 [+0.025, +0.127], Holm p 0.0075);
  * `match_panel` 0.621 (+0.229 [+0.162, +0.298]);
  * frozen lookahead 0.742 (+0.108 [+0.051, +0.172]).
* Virtual Cell prior: `vc0` beat `knn` by +0.075 [+0.014, +0.137] but not `item`
  (-0.008 [-0.063, +0.050]).
* P2 = 0 (same procedure); P5 is non-inferior only trivially.
* Expected PARTIAL (decline to bridge); got CONFIRMED.
* LLM arm (gate open): 0.835, 520 deepseek-flash calls, 0.2768 USD; no increment over
  `maestro` or the corrected lookahead.
* Post hoc:
  * The lookahead's loss is a greedy-batch baseline defect: 29% of its bridge queries were
    measured.
  * The corrected rule ties exploit on Beat AML (0.850). On PRISM 19Q4 the correction is neutral
    (+0.025 line, −0.046 lineage holdout).
  * The correction is development-grade.
* The process report misstates `maestro`'s wasted wells (`DEVIATIONS.json`).
* 0 wells purchased; 2 assay rounds per sample for `maestro` (about 72 h more); about 354 MB
  downloaded.
* Additional events: 442 against 404 for `vc0`, about 7.3 per 100 samples under the event
  definition; 44 samples improved, 27 worsened. This is not a 7.3% patient benefit.

2026-10-17: [Research-method transfer programme](../log/RESEARCH_PROGRAM.md)
and [thin-loop audit](../log/program_review_20261017/LOOP_AUDIT.json).
Engineering diagnosis only: committed HEAD and current working copy both select
A -> B -> C under all-H1 and all-H2 synthetic feedback. Smoothed same-label share
is 17/18 after 16 observations and 0.95 after 18; it is not a calibrated scientific
posterior. No automatic future-score update was implemented or validated.
No new biological experiment, procedure-value fit, paid provider call or sealed
outcome opening. Preserve previous scientific verdicts; cross-task procedure
learning, dual-core interaction and selected-candidate reliability remain tests.

2026-10-16: [Anchor-purchase study](anchor_purchase_20261016/REPORT.md),
**BLOCKED_INDEPENDENT_ENDPOINT / DEVELOPMENT_ONLY_TECHNICAL_REPEAT**.
794 cores, 792 connectivity identities, 343 components, five grouped folds;
564 metadata contexts, 199,259/447,816 unknown pairs retained. Inner-selected
context means: 1,113 known top-4 hits, 888 unknown nominations. Unpriced X1
reference: 1,357, 855 unknown; difference +0.3073/drug [0.2309,0.3847], conservative
missing bounds [-0.8111,+1.3841]. X1 vs shuffled +0.5050 [0.4297,0.5840].
Scalar offset cannot change ranks; assumed information costs 1/2 reduce known
hits to 853/605 at the same four-unit ceiling. Oracle known-hit headroom remains,
but no scalar action achieves it and no independent endpoint or actual bundle
price is authenticated. No residual model, selective policy or LLM run.
0 paid calls/assays, 2,501,144 successful retrieval bytes, 29.281 evaluation CPU
seconds. Independent trace/source reconstruction passed; verifier-only amendment
and initial metadata failure retained. Previous PRESAGE NO-GO remains unchanged.

2026-10-16: [PRESAGE-inspired pathway transfer P0](presage_transfer_20261016/REPORT.md),
**NO_GO**, historically exposed PRISM 19Q4 development, 4,528 drugs / 568 lines /
1,145 family-connectivity clusters, 5 outer folds, 20 correspondence permutations.
Pathway Pearson 0.116137; chemistry 0.144958; chemistry+MoA 0.113347.
Increment over chemistry+MoA +0.002791, clustered CI [-0.001964,+0.008300],
below frozen 0.01 requirement. Null mean 0.111472, randomisation p=1/21;
nominal correspondence signal does not pass the useful-increment gate.
Top-3 historical viability hits: pathway 1,903 vs ungated neighbours 2,223 at
13,584 slots each; diagnostic yield difference -2.36 points [-4.00,-1.12].
P1/P2/P3/LLM/sealed confirmation NOT_RUN. 75.63 s evaluation wall, 0 provider
calls, 0 purchased assays, 0 paid USD; public retrieval recorded separately.
Protocol, initial failure/amendment, freeze, real predictions, source/split manifests,
RESULTS and executable verifier retained. No previous outcome relabelled confirmation.

Latest addition (2026-10-14): [mechanism-falsification feasibility and contract repair](mechanism_falsification_20261014/README.md).
Not an experiment: ASSET_BLOCKED (A0 INSUFFICIENT_MECHANISM_TRUTH; 0 measured mechanism references locally).
Strict decision contracts reproduce-and-fix five P0/P1 defects (35 tests); a 21-task benchmark is specification
conformance only; conformal selection FDR was exceeded on exposed data (exploratory).

Previous addition (2026-10-13): [orbit-contrast evidence admission](orbit_contrast_20261013/README.md).
Pre-registered, frozen (21 files) and validated once on exposed L1000 GSE92742, outer folds 1-4;
exploratory replication grade. A': cold-start compounds, 392 compounds / 805 active cells. B:
unseen-gene shRNA knockdowns, 3,481 genes. Identity-attributable accuracy is
Delta_id = score - score(null-invariant orbit model).
- V1 self-knockdown +0.0998 [+0.0884, +0.1114] PASS; V2 relabelled Delta_id -0.0002 (A' and B)
  PASS.
- H1-A' +0.0104 [+0.0074, +0.0140], p < 1e-4, PASS. The orbit-mean part adds +0.0010; know
  ablation +0.0099; genetic ablation +0.0005 [-0.0001, +0.0011] -> MECHANISM_CLASS_ONLY.
- Sign flip reverses the genetic identity contrast (+0.0291 -> -0.0303): real, but redundant.
- H1-B +0.0005 (p 0.15, power 1.00) FAIL.
- H2a F - R: A' -0.0045 [-0.0071, -0.0019] (significantly negative), B -0.0001.
- H2b F - C': A' +0.0001, B -0.0001. Both FAIL.
- Identity-gate Spearman equals the accuracy gate's (know 0.139 / 0.129; genetic -0.021 / -0.007).
Verdict IDENTITY_WITHOUT_METHOD: no methodological originality.
Task C (exploratory, hashed addendum D5), target triage at 10 assays per compound, 1,148
compounds, hits@10:
- random 0.012, degree prior 0.434, chemical-neighbour transfer 0.984;
- raw connectivity 0.017, CMap z 0.017, orbit-contrast 0.019, OCEA-admitted 0.186 (via the
  prior fallback); F - P -0.247.
Task C: NOT_SUPPORTED.
Deviation D4: the frozen S2 entry crashed in controls before any output; reran via a one-call
wrapper, deterministic. Also added: freeze-schema validator fix with regression tests, an
asset-free CI workflow (not pushed), and an [evaluator audit](evaluator_audit_20261013/README.md)
(corrections C1-C7).
Status: OCEA NO-GO; Brief 5's M3 - M1 INSUFFICIENT EVIDENCE (DepMap Achilles 218.3 MB not
authorised); PRISM 24Q2 stays sealed. Nothing promoted. 0 wells, 0 provider calls, no
downloads. Default suite: 858 passed.

Previous addition (2026-10-13): [knowledge reality](knowledge_reality_20261013/README.md).
Exploratory gate on exposed PRISM 19Q4. Setup: 4,528 compounds in 5 MoA-family folds, 1,460
active; T0 strict cold start; endpoint the per-compound r of the selective profile; 20 seeds of
each knowledge control.
- G1: know_full - chem_full +0.0056 [+0.0028, +0.0085], p < 1e-4, passes.
- G3: specificity +0.0056, passes.
- G2: fails. The gain is above every degree and set-permutation null (gain -0.0001), but equal
  to the gene-relabelling null (+0.0057, empirical p 0.95).
- Reading: the gain is mechanism-class membership, not target biology in context.
- No measurable gain from typing, provenance, context or T1 engagement edges:
  - know_full vs rkt_full +0.0003 (p 0.27), vs annot_full +0.0007 (p 0.20);
  - target-context route alone r 0.009;
  - strict new targets +0.0007 (p 0.39);
  - after a primary screen +0.0004 (p 0.063), on r 0.20.
- Decisions, descriptive: 143 vs 142 selective events per 1,000 nominations; 141 vs 108
  secondary-confirmed; annot_full 161 / 154.
Sealed PRISM 24Q2 REP.1M protocol (1,229 compounds) frozen, not run: gate FAIL, and power 52%
(762 actives needed, about 396 expected). Status: knowledge biology NOT_SUPPORTED; confirmation
NOT_RUN; LLM layer not built (stop rule). Promoted: `maestro.information_tier` only.
0 wells, 0 provider calls; the 24Q2 outcome file has not been downloaded. Default suite: 848 passed.

Earlier addition (2026-10-13): [selective hit triage and decision review](selective_hit_triage_20261013/README.md).
PRISM 19Q4 primary screen triaged at 16 CTRP v2 confirmation curves and 4 PRISM secondary
dose-responses per 16-compound campaign; 128 sealed test compounds in 8 campaigns, split by
mechanism family; frozen and run once; validated selective hit = CTRP AUC robust z <= -2 and
top-dose viability <= 0.5. P1 MAESTRO 22 vs D3 12 (+10 [+4, +18], p 0.004) CONFIRMED; P2
MAESTRO_LOOP 23 vs CONV_LOOP 18 (p 0.18) NOT_CONFIRMED; post hoc ML+context 38 hits with 0
secondaries (+15 over MAESTRO_LOOP, p 0.004). Decision review: R2 CONFIRMED (predictions
admitted as evidence: 15 vs 3 false NO-GOs; 13 of 29 prediction vetoes confirmable); R1
NOT_CONFIRMED (vetoed 3/23 vs 15/42 confirmable, p 0.045); acquisition +1, re-rank -1.
Development was dominated by one 56-compound kinase family (82% of validated signal; pairs
with z_r <= -3 validated 30% vs 9% on test). Post-opening correction: the frozen reader
divided test viabilities by 100; registered endpoint restored and disclosed; VC+S read 98
secondaries but booked 0. Status: retrospective independent-platform confirmation on
exposed sources; agentic advantage NOT_SUPPORTED. Promoted contracts only. 0 wells, 0
provider calls; LLM arms NOT_RUN. Default suite: 843 passed.

Earlier addition (2026-10-13): [collaboration limits](collaboration_limits_20261013/README.md).
Frozen before the fresh GCP lines (A549, NPC, Astrocyte) were downloaded and run once:
65 references, 47 queries, 141 (query, line) decisions, A375 anchor. Ranking follow-ups by
calibrated P(hit) instead of the largest standardised prediction raised per-line hits from
55 to 77 (+15.6 points [+9.2, +22.7], p 5e-5); calibrated P(hit) at least 0.5 hit 81% vs
38% below (lower bound +0.27). The 14-vs-12 agent gap reversed on the fresh lines (no-agent
7/20, integrated 9/20, n.s.); agent donor sets lowered residual cosine on every tier
(fresh: all CIs include 0). Exploratory L1000 (exposed): same compound in another line,
mapped, carries specific cosine 0.81 against 0.48 for the best between-compound relation;
memory admission gives +0.0037 zero-shot and exactly 0 map utility (single-line hub rows);
self-training raises zero-shot +0.014 but lowers map utility -0.0029. Status: P1/P2
CONFIRMED on the GCP tier; agent benefit NOT_SUPPORTED; memory learning NOT_SUPPORTED.
Promoted `maestro.endpoint_decision`. 0 wells, 0 provider calls. Default suite: 822 passed.

Earlier addition (2026-10-13): [evidence-conditioned GCP transfer](evidence_transfer_20261013/README.md).
Fresh assay source, retrospective public-data study; connectivity-separated 66/27/20
reference/development/test compounds and 34 reference-supported histone features.
LVL3 is centered only on same-plate vehicle controls. Strongest development-selected
deterministic policy: 14/20 directional hits; integrated source-qualified agent:
12/20; conventional agent with the same model/source access: 12/20; agent-only: 10/20.
Integrated-minus-deterministic: -10 percentage points, paired bootstrap 95% CI
[-30, +10], exact paired p=.625. Integrated-minus-conventional: 0 points, CI [-15, +15].
Status: EXPLORATORY; positive dual-core synergy NOT_DEMONSTRATED; no scientific
promotion. Culture independence, mechanism specificity and functional efficacy
are not established. Source disclosure uses a shared live PubChem cache, not an
autonomous new-corpus search. Production campaign persistence passes engineering
checks; it does not establish cross-case learning. Default suite: 815 passed.

Earlier addition (2026-10-13): [context-discrimination research report](context_discrimination_20261013/README.md).
On 702 development-exposed GSE70138 compounds, two-slot RKT acquisition finds 158
activity-discordant compounds versus 133 for the reference-derived fixed pair
(+3.56 percentage points, paired exploratory 95% CI [0.28, 6.84]); strict-margin
counts are 38 versus 35 (+0.43 points, CI [-1.57, 2.42]). The matched 84-compound
agent pilot finds 10 hits for integrated reasoning, 16 fixed, 15 deterministic RKT,
14 agent-only and 12 conventional LLM+VC. Operational interaction is -11.90 points
(98.75% prompt-batch CI [-26.19, 0.00], Holm p=1). Status: EXPLORATORY; agent benefit
and positive synergy NOT_DEMONSTRATED; independent confirmation NOT_RUN; no promotion.
71 DeepSeek Flash requests, usage-priced estimate USD 0.03996, conservative reservations
USD 0.71, no new laboratory experiments. Source/protocol pins and replay verification
pass. Below are the previously registered historical summaries.

These are historical evidence summaries, not results rerun during consolidation. Completed, failed and source-audit packets were retired from the executable tree after consolidation. Original protocols, amendments, receipts and tracked observations remain addressable in Git at `ef49d423fcaa13134dfa1a34b5a7a48c38c70e5b`; retrieve a cited entry with `git show COMMIT:PATH`. This requires repository history and is not a clean-checkout research execution path. No archive or replacement data bundle was created.

| Research question | Data and units | Training/test isolation | Main control | Metric and effect/interval | Status | Limits | Entry |
|---|---|---|---|---|---|---|---|
| Collaboration limits: why did agent arms trail the deterministic GCP model, and is the follow-up decision aligned with the hit criterion? | GCP histone peptides, 24 h, LVL3 minus same-plate DMSO median; fresh lines A549, NPC, Astrocyte with A375 anchor; 65 references, 47 queries (27 development, 20 test), 37 features, 141 per-line decisions. Exploratory: exposed Block Q L1000 tier (702 compounds, 1,105 active cells) | Frozen 2026-10-13T03:48:57Z (8 digests) before fresh plates were downloaded; decision model fitted on fresh reference leave-one-out only; agent donors re-decoded from cached frozen sets (no new calls); one-shot evaluation with tamper refusal | Frozen z decoder on the same forecast; raw-scale decoder; no-anchor reference-mean zero arm; no-agent blend vs integrated, conventional, agent-only and pre-disclosure donor sets; no-memory and shuffled-memory arms | P1 per-line hits 77/141 vs 55/141, +15.6 points [+9.2,+22.7], p 5e-5 PASS; P2 calibrated q>=.5 hit .815 (54) vs .379 (87), bound +.272 PASS, CITL -.031 [-.108,+.050]. S2 scale alone +20 (p .0002), uncertainty beyond scale +2 (p .68). S3 agent donors -.008 to -.024 residual cosine, all CIs include 0. S4 frozen endpoint no-agent 7/20 vs integrated 9/20. S5 anchor 77 vs 53. L1000: one-line .528, no-anchor .360, oracle donor .600; +.003-.005 per 64-compound campaign | PARTIAL: decision alignment CONFIRMED (GCP); agent donor value NOT_SUPPORTED; memory learning NOT_SUPPORTED | Retrospective public records, now exposed; all seven GCP backgrounds opened at 24 h. Connectivity split, not mechanism-family. Replicates are plate records, not cultures. Endpoint rewards generic responders. Platt slope .45 fresh vs .80 development: refit per line set. L1000 analyses post hoc on exposed data | `research/collaboration_limits_20261013/README.md` (untracked; cite by commit once committed) |
| Block Q routed knowledge transfer: does certified multi-route transfer predict unprofiled compounds' responses, and do certificate-planned wells beat fixed designs and LLM agents? | Sealed GSE70138 tier: 702 compounds absent from GSE92742, 7 lines, 4,808 cells, 1,105 active (23%) on 348 compounds; reference atlas 979 compounds; 11 equal-well campaigns of 63-64 compounds | Meta-models fitted on GSE92742 only; frozen 2026-10-12T12:24:32Z (34 digests) and run once; phase-2 exposure in belief planning (38 compounds), blocks N and P disclosed; no deviations | Generic direction, best single route, monolithic knowledge ridge, applicability distance; zero/generic/VC-only, dense and sparse fixed designs, activity-greedy, route-blind uncertainty, three deepseek-flash agents, oracle | Virtual cell, one profiled line (Bonferroni one-sided alpha .00714): pooled vs generic +.218 [+.202,+.235]; pooled vs context route +.033 [+.015,+.052], p=.0003; AURC .347 vs .428 for applicability. Unprofiled compounds: +.050 vs generic, +.025 vs monolithic. Campaigns at W=N: planner vs sparse_hub -.044 (0/11) FAIL; planner vs activity-greedy +.034 (10/11), p=.001; planner vs ReAct+VC +.024, p=.029 FAIL; sparse_hub vs dense +.181 (11/11), p=.0005. At 2N, planner vs sparse_hub +.053 (10/11). $0.32 for 214 calls | PARTIAL: VC SUPPORTED, decision NOT_SUPPORTED | L1000 landmark 10 uM / 24 h only. The confirmation tier was three times as active as development (23% vs 7%). Regime-B P(active) is under-predicted (.132 vs .23, AUROC .64). The coverage-beats-planning reading is post hoc. LLM fallback cells: 63/702 (no VC) and 48/702 (ReAct) | `research/knowledge_transfer_20261012/README.md` (untracked; cite by commit once committed) |
| Dual-core adaptive scientific decision | {'reference_compounds': 701, 'calibration_compounds': 281, 'test_compounds': 421, 'test_mechanism_clusters': 211, 'descriptive_active_compounds': 101, 'paired_secondary_compounds_vs_gp': 116}; Previously exposed public Block N L1000/PRISM inputs; reference 701, calibration 281, algorithm test 421 compounds. | Exposed retrospective replay, no LLM calls | Strongest calibration-selected Gaussian batch; same-posterior batch | Adaptive minus Gaussian batch +0.0021701; Holm p=0.40643. L1000 contribution +0.0315567 (Holm p=0.00690), true versus shuffled feedback +0.0733459 (Holm p=0.000150). Same-posterior adaptive-minus-batch +0.0083965, CI [-0.0041235, +0.0209354], secondary p=0.09615. Secondary utility does not confirm and active-subgroup coverage fails.; interval {'level': 0.95, 'lower': -0.015619487782731546, 'upper': 0.019697150473565544, 'scope': 'Nominal paired drug bootstrap for registered adaptive-minus-Gaussian utility; Holm correction is applied to three primary one-sided p-values; mechanism-cluster sensitivity retained separately.'} | NOT_SUPPORTED | Retrospective exposed data, known line identities, empirical surrogate, non-causal mechanism labels, no LLM attribution, marginal but not active-subgroup calibration, secondary transport unconfirmed, simulated turnaround costs. The information controls establish content value within this replay rather than adaptive necessity. | Historical `ef49d423fcaa:research/dual_core_scientific_20261011/experiment/TEST_RESULTS.json` |
| Block O feasibility reversal | 247 exposed killers; 8-unit smoke comparison | Unregistered, no sealed confirmation | Fixed viability, fixed mixed, adaptive viability/mixed | At budget16: adaptive viability .210, fixed mixed .177, adaptive mixed .169; the 8-unit smoke result had the opposite sign | EXPLORATORY | Small feasibility screens can reverse signs; not independent verification or an Agent benefit | Historical `ef49d423fcaa:research/astra/selective_discovery_20261011/preserved/README.md` |
| decision_interface_engineering_20261011 | Asset-free contract fixtures and configured-provider synthetic response scenarios.; units {'real_http_requests': 4, 'offline_response_replays': 6, 'provider_reported_tokens': 4896} | Previously exposed/source-processed; independent biology false | Existing budgeted/expected coverage and discrimination defaults retained. | Final rule/table-binding scenarios pass offline with zero new HTTP. Four historical live calls preserved; deterministic gate overrides flat-value proposal, all-flat and external shift refuse, no real measurement result or budget spend. Production routing/report prototypes are byte-identical to research contracts.; declared resources {'provider_reported_tokens': 4896, 'actual_http_requests': 4, 'measurement_spend': 0, 'monetary_api_cost': None} | ENGINEERING_ONLY | Myopic hypothesis-decision loss is distinct from research PRISM top-10 utility. External evaluation authority remains responsible for scientific calibration and transport. No incremental LLM benefit. | Historical `ef49d423fcaa:research/SCIENTIFIC_STATUS.json` |
| budgeted_feedback_20261011 | Previously exposed PRISM/L1000 replay; 701 reference and 281 exposed development compounds; units 421 | Previously exposed/source-processed; independent biology false | Frozen prior/batch comparisons; see historical protocol | 0.0008215856065202175; interval [-0.011024442595345508, 0.0129016256651586]; declared resources Declared scenario: cap18, read1, turnaround2; batch16 vs at most4+10; real monetary costs unestablished | NOT_SUPPORTED | Post hoc reliability audit, not reliability-gated purchasing; active coverage .6733; secondary paired n120 fails; no LLM calls or independent biological confirmation | Historical `ef49d423fcaa:research/budgeted_feedback_20261011/README.md` |
| context_probe_20261011 | Published ComBat-normalized PRISM HTS exactly 2.5 uM, reference-qualified known drugs; public basal expression; units 106 | Previously exposed/source-processed; independent biology false | Frozen prior/batch comparisons; see historical protocol | -0.011932837213069238; interval [-0.03529999520459789, 0.010252610445252613] | NOT_SUPPORTED | Five incomplete selected endpoints; model-side target isolation after unrebuilt publisher preprocessing; no coverage guarantee, culture independence, real monetary cost or LLM contribution | Historical `ef49d423fcaa:research/context_probe_20261011/README.md` |
| discrepancy_p0_20261012 | Immutable exact-dose PRISM fixed8 predictions/commits; official repeat/pool metadata; original PRISM, CXCL9 and BATCHIE methods; units {'contexts': 106, 'arm_contexts': 636, 'complete_paired_selections': 101, 'complete_fixed_menus': 75} | Previously exposed/source-processed; independent biology false | Frozen prior/batch comparisons; see historical protocol | {"conditional_global_mse_reduction_pct":10.006138141662124,"conditional_boundary_pair_mse_reduction_pct":0.33655535731060837,"conditional_utility_increment":-0.005818119688485129,"prior_exact_realized_regret_n75":0.6369930915118} | NOT_SUPPORTED | Exposed noisy published endpoints, shared publisher preprocessing, five incomplete selections, culture-start hierarchy unverified; oracle opportunity does not establish EVSI, causal mechanisms or real cost-effective gain | Historical `ef49d423fcaa:research/discrepancy_p0_20261012/README.md` |
| replicate_stability_20261012 | Published ComBat-corrected secondary PRISM HTS002 exactly 2.5 uM repeats matched to archived prefeedback primary prior; units {'intended_contexts': 106, 'intended_comparisons': 10600, 'metadata_eligible_comparisons': 292, 'complete_comparisons': 126, 'contexts_with_complete_comparisons': 58} | Previously exposed/source-processed; independent biology false | Frozen prior/batch comparisons; see historical protocol | {"complete_supports_prior":54,"complete_opposes_prior":19,"complete_repeat_conflicts":53,"primary_wrong_complete_pairs":55,"primary_wrong_stable_secondary_pairs":7} | EXPLORATORY | Same-plate complete coverage 1.19% of intended comparisons, joint publisher ComBat, repeated drugs/plates/pools, one missing primary comparison, unresolved culture/exposure provenance; no causal source attribution, full-menu utility, EVPI/EVSI or useful paid feedback established | Historical `ef49d423fcaa:research/replicate_stability_20261012/README.md` |
| Engineering closure: Does the operational agent-to-measurement loop preserve request, budget, result and restart contracts? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Two-round execution, feedback and durable CaseStore behavior pass the asset-free contract suite. | ENGINEERING_ONLY | Operational correctness does not establish biological validity or agent advantage. | Historical `ef49d423fcaa:research/EVIDENCE.md` |
| STATE zero-shot RNA prediction: Does pretrained STATE improve RNA response prediction on checkpoint-held-out contexts? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | M0 error 14.37 versus M2 error 8.50 (x10^-4), about 41% lower; all three evaluation contexts improve. | EXPLORATORY | Only three context units; exposed later; RNA is not functional phenotype or mechanism. | Historical `ef49d423fcaa:research/astra/zeroshot_context_20261007/` |
| Boundary acquisition: Does boundary-aware acquisition improve the equal-budget result over KG? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | M2 boundary, residual, design and no-stop all match KG: mean B utility 0.15966294 at 65 simulated profiles; no savings. | EXPLORATORY | Five previously exposed contexts; simulated RNA endpoint, not independent cultures or phenotype. | Historical `ef49d423fcaa:research/astra/boundary_acquisition_20261007/packet2/` |
| MAP released-weight/native-forward audit: Can the released checkpoint support an authenticated native STATE-SE RNA comparison? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | A prior audit recorded strict tensor loading and a finite native forward; no response comparison was produced. | BLOCKED | External weights, source, compatibility packages and Tahoe metadata are absent from a clean checkout; output order and training-time semantics remain unresolved. | Historical `ef49d423fcaa:research/astra/map_release_test_20261008/ASSET_MANIFEST.json` |
| STATE readout repair: Does a drug-shared readout gain improve prediction and final selection? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Recorded development result: reference outer MSE improves 2.17%; five-target MSE improves 7.84%; final equal-budget selections match M2. | BLOCKED | Development only; contexts previously exposed; Tahoe feature-name metadata is missing in a clean checkout. | Historical `ef49d423fcaa:research/EVIDENCE.md` |
| STATE joint-feedback repair: Does joint A/B error feedback help prediction and acquisition? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Recorded result: matched-information reference utility rises 5.10%; adaptive target utility falls 0.87%; target posterior MSE improves descriptively. | EXPLORATORY | Exposed targets and overlapping pretraining; no independent transfer or decision benefit; generated results are ignored. | Historical `ef49d423fcaa:research/EVIDENCE.md` |
| Decision value / no-screen: Does screening earn its cost versus no-screen under strict complete-context LOO? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Recorded result: Joint KG is 0.0000544 above no-screen and uses eight additional measurements; strict EVSI refuses purchases. | EXPLORATORY | RNA-only utility, 43 evaluable reference contexts, no independent model-risk or cost contract; generated results are ignored. | Historical `ef49d423fcaa:research/astra/boundary_acquisition_20261007/packet2/` |
| Risk-calibration failure: Can the fixed policy certify useful marginal and conditional decision risk? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Recorded result: no conditional threshold is certified; marginal coverage is 2.6% to 3.4%, below the 20% gate. | BLOCKED | Exposed, class-stratified units do not establish the IID deployment assumption; prepared inputs are ignored local outputs. | Historical `ef49d423fcaa:research/viability_contrast/run10.py` |
| MAP-KG knowledge-layer content: Does the cached knowledge representation retrieve known targets better than structural controls? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Knowledge hit@5 is 11/44; molecule encoder 9/44; Morgan fingerprints 13/44; identity permutation 1/44. Explicit-mode hit is knowledge 6/30 and Morgan 6/30. | EXPLORATORY | Graph exposure during encoder pretraining is possible; unknown annotations are not negatives; protein shared-space, RNA utility and agent benefits are not tested. | Historical `ef49d423fcaa:research/knowledge_layer_validation_20261009/` |
| MAP feedback replacement and scarcity: Does knowledge-conditioned feedback improve matched-budget RNA selections, including sparse historical labels? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Full-history knowledge mean B is 0.164912 versus empirical 0.164965. With eight histories, knowledge exceeds empirical by 11.17%, but does not reliably exceed molecule, Morgan, shuffled knowledge or no-screen. | NOT_SUPPORTED | Unchanged pretrained STATE cache; exposed RNA development units; repeats grouped within backgrounds; reduced harmful updating is not knowledge-specific biology or net information value. | Historical `ef49d423fcaa:research/map_module_replacement_20261009/` |
| MAP agent source acquisition: Does typed context improve source qualification and bounded tool choice under missing records and noisy priors? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Easy task: all arms 12/12. Hard task: lexical 27/72 exact, typed 26/72, deterministic 72/72. Typed improves positive card/mode fields but schema and routing failures remain. | NOT_SUPPORTED | Repeated twelve exposed source cases; most violations are null Boolean fields under an underspecified prototype prompt; no measured engagement or whole-agent advantage. | Historical `ef49d423fcaa:research/map_module_replacement_20261009/agent_trial/` |
| Released MAP protein and relation content: Does original shared-space and ordered fusion recover source-known targets better than simple controls? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Plain molecule/protein hit@5 is 3/44. Generic outgoing relation hit is 5/32, equal to structural votes and below popularity 6/32; incoming is 12/32. Canonical name anchors reach 25/32 and 26/32. | NOT_SUPPORTED | Possible graph pretraining exposure; target-enriched gallery; directions fixed and reported separately; native RNA decoder remains unauthenticated. | Historical `ef49d423fcaa:research/map_module_replacement_20261009/asset_audit/` |
| Conditional pairwise correction: Can condition-bound knowledge and one shared A observation improve frozen boundary comparisons? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | At eight histories, knowledge+feedback regret 0.00653089 versus no-update 0.00640195; 43 corrected/51 harmful flips. All 6,192 policy rows independently reconstructed; portable cached replay exact. | NOT_SUPPORTED | Exposed RNA development, STATE overlap and no independent cultures. Four-history support gate structurally disables feedback. Sixteen-history mean-only signal remains descriptive. | Historical `ef49d423fcaa:research/decision_value/pairwise_20261009/` |
| Dual-source residual transfer v3: Does one A observation add decision value after correcting both conditional means and refitting their residual dependence? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | All 3,870 rows independently reconstructed. At eight histories, feedback adds 0.0000128654 over its mean-only model, nominal CI includes zero; no update remains slightly better. Prebuy stop saves 94/129 A purchases with unchanged matched-arm actions. | NOT_SUPPORTED | Previously exposed RNA units, transductive public-state geometry, insufficient feedback coverage and no independent risk or knowledge-specific benefit. | Historical `ef49d423fcaa:research/decision_value/pairwise_v3/` |
| Observation reliability P0.5: Can control-only source comparisons authenticate the 39 endpoint coordinates before a scalar-noise audit? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | 448 DMSO cells; 27/39 unique matches in c40 and 34/39 in c44. Offline reconstruction passes; the complete identity certificate fails and 250 noise cells remain unopened. | BLOCKED | Sparse/all-zero coordinates are unidentifiable, not contradicted. No endpoint variance, full-axis/checkpoint certification or A/B cause is established. | Historical `ef49d423fcaa:research/decision_value/observation_reliability/axis/` |
| Source-time/repeat qualification P0.6: What source timing and repeat units are actually supported, and which cheap diagnostic channel should be proposed? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Tahoe methods authenticate global 24 hours and author-described plate6/14 biological repetition; exact sample joins pass. The revised six-treatment c44/c45 proposal needs 6.144 MB future RNA. | EXPLORATORY | Pooled line partitions are dependent; per-sample timestamps and a third confirmation source are absent. No treated expression, channel gain or LLM advantage tested. | Historical `ef49d423fcaa:research/decision_value/observation_reliability/literature/SOURCE_QUALIFICATION.json` |
| Public ordered-axis search P0.5R: Is an authoritative ordered axis available for the precise filtered dataset and checkpoint? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Official static 2,000 list agrees with all 39 historical positions and earlier unique matches; pinned checkpoint metadata names 62,710 full genes but omits the ordered subset. | EXPLORATORY | List agreement is not exact release lineage, per-file identity or decoder certification. | Historical `ef49d423fcaa:research/decision_value/axis_recovery_20261010/authority/` |
| Informative paired-axis recovery P0.5R: Can expression-guided source conditions make all 39 coordinates uniquely identifiable in c44/c45? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | First pool lacks support; supplement screens 3,354 QC cells and reads 74 paired cells. All endpoints meet two/one nonzeros, but only 16/39 c44 and 23/39 c45 uniquely match. Combined calibration 24,533,272 known body bytes. | BLOCKED | Remaining trajectories are nonunique, not contradicted names. Adaptive cell-level holdout is not culture independence; no gate relaxation or P0.6 release. | Historical `ef49d423fcaa:research/decision_value/axis_recovery_20261010/calibration_v2/` |
| Direct-name control observation P0.5R: What does gene covariance do to a separately named 39-gene control scalar? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | 224 retained c44 controls, 28 groups, actual n=8; full/diagonal variance ratio median 1.473, range 0.709–3.731; independent vectors/bootstrap reproduced. | EXPLORATORY | Only one unadjusted interval wholly exceeds one; no culture-level noise, old endpoint equivalence, treated reliability or decision gain. | Historical `ef49d423fcaa:research/decision_value/axis_recovery_20261010/named_channel/` |
| Axis selection diagnostic: Did positive-coverage allocation omit identifying zero contrasts? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Full retained support patterns are unique for all 39 genes per file; a heuristic adds 11 discovery rows per file, with fixed holdout and projected paired cost 340,068 bytes. | EXPLORATORY | Binary presence need not equal numerical nonzero; this closed diagnostic reads no extra RNA, its numerical gate remains failed, and its row count is not proven minimal. | Historical `ef49d423fcaa:research/decision_value/axis_recovery_20261010/calibration_v2/diagnosis/` |
| Measure or predict (block K): Can a frozen virtual cell's 24 h forecast replace measurement for a 5-day decision, and is any failure a ceiling, transport or timing failure? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | MIX-Seq, 48 lines: measurement over the DepMap prior -0.021 [-0.109, +0.078]; STATE -0.091 [-0.182, -0.005]. Same-line cross-platform response r 0.13 or less versus within-platform 0.65. Trametinib 5-day information appears at 24-48 h (+0.16 at 48 h). Tahoe early state below the prior (USE_PRIOR confirmed). | NOT_SUPPORTED | Six drugs; one time-course drug; small cell counts; unpaired evaluator estimand (verdicts unchanged when paired); candidate gene order supported, not certified. | Historical `ef49d423fcaa:research/astra/kinetic_horizon_20261010/` |
| Mechanism falsification (block M): Can an LLM agent plus a world model falsify mechanism hypotheses with calibrated error, design falsifying observations and detect inadequate hypothesis sets? | See result and limitation | Sealed compounds/classes; source preprocessing already published | Controls stated in result; historical protocol | 502 sealed L1000 drugs, 424 classes, four profiles: coverage 0.892 [0.862, 0.917] but 0.776 in the most active tier (n 49). Class content -19.0 [-29.2, -8.6] survivors. Every knowledge, design, identifiability and adequacy test not supported. Agent alone coverage 0.00; credible sets 0.217. | NOT_SUPPORTED | Four profiles at one dose; class-level labels; 49-drug active tier; set-size knowledge contrasts nearly permutation-invariant; 100-drug LLM arms; L1000 exposed in earlier blocks for other estimands. | Historical `ef49d423fcaa:research/astra/mechanism_falsification_20261010/` |
| Selective discovery campaigns (block P): Given a library profiled only by L1000 and a screening budget, does the virtual cell contribute selective-killer discoveries annotation cannot anticipate, and does the agent loop contribute yield the virtual cell alone cannot reach? | See result and limitation | Sealed compounds/classes; source preprocessing already published | Controls stated in result; historical protocol | 38 campaigns on 975 sealed compounds, 1,216 screens per arm: virtual cell +17 unexpected hits [+11, +23] p 0.00098 (10 of 10 informative lineages, none opposed), +46 over a fixed workflow, +28 verified on the secondary screen; agent loop +14 total hits p 0.075 at 7x the turnaround, level on novelty, and matched by a conventional agent-with-tool loop (136 vs 141 hits); feedback +12 fails family-wise; portfolio -1. | NOT_SUPPORTED | One assay/dose/platform; novelty is annotation-relative; no mechanism claimed; verification conditioned on the activity-enriched secondary subset; no refusal path exercised. | Historical `ef49d423fcaa:research/astra/selective_discovery_20261011/` |
| Mechanism routing of killing profiles (block N): Does an LLM add value to a virtual cell that predicts which lines an unseen compound kills, beyond target, chemical and partial-screen baselines? | See result and limitation | Sealed compounds/classes; source preprocessing already published | Controls stated in result; historical protocol | 421 sealed drugs (101 killers): VC transfer beats targets +0.116 [+0.053, +0.181] and chemistry +0.100 for unseen classes, replicates on the secondary screen (+0.103), adds to a 160-line screen +0.049; trust by similarity +0.097. Agent forecaster, critic, explainer and trust judge: no gain; critic -0.052 and forecaster+VC -0.025 harm. | NOT_SUPPORTED | One assay/dose; class-level novelty; 101 killers; memorised PRISM knowledge not excludable; one frozen check failed on a CSV tie (no verdict change). | Historical `ef49d423fcaa:research/astra/mechanism_routing_20261011/` |
| Historical union and targeted axis extension: Can exposed c44 bytes and eleven explicitly discriminating c45 rows complete the data-coordinate gate cheaply? | See result and limitation | Recorded development/source audit; exposed units are not independent confirmation | Controls stated in result; historical protocol | Both files pass 39/39 unique matches among all 62,710 genes at 1e-5. c44 adds 0 bytes; c45 receives exactly 133,564. Separate logical-slice/blockwise reconstruction agrees; 3,334 protected old files unchanged. | BLOCKED | Historical/adaptive coordinate evidence; exposed consistency is not fresh validation. Initial parser failure preserved with a zero-download offline amendment. Full 2,000/checkpoint axes and P06/P2 execution remain unqualified. | Historical `ef49d423fcaa:research/decision_value/axis_extension_20261010/QUALIFIED_CERTIFICATE.json` |

## Source identity and refusal boundaries

The c44/c45 endpoint39 certificate used `arcinstitute/State-Tahoe-Filtered` revision `fdf87abece385feea6fa5e9944ab46e173b6af50`, `log1p(stored normalized X)` once, and absolute tolerance 1e-5. Maximum errors were 1.441582098138383e-7 and 1.4611107745921004e-7. Certificate SHA256: `b5d4c1e70f5308d54173e7900e6678d12e6c0faa1e90e92355b3fa91f8c0e379`. This certifies 39 file-local coordinates, not full2000/checkpoint axes, culture independence or P0.6 release. The initial parser failure and zero-download amendment remain historical failures.

The repeat audit fixed 106 contexts and 10,600 intended comparisons: 292 metadata-eligible, 126 complete, 54 supporting prior order, 19 opposing and 53 conflicting. Of 876 expected repeat-pair differences, 414 were missing; 130/462 observed nonzero differences disagreed. Complete-menu coverage was 1.19%; context-macro discordance 26.95%. Seven of 55 primary-wrong complete comparisons opposed the prior in all secondary repeats; pair and context estimands differ. Shared released ComBat and plate/pool dependencies preclude independent raw/culture confirmation. No inference interval was introduced.

Discrepancy P0 rebuilt 636 records: conditional global MSE improved 10.006%, boundary-pair MSE only .337%, terminal utility -0.0058181 (44 improved,45 harmed,12 unchanged). Exact prior regret .6369931 covers only 75 full menus; 31 oracles remain null. Observed-subset regret lower bound .7193264 on 101 selections is a different population, not EVSI. Official metadata downloads totaled 5,322,352 bytes; original primary/secondary repeated-treatment groups numbered 3,947/1,489. Culture-start hierarchy and QC remain unresolved.

CXCL9 source correction: DOI `10.1038/s44320-026-00221-w` measures 24-hour supernatant secretion with LEGENDplex capture beads/FACS PE. Bead events and technical duplicates are not independent cells; two BxPC3 screenings do not authenticate matched apoptosis/viability or Caspase-3 pairing. Source-access failure is not evidence of absence.

RNA forecasts, measurements, references and derived analyses retain different origins. RNA is not viability, apoptosis, protein engagement or causal mechanism. Public processed-file replication, numerical reconstruction and repeated source copies do not create independent biological units. Declared read/turnaround prices are scenarios, not authenticated invoices. Fixed8, P2 and independent dual-core superiority remain unreleased. Missing assets are BLOCKED, distinct from a failed scientific gate.

The adaptive replay had 62.38% active-drug interval coverage and failed secondary confirmation. Phenotype reference-oracle gain was .003, below MUB .05. These failures are not repaired by consolidation.


## Temporary-history conclusions retained before disk release (2026-10-14)

The user requested key experiment records rather than backups. The external
simplification snapshot and temporary-history tree were reviewed, then designated
for deletion in full. This section preserves additional directions, failures,
successes and caveats found there; the numerical register above remains current
where later evidence supersedes an older claim. This is a historical readout, not
a rerun or new validation. Downloaded originals, old source checkouts, presentations,
raw prediction banks, installed dependencies and caches are not preserved here.

### GDSC same-plate phenotype and later-layout transport

- **Question:** does cheap state information improve a decision between Afatinib
  2 uM, PLX-4720 10 uM and PD0325901 0.25 uM beyond a simple background model?
- **Source:** official gdscIC50 example, commit
  `34d842254a33bd04f318449969ff9976237c9295`; RDA SHA256
  `40bc65d4fd9cd61bb8c0faf5fa60ee32a05fccce7eb441cc74e3ed37666ef10a`.
  873,525 native rows / 1,837 plates / 739 lines; selected layout 159.
  Development: 617 plates, 516 donor/parent groups, 48 dates. Confirmation:
  222 plates, 214 groups, 19 later dates, starting 2015-10-22 23:00:00.
- **Result:** density plus background minus background alone was -0.52 ATP
  inhibition percentage points, 97.5% interval [-1.69, +0.65]. The interval upper
  bound was below the predeclared 2/5/10/20-point sensitivity thresholds. Stop
  adding complexity or measurement spend to this tested density input. Background
  alone beat the fixed action by +3.32 points (auxiliary); useful net benefit,
  prospective molecular-state value and State-model advantage remain unknown.
- **Reason/limits:** density did not improve action-difference prediction or
  selected response. Fixed drug positions, later-version background annotations,
  missing all-attempt/QC denominator and unresolved independent culture starts
  limit interpretation. ATP inhibition is not death fraction or mechanism truth.
  Ridge alpha 10 won development selection; random forests earned no advantage.
  888 ledger cases reused 222 historical plates, not 888 independent experiments.
- **Repeat diagnostic:** 43 development lines with different-date repeats had
  +10.90 points [3.90,17.89] when the first reading selected an action evaluated
  on the last. 37/43 reused CELL_ID expansion: assay repeatability only, not new
  parent generalisation, and not a free pre-decision state observation.
- **Transport follow-up:** official GDSC release contained 15,069,449 records;
  expanded CTRPv2 archive had 545 compounds / 12,470,175 raw-well metadata rows.
  CTRP could not supply the exact original menu (nearest 2.1/8.3 uM; no PD0325901),
  so no dose interpolation or substitute drug was admitted. 37 HTTP attempts
  included timeouts, invalid routes, access failures and misleading HTTP 200
  redirects. Access failure is not a negative biological finding.
- **Later layouts 231/284:** 992 metadata-complete scans, 694 overlapping original
  development groups, 98 without unique annotation/identity, 200 selected scans
  on 196 patient/parent units and 41 dates. Only exact PLX/PD pairs qualify;
  this is two-action within-GDSC transport, not three-action independent confirmation.
  Rebuilt original C Ridge reproduced forecasts to 8.326673e-16 without target
  refitting. C2 beat development-fixed PD by +4.207 points (+2.509 / +4.411 by
  layout), but lost 0.961 points to fixed PLX in the labelled post-outcome
  diagnostic. Predictions favoured PD by +3.893 vs measured -5.168 points;
  mean contrast error +9.061, RMSE 26.975. 113 rankings agreed, 86 disagreed,
  one tied. This identifies calibration/transport and comparator weakness,
  not Agent gain; no physical confidence interval or net monetary value certified.
- **Unexecuted next direction:** randomise well positions, independent culture
  starts and all three exact actions, include every fixed policy, and record
  all failures/costs. Initial design: 12 lines / 24 starts / 384 basic wells;
  later generated pilot used 336 terminal + 48 destructive sister wells on
  eight plates across four days. All execution flags were false, outcomes/costs
  empty. The pilot tests feasibility/repeatability, not population policy benefit.
  No physical experiment, RNA acquisition, State forward or LLM call was performed
  in the transport follow-up. Scoped 358-test verification was engineering-only.

Sources: official [raw format](https://github.com/CancerRxGene/gdscIC50/blob/34d842254a33bd04f318449969ff9976237c9295/vignettes/gdsc_raw_data_format.Rmd),
[GDSC protocol](https://depmap.sanger.ac.uk/documentation/datasets/drug-sensitivity/),
and [release 8.5 identities](https://cog.sanger.ac.uk/cancerrxgene/GDSC_release8.5/screened_compounds_rel_8.5.csv).
Temporary source reports were `gdsc_reproduction_snapshot/research/astra/GDSC_SCREEN.md`
and `gdsc_transport_log_addendum.txt`; those copies are intentionally deleted.

### Earlier research directions and their stop reasons

| Direction | Historical outcome | Reason, retained lesson or next requirement |
|---|---|---|
| Belief planning | INCONCLUSIVE; practical +0.02 improvement not supported | Fixed order remained strong. VC changed about 1% of sequences without outcome gain; feedback changed 23% without result gain. Extra measurements/wrong decisions failed cost/safety gates. Conditional readings cannot be treated as independent. |
| Acquisition link / two-step follow-up | Inconclusive / negative; fixed sequence won | Keep directional exclusion probabilities separate from correctness. Reference likelihoods require valid real history. One live request failed with LLMTransportError; no reply or measurement, conservative $0.01 reservation was not a confirmed charge. |
| Early-stop sequence audit | Negative; fallback gain +0.0013 utility | Negligible terminal gain: no promotion merely because more actions changed. |
| Sparse-reference value | Inconclusive | Parent-reference smoothing is a transfer assumption, not recovered true conditional data. QC-passing references omit the all-attempt failure denominator, so economic optimality is unqualified. |
| Dynamic world model | Negative; transition cosine +0.283, decision +0.003 | Prediction improvement did not satisfy decision-promotion gates. |
| Biological depth | Negative; latent model matched PCA | Structure retrieval carried the useful signal; deeper latent modelling did not earn promotion. |
| In-context world | E-WM1/E-WM2 gates passed; promotion deferred | Shared-direction forecast success did not establish discrimination. E-DATA1 decision tier was underpowered (105/314 and 205/714 eligible units); nothing promoted. |
| Dual-core development / protocol v2 | Negative | Selected-action risk and decision/calibration qualification failed; operational wiring does not prove scientific benefit. |
| Dual-core v2 repairs | Engineering repairs verified, no scientific promotion | Risk controls, lineage and transfer-error contracts became research standards; no superior biology demonstrated. |
| Viability contrast v1-v5b | Negative; realistic arms did not certify | World-model contribution was non-binding for this task-policy pair. Reformulate the task before increasing model complexity. |
| Scientific case memory | Engineering contracts verified | Typed append-only records, scoped retrieval, hypothesis graphs and numerical parity do not establish improved terminal decisions. |
| MAESTRO VC memory replay | Negative on 6,601 real episodes; 23/23 screens NO_DEVELOPMENT_SIGNAL | No terminal-decision or calibration improvement. Keep failure cases; adaptation and conditional forecasts help intermediate predictions only. |
| External validation | Negative / external test blocked | MAESTRO VC rejected under frozen development gates; do not substitute exposed replays for external confirmation. |
| Premise forecast | NOT_READY | Zero of 30 required target genes available; stop rather than fabricate an endpoint. |
| Live dual-core API tests | Engineering execution demonstrated; biology inconclusive | Post-fix 1,621 passes still included one historical prose failure and two deselections. Provider response success is not biological efficacy. |
| Dual-core completion | Engineering closure | 21 dataset/version checks; 1,526 passes plus an inherited prose failure. Terminal biological benefit unestablished. |
| Dual-core follow-up | Inconclusive | 19,704 paired policy paths and 44,520 frozen queries; anchor did not establish utility above fixed. All 112 valid-readout forecasts refused without experiment-validity probability. Missing all-attempt denominator cannot be priced by invented QC probabilities. |
| Identifiability audit | Diagnostic research, no promotion | State and case-memory targets/populations differ. Conditional prediction, source uncertainty and validator bottlenecks must be separated; unknown comparisons retain declared utility bounds. |
| ASRG / gated plan / dataset discovery | Design only, not completed experiments | Action-supported repair and capability/menu qualification remain proposed directions. A literature review or plan is not experimental success. |
| Scientific optimisation pilots | Exploratory and superseded | Earlier PASS labels were superseded by later dual-core audits; do not re-promote them from an old draft. |

### Historical provider accounting retained as compact records

| Ledger | Recorded calls | Recorded total USD | Unknown-charge counter | Entry status counts |
|---|---:|---:|---:|---|
| `mechanism_falsification_spend.json` | 3549 | 6.46689198 | 7 | `{"failed_unpriced": 7, "ok": 3542}` |
| `mechanism_routing_spend.json` | 2453 | 7.45753203 | 88 | `{"failed_unpriced": 2, "killed_in_flight_unpriced": 1, "ok": 2450}` |
| `phenotype_anchor_20261010_spend.json` | 5 | 0.0120063 | 0 | `{"ok": 5}` |
| `selective_discovery_spend.json` | 3466 | 1.50627302 | 0 | `{"ok": 3466}` |

These DeepSeek-flash totals use priced usage plus reservations for unknown charges,
not invoices. The mechanism-routing unknown-charge counter (88) differs from its
three failure/in-flight entry statuses; both original counters are preserved without
claiming a reconciliation. Provider costs do not constitute assay costs or science
success. Earlier numerical evidence and failures for Blocks M/N/P and phenotype
anchors remain in the main register.

### Disk-release boundary

Only `D:/MAESTRO-retained/20261014-simplification/` is removed in this release.
Current runtime, nine registered studies, the central evidence register and primary
assets under the active repository remain. The retained-history material is now a
summary record, not a complete reproducible backup. Git history is not rewritten.

Deletion receipt: 4,760 files / 2,952,169,169 logical bytes removed on 2026-10-14;
external retention target confirmed absent. No backup remains in that directory.
