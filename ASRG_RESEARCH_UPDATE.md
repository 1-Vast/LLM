# Research-claim update: Action-Supported Repair Geometry

The first E0-DIR hypothesis is retained as a separate comparison, but it is no
longer the only route to a useful experiment. The current primary research
question is narrower:

> Given a target response, a current actionable candidate, and a fixed candidate
> set, can an effect representation preserve the directions that real candidates
> can change, and can that information improve final-candidate selection?

## What changed

`ideal_hat` is no longer required for the exploratory action-supported path. The
registered State backend still predicts only registered concrete drug conditions.
The new path operates on a common response-effect space and uses:

```text
delta_a = predicted_response(a) - predicted_response(a0)
gain(a) = 2 r^T W delta_a - delta_a^T W delta_a
r = target - predicted_response(a0)
```

This is an analytic baseline. Under the same unweighted squared loss it is
algebraically equivalent to choosing the candidate with the smallest predicted
distance to the target. Its value is therefore diagnostic: any learned ASRG
controller must beat this baseline under equal candidate menus and budgets.

## Exploratory result

`evaluation.asrg prepare` and `evaluate` ran on the existing SciPlex3 condition
table and the previously generated molecular-holdout prediction artifact:

- 276 condition-level tasks;
- 23 reference molecular clusters;
- mean observed gain over the initial candidate: `0.5744` normalized loss units;
- cluster bootstrap 95% interval: `[0.1193, 1.1382]`;
- replacement worse than the initial candidate: `37.68%`;
- analytic choice exactly equalled nearest predicted candidate on every task.

This is **exploratory inspected-holdout evidence**, not a fresh confirmatory
result. The prediction artifact was produced by the earlier model-validation
run, and all candidate predictions were precomputed. It does not establish
four-query efficiency, a learned value model, external generalization, a causal
mechanism, or a wet-lab effect.

## Required next studies

1. Freeze an independent split and train a small effect predictor using only
   out-of-fold features.
2. Compare fixed response representations, predictive representations and
   action-ranking representations.
3. Add action support to each proposed subgoal: a latent/effect prototype must
   carry its registered candidate set and applicability context.
4. Train and evaluate an operation-value model from held-out real responses;
   never label a branch from residual magnitude.
5. Compare the analytic baseline, ordinary nearest-candidate search, balanced
   search, ASRG without an LLM and ASRG with an LLM.
6. Use Cell Painting/L1000 only as separately conditioned external validation;
   mismatched cell context, time and platform cannot be treated as paired truth.
7. Reserve target engagement, protein/phosphorylation and rescue experiments for
   later mechanism claims. They are not required to start the response-selection
   study, but are required before interpreting a residual as a biological failure
   source.

