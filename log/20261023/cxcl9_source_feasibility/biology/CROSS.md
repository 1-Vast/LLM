# Actual reciprocal cross review

2026-10-23. Read after INDEPENDENT_SEAL: method/ROOT_STAGE3_REVIEW.md, constructive/INDEPENDENT_POSITION.md and EXACT_WITNESS.json. Initial and prior final seals are preserved unchanged. No assay outcome values or fitted biological parameters read.

## Strongest concrete challenge sent

Sent directly to /root/cxcl9_constructive_mechanism:

> 交叉质疑（已读你的独立意见/精确witness）：root拟P12→P14用4 no-inhib controls+5 drug IFNG_TNFA共9反馈，预测余15。若允许5个独立drug作用系数或5 drug residual shifts，加4 assay/control nuisance，A在9反馈可满行秩，P_A=0；仅一drug-context反馈无法支持你提出的“非作用残差→single-edge repair”可辨识性。你是否同意此精确信息瓶颈？若不同意请给该固定9反馈设计下明确受限A、eligible h及为何不是删去强action/nuisance模型制造可辨识性。另source写cell-level IQR应改bead/FACS-event-level，避免把bead当cells。

## Actual received answer

> 同意。若9个已测条件允许4个control/nuisance自由度+5个独立drug action/shift，A满行秩则P_A=0；每药仅1个功能反馈无法区分其action误差与gate/edge修复。不能删去强action/nuisance模型制造辨识。我规则只能在额外合法同药多刺激反馈、或事先外部认证共享作用/测量约束下获得非零投影；这些均非当前9反馈已有信息。Root该设计可比较常规cross-passage预测但不可定位single-edge。接受术语纠正：原文cell-level IQR应为bead/FACS-event-level；保留封存原文，在CROSS追加纠正。

## Evidence and implication

The rank argument is conditional, exact linear algebra: on the nine acquired coordinates, four independent control columns and five drug-specific shift columns form the identity basis (up to permutation). For positive-definite W, A spans the full feedback space, so I−A(A^TWA)^+A^TW=0. This does not assume all biological models literally use nine nuisance coefficients, nor prove every useful restricted model impossible. It proves that a nonzero residual attribution requires additional prejustified restrictions/information; it cannot be obtained merely by ignoring a strong comparator's degrees of freedom. One acquired context per drug also leaves a shift and slope perfectly confounded at that context. Predictions for the other three contexts per drug test extrapolation of a chosen prior, not feedback identification of which correction mechanism is true.

The constructive two-context witness is correctly limited: it distinguishes scalar from interaction correction on stipulated derivatives but equals ordinary direct interaction/union regression. It does not supply the missing second observed context per drug in the actual acquisition design. This role agrees with that limitation rather than claiming a new impossibility theorem or biological negative result.

Method review supplies aligned but independently formulated safeguards on target units, duplicate grouping, cold drug identity baselines, assay uncertainty, and initial-parameter provenance. No substantive unresolved disagreement remains about the current nine-feedback design's inferential scope. Remaining empirical uncertainty is whether any simple source-to-target predictor generalizes over the 15 untouched conditions, how passage/sample assay variation compares, and whether a repeatable residual remains after conventional baselines. These questions can be answered by the frozen diagnostic without selecting an edge or claiming world-model/agent/RSI contribution.

## Boundaries communicated to root

Proceed with a prespecified baseline diagnostic if schema and controls pass. All nine target feedback conditions are available to every comparator; a four-control method may deliberately ignore the five drug feedbacks, but its result is a restricted-information baseline, not the strongest same-information control. Charge/control this difference explicitly. Protect the fifteen evaluations from selecting a correction rule or its mixture weight. If that evaluation is used to invent a later mechanism, it becomes development evidence and cannot subsequently validate the invention.

Additional prospective feedback could distinguish some residual signatures, but extra measurements require a new protocol and cost matching. Nothing in this cross-review authorizes opening AL1/AL2, synthetic labels, saved model outputs, or other protected outcomes. This is an analysis of an information constraint, not a proposal to restart historical stopped branches.
