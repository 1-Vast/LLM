# Independent A1 arithmetic and access review, initial version

2026-10-31. Source investigator review of frozen `a_protocol_v1.md`. The source report and identity admission artifacts are complete under `egi_admission/`. This review is correctness/access work, not scientific-core design. **Synthetic arithmetic passes; the two protocol clarifications below remain required before numerical launch. Root implementation integration has not yet been checked.** No real count or GI value was accessed.

`a_arithmetic_expectations_v1.json` was written before any reading of `a_experiment.py`. `a_check_arithmetic.py` is a standard-library independent reference with hand-computable fixtures. It never opens a real count/matrix, imports the experiment or executes author code.

## Required clarifications

1. **Shared T0 eligibility versus source-only predictors.** The protocol retains constructs using both cultures' T0 counts, uses the same masks for source/control calculations, and then says no target-culture values enter source fitting, graph or tuning. A target T0 change from 30 to 29 can change source eligibility and therefore source feature/graph inputs. This is a genuine declared-information dependency even though target T0 is untreated baseline information. The coordinator must explicitly admit a fixed shared baseline-eligibility exception or repair the masks so predictor construction uses source-only values. Do not claim strict absence of all target-culture dependence while using a target-dependent preprocessing mask.

2. **Median aggregation does not commute with subtraction.** The defined endpoint `Q(DRUG/UT)` is valid as a directly defined contrast. Each ordered-construct log ratio obeys `L(DRUG/UT)=L(DRUG/T0)-L(UT/T0)` for the same pseudocount construction. However, `Q(DRUG/UT)` generally differs from `Q(DRUG/T0)-Q(UT/T0)` because the three control medians are nonlinear. The fixture has 13 controls: the first single-control UT vector has nine zeros/four hundreds, DRUG vector four zeros/nine hundreds, and other terms zero. The direct difference vector has eight zeros/five hundreds, giving direct Q=0; the difference of aggregated Q values is -100. T0 cancellation must be described and implemented before medians/guide/gene aggregation. No post-access endpoint reinterpretation is acceptable.

## Independently checked expectations

- Counts are synthetic `2^k-1`, making protocol pseudocount +1 yield exact integer log2 ratios. A known pair has untreated Q=1 and environmental Q=2 for all eight two-guide/orientation constructs.
- Adding a common +3 to every L leaves Q unchanged. This proves additive log-offset cancellation; it does not assert that multiplying raw counts with an additive pseudocount is exactly invariant at low counts.
- Eight excluded single-control outliers do not affect a masked Q when five controls remain. Unmasked medians change, verifying the mask matters. The NTC-NTC support remains above 25.
- Two guides per gene give four AB and four BA ordered constructs. Four constructs with three AB/one BA satisfy the orientation gate; four constructs all from AB fail. Reversing gene or guide orientation cannot change the pair fold. Exact example folds are A-B=1, A-C=9 and B-C=4.
- A source-only input guard excludes source held-DRUG doubles and all target-culture values. Mutating source held A-C DRUG doubles leaves the independent allowed input record unchanged. A request to read a target value or held double raises an error. These tests verify the independent access partition, not yet the root implementation.

The shared T0 mask perturbation intentionally demonstrates the first clarification. The source-only input witness does not silently implement that joint-mask exception. Root's final access boundary, once fixed, must be checked against the actual implementation on synthetic values before launch.

## Limits and disposition

No scientific fit, response quality gate, headroom analysis, real matrix execution, candidate performance, error recovery or spare run occurred. No recent biological-result claim is assessed. The audit confirms local endpoint algebra and identifies a preprocessing boundary that must be stated accurately. A passing synthetic checker cannot establish empirical reproducibility, effect magnitude or biological mechanism. Preserve this original review and expectation receipt before any root response or implementation-specific update.
