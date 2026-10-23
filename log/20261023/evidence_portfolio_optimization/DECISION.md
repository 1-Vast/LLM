# Paid feedback helps repeatability; a new core is not established

Question: can an adaptive two-stage purchase policy improve repeated positive observations at equal total read cost?
Frozen rule: at threshold 0.10, feedback/fixed >= 1.20, positive SIDM-bootstrap difference versus fixed, and a positive difference versus fixed paired acquisition.
Result: 919 repeats versus 675 fixed-scout and 876 fixed-paired; +43 versus the strong control, conditional 95% interval [9, 78]. Simple post-result gate plus original rank achieves 898.
Decision: DEVELOPMENT_FEASIBILITY_PASS for the frozen repeatability task; retain ordinary feedback screening, but no demonstrated new core and no certification/RSI expansion yet.
Does not show: true-hit FDR, prospective wet-lab utility, world-model, agent, inheritance, joint or recursive gains.

## What the actual data show

One frozen metadata-defined pool contains 5,390 single-anchor units across 78 SIDM clusters. Global validation-plate roles are disjoint. Every arm pays 3,234 reads, represented by 22,638 combination-well proxies. No selected read was missing. The data were already exposed and validation-selected; this is a developmental replay, not a fresh confirmation trial.

| Policy | Scout reads | Final reads | Both reads > 0.10 | Repeats / 1,000 proxy wells |
|---|---:|---:|---:|---:|
| Fixed original rank after same scouts | 2,156 | 1,078 | 675 | 29.82 |
| Scout magnitude feedback | 2,156 | 1,078 | 919 | 40.60 |
| Equal original/scout rank mix | 2,156 | 1,078 | 830 | 36.66 |
| Fixed hash after same scouts | 2,156 | 1,078 | 513 | 22.66 |
| Strong fixed paired acquisition | 1,617 | 1,617 | 876 | 38.70 |
| Post-result scout gate + original rank | 2,156 | 1,078 | 898 | 39.67 |
| Post-result scout gate + hash | 2,156 | 1,078 | 869 | 38.39 |

Feedback beats the shared-scout fixed arm by 36.1%, but the stronger equal-cost fixed-pair arm narrows this to **4.91%**, or **1.90 repeats per 1,000 proxy wells**. Cost-aware post-result resampling gives a conditional interval [0.40, 3.28] repeats per 1,000 proxy wells. These intervals resample fixed-policy contributions by SIDM; neither they nor the number of bootstrap draws establish prospective policy significance or independent biological tasks.

The ordinary gated-original control captures most of the gain. Feedback's additional 21 repeats have a fixed-count interval [-11, 52]; the cost-aware difference is 0.93 per 1,000 wells, interval [-0.01, 1.88]. Superiority over that simpler control is not established; equivalence is not established either. The control was added after the primary result, with explicit post-result status and choices saved before converting its additionally required final responses.

At threshold > 0, feedback has 1,061 repeats versus **1,409** for fixed paired acquisition. Feedback's maximum possible repeats are only 1,078, so this sensitivity loss is structural at the fixed budget allocation. Do not retune the threshold, budget, role split or seed on these outcomes. At the primary threshold, final-only positive counts are also lower for feedback (919 versus 1,037 fixed-paired). The positive primary result is specifically a two-read repeatability acquisition result.

## Why this is useful but insufficient

The selected scout is itself one half of the primary endpoint. Paying to discard scout failures can improve observed repeats even if the scout magnitude has no predictive information about the later read. A simple independent-positivity example is recorded in [the post-result plan](SIMPLE_CONTROL_PLAN.md). This is an operational benefit with an explicit paid contract, but it cannot establish a learned updating law, lower latent false-positive rates or cell-state prediction. The post-result gated controls are necessary to distinguish ordinary filtering from magnitude-based prediction.

The three independent reviews and actual cross-discussion corrected the original final-only design before outcomes: direct acquisition would have contained all possible adaptive finals, making the proposed win impossible. The schema-only freeze also failed on 2,880 multi-anchor rows before response conversion; the task now explicitly excludes those metadata records. See [pre-freeze revisions](PRE_FREEZE_REVISIONS.md). These failures are preserved rather than counted as biological negative results.

Primary literature already covers adaptive e-growth allocation, e-BH, iterative proxies, mixtures and self-edit gates. This does not rule out contributions using established estimators, but the attachment's generic portfolio/credit wrapper is insufficient novelty. Same-stream expert scores do not identify unobserved allocation trajectories, and half weight per multiplier is not half protected capital. See [the primary-source review](PRIMARY_REVIEW.md).

## Code changes and verification

- The unfinished Gate 1 prototype now fails closed on missing required pools/cells; even a pass is explicitly diagnostic. Failed or empty synthetic test selections exit nonzero. Empty admissible numerical bet grids refuse a fallback. Finite-grid and fitted-noise checks no longer claim mathematical certification.
- Prototype prepared arrays, weights, traces and detailed replay tables route to `data/processed/`; key summaries remain in `log/`. No `src/` or `tools/` implementation was promoted. The full fitted-noise Gate 0/1 campaign was not executed.
- Four statistical primitive groups passed; nine lightweight regression/integration checks cover failure propagation, metadata-only eligibility, future-value noninterference, missingness, costs and schema handling. These software checks do not validate biological assumptions.
- The independent verifier reconstructed eligibility, global roles, selected original/scout/final values, nominations, charges, counts and all 2,000 bootstrap draws from the source CSVs. All ten frozen bindings remained unchanged. It also reconstructed post-result control choices/results and the cost-aware sensitivity. See [numeric audit](NUMERIC_EVIDENCE_AUDIT.json) and [result evidence review](RESULT_EVIDENCE_REVIEW.md).
- A transient supplementary-plan binding mismatch was caught during concurrent auditing and restored to the original bytes without replacing its receipt. The failed audit and resolution remain in [audit events](AUDIT_EVENTS.md).

## Next research contract

Keep the ordinary binary-gate-plus-prior policy as a required baseline. Before another core-mechanism claim, define a downstream outcome whose success is not partly the already-used selector, identify a justified real acquisition cost and independent future task unit, and demonstrate an incremental update benefit over direct prediction, ordinary conditioning/retraining, simple gated screening and equal-budget allocation. Compute structural headroom and detectable effect first. Do not reopen this frozen split to optimize its threshold or budget.

Only then test a distinctive world-model or update mechanism on the same information, followed by inheritance across independent ordered tasks. A later RSI test must compare the changed improver with its frozen predecessor and ordinary equal-budget search. No current arm is a learned world model, an LLM agent, an inherited updater or an improved improver, so all five required contribution claims remain unestablished.

Real-data work here uses Jaaks only. No AZ numeric outcome, reserve, new wet experiment, GPU training or DeepSeek request was used. Literature retrieval retained five successful source bodies and two denial responses outside `log/`; browser discovery operations are additional, uncounted in those seven local HTTP receipts. Native-agent token/currency costs were unavailable. The overall research goal remains active.
