# EG-RPT first-stage protocol (DRAFT for review; not frozen; nothing executed)

Study `research/eg_rpt_20261019`. Development study on exposed data; **never independent confirmation**. No sealed tier, download, paid LLM call or assay
purchase. Thresholds marked **[T]** are set from Phase-0 data before any evaluation read. Hypothetical costs unless stated.

## 1. Scope: one narrow task first (Task A only)

Task A, drug response / sensitivity discovery on PRISM 19Q4 replay (the only task family with enough local structure to generate many tasks). Task B (mechanism
discrimination) lacks measured mechanism truth (`mechanism_falsification_20261014` ASSET_BLOCKED); Task C needs plate/dose data and independent synergy validation
(NCI-ALMANAC is used elsewhere and exposed); Task D is a later external test. They are not averaged with A.

## 2. Question and hypotheses

Can evidence about past research procedures plus a Virtual Cell reliability report choose, per **new task**, a procedure that raises terminal utility over the best fixed
policy, at equal total cost, on chemical families and lineages not used to build the memory?

* **H0 (identifiable headroom).** Between candidate procedures, the per-task utility difference is reproducible across two independent probe-noise draws: split-noise
  rank agreement and an oracle-minus-best-fixed gap computed by choosing on draw 1 and evaluating on draw 2 exceed **[T]** (proposed: lower bound > 0.1875 events/64,
  the carried practical floor). The existing 131-vs-100 figure is **not** evidence (`NOISE_HEADROOM.json`). If H0 fails, stop: no meta-learner is built (route: expand the
  action space or change the task).
* **H1 (transfer).** On tasks of held-out families and lineages, EG-RPT's chosen policy beats the best fixed policy and the non-LLM meta-selector (below) by the
  practical floor, with a positive cluster lower bound.
* **H2 (reliability value).** The Virtual Cell reliability report improves H1 selections (ablation without it) and lowers false progression.
* **H3 (agent).** Only if H1 holds with non-LLM selectors: an agent reading the same memory adds utility over the non-LLM selector (agent null in 5 prior studies).

## 3. Task, policy and utility definitions

Task `tau = (c, d, A, O, B, U)` as `policy_memory.ResearchTask`. A task = a 64-compound purged chemical batch x a lineage group (search/held-out lineage split from
`observable_state_20261018/STAGE0.json`), observations = published PRISM values (no synthetic noise in the primary grader; synthetic probe noise only for the H0
split-noise test), A = pool reads (23 pools, 3 reads per compound), U = qualified nominations among unmeasured pairs per 64 compounds (registered event rule; 32
nominations, <= 3 per compound). Candidate procedures (finite, non-LLM): prior only; ridge+feedback; mixture mean; kNN-K10; R1; random forest; fixed A-optimal vs
posterior-sampling read order (`observable_state_20261018/policies.py`). Every procedure is run on every task, so per-task utilities are **observed, not
counterfactual** (replay). Utility is never pooled across units.

## 4. Policy memory and reliability

* `PolicyExperience` records (`policy_memory.py`): task, policy, baseline, delta_u, ci95, unit, tier, outcome, dependence group, failure mode, applicability. Negative
  and withdrawn results are stored as records. Independence = number of dependence groups (families/lineages), never records or noise draws.
* The 13 study-level records are context only. Training data for the meta-selector = per-task observed utilities from the generated task panel; the memory for a
  held-out task excludes its family and lineage (`leave_group_out`).
* Task descriptors (legal at decision time): chemical-family size/novelty, max Tanimoto to training set, seed-pool response statistics, lineage group, available
  DepMap state counts. No hidden outcomes.
* Virtual Cell reliability (`ReliabilityReport`): disagreement across the model classes above, calibration residual on training tasks, domain distance, in-scope flag;
  refusal and fallback to the strongest simple baseline. `choose_under_uncertainty` compares proceed / acquire / test-assumption / baseline in one unit.

## 5. Arms (feasible in the first study marked *)

Fixed best-on-training policy*; random policy*; expert rule (ridge+feedback)*; non-LLM meta-selectors on the same descriptors* (nearest-task retrieval; regularised
regression on descriptors; reliability-gated rule); Virtual Cell + fixed policy*; **EG-RPT non-LLM** (retrieval over evidence-qualified memory + reliability gate)*; oracle
(hindsight, unavailable)*. Agent-only, agent+VC without memory and full agent EG-RPT: **not run unless H1 holds** (declared infeasible/unpowered otherwise). Ablations*:
no failure memory, no reliability report, no cross-task transfer (within-family memory only).

## 6. Splits and data roles

`D_search`: folds 0-1 x search lineages (build the panel, derive thresholds). `D_select`: fold 2, bounded pass/fail through `observable_state_20261018/masked_interface.py`.
`D_transfer`: folds 3-4 x held-out lineages, evaluated once after a hashed freeze. Everything is exposed PRISM 19Q4 => internal development assessment.
External confirmation requires an independent screen (sealed PRISM 24Q2, GDSC/CTRP-style, or new experiments): **blocked**, not authorised.

## 7. Statistics and power

Cluster = MoA family (chemical axis) and lineage group (context axis); bootstrap 4,000 draws seed 20261018, one-sided family sign-flip, Holm over H1 comparisons. Power is
derived in Phase 0 from the split-noise reliability, not from the unreliable campaign-level SDs; the carried scale (acquisition-like SE 0.07-0.08 at ~2,300 compounds,
predictor-changing SE ~0.2) means a selector that changes the predictor needs thousands of compounds and is declared descriptive in advance unless the pilot SE is small.

## 8. Costs and reporting

Costs itemised (assay_wells, compute, curation, rounds, logical queries), hypothetical, with sensitivity at x0.5/x2 per-read price; no double counting between Delta U and
cost. Report prediction metrics, perturbation- and context-specific metrics, terminal utility, regret vs oracle, selected-candidate error, false progression/rejection,
calibration and domain applicability for every arm.

## 9. Stop, continue, reroute, promotion

Stop at H0 failure. Reroute by headroom/identifiability/transport (`observable_state_20261018/research_edit.route`). Continue to the agent arm only if the non-LLM
EG-RPT beats the fixed policy and non-LLM selector. Promote nothing without independent confirmation; a failed hypothesis rejects that hypothesis, not MAESTRO.

## 10. Minimum repository changes

New files only (`policy_memory.py`, `experiences.py`, audit, tests, verify); reuse `observable_state_20261018` (masked interface, policies, STAGE0 splits) and
`feedback_propagation_20261018.bench`. Not built: the task-panel generator, meta-selectors, reliability estimators, any run.
