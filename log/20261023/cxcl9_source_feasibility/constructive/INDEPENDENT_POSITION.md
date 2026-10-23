# Independent constructive assessment

2026-10-23. Read only supplied author source files/metadata and the preceding action_rule_search/DECISION.md; no peer opinion and no numeric biological outcome payload. No literature novelty clearance beyond the previous phase. Full goal remains active and unachieved.

## One concrete operation examined

Application: sparse inhibitor/cytokine feedback repairing a context-gated signaling interaction before ranking later CXCL9 secretion conditions. This is a proximal immune-chemokine endpoint, not demonstrated tumor control. A useful error could be a drug's effect requiring a second signaling input, rather than a uniform action-strength error.

Consider one candidate operation, **contrast-triggered single-edge repair**. At the current world, let r be the allowed functional-feedback residual, A the Jacobian of ordinary drug-action and declared assay-nuisance parameters, h_e the response sensitivity of candidate edge e, W a frozen noise precision matrix. Remove the nuisance/action span with P_A = I - A(A^TWA)^+A^TW. For each eligible edge calculate

    z_e = (h_e^T W P_A r)/(h_e^T W P_A h_e + lambda)

and select the edge giving the greatest prespecified held-feedback loss reduction after charging edit/search cost. Refit ordinary action parameters conditional on that one edge update. If the projected norm is zero, no edge attribution is possible from this batch, so do not select that edge. A later task can inherit an edge eligibility/order learned solely from prior tasks, not fitted edge values or held outcomes. The threshold must use meaningful uncertainty/utility and prospective validation, never the previous phase's shrinking absolute-effect bound.

This changes an interaction in the world rather than only drug coefficients, and ties edits to residual signatures that scalar action calibration cannot span. It does not require unique physical occupancy. Nor does it require full-state identification. It is deliberately a small operation, with one structural edit rather than a stack of editors.

## Exact discriminating witness and equally exact limitation

Toy two-context response signatures are A=(1,1), h=(0,1), true residual r=(0,1). The best scalar-only action update is 1/2 with SSE 1/2. Projection gives P_A r=P_A h=(-1/2,1/2), so the edge update is 1 and residual SSE zero. If h=A, the projected signature is zero: the two mechanisms cannot be separated by those contexts. These are stipulated synthetic derivatives, not observations from CXCL9.

But a direct predictor with drug x cytokine interaction has exactly the columns [A,h]. Ordinary union least squares on the same allowed feedback produces the same correction (0,1). The projected rule is algebraically partial regression in this local model; single-edge enumeration is best-subset coordinate search. This exact operational counterpart defeats a claim that the witness establishes an independent new learning rule or world-model necessity. It is not rejected merely for belonging to conventional mathematics: an actual nonlinear biological restriction and independently demonstrated compositional transfer could still distinguish it. That evidence is absent here.

Therefore **NONE / no core promotion** in this independent assessment. The candidate is concrete enough to falsify but currently has no justified reason to beat the required strong direct interaction, mixed-effects interaction, ordinary union refit or equal-budget coordinate/program search controls. Do not perform a biological fit merely because the toy beats scalar calibration. Preserve action-specific calibration as a valid baseline, not a straw comparator.

## What the actual source establishes

Author 02_active_learning/optimization.R lines 132-134 warm-start each round from the previous model of the same run, and refits the model using parEstimationLBode with all current MIDAS training data. That already supplies ordinary continuing/union fitting. The code uses 10 runs, 5 rounds, up to 5 convergence attempts and maxtime 4000; a new editor must charge this baseline fairly instead of treating its optimizer as cost-free or crediting our search as free.

The checked-in loop explicitly reads synthetic_data/CXCL9_values_AsPC1.csv (line 43) and inserts synthetic_mean into the next training MIDAS file (lines 266-285). A comment says experimental or synthetic, but this literal script path always uses that table. This alone does not show whether any rows inside that table were experimentally replaced, nor invalidate the paper's actual wet rounds. Values and generation scripts have not been accessed here. Hence do not label a replay of this loop as a new real functional feedback experiment without provenance for each selected label.

01_preparing_inputs.R computes cell-level IQR cleaning after pooling records by cytokine/inhibitor, then obtains per-sample condition means and performs range normalization across all that sample's conditions. A legitimate masked feedback oracle must refit its transforms on allowed training/control information or define an externally fixed assay calibration; simply masking already normalized condition means is insufficient. Cell rows are FACS measurements, not independent task/replicate units. Metadata gives two cell lines and two passage samples per line in the initial assay, plus AL1/AL2 per line; these cannot automatically supply many later-task editor generations.

02_active_learning/utils.R computes a t.test confidence interval over optimized model outputs, and greedy/uncertainty/GU/random selection. Such an interval is ensemble variation, not independently calibrated assay coverage. Repairing that terminology would not be our novel updater mechanism.

## Conditions for reconsidering the operation

Before any further response access: authenticate the real raw-functional unit and preprocessing; freeze one-step held drug/cytokine interaction task and utility; demonstrate a non-action residual signature on development feedback; compare the exact single-edge restriction against same-information direct interaction/kernel models, scalar/mixed-effects action and interaction calibration, union refit, continual learning, AL, mixtures and the identical candidate-edge search with equal total budget. Stop if ordinary interaction models explain the effect or if edge signatures collapse into the action/nuisance span.

A claim of world contribution would require held compositional contexts where actual simulated downstream structure improves decision utility over direct interaction models. Agent contribution needs identical initial worlds and data budgets. Inheritance requires unseen independent tasks with the old/new updater starting from the same world. Improved-improver requires old/new edit-selection strategy producing descendants from the same updater and history under matched total cost; inheriting an edge order alone is not that proof. The currently inspected two-context repository does not establish these requirements.

No biological fitting, API calls, new source GETs or wet experiments by this role. One exact rational synthetic witness is separately executable. Native agent model/token/money identity not attested. Previous biological/protected STOPs unchanged. No claim to comprehensive novelty rejection.
