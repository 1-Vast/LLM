# Protocol: dual-core innovation validation on the PTV-1 / ProteinTalks release

Status: FROZEN when `FREEZE.json` exists (sections 1-9 are the frozen text). Public-data replay of an exposed release. Nothing here is prospective laboratory discovery, and no
numerical result of the final stage was seen before the freeze. Dates: study 2026-10-21. No commit, push, purchase, author contact or access
application. Predecessor packages are untouched.

## 1. Capability specification (what is actually tested)

**W - the world model.** Candidate = the published ProteinTalks `ppODE` architecture, re-implemented from the released `model.py` and retrained from scratch
under this study's grouped partitions (hidden width 16 instead of 64 for the CPU budget; classic RK4 in place of torchdyn; MSE masked to quantified proteins;
phenotype loss on single-agent rows only; NaN fingerprint entries set to 0 before the per-vector min-max, because the release code turns the whole fingerprint of
such a drug into a constant).

- Inputs: stock baseline proteome (5,585 proteins, log1p then per-sample min-max, median over the stock's usable 0 h rows), a per-protein perturbation encoding
  that is a *drug-target node flag* (value 0.5 on target nodes, a per-perturbation constant; 23 of 63 single drugs have no target node), and the drug fingerprint /
  physicochemical vector (935 dims; pair rows carry two drugs).
- Predicted readouts: a protein-abundance trajectory at 6, 24 and 48 h (one fixed dose, dose not recorded in the release) and the published sensitive/resistant
  probability. It is a fixed-horizon, mean-profile model: it does not claim single-cell heterogeneity, arbitrary dosing or continuous dynamics.
- The "explicit intervention-state pathway" is a *pointwise* neural ODE over (baseline abundance, target flag) per protein. It has no cross-protein interaction;
  all cross-protein mixing is in the dense phenotype head. For the 23 zero-target drugs the predicted trajectory is a drug-independent function of the baseline.
  The fingerprint reaches only the phenotype head, never the trajectory model.
- What changes after real feedback: nothing in the released method. A feedback update (fine-tuning on revealed support measurements) is a *declared* extension
  tested in Experiment Q and compared with ordinary same-data updating.
- Closest ordinary comparator: a regularised direct predictor on the same information (drug features, baseline PCs, training label rates, baseline-similarity-
  weighted neighbour rate) and the plain drug label-rate prior. If M1 is only a renamed multi-task model of this kind the report says so.

**A - the research program.** An executable Python function `run(env)` (sections 6-7) that decides which candidate to query functionally or molecularly, how to
update after results, and when budget is exhausted. Editable: the whole program body. Not editable: the evaluator, outcome access, action legality, cost
accounting, pool definition. "Program modification" = changing control flow, query-selection logic, update rule or use of the molecular tool; changing only a
numerical constant is parameter refitting and is reported as such. What is inherited between tasks = program *source* (algorithm), not fitted background
parameters or stored examples (a structural check lists numeric literals and dictionary/list literals in accepted code).

**Joint system.** W supplies scores to the program; the program's selected measurements update W only inside Experiment Q. The externally measured benefit is
yield of confirmed sensitive drugs per cost in held-out backgrounds. Algorithmic novelty is **NOT_ESTABLISHED a priori**: all components are existing methods
(neural-ODE proteomics model; LLM-edited programs). The study tests utility.

## 2. Data contract (sections of the release, Section 4 of the brief)

Identity and semantics are in `CENSUS.json` and `SOURCE_MANIFEST.json`. Facts that bound the claims:
- 18 stocks / 17 lineages (MDA-MB-453 and MDA-MB-453(ATCC) are one lineage and always held out together). 63 single drugs, 59 drug pairs, 1,535 cell-by-perturbation
  units (1,110 single, 425 pair), 4 duplicated runs (same label), 7 single-drug labels missing.
- Missing phenotype is missing, never resistant (the release loader would turn it into 0). Zero abundance is protein non-quantification and is masked, never
  treated as a measured level, in all losses and molecular metrics.
- Dose, plate/batch, replicate id, the numerical sensitivity threshold and the meaning of the pair label are NOT in the release; the study is a
  **published-label prediction task**: the label is the authors' 24 h sensitive(1)/resistant(0) call for single-drug rows. The pair label (3.8 percent positive)
  is a different, unauthenticated endpoint with 8 positives outside the sealed lineages: pair-label decision tasks are **NOT_TESTABLE_ON_THIS_ASSET**. Pair rows are
  used only for molecular trajectory supervision/evaluation.
- Vehicle controls at 6/24/48 h exist for 7 of 18 stocks only after a quality screen and are heterogeneous; the intervention contrast is therefore relative to the
  stock baseline (includes time-in-culture), and this is stated wherever used.
- Checkpoint training exposure is UNKNOWN (layout matches this release); the released checkpoint is not used. All models are retrained under the partition.

## 3. Partition and stage gates

Lineage -> {dev, sel, final} by SHA-256 of `lineage|dual_core_20261021` (dev 5: HS578T, HCC1937, MCF7, HCC1806, BT549; sel 5: HCC1143, MDA-MB-468, DU4475,
MDA-MB-453 (two stocks), MDA-MB-231; final 7: HCC1395, MDA-MB-436, HCC38, HCC1187, T47D, BT20, HCC70). Fixed before any labelled analysis.
Stage ledger (`STAGE_LEDGER.json`, write-once). Treated-experiment outcomes (labels, treated proteomes) of final lineages are refused by `ptv_data` until the
`final` stage is claimed, which requires `FREEZE.json`. Baselines/controls of final backgrounds are inputs and stay readable. Everything inspected is
**exposed** (public release; label prevalence by lineage was seen before the partition; dev/sel outcomes are used freely).

## 4. Tasks, contracts and endpoints

Unit of replication = a held-out background LINEAGE (7 final lineages; dev 5, sel 5). Wells, doses, drugs and the two stocks of one lineage are never independent units.
Endpoint = the authors' published 24 h sensitive(1)/resistant(0) call for a single-agent condition (missing = missing). Decisions are made on the **contested pool**
of a background: the available drugs whose label rate over the *other* training lineages lies in [0.2, 0.8] (the all-drug top-5 task is saturated by the drug prior on
development data and cannot distinguish models). A background needs >= 6 pool drugs to enter a precision@5 comparison; exclusions are reported.

- **Task T (unmeasured-target prediction, no functional query).** Nominate k = 5 pool drugs from a score computed from baseline proteome, drug features and training
  backgrounds only. Primary metric precision@5 on the published label. Secondary: AUROC on the pool, Brier score and calibration slope on pooled pool predictions.
- **Task E (end-to-end screening).** Per background a program spends a budget of 5.0 units: a functional (published-label) query costs 1.0, a molecular query (the
  authentic 24 h treated proteome of that condition, projected on 8 training principal components and scored by a conditional predictor g_mol trained on training
  backgrounds) costs lambda = 0.5. Yield = number of DISTINCT drugs whose queried functional label is positive (confirmed positives count once; re-reading a recorded
  result is free and gives no information). All probes are charged; a program may make zero molecular queries. The direct-confirmation comparator is static
  confirmation of the top 5 of the strongest conventional score (B1) under the same budget. Price sensitivity lambda in {0.1, 0.25, 0.5, 1.0} is reported for the
  molecular-using menu programs; no currency is claimed (no prices exist). The hindsight ceiling min(5, positives) is optimistic: label noise is unknown.
- **Pair-label tasks and combination claims: NOT_TESTABLE_ON_THIS_ASSET** (8 positive pair labels outside the sealed lineages; meaning of the pair label not documented).
- **Not claimed:** single-cell heterogeneity, arbitrary dose or continuous-time dynamics, causal pathway mechanism, new biology, prospective discovery.

### Experiment R (world model on the same information; M0-M3)
Models: M0 = regularised logistic direct predictor on [drug label-rate prior, baseline-similarity-weighted neighbour rate, number of target nodes, 8 fingerprint PCs,
3 baseline PCs] (an HGB variant is also computed; LR chosen on sel by pool AUROC 0.733 vs 0.599); comparators B0 drug prior, B1 baseline-similarity-weighted prior
(strongest conventional score on sel, AUROC_pool 0.760: C* = B1). M1 = ppODE (full), M2 = no predicted-trajectory pathway, M3 = no direct fingerprint shortcut. Hidden
width 16, lr 5e-4, batch 32, lambda 0.8, weight decay 1e-4. Epoch counts fixed on sel by minimum held-out BCE per variant: M1 30, M2 30, M3 45
(`RUN/selection/sel_epoch_table.txt`). Final training = dev + sel lineages (10), 7 final lineages held out, seeds 0 and 1; seed 0 is primary, the seed mean secondary.
Interpretation rules (declared): M1 - M2 isolates the trajectory pathway (the fingerprint reaches the phenotype head in both); M1 - M3 removes the fingerprint branch
only, so it measures what the trajectory pathway alone carries and does NOT show that the state pathway is useless if performance is kept (the head still sees the
baseline and target channels); M1 - M0 and M1 - B1 measure whether the mechanism beats a direct predictor on the same information. Auxiliary supervision (trajectory MSE
on measured proteomes of training backgrounds) is an extra training signal that M0 does not receive: a gain over M0 cannot be attributed to the mechanism rather than to
this supervision without a model that shares the supervision but not the mechanism (not built; named as the distinguishing experiment). Molecular skill (authentic
held-out treated proteomes, quantified proteins only): MSE and correlation of the predicted CHANGE from baseline against C1 baseline persistence, C2 baseline + mean
training shift and C3 baseline + drug-specific mean shift; target-node proteins are scored separately. Baseline reconstruction (low MSE from copying x) is not
intervention skill.

### Experiment Q (real feedback) and what it is not
Experiment R (does a predicted state help) does not establish Q. Q: for each held-out background the 3 pool drugs whose training label rate is closest to 0.5
(ties by id) form the support; their published labels (functional feedback, cost 3 F), 24 h proteomes (molecular feedback, cost 3 M) or both are revealed; the declared
update is fine-tuning M1 for 10 steps at lr 1e-4 (func = phenotype head on support labels; mol = trajectory ODE parameters on the support 24 h proteome MSE; both = both
loss terms), configuration chosen on sel by minimum target Brier among {10 x 1e-4, 30 x 1e-4, 30 x 5e-4}. Targets = the remaining pool drugs (>= 6 required), never used
for updating. Comparators on the same support: no update; ordinary same-data updating = fingerprint-kernel residual update of M1, B1 and M0 with gain kappa = 0.25 (chosen
on sel by minimum Brier among {0.25, 0.5, 1, 2}); conditional predictor g_mol fed a kernel-imputed measured state. Observation noise vs shared-parameter uncertainty: one
fine-tuned model per background, no posterior is claimed; metrics are evaluated on published labels. The architecture has no cross-protein interaction and the
fingerprint never reaches the trajectory model, so molecular feedback can reach the phenotype only through target-flag proteins (23 of 63 drugs have none); this is a
declared structural limit of Q on this model.

## 5. Agent arms, search budgets and LLM use

Hold one qualified world model fixed per cell of the 2x2: W0 = M0 logistic direct predictor, W1 = M1 seed 0. A program is Python source `run(env)` executed in a fresh
numpy-only interpreter with AST checks (no imports, no private attributes, restricted builtins, 60 s timeout, process faults retried); the evaluator, outcome access,
action legality and cost accounting are outside editable code.
- **A0** (strong fixed procedure): confirm the top 5 by W, static. Fixed by the pre-declared rule "kappa maximising mean development yield over W0, W1, B1; ties to the
  smaller kappa": kappa in {0, 0.25, 0.5, 1, 2} gave 9.0 for kappa 0 and 9.0 for kappa 1 on dev, so kappa = 0 (`RUN/selection/a0_kappa_grid.txt`).
- **A1** (inherited chain, <= 3 generations): g1 on dev backgrounds (W1), g2 on dev+sel (W1), g3 on dev+sel under W0 and W1; each generation gets the incumbent source and
  a text summary of development evidence (opaque ids, per-background AUROC of W, prior, neighbour and molecular scores, incumbent trace, labels in W-rank order); one
  LLM request per generation.
- **A2** (restart, matched cumulative requests): 3 independent requests from A0 on the g3 evidence, no inherited program; best candidate on the g3 validation set.
- **Aconv** (conventional optimiser, no LLM): 8-candidate menu {kappa in {0, 1}} x {blend beta in {0, 0.5, 1} of W and prior} plus 2 molecular-screening variants, best by
  mean validation yield on dev+sel under W0 and W1 (22 episodes); it spends 8 evaluations of compute and no API.
- Acceptance (all arms): strictly greater mean validation yield than the incumbent, structure signature changed (not a constant-only change), no embedded data
  (identity audit), no program error, no runner fault. A tie is rejected. Archive membership is not deployment approval; only an accepted program is evaluated finally.
- LLM: `deepseek-flash` (DeepSeek V4.1 Flash) through the maintained client, thinking disabled, <= 8 logical requests and <= 50,000 tokens, <= 2,200 output tokens per
  request, ledger `RUN/llm_ledger.jsonl` (prompt hashes, usage, outcome; no credentials). No final-stage feedback ever reaches the editor. Six requests (A1 x 3, A2 x 3) are
  used before the freeze; two requests and about 33,000 tokens remain unused and are not spent after the freeze.
- Development result recorded before the freeze: no LLM candidate was accepted (A1: g1 returned the incumbent unchanged, g2 and g3 tied or lost; A2: the three requests
  returned the same answer, a tie). A1 and A2 are therefore the same program as A0 and the LLM contribution is exactly zero by construction: it is reported as such and not
  evaluated as a separate effect. Aconv is accepted (validation 3.36 vs 3.18 for A0) and is selected on exposed development episodes.
- Infrastructure fault found and fixed before any LLM result was scored: the first search run lost some worker processes (empty output, scored as zero). `run_program` now
  retries process faults and the search refuses to score a fault. The A1 candidates were then re-accepted from the recorded candidate files without new requests.

## 6. Final evaluation procedure (one pass)

1. Write `FREEZE.json` with the hashes of every frozen file (code, programs, selection artefacts, episode caches, source manifest, this protocol).
2. `python run_final.py`: claims the final stage (write-once ledger; refuses if a frozen file changed), trains M1 and M2 (30 epochs) and M3 (45 epochs) with seeds 0 and 1
   on the GPU, then `final_eval.py final` produces `RUN/final_eval/RESULTS.json` and CSVs: Experiment R (decision, probability, calibration, molecular skill), Experiment Q,
   and the program yields with the 2x2 and price sensitivity.
3. No code, margin, program or selection rule changes after step 1. If the run fails technically it is repaired only for the failure (documented) and re-run on the same
   inputs; no outcome is used to choose any setting. The final outcomes are exposed after the run.

## 7. Statistics, margins, decision labels

- Inference: paired per-background differences, cluster bootstrap over lineages with multiplicity (B = 10,000, seed 20261021); the stated n is the number of final
  lineages with a valid pool (up to 7). The two stocks of one lineage are one cluster. Point estimates, 95% interval, margin, resource use, exclusions and failures are reported.
- Margins (declared from the scientific decision, not from results): T: delta_T = 0.09 precision@5 (about 0.45 additional confirmed positives among 5 nominations per
  background, roughly one additional confirmed sensitive drug per 2 backgrounds); E: delta_E = 0.40 confirmed hits per background under the 5.0-unit budget. A useful gain
  must exceed the margin with the interval's lower bound. Probability and ranking metrics (AUROC, Brier) use margin 0 and are supporting evidence only.
- Attainable precision (exposed sel dry run, SD of paired differences x 1.96 / sqrt 7): T about +/- 0.13 precision@5 (above the margin 0.09); E about +/- 0.66 to 0.78 hits
  (above 0.40). **The design is therefore an estimation pilot**: it can establish a gain larger than roughly twice the margin and can rule out a useful gain only if the
  whole interval lies below the margin.
- Labels: SUPPORTED_USEFUL_GAIN (lower bound > margin); NO_USEFUL_GAIN_WITHIN_RESOLUTION (upper bound < margin; a separate flag marks intervals entirely below zero);
  INCONCLUSIVE otherwise; NOT_TESTED (arm cannot differ from its comparator, for example no accepted edit); NOT_TESTABLE_ON_THIS_ASSET (data cannot support it).
- Pre-declared primary contrasts (no pooling of heterogeneous quantities, no multiplicity adjustment; every other contrast is descriptive): P1 M1 vs B1 (T, precision@5);
  P2 Q func-update vs no update and vs ordinary kernel update (precision@5); P3 Aconv vs A0 and A1 vs A0 under W1 (E, hits); P4 A0 under W1 vs static confirmation of B1's
  top 5 (E, hits). The combined claim H_C requires an A1 that differs from A0; if none exists it is NOT_TESTED and only the exploratory Aconv x W interaction is shown.
  Directional A->W and W->A learning are NOT_TESTED (no accepted agent edit, no cross-world-model sequence beyond the declared g3 task).

## 8. Closest conventional explanation and distinguishing experiment (declared)

- An M1 advantage over the prior would be explained by a direct regularised predictor with the same features (M0/B1); the distinguishing experiment is M1 vs M0/B1 on the
  same lineages (P1), plus a model with the same trajectory supervision but no ODE.
- A feedback gain would be explained by ordinary kernel updating on the same labels; distinguished by Q (func vs kernel).
- A program gain would be explained by a menu search over kappa and beta (Aconv); an LLM-specific claim needs A1 to beat Aconv, which is untestable here because A1 = A0.
- Any gain is a replay on a public, exposed release (published-label task). It cannot show open-ended evolution or new biology.

## 9. Access rules, disclosures and known limits

- Final outcomes are reachable only through the stage ledger after FREEZE.json; dev and sel outcomes were used freely (exposed). No author contact, no access application,
  no download beyond the sources in `SOURCE_MANIFEST.json`.
- Dev-stage models were trained on CPU, selection and final models on GPU (not bit-reproducible: a same-seed 30-epoch rerun differed from the 30-epoch checkpoint of a
  45-epoch run by up to 0.22 in probability, correlation 0.993-0.998; `RUN/sel30`). One or two seeds only; checkpoint training exposure of the released model is UNKNOWN
  and the released checkpoint is not used; label threshold, dose and replicate ids are absent; vehicle controls are heterogeneous.
- M3 trajectory outputs for target-node proteins are numerically unstable in the dry run (target MSE far above persistence); M3 is reported for its phenotype head and its
  trajectory is reported as unstable, not as a competitor in molecular skill.
- The Aconv selection and the A0 rule are fitted on exposed development evidence; the final contrast is the only confirmatory use.
