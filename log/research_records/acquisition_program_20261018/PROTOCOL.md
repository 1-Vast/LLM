# Acquisition-value programs on a whole-pool target task: protocol

Study: `research/acquisition_program_20261018`. A bounded Auto-Research development cycle on experimental decision-making.
It is distinct from `feedback_propagation_20261018`: the registered R1 result (STOP at P1) is preserved and is not a
prerequisite. All data are exposed PRISM 19Q4; every result is an **internal development assessment, not independent biological
confirmation**. No sealed tier is opened; nothing is committed or pushed; predecessor studies are untouched except for an
appended clarification in the predecessor's `REPORT.md` section 8 (hindsight diagnostics).

## 0. Clarification of the predecessor's hindsight diagnostic

`D_hindsight` of the predecessor chose between rules per compound by squared error on unmeasured cells, a model-fit
criterion, not terminal decision utility. Recomputed from its public records (`hindsight_clarification.py`): choosing, per
complete campaign, the better of the ridge and R1 nomination lists by realised hits gives 131 hits against R1's 100 (ridge
95) over 36 campaigns. This is an unavailable hindsight diagnostic, never a policy.

## 1. Task (immutable once frozen)

* Compounds: an unseen, chemically purged batch (the predecessor's fold construction and purge at Tanimoto 0.5).
* **Target set of whole pools.** The 23 pools are ordered by a salted hash (`tc.h("pool<id>", "ap-target-group")`) and cut into
  four groups of 6, 6, 6 and 5 whole pools. A task is (fold, group). Nominations are restricted to admissible lines
  (≥ 90% training-finite) of the group's pools. **Probes may only buy pools outside the group**, so no probe reveals a target entry.
* Events, nomination constraints (32 pairs per 64 compounds, ≤ 3 per compound), budget (3 pools per compound) and scoring
  (ridge-plus-feedback conditional mean → `call_score`) are those of the predecessor and are never edited. The predecessor's
  endpoint is not revised.
* Decision under study: after a fixed seed pool (the first non-target pool of the A-optimal order), which of the remaining non-target
  candidate pools to read second; the third pool is bought by the **fixed policy** (the next pool of the fixed order not yet read).
  The fixed design is: second pool = next in the fixed order.
* Units are hypothetical pool wells; no plate/well mapping exists. All policies buy exactly 3 pools per compound; lines per
  compound are reported (pools hold 19-25 lines).
* Immutable backend: structure prior + low-rank-plus-diagonal covariance, ridge-plus-feedback update (`rules.conditional_mean`).
* Comparators rerun under this task (identical fixed-design histories): prior, ridge-plus-feedback, mixture mean, empirical
  covariance (0.1), kNN (K = 10, 20, 40), random forest, R1 (K = 10, lam = 1.0), gated R1 (kill loss). The predecessor's
  value-greedy closed loops are replaced by the acquisition policies below (their target is not separable from the pools they buy).

## 2. Data roles and noise

* Development tasks: folds 0 and 1 (each trained on the other, after the purge), groups 0 and 1, all complete campaigns (15 and 17).
* Paired noise scenarios: five frozen draws (`dev1`..`dev5`) keyed by (core, salt), identical for every policy; the same training
  support (one world per fold) for all policies. Noise scenarios are **not** additional biological samples: they are averaged
  within a compound and never counted as units.
* Held-out task groups (used only after the freeze): folds 2, 3, 4 (trained on the other four), groups 2 and 3, all complete campaigns,
  five fresh noise draws (`fresh1`..`fresh5`). These folds were opened by earlier studies; this is an internal assessment.

## 3. Handwritten one-step lookahead baseline (conventional)

Per compound, from the seed history only: the joint Gaussian posterior of the latent profile; for each candidate pool, 16
posterior-predictive outcome vectors of the whole pool (joint over its lines, with probe noise) are sampled; each is applied by the
exact Gaussian update; 32 posterior profile draws on the target lines give **posterior-sampled event estimates** with the
registered event rule (`tc.events` on the full profile); the terminal utility of an outcome is the sum of those event estimates over
the 3 target lines the ridge scoring rule would nominate; `la` is its mean over outcomes. Value = `la`; ties go to the fixed order.
Model probabilities are unvalidated estimates; their calibration is reported, not assumed. Posterior sampling is a planning
instrument; it never grades anything.

## 4. Editable object: the acquisition-value program

An expression over `la, ev0, gain, vr, vr_rel, shift, flip, rank, n_lines, obs_min` (definitions in `ap_search.FEATURE_HELP`) with
`+ - * /`, comparisons, numeric constants, `abs sqrt log1p exp tanh minimum maximum where zs rk`; no powers, no names other than
features, at most 400 characters; argmax over candidate pools. Agent-generated edits are restricted to this object. Every agent
proposal states, before evaluation, a falsifiable decision hypothesis, the expected nomination change (share of compounds
choosing a different pool than the incumbent and the direction of total events) and then records the observed result.

## 5. Search design

* Profiling (one development campaign, 64 compounds): building a scenario costs 25-55 s per campaign (features and counterfactual
  table); evaluating a program on cached cells takes seconds. Budget fixed at **12 proposals** per search, for every searcher.
* Arms: (a) fixed design; (b) handwritten lookahead `la`; (c) budget-matched conventional search: 12 random linear
  combinations of `zs(la), zs(gain), zs(vr_rel), zs(shift), zs(flip)` (weights uniform(−1,1), rounded to 0.01, seed 20261018);
  (d) agent search: 12 proposals by `deepseek-flash` through the project client with the incumbent, aggregated development results
  of previous proposals and their stated hypotheses.
* Both searches start from the incumbent `la`. Development objective: total target events over the 20 development cells (2
  folds × 2 groups × 5 scenarios). **Acceptance rule**: a candidate replaces the incumbent only if its total exceeds the
  incumbent's and it wins more cells than it loses; otherwise the incumbent is retained and the allocated cycle continues. Invalid
  proposals consume budget. The search trace is complete and retained.
* Seen before FREEZE1 (development cells only): fixed design 305 events, handwritten lookahead 337 (+0.100 per 64 compounds [-0.003, +0.199]), the
  unavailable hindsight choice ceiling 410; comparators prior 230, mixture mean 324, kNN10 370, R1 395, gated 401.
* The selected incumbents are frozen (`INCUMBENTS.json` in `FREEZE.json`) before any held-out scenario is built.

## 6. Held-out internal assessment and uncertainty

Arms: fixed, `la`, conventional-search incumbent, agent-search incumbent, and the comparators of section 1. Per-compound events are
averaged over the 5 scenarios, summed over the 2 groups and divided by 2, expressed per 64 compounds. Interval: family-cluster
bootstrap (4,000 draws, seed 20261018); one-sided family sign-flip p; contrasts: lookahead − fixed, each searched incumbent −
fixed, − lookahead, agent − conventional. Practical-effect floor 0.1875 events per 64 compounds (carried from the predecessor's
derivation; the choice is free of extra budget, so this is a complexity floor, not a cost equivalence). Reported with every
contrast: totals per task and scenario, unknown nominations, lines per compound, agreement with the fixed design, choice
histogram, calibration of `la`, and the unavailable hindsight ceiling of the acquisition choice (per compound the candidate whose own
top-3 contains the most true events; reads the outcome; never a policy).

## 7. Reading rules

An individual candidate failing is recorded as such and the incumbent retained; no individual failure becomes a project-wide STOP.
Unchanged performance is reported as unchanged. A gain is a development finding only. Virtual-cell/posterior simulations support
planning and never grade a program. Noise seeds are not biological samples.

## 8. Files

`ap_task.py` (task, features, grammar), `ap_build.py` (parallel cache), `ap_search.py`, `ap_analyse.py`, `run_search.py`,
`evaluate.py`, `seal.py`, `verify.py`, `test_science.py`; outputs `SEARCH_TRACE_*.json`, `INCUMBENTS.json`, `RESULTS.json`, `REPORT.md`.
