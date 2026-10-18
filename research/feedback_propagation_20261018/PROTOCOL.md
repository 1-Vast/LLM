# Feedback propagation to unmeasured compound/line pairs: protocol

Study: `research/feedback_propagation_20261018`. Status when frozen: registered before any outcome of a new arm is scored on the
estimation folds 2, 3 and 4. The data are **exposed** (see section 2); this study can only be development-grade, never a
confirmation.

## 0. What is and is not being done

- One bounded question: **can observed feedback identify and repair a failure in how responses propagate to unmeasured
  compound/line pairs?** One editable object: the *feedback-update program* that maps a compound's observed history to scores
  for every line. The base predictor (structure prior + low-rank-plus-diagonal line covariance, `world.py` of
  `indication_triage_20261016`), the endpoint (selective residual event), the nomination rule and the acquisition rule are fixed.
- Not done, by instruction: no new foundation model, learned evaluator, general procedure-value model or extra agent role; no
  LLM proposal search, grammar search, Beat AML low-rank development or PRISM seed-library revision; no sealed outcome opened
  (PRISM 24Q2 REP.1M, GSE70138 sealed tiers and the Vis 2024 release stay closed); no frozen study overwritten; no commit, no push.
- Registered NO-GO decisions of `log/RESEARCH_PROGRAM.md` and `research/EVIDENCE.md` are preserved. In particular the
  covariance-inflation and model-averaging repairs of the bridged prior stay closed; the repair studied here changes the *prior of
  the update* (analogue anchor), a different object, and is reported with its attribution to conventional methods.
- LLM and agent roles are not exercised: the study asks whether a deterministic repair leaves residual opportunity that a
  program search could in principle capture. If the decision rule of section 10 says STOP, no search is drafted or launched.

## 1. Verified facts (audit; `AUDIT.json`, `audit_task.py`)

1. HEAD is 5d713d5ca3194fbd131ce45835355538d10a4b66, identical to the target commit; the working tree differs only by this
   study and the seed-attribution erratum files (untracked). Tables (`tables.npz`, 4,528 cores × 545 lines) match
   `indication_triage_20261016/BUILD.json` by sha256.
2. Equal-lineage bootstrap erratum (task 1): the secondary interval of `seed_attribution_20261017/analyse.py` collapsed repeated
   lineage draws with `set(groups)`. Recomputed from the public per-lineage means in `RESULTS.json`
   (`erratum_equal_lineage_bootstrap.py`): policy +0.057 [-0.206, +0.355]; I2 +0.100 [+0.002, +0.202]; I1 +0.076 [-0.105, +0.278].
   Primary tests and stop decisions are unchanged. Recorded in `research/seed_attribution_20261017/ERRATUM_20261018.md`.
3. **The saved indication-triage totals reproduce exactly (MAESTRO loop 395 hits, two-stage 293 on folds 2-4), and 394 of the
   395 (and 293 of 293) hits are pairs the arm itself probed.** Those nominations re-read, with synthetic noise, the cell they
   are graded on. The old task therefore says nothing about propagation to unmeasured pairs. (A first version of this audit
   compared campaign-local with global compound indices and reported 1.5%; corrected before use, see `DEVIATIONS.json`.)
4. Chemical separation: folds are MoA-family folds (1,145 families, none spans folds; no connectivity unit spans folds). About
   28-38% of evaluation compounds have an ECFP4 Tanimoto ≥ 0.5 analogue in other folds; the purge removes those training
   compounds (402-468 per fold), after which the maximum Tanimoto to any training compound is < 0.5 for every evaluation
   compound. **Murcko scaffolds are not disjoint**: 24-29% of evaluation compounds still share a scaffold with a retained
   training compound. "Unseen" means unseen identity, family and close analogue, not unseen chemotype.
5. Outcome masking: a run's queries, observations, scores and lists are unchanged when every cell the run never queried is
   replaced by random values (ridge, kNN, mixture, empirical-covariance rules; 30,000+ scrambled cells each); a leaky control
   that reads the hidden matrix is detected. Arms see only oracle answers. This does not make a probe independent of the cell
   it grades: the probe is the scoring-matrix value plus synthetic noise (replicate spread of the secondary screen).
6. Missingness: 97.6% of cells finite; 39 lines are below 90% finite and are inadmissible (506 admissible lines per fold);
   ~8% of events sit on inadmissible lines and are unreachable. Missing cells on admissible lines (~0.65%) are failed units
   when probed and non-hits when nominated; nominated-unknown counts are reported with every utility, not imputed.
7. Action support: nominations are the top 32 pairs per 64-compound campaign, at most 3 per compound, from admissible lines
   (unmeasured nominations also exclude every pair a unit was spent on).
8. Measurement granularity: a PRISM well reads a pool of ~24 lines (23 pools of 19-25 lines; 97% concordance between the HTS
   and MTS004 groupings). Compound plate, well, detection plate and replicate mapping are **not** available for the
   replicate-collapsed primary data. So costs are hypothetical: the pool-well grain (one unit = one compound × one pool,
   returning every admissible line of that pool) is the physically motivated read unit; the logical grain (one line = one unit)
   is a sensitivity; neither is a priced design.

## 2. Task qualification

The task is **QUALIFIED AS A DEVELOPMENT TASK**, with the following status and limits.

- Task: a previously unseen compound batch (an evaluation fold, chemically purged), a limited measurement budget (B pool reads
  per compound), then compound/line nominations (32 per 64 compounds) graded on the registered selective-event endpoint
  of the published matrix. It is distinct from `indication_triage_20261016` because the graded nominations are restricted to
  pairs no unit was spent on (finding 3 shows why the old grading cannot test propagation).
- Data status: PRISM 19Q4 folds 0 and 1 are development data (Phase D). Folds 2, 3, 4 were opened by `indication_triage_20261016`
  (estimation) and, in aggregate (event counts, reproduced totals), by this study's audit. No outcome of a new arm has been
  scored on them. A fresh protocol on exposed data is a *replication of method on exposed data*, not an independent confirmation.
  No new independent data exist for this task: the sealed tiers are unopened and must stay so.
- Feedback is not independent assay feedback: the probe is a noisy copy of published data. Conclusions concern the update rule
  as a statistical procedure under that measurement model.
- Therefore every claim below is "development-grade"; a positive result would justify an independent test, not a deployment.

## 3. Hypotheses

- H1 (update attribution). With identical histories, the analogue-anchored repair R1 nominates more true selective events on
  unmeasured pairs than ridge-plus-feedback, by at least δ* per 64 compounds.
- H2 (conventional explanation). R1 also beats the strongest conventional adaptive/conditional comparator C* (kNN analogue
  regression), by at least δ*. If H2 fails, conventional methods explain the gain.
- H3 (identification). A feedback-only diagnosis (leave-one-pool-out propagation error) selects, per compound, between the base
  update and R1 and nominates more events than R1 alone, by at least δ*. If H3 fails, observed feedback does not identify the
  failure compound by compound, and a program search over diagnosis rules has no identifiable headroom.

## 4. Units, utilities, histories

- Cost unit: pool well (hypothetical). B = 3 pools per compound is primary. A seed pool is the first pool of the A-optimal pool
  order of the base covariance; histories are the first B pools of that order for every compound (identical histories).
- Utilities (all graded on the clean published cell, events as registered; incomplete 64-compound campaigns are run but excluded
  from the statistics):
  - **U1 (primary) nomination utility**: true selective events among nominated *unmeasured* pairs, per 64 compounds.
  - **U2 unique candidate yield**: compounds with ≥ 1 such event among their nominated unmeasured pairs, per 64 compounds.
  - U3 (secondary, total): events among nominations drawn from all admissible pairs, with the measured-pair share reported; its
    measured part re-reads the graded cell and is an upper bound on independent yield.
  - Reported with every utility: nominated pairs, nominated-unknown pairs, lineage hits, cost in lines and pools.

## 5. Programs

All programs share the base predictor and differ only in how the history `(P, y)` is turned into a profile:

| name | program |
|---|---|
| prior | no feedback (zero arm; also reported with no measurement at all) |
| ridge | Gaussian conditional mean, single unit scale (`World.point_mean`); the registered ridge-plus-feedback comparator |
| mixture_mean | same update with the world's empirical-Bayes scale mixture (existing MAESTRO update, mean profile) |
| empcov_0.1 | Gaussian update with the full-rank empirical covariance of training residuals, 10% diagonal shrinkage |
| C* = knn10 | analogue regression: mean profile of the K = 10 training compounds closest to the history on the probed lines, probed values plugged in |
| knn20, knn40 | same with K = 20, 40 (secondary) |
| forest | multi-output random forest from the probed values to the training residual profile (identical histories only) |
| **R1** | analogue-anchored update: m = (1 − lam)·prior + lam·(K-analogue mean), then the Gaussian update of the residual; **K = 10, lam = 1.0** |
| gated (H3) | leave-one-pool-out diagnosis: each probed pool is predicted from the others by the base update and by R1; if R1's loss-weighted ("kill": weight 4 on observed log2FC ≤ −1) squared error is smaller R1 propagates, otherwise ridge; histories of < 3 pools keep ridge |

R1 reduces to ridge when `lam = 0`; the gate reads only the history, the training set and the fitted world (unit-tested).
The Phase D rules chose these settings (section 6); nothing is tuned on folds 2-4.

## 6. Phase D (development; `develop.py`, `DEVELOPMENT.json`)

- Folds 0 and 1, each predicted from a world fitted on the other fold only (after the purge): no estimation-fold outcome enters.
- Selection (B = 3, identical histories, pooled U1): R1 grid K ∈ {10, 20} × lam ∈ {0.5, 1.0}; C* among nine conventional
  settings; gate loss ∈ {mse, kill, spearman}. Ties as written in `develop.py`.
- Selected: R1 = (K = 10, lam = 1.0) with 89 unmeasured hits; C* = knn10 with 76; gated loss = kill with 82; ridge 62; prior 38.
  (34 complete-or-partial campaigns, 2,130 compounds.) These are selected maxima and optimistic.
- Diagnosed on the development folds: at the logical grain with 16 or 64 lines no rule exceeds the structure prior on U1 by more
  than 6 hits of about 35 (prior 36 and 31; ridge 37 and 25), so there is no propagation headroom at the cost the old study
  priced; at 128 logical lines ridge still does not (20 vs 20 for the prior) while empirical-covariance, kNN and R1 do (30, 31,
  41). At the pool grain (about 24 lines per unit, B = 3 is about 72 lines) ridge beats the prior (62 vs 38) and analogue
  methods beat ridge. Gate
  identification is weak (agreement with the truly better rule 55-57%, AUC 0.59; hindsight gate 91 hits vs ungated R1 89).
  Item-specificity control: with histories assigned to the wrong compound all rules fall below the prior.
- Exploratory scripts (not frozen, `scratchpad/explore1-5.py`) touched folds 0 and 1 only.
- Closed loops with value-greedy pool acquisition lose to the fixed A-optimal design on U1 in development (27-60 vs 62): the
  loop buys the pools that contain its own predicted events, which removes them from the unmeasured set. This is a property of the
  acquisition/utility pair and is reported, not repaired (the acquisition rule is fixed initially).

## 7. Practical-effect threshold δ* and attainable precision (`thresholds.py`, `THRESHOLDS.json`; derived from folds 0-1 only)

- δ_cost: ridge-plus-feedback on a common target set (pairs outside the first four pools) gains on average 0.1875 U1 per 64
  compounds per additional pool (1.4375, 1.6875, 1.8125 hits per 64 compounds at 1, 2, 3 pools; 1.625 at 4). A repair is
  practically worth acting on only if it buys at least what one more pool read per compound (+33% of the 3-pool cost) buys the
  baseline.
- δ_rel = 10% of the ridge utility at B = 3 (0.175 per 64). **δ\* = max(δ_cost, δ_rel) = 0.1875 hits per 64 compounds.**
- Attainable precision at 36 complete campaigns (estimation folds): expected SE ≈ 0.27 for R1 − ridge, minimum detectable gain
  (one-sided α = 0.05, power 0.80) ≈ 0.68. The threshold δ* is below the MDE: a gain of δ* cannot be resolved; the practical
  criterion below therefore requires the *lower confidence bound* to exceed δ*, i.e. a point estimate near 0.7 or more.
  Development contrasts (family bootstrap): R1 − ridge +0.81 [+0.24, +1.37]; R1 − C* +0.34 [−0.14, +0.81]; gated − R1 −0.19
  [−0.62, +0.28]. Expected outcome stated in advance: H1 holds in direction, H2 is uncertain, H3 fails; the decision is STOP unless
  the estimation folds say otherwise.

## 8. Phase E arms (`compare.py`)

For each of folds 2, 3, 4 (world fitted on the other four folds after the purge; K, lam, C*, gate loss fixed by Phase D):

- A. Identical histories, B = 3: prior (history-matched unmeasured set; and no measurement), ridge, mixture_mean, empcov_0.1,
  knn10, knn20, knn40, forest, R1, gated. B = 2 and 4 (ridge, knn10, R1) as budget sensitivities.
- B. Cost-matched closed loops (B pools per compound; uniform allocation; each round every compound recomputes scores from its
  whole history with the arm's own update and buys the pool whose unqueried admissible lines have the largest sum of their three
  highest scores): loop_ridge, loop_knn10, loop_R1, loop_gated, plus the conventional two-stage allocation with ridge. Costs
  in lines and pools are recorded per arm and compared with the fixed design.
- C. Sensitivities: logical 16-line grain (prior, ridge, knn10, R1); a second synthetic-noise draw (salt `probe2`); the
  deranged-history negative control (each compound receives another compound's observations); the budget curve on the common
  target set.
- D. Hindsight diagnostics that read the hidden side and are never policies: truly-better indicator of R1 over ridge per compound
  and the AUC of the gate's loss difference for it; hindsight gate (R1 or ridge by true error); hindsight best-of {ridge,
  mixture_mean, knn10, R1} per compound; the oracle nomination ceiling.

## 9. Uncertainty analysis (`metrics.py`, `analyse.py`)

- Estimate: mean paired difference per 64 compounds from per-compound hit differences, over complete campaigns.
- Interval: cluster bootstrap over MoA families (families never cross folds and are the independent chemistry-biology groups;
  campaigns mix families), 4,000 draws, seed 20261018, percentile 95%. One-sided p: family sign-flip (4,000). Secondary: paired
  sign-flip over complete campaigns.
- Confirmatory family {P1, P2} Holm-adjusted; P3 is tested at one-sided α = 0.05 as it only matters for the continue rule.
  Everything else is descriptive, with the same intervals and no adjustment.

## 10. Decision rule (applied by `analyse.py`; stop rule before any search)

- P1 = R1 − ridge, P2 = R1 − C*, P3 = gated − R1, all on U1, B = 3, identical histories, folds 2-4 pooled.
- P1 practical: Holm p < 0.05 **and** lower 95% bound ≥ δ*. P2: Holm p < 0.05, lower bound > 0 and point ≥ δ*. P3: p < 0.05, lower
  bound > 0, point ≥ δ*. U2 (unique candidate yield) for P1 must not contradict in sign.
- CONTINUE (draft, not launch, a bounded program-search experiment) only if P1 practical, P2 and P3 all hold. Otherwise STOP, and
  the first failed condition is named: P1 not practical; conventional methods explain the gain (P2); no identifiable residual for a
  diagnosis program (P3).
- If CONTINUE, the drafted experiment must compare agent-generated programs with the fixed rule R1, conventional search over the
  same parameter space (K, lam, loss, gate rule) and generic code search under matched information and evaluation budgets, and
  freeze the chosen program before any transfer evaluation. If STOP, none is drafted.
- Closed-loop contrasts (section 8B) and sensitivities are reported with the same intervals; they cannot rescue a STOP.

## 11. Files and integrity

`FREEZE.json` hashes (LF-normalised) this protocol, the code, `DEVELOPMENT.json` and `THRESHOLDS.json`. `DEVIATIONS.json` is not
hashed. `ACCESS.json` is written once at the first estimation-fold run. `verify.py` recomputes `RESULTS.json` from
`records/E_fold*.json` and checks the freeze, the Phase D wiring, δ*, the erratum files and the frozen predecessors.
Environment: Python 3.14.4; the tables cache is `tmp/indication_triage_20261016/tables.npz`.
