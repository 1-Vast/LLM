# Related work and positioning

These works are design inspirations. None shows that the methods here work biologically.

**What was verified.** Bibliographic details were checked on 2026-10-17:

* against the official page, an abstract service, or the copies cached under
  `log/program_review_20261017/` and `research/anchor_purchase_20261016/source_review/`;
* for abstracts and metadata only, unless a fuller reading is stated.

## Assay and domain

* **Tyner et al. 2018**, *Nature* 562:526–531, PMC6280667 (Methods read). This is the source for
  the assay design behind every cost figure in `COST_UNITS.json`:
  * a 7-point, 3-fold series from 10 to 0.0137 µM, with one well per concentration;
  * 10,000 cells per well in 384-well plates, plated within 24 h of collection;
  * 72 h of culture, then an MTS readout;
  * DMSO vehicle and a positive-control combination on each plate;
  * a probit fit to the 7 points.
* **Bottomly et al. 2022**, *Cancer Cell*, PMC9378589 (results and methods passages read).
  * The assay is the same as in 2018. Curve QC uses deviance and AIC, plus a plate-variability
    rule.
  * 73 drugs correlate with at least one of six malignant cell-type scores (from van Galen et al.
    2019 signatures). The authors describe most drugs and families as showing "cell maturation
    state-biased response".
  * This motivates the decomposition diagnostic. The frozen endpoint removes overall sensitivity,
    and a state prior that mainly predicts overall sensitivity would add little on it. That is a
    hypothesis, not an explanation.
  * The cell-type score file ("Malignant Cell Types", BeatAML2 site) is not local. Its use is the
    next step only if the RNA state shows independent value.

## Planning, identification and experiment design

* **Kriging believer.** Ginsbourger, Le Riche and Carraro 2010, the greedy batch heuristic behind
  the lookahead rule. The `lookahead_v1` defect was an inconsistent baseline inside that heuristic.
* **DINO-WM.** Zhou, Pan, LeCun and Pinto, ICML 2025, PMLR 267:79115–79135.
  * An action-conditioned world model in pretrained (DINOv2) feature space, trained offline and
    used for test-time planning.
  * Relevance: planning by predicting the consequence of an action in a learned representation.
    Here the "action" is a query and its consequence is a readout; there are no dynamics.
* **Provably-safe online system identification.** Zhang, Zhou and Vasudevan, RSS XXI (2025),
  paper 121.
  * It plans exciting trajectories that identify payload parameters while respecting
    constraints. Its bounds assume bounded sensor noise.
  * Relevance: probes as identification actions with a control cost (here, the opportunity cost
    of displaced candidates). Its guarantees do not transfer to biological readouts without proof.
* **R-IDeA.** Tang, Sloman and Kaski, AISTATS 2026, PMLR 300:3016–3024.
  * Under model misspecification, informativeness-only Bayesian experimental design can amplify
    generalisation error. Acquisitions should also be representative and de-amplifying.
  * Relevance: exploit-first and value-of-information probes both sample where the model already
    expects value. They may miss the observations that expose model error. The deranged and
    global-only controls are a first check of what the readouts actually carry.
* **MDA (Model Discovery Agent).** arXiv 2608.09696 v5. LLM-assisted Bayesian experiment design
  for discovering mechanistic world models.
  * Earlier review read the cached full text: residual-guided model expansion, Bayes-risk design,
    and evaluation on the same patients rather than unseen ones.
  * Relevance: this is the closest precedent for "propose a model, run an experiment, revise the
    structure". MAESTRO's novelty must lie elsewhere: shared response structure across drug and
    cell tasks, failure detection, and functional decision value on unseen contexts.

## Procedures, abstractions and selection

* **RLAD.** Qu, Singh, Lee, Setlur, Salakhutdinov, Finn and Kumar, ICLR 2026 (abstract).
  * A two-player RL paradigm: one model proposes reasoning abstractions, and a solver is trained
    to use them.
  * Lesson: judge learned abstractions by their utility on later problems, and test whether the
    executor actually uses them. This rules out counting knowledge entries or procedures.
* **LACE.** Gong, Wang, Song, Sheu and Yan, *Nature Machine Intelligence*, published
  1 October 2026 (abstract; full text is subscription-only and was not audited).
  * LLM-driven construction of complementary heuristic programs for combinatorial optimisation,
    within constrained interfaces.
  * This is prior art for procedure generation and evolution.
* **CSPI-MT.** Cho, Pop, Gan, Corbett-Davies, Nir, Evnine and Kallus, arXiv 2408.12004 v1,
  August 2024 (HTML read).
  * Method:
    * a random tuning/test split, with 20% of units for tuning;
    * simultaneous max-type confidence bands across candidate cutoffs;
    * an asymptotic guarantee that a policy worse than the baseline is adopted with probability
      at most γ.
  * Assumptions: i.i.d. units, unconfoundedness and positivity. Missing outcomes are not
    addressed.
  * `tuned.py`'s calibrated selector borrows the generate-then-calibrate pattern. It differs in
    four ways:
    * its units are patients;
    * it splits 50/50 by patient hash;
    * it uses Bonferroni, which is more conservative than the max-type band;
    * it charges a declared round cost.

    Its guarantee is likewise asymptotic and assumes independent patients.

## State-based drug-response models

* **CellHit.** Carli et al., "Learning and actioning general principles of cancer cell drug
  sensitivity", *Nature Communications* 16:1654 (2025), DOI 10.1038/s41467-025-56827-5 (Europe PMC
  abstract).
  * Drug-response models on transcriptomics, restricted to genes in LLM-curated mechanism-of-action
    pathways, aligned from cell lines to patient samples.
  * The abstract does not name the learner. The assessment's "drug-specific XGBoost" is therefore
    not verified here, and XGBoost is not installed in this environment.
  * `S_ridge` and `S_gbm` (scikit-learn histogram gradient boosting) are simpler stand-ins on the
    same 30 basal PCs, without mechanism-gene curation. Beating them is necessary, not sufficient,
    for a claim of unique Virtual Cell value.

## Reporting

* **Zhao et al. 2026**, *npj Drug Discovery*, DOI 10.1038/s44386-026-00075-0 (see
  `log/transfer_review_20261017/REVIEW.md` §10).
  * Its autonomy levels and reporting metrics (HIC, AERR, SCR) inform reporting. They do not
    replace method gains.
  * Runtime recovery by the evaluated system must be kept apart from repairs the developer made to
    code. The `lookahead_v1` correction is a developer repair.

## Positioning

**Precedents.** These parts are not new:

* "model proposal → experiment → feedback → structural revision" (MDA);
* LLM-generated executable procedures with accumulated experience (LACE, and agentic
  context-engineering work);
* exploit-first feedback re-ranking, a standard design.

**Possible contribution.** If any, it would be the three pieces below, shown by better terminal
decisions on tasks that did not shape the method:

* response relationships that transfer across drug and cell tasks;
* the conditions in which they hold;
* executable experiments that detect when they fail.

This study supplies none of that yet. Its job is to find which part of the existing gain is real
and where it comes from.
