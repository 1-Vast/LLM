# Observable-State Discovery Campaign: protocol (DRAFT for review, not frozen)

Study: `research/observable_state_20261018`. **Development study on exposed data; never independent confirmation.** No sealed
tier is opened, nothing is run that costs money, no data are downloaded, nothing historical is edited. Status `exploratory`
in `research/STUDIES.json`; freezing happens only after review and Phase 1 (section 11). Every threshold marked **[T]** is a
parameter that must be fixed from pilot data on `D_search` and frozen before `D_select`/`D_transfer` are touched.

## 1. Question and hypotheses (falsifiable)

Can a typed, experimentally falsifiable edit to a Virtual Cell's response-state abstraction, proposed with a discriminating
assay, reduce the assay budget (or raise qualified nominations at equal budget) of future campaigns against strong fixed and
adaptive baselines, on chemical families and lineages not used to discover it?

* **H0 (headroom).** Within the campaign action space (allocation across compounds x contexts, 3-5 rounds) an oracle
  allocation beats the fixed design by at least `h_min` **[T]** (proposed 15%). If not, route EXPAND_ACTION_ABSTRACTION; no search.
* **H1 (identifiability).** For at least one candidate state distinction, a legal assay program of cost <= B identifies the
  state with risk <= delta **[T]**, and the competing explanations' predictions are separable (held-out AUC >= i_min **[T]**,
  proposed 0.75, calibration slope within [0.7, 1.3]).
* **H2 (decision sufficiency).** Replacing the full history by the state costs less than eps **[T]** in qualified nominations
  (verdict via `research_edit.sufficiency_verdict`; SUFFICIENT needs the one-sided 95% upper bound of the loss < eps).
* **H3 (transfer).** Dev. Delta U_future (full MAESTRO - strong fixed) has a positive one-sided 95% cluster lower bound on
  held-out families, and again on held-out lineages, with no sign reversal in >= 80% of held-out clusters.
* **H4 (necessity).** Factorial Delta_interaction = U11 - U10 - U01 + U00 > 0; if editable-VC-only or conventional search matches
  the agent, the agent/LLM is not a necessary contributor and the claim is withdrawn for that component.

## 2. Observable decision-sufficient response state (definitions)

State z = Phi(H): a small categorical or low-dimensional vector of response distinctions (e.g. family-by-state interaction
indicator) computed from *legal* inputs only: chemistry, inexpensive context features and bought measurements.

* **Decision sufficiency:** U(d*(z)) >= U(d*(H)) - eps. U is the qualified-nomination utility of section 4; d* is the
  nomination list produced by the fixed scoring rule from z or from H; compared per cluster, eps **[T]**.
* **Observability:** a legal assay program A costs <= B and gives Risk[zhat(A) - z] <= delta, where the reference z is
  defined from labels *disjoint* from the evaluation labels. States defined from hidden target outcomes are inadmissible.
* **Transferability:** Delta U_future = U(learned state) - U(strong baseline) > 0 separately for unseen chemical families,
  unseen contexts, the joint holdout, and (blocked) an independent source.

## 3. Data, eligibility and splits

Assets: PRISM 19Q4 primary screen (4,528 cores x 545 lines, 23 pools; MoA-family folds 0-4; Tanimoto 0.5 purge), all
**exposed** (folds 2-4 opened by indication-triage and later studies). Probes are published values plus synthetic noise:
**noise draws are paired scenarios, not biological replicates**, and are averaged within a compound.

* Campaign = 64 compounds from one chemically purged batch, 12 contexts, 3-5 rounds, a total budget of 3 pool-reads per
  compound on average **allocated freely across compound-context pairs** (units are hypothetical pool wells; no plate map exists).
* Contexts: Phase 0 must verify whether pools are lineage-pure. If not, a context is a lineage group of lines and a read is
  the hypothetical well covering it; the grouping is fixed before any outcome is read (Q1 below).
* Roles: `D_search` = folds 0-1 with a search lineage set; `D_select` = fold 2, search lineages (bounded pass/fail only);
  `D_transfer` = folds 3-4, with chemistry holdout, and lineage holdout (lineage groups never used for discovery) and the
  joint holdout. Lineage groups come from DepMap `primary_tissue` by salted hash, written down in Phase 0.
* Eligibility: lines >= 90% training-finite (predecessor rule); events as registered (robust-z <= -3 and log2FC <= -1).
* **Q2, PRISM-L1000 (metadata only, done):** `QUALIFICATION_L1000.json`. 1,845 compounds and 35 cell names overlap by Broad
  13-character id and normalised name; only 6 lines (MCF7, PC3, A375, A549, HT29, HEPG2) have > 1,000 overlapping
  compounds, the rest ~156. Dose (2.5 uM vs mostly 10 uM), time (5 d vs 6/24 h) and endpoint differ; identity by structure
  was not checked. Earlier blocks already used this intersection. **Decision: the assay-escalation question
  is a pilot with 6 lines at most, analysed on exposed data; the main campaign study is PRISM-only and is not blocked.**

## 4. Outcome, decision utility and cost

* **Primary utility U:** qualified nominations per 64 compounds among **unmeasured** compound-context pairs (32
  nominations, <= 3 per compound), graded by the registered event rule. Re-reads of probed cells are excluded (the old
  triage utility was 394/395 re-reads).
* **Progression list:** the 8 highest-ranked compounds per 64; **false progression** = progressed compound with no
  event in any nominated context; **false rejection** = non-progressed compound with >= 2 events.
* **Secondary:** unique qualified compounds; transfer-failure detection (contexts flagged as outside scope vs observed
  failures); selected-candidate error; prediction metrics (perturbation-specific and context-specific, centred on the
  perturbation mean, per Systema: global control-shift metrics are not reported alone).
* **Costs, never merged:** `assay_wells` (hypothetical pool reads), `compute`, `curation`, `rounds`, `logical_queries`.
  Primary comparisons are at equal `assay_wells`; the robust objective J uses one conversion for assay cost, and
  Delta U is reported either gross or at equal budget, never both in the same J.
* `E90`, `Saving90 = 1 - E90(MAESTRO)/E90(baseline)` on budget-utility curves at budgets of 1, 2, 3, 4, 5 reads per
  compound; area under the curve; `N_BE = research cost / average per-project saving` in wells.

## 5. Edit language and proposal schema

Primitives (typed, `research_edit.PRIMITIVES`): split, merge, interaction (drug family x cell state), local exception
(bounded subfamily or context), observation request. Numeric parameters are fitted by ordinary statistics (OLS in
`fit_interaction`, ridge, EB), never by the language model. A proposal is a `ResearchEdit` with: observed failure,
>= 2 competing explanations including the strong simple baseline, directional predictions with magnitudes under each,
a discriminating assay with itemised cost, an expected nomination change with direction, a numeric rejection
condition, applicability scope and a dependence group. `validate()` refuses incomplete proposals and any proposal
whose predictions are identical across explanations or whose only claim is "utility goes up". Predictions must be
registered (hashed) before outcomes are revealed. Worked template: `test_science.example_edit()` (illustrative, not a
finding): main effects Y = a_d + b_c against + gamma*I(d in F)*I(z_c = 1), crossed contrast
[Y(d,c)-Y(d',c)] - [Y(d,c')-Y(d',c')], read first as a functional response pattern, not a mechanism.

## 6. Experiment value

Search ranks candidate assays by `D_dec` (decision-weighted discrimination, `research_edit.d_dec`), not generic
information gain. Misspecification risk is not taken from the Virtual Cell's own confidence: signals are cross-model
disagreement (ridge, kNN, forest, VC), calibration residuals from `D_search` (the lookahead probabilities were about
10x overconfident), target representativeness, and development-to-held-out error amplification (the R-IDeA concepts).
Candidate objective `J = LCB[Delta U_future] - lam*cost - eta*complexity - rho*misspec` with all terms in
qualified nominations per 64 compounds and `lam, eta, rho` fixed **[T]** before `D_select`.

## 7. Arms

1. **A0** strong fixed: fixed Virtual Cell (ridge-plus-feedback on the structure prior; kNN, forest, chemistry-only, context-only
   as comparators) with the fixed A-optimal read order.
2. **A1** standard adaptive design, VC fixed: a BATCHIE-style batch Bayesian design and a PS-BAX-style target-set posterior-sampling
   design (the target set = the qualified-event set), both re-implemented from the primary papers and checked against
   their published descriptions before use; plus an AssayLoop-style amortised policy **only if** a cross-campaign
   acquisition model is trained on `D_search`.
3. **A2** editable VC, conventional (non-agent) proposer: enumerate typed edits, score by the same J on `D_search`.
4. **A3** full MAESTRO: agent-proposed epistemic edits and discriminating experiments (deepseek-flash only), same budget
   of proposals as A2.
5. Factorial: U00 (A0), U01 (editable VC, conventional), U10 (fixed VC, agent edit limited to observation requests and
   applicability/refusal scope, not model change), U11 (A3). `Delta_interaction = U11 - U10 - U01 + U00`.
   Matched arms: same histories for component isolation; separate cost-matched closed loops for total effects.
6. Zero arm (no feedback prior) and unconditional-residual arm in every comparison. Closed-loop greedy acquisition lost to
   the fixed design before; the protocol therefore compares against A0 at equal wells, not against "no design".

## 8. Access rules (`masked_interface.py`)

`search`: scalar utility, cap 40 calls per search. `select`: one bit (pass/fail against a threshold fixed at
construction), cap 8, bits logged. `transfer`: once, only while the FREEZE digests hold. Every call goes to an append-only
ledger. The agent sees aggregated development numbers only; no per-cell labels from `D_select`/`D_transfer`. Held-out
results are not inspected and then tuned against; a second look is a new, separately labelled study.

## 9. Diagnostics: headroom, identifiability, transport

For every evaluated failure report H = (oracle - fixed)/fixed in the same action space, I = held-out AUC of the legal-observation
predictor of "which explanation holds" with a calibration slope, T = share of held-out clusters with the same sign as
`D_search` plus size retention. Route with `research_edit.route` (thresholds **[T]**, no defaults). A failed edit rejects
the edit; the incumbent predictor, fixed or standard adaptive design and feedback workflow are always retained.

## 10. Statistics

* Cluster unit: MoA family for chemistry holdouts, lineage group for lineage holdouts; joint holdout reports both,
  primary = the larger (more conservative) interval. Compounds, campaigns and noise draws are never units.
* Uncertainty: family-cluster bootstrap 4,000 draws, seed 20261018, one-sided family sign-flip; 95% one-sided lower bounds.
* Primary family (Holm): P1 A3 - A0, P2 A3 - A2, P3 A3 - A1, each at equal wells on the chemistry-and-lineage held-out set.
  Secondary: Delta_interaction, Saving90, false progression, N_BE, transfer by lineage.
* **Power (`POWER.json`, from the last study's recorded intervals, 80% power, alpha 0.025):** an acquisition-only contrast
  at fixed backend (SE 0.072 at 2,304 compounds) is resolvable: floor 0.1875 needs ~2,700 compounds (43 campaigns), a 15%
  gain (0.27) ~1,300 (20). A contrast that changes the predictor (R1-type, SE 0.199) needs ~9,600-20,400 compounds, more
  than the 4,528 PRISM cores, and the factorial interaction under the conservative independent-arm assumption needs
  ~38,000-82,000. **Therefore, unless the Phase-1 pilot measures a paired-arm SE small enough that required n <= available n,
  P1-P3 and the interaction are declared descriptive in advance, not confirmatory.** The aspirations (20-30% fewer bundles,
  >= 15% more qualified nominations with a positive cluster bound) are targets only.
* Practical floor: max(0.1875 events/64, the value that offsets the cost of one extra read for A0) **[T]**.

## 11. Phases, stop, reroute, promotion

* **Phase 0 (no outcomes):** lineage and pool composition (Q1), split definition, SE pilot design; freeze FREEZE1 (protocol,
  code, split list).
* **Phase 1 (`D_search`):** headroom H0, identifiability, power refresh, threshold derivation; freeze thresholds.
* **Phase 2:** budgeted edit search for A2/A3 (equal proposal counts, 12-24), `D_select` bits; freeze FREEZE2 (edits, states,
  scoring); one `D_transfer` evaluation.
* **Stop:** H0 fails (route to a new action abstraction); the edit set is empty after validation; an arm needs an
  unqualified label. **Reroute** by the section-9 table. **Promote** to "candidate for independent evaluation" only if H3
  holds on both axes with no reversal, A3 beats A2 and A1, and the factorial analysis names the necessary component;
  otherwise report the unchanged or negative result for that edit without a project-wide STOP.
* Limitations: exposed data, synthetic probe noise, hypothetical well costs, single dose, replay not a prospective assay;
  confirmation needs an independent source with plate-level costs and repeated measurements. Nothing here has been run beyond the
  scaffolding tests, metadata qualification and power arithmetic.

## 12. Minimum repository changes

New folder only: `research_edit.py`, `masked_interface.py`, `audit_priors.py`, `qualify_l1000.py`, tests, `verify.py`,
registry entry, a `log/DIRECTIONS.md` item. Not changed: `src/`, every frozen study. Next code (after review): a
campaign-level task builder reusing `feedback_propagation_20261018.bench` and `acquisition_program_20261018.ap_task`, the
BATCHIE/PS-BAX baselines, and an agent prompt restricted to the `ResearchEdit` schema.

## 13. Built after review approval (2026-10-18): task builder and baselines

`campaign.py` (Gaussian-belief campaign, seed round + adaptive rounds, free allocation over compound x context reads, itemised ledger,
grader and `grader_for` for the masked interface), `policies.py` (`FixedPolicy`, `BatchEIGPolicy`, `PSBAXPolicy`), `real_adapter.py`
(builds a campaign from an exposed PRISM fold; construction only), `test_campaign.py` (8 synthetic tests). No outcome was read:
the real-fold smoke used placeholder values and timed the planners only (fixed 0.0 s, batch-EIG 0.5 s, PS-BAX-style 8.7 s per 64-read round).

Findings that change section 7:
* **The batch-EIG baseline is outcome-independent** in the homoscedastic Gaussian model (posterior variance does not depend on observed values), so
  before outcomes arrive it picks one pool for every compound: it is a fixed design with per-compound ordering, not an adaptive one. Only
  value-dependent criteria (PS-BAX-style: 18 distinct pools on the same state) allocate adaptively. A1 therefore needs a value-dependent
  design to be a meaningful 'standard adaptive' arm; PS-BAX-style supplies it.
* Both baselines are labelled simplifications. BATCHIE's PDBAL and the exact PS-BAX selection rule are NOT ported; the primary papers must be read
  (this session read abstracts only) before any result is called BATCHIE or PS-BAX.
* The belief uses a scalar probe-noise variance while the oracle noise is heteroscedastic (as in the predecessor).
* Not built: AssayLoop-style amortised policy, the A2/A3 edit proposers, the campaign-level evaluator, any run on `D_search`.
