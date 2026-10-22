## Verdict

**No defensible recursive-improvement mechanism survives as novel.** The one minimal mechanism I can state without renaming an existing estimator is an **ordinary contextual bandit over improvement operators, with a verified-attempt replay buffer and a conservative rollback**. That is a strong conventional comparator, not a new core. I therefore give (a) the strongest faithful comparator, (b) the single retained object and update that *would* be required for a genuine improvement law, (c) the exact missing premise and a test, rather than claim novelty.

## Strongest faithful ordinary comparator (the bar to beat)

- **Object:** per-operator empirical success table `Q[o] = (successes+1)/(attempts+2)` over a fixed finite operator set `O` (e.g., "increase dose", "switch to combination", "add adaptation-reversal agent", "replicate well").
- **Policy:** ε-greedy or Thompson sampling over `Q`.
- **Update:** Beta–Bernoulli posterior per operator; no cross-operator transfer.
- **Target:** next legal intervention with highest posterior mean.
- **Feedback:** verified downstream outcome on a common fresh start.
- **Rollback:** revert to uniform if the lower confidence bound of the chosen operator falls below the pooled mean.

This is a fully optimized contextual algorithm portfolio. Any proposal must beat it on identical information, matched total early+later compute/feedback/LLM-call cost, common fresh downstream starts, and independent later tasks. I do not have evidence that anything does.

## The only retained object/update that could in principle differ

The comparator treats operators as exchangeable. The only non-renamed reduction I can state is **operator-conditioned credit assignment through a shared, verified transition kernel on cell-state summaries**, i.e.:

- **Retained object:** a finite set of *improvement operators* `O` and, per operator, a small transition model `T_o(s' | s, a)` over a **fixed, pre-registered low-dimensional cell-state summary** `s` (e.g., viability + a resistance-marker ratio), plus a scalar `r_o` = verified probability that the next common-challenge run improves.
- **Update:** `T_o ← (1−η)T_o + η·δ_{observed transition}`, `r_o ←` Beta update. **No free labels**: transitions and `r` come only from verified runs on common fresh starts.
- **Next-proposal distribution:** `π(a|s) ∝ exp(β·(r_o + λ·V_{T_o}(s,a)))` restricted to legal actions.
- **Target:** maximize verified improvement probability on the *next* common fresh downstream start.
- **Legal feedback:** only outcomes of executed, logged, cost-accounted runs; no posterior oracle, no outcome-dependent test search.
- **Rollback:** if the lower confidence bound of `r_o + λV_{T_o}` under the comparator's posterior does not exceed the comparator's LCB, revert to the comparator policy for that context.

**Why this could reduce something the comparator cannot:** the comparator needs one attempt per operator per context to learn; a shared transition kernel lets an operator's *effect on `s`* inform its value in a *new* context without a direct attempt there. That is a concrete sample-complexity tradeoff — **but it is exactly the tradeoff supplied by ordinary model-based contextual bandits / Dyna-style planning**, which is the faithful ordinary control. So this is *not* novel; it is a model-based bandit. I will not dress it as new.

## Missing factual premise (the honest answer)

**Premise:** that a fixed, pre-registered low-dimensional cell-state summary `s` exists such that (i) it is measurable in the public/available data at the required time resolution, and (ii) the operator-conditioned transition `T_o(s'|s,a)` is *stable across the common fresh starts used for evaluation* (i.e., the Markov summary is sufficient and stationary over the evaluation horizon).

Without this, model-based planning over `s` collapses to the same-history direct table (already stopped) or to ordinary conditioning (already stopped). The prior sources AP1, WM1366, Watermelon, ResponseDynamics **lack the specific common-challenge/run/state-function joins** to certify this; I do not claim they qualify.

## Test for the missing premise (no wet lab, no fabricated data)

- **Data contract (to be authenticated later; not claimed available):** for each run, a record `(cellline, condition, well_id, common_fresh_start_id, time_index, s_vector, intervention, verified_outcome)`, where `s_vector` is computed by a *frozen, pre-registered* transform from raw public reporters, and `common_fresh_start_id` groups runs sharing a genuine fresh start. Wells/conditions are **not** treated as independent later tasks; only `common_fresh_start_id` × independent later task IDs are.
- **Test:** split by `common_fresh_start_id` into early/later. Fit `T_o` on early, evaluate next-proposal on later. Compare, at **matched total early+later compute, feedback, and LLM-call cost**, against the ordinary contextual bandit above. Report (a) Markov sufficiency check: does adding one extra state coordinate change `T_o` predictions beyond noise? (b) stationarity check: `T_o` fit on early predicts later transitions within pre-registered tolerance?
- **Decision rule:** if (a) fails or (b) fails, the premise is refuted and the mechanism reduces to the comparator — stop.

## One explicit finite example separating it from the comparator (toy only)

Two operators `{A, B}`, two contexts `{s=0, s=1}`, deterministic transitions: `A` maps `s→1`, `B` maps `s→0`; reward `r=1` iff next `s=1`. True: `A` good in both contexts, `B` bad in both. Comparator (per-context table) must attempt `B` in context `s=1` at least once to learn it is bad there → ≥1 wasted verified run. Model-based `T_o` learned from context `s=0` (where `A` was tried and `B` tried) transfers the *transition* to `s=1` and avoids that attempt → saves 1 verified run at matched cost. **This is a mathematical toy effect, not biological performance, and it is the standard model-based-bandit sample-complexity gain, not algorithmic novelty.**

## Counterexample / ablation that would make me stop

If, on the pre-registered data contract, the shared `T_o` gives **no reduction in verified runs to reach a fixed improvement-probability threshold** versus the ordinary contextual bandit at matched cost — or if the Markov-sufficiency check (a) shows the extra state coordinate changes predictions beyond noise — the mechanism is refuted; revert to the comparator and stop claiming an improvement law.

## Why virtual-cell transition modeling and autonomous intervention choices are necessary

Only because the *decision* is sequential under resistance heterogeneity: observed resistance may be selection or adaptation, and the next legal intervention depends on which. A transition model over a sufficient summary is the minimal way to condition the next choice on *predicted* state rather than the last observed outcome. If the summary is not sufficient/stationary (the missing premise), autonomous choice adds nothing over the comparator. I make no biological-performance claim.

## Citations

None given; I do not have verified exact references for the specific sources named, and I will not fabricate them. The stopped operations (Gaussian closure, moment bounds, PAES, MetaGenSim-like reweighting, semigroup/stencil/rank-one, state splitting, common-domination bounds) are treated as already reduced to their faithful ordinary equivalents, as stated.