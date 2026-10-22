# Actual design-to-implementation cross-review

2026-10-22. The independent position remains sealed at SHA256 da3f15aca0d932327666b89969e9b05f2f1e5b7dcd83baa4f2f7302f39763c8c. After that seal I read the user's complete expanded goal, the new PROTOCOL.md, the draft probe.py, its predecessor model implementation, and the seven synthetic tests in test_boundaries.py. I did not open new biological numerical arrays or run any fits. The expanded goal requires a substantive world/agent research contribution; this conventional diagnostic supplies possible eligibility information only and cannot itself satisfy that goal.

## Resolved design questions

The actual protocol fixes 38/14/6 feature dimensions, source identity categories, all-context input preprocessing before per-head response filtering, unpenalized intercept, sum-to-one original site/context weights without post-mask renormalization, and alpha in {1,32}. Scaling all columns including dummies/masks differs from my preference but is a legitimate frozen ordinary estimator; it is not a reason to change the design. Source-specific platform columns have zero fitted coefficients when absent from a training fold. One/zero observed target-H rows have explicit intercept/global-source fallbacks. Missing target truth is never imputed.

The protocol nests conditional and ordinary-family selection, retains the same paid controls and target masks, and makes the strongest outer benchmark an explicitly retrospective conservative hurdle. The comparison is descriptive source reuse. Its administrative 0.005 margin, component nonworsening, four-site benefit and delete-one-site checks are adequately specified. None is a clinical benefit threshold, significance test, or authorization to open a reserve.

I checked the implemented pooled-H calculation: each outer site's predictions and observed H are divided by that site's training-only scale before concatenation, then passed to the pooled loss with scale 1. This is the correct treatment of differing outer IQRs; computing a single pooled raw MAE and dividing by one arbitrary scale would not be equivalent. Raw H errors are retained separately.

## Direct challenge, response and verification

I sent the implementer and root a concrete mismatch: the protocol required paired-site and delete-one-site differences below -1e-12, whereas the draft scorer tested below zero. I also asked whether preprocessing was serialized and why all 34 candidate configurations were fitted again in each outer fold despite only selected families being primary evaluation outputs.

The implementer's actual response was:

> Corrected both gate signs to <-1e-12, strongest ordinary only 7 families + mixture + portfolio. PREPROCESSING is serialized in FIT_COUNTS and forecast seal binds it, includes input means/population SD/imputation, source context IDs, site weights, H scale. Outer all 34 predictions saved under all_candidate_predictions because root originally requested all candidate outputs; selected methods remain only score populations. Will ask root confirm deliberate extra outer audit.

I then inspected the edited file and verified both epsilon predicates, the explicit ordinary reference list and conditional_preprocessing in FIT_COUNTS. The forecast seal binds FIT_COUNTS. I replied accepting the all-candidate outer audit if its extra fits and exclusion from selection/gates are explicit in the final protocol. It creates no outer-label leakage, but its cost must not disappear from accounting. Running all candidates does not permit changing the primary or tuning it from outer scores.

The seven synthetic tests were inspected, not run by this reviewer. Their checks cover the weighted normal equations with an unpenalized intercept, source-only field projection, preprocessing before response masking, zero/one response-H fallbacks, restricted prediction inputs, fixed variant dimensions/unseen metadata, and fail-closed freeze inputs. These are meaningful checks of the main implementation risks. Actual test results and hashes remain the implementer's/root's responsibility; this note does not fabricate successful execution.

## Decision and unresolved evidence

NO_BLOCKING_DESIGN_OBJECTION after the inspected corrections, conditional on root's complete project/resource audit, passing prefit tests, preparation eligibility checks and a freeze binding final versions. This is scientific design review, not independent confirmation of numerical data or a completed postrun audit. Exact final code and protocol hashes must be frozen because implementation was still under active revision during review.

The fundamental limitations remain four training sites per outer fold, five outer transport units, sparse H supervision, source reuse, and an arbitrary composite opportunity margin. A favorable result is ordinary cross-drug conditional prediction; a failed result stops this raw linear candidate without establishing a universal nonlinear impossibility. No world, adaptive agent, inherited improver, synergy or RSI benefit is established by this design. The earlier failed multivariate configuration stays stopped, and development/reserve outcomes provide no new numerical evidence here.
