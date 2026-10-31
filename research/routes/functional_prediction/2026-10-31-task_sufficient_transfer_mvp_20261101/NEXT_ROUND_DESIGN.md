# Next-round design: test transferable next-treatment contrasts first

Updated: 2026-10-31 (Asia/Shanghai). Maintained research design, not a frozen numerical protocol.

## Decision and evidence inherited

The immediate research object is a bounded biological relation that can be tested with inexpensive functional measurements. A complete cell simulator is not a prerequisite. Full outcome-distribution sufficiency, organoid construction and Agent policies are later, separate claims.

The [static decision baseline](../2026-10-31-decision-focused-selection-mvp/REPORT.md) remains PARKED: saved-run active overlap/regret are raw-k20 .21203/.99476, ordinary ridge .19857/1.03248, and decision-top10 ridge .18684/1.12913. The last arm is ridge on binary top-set membership, not a direct optimization of selection regret or a general SPO test. This one surrogate result does not reject decision-focused learning as a field. No additional static-head tuning is the research priority.

Verification layers remain distinct: original verifier FAIL; post-clarification saved-prediction arithmetic supplement PASS (1,403 queries x three methods, zero primary-metric error); scientific gate INCONCLUSIVE. Model fitting was not independently certified by that supplement. Earlier GAT all-arm replay uses different transforms and metrics; corrected comparable replay is still outstanding and cannot be treated as a biological failure.

The [cross-field report](../2026-10-31-crossfield-state-learning/REPORT.md) and [independent challenge](../2026-10-31-crossfield-state-learning/CHALLENGE.md) establish prior ownership of PSR/R-PSR/PVE/VIB/SPO, active identification and causal transport. DBP and ordinary response-panel ridge are close biological/statistical rivals. No mathematical-method novelty or validated cell-state discovery is claimed.

## Primary scientific question

Let H be prior treatment history, S an early measured functional state available before the next action, and Y a fixed later functional loss. The initial action menu and selection-regret oracle are exactly {A,B}. Expanding the menu requires checking every relevant contrast against a declared reference action; one invariant pair does not certify whole-menu utility. Test

```text
tau(s,h) = E[Y(A)-Y(B) | S=s,H=h]
tau(s,h) approximately equals tau(s)
```

Define the outcome direction and scale before testing. For lower-is-better Y, negative tau favors A. The tolerance concerns the action contrast across histories, not equality of both absolute outcomes. History may change a common baseline term b(s,h) while leaving the action contrast stable. A reproducible biological relation, the measured conditions where it holds, and an informative failure boundary are potential scientific results; the generic invariance formula is inherited theory.

Keep S and H distinct. The first S consists of pre-action measured growth/viability and any prespecified functional readouts. Recorded history identity/descriptors enter stratification and the S-plus-H comparator, not S by default. Including the full H in S would make the displayed invariance tautological. If a current exposure measurement or other history-derived descriptor is deliberately included in S, declare it before fitting and require nontrivial state overlap across distinct histories; an encoded history identifier cannot satisfy the claim by definition.

There are three different targets, to be reported separately:

1. contrast magnitude equivalence within a prespecified consequential margin;
2. treatment preference/sign preservation outside a prespecified tie/abstention zone;
3. absolute efficacy, safety or distribution-tail prediction, which require extra calibration and cannot follow from 1 or 2.

A sign-only result supports a bounded choice rule, not the displayed magnitude-equivalence claim. Similarity on a compressed state alone is not sufficient evidence of true overlap or equivalence.

## Resource triage before modeling

Reuse the existing [functional-state](../2026-10-31-functional-state-drug-response/report.md), [paired-resource](../2026-10-30-paired-functional-resource-r2/report.md), [dose-window](../2026-10-30-dose-window-transfer/report.md), and [cross-field causal source](../2026-10-31-crossfield-state-learning/causal_sources.md) audits before new searches. Prior exposed endpoints stay exposed. Neither file existence nor matching drug/cell names authenticates a sequential experiment.

Use claim-specific admission rather than demanding every ideal modality:

| Resource tier | What is actually present | Permitted conclusion |
|---|---|---|
| Static endpoint | drug/cell context and one terminal response | Static prediction/selection only; no history transport |
| History x next-action endpoint | authenticated history, two supported subsequent actions, dose/time, controls and preparation/replicate identity | History-dependent contrasts or preference reversals; no measured-state sufficiency claim |
| Early state + history x action endpoint | above plus a pre-action state with a valid preparation/sibling join and state overlap | Conditional contrast equivalence and a source-frozen transport test |
| Independent transport | above plus independent reserved preparation/history blocks | Validation of the frozen contrast rule within the declared scope |

Baseline growth/viability is the first candidate measured state; recorded history/exposure supplies the design and comparator information, subject to the S/H separation above. A standardized panel of two to four functional probes is a proposed increment, not a mandatory count or a precondition for the endpoint census. Single-cell omics, spatial measurements, ECM and proteomics are not prerequisites. Chemical/MOA labels are required only for the particular chemical/MOA holdout claim; supported-menu history transport can be tested without a new-action scaffold benchmark.

Record physical dose, time, observation availability, control, continued exposure/washout or carryover, preparation lineage, endpoint denominator and replicate identity whenever relevant to the chosen estimand. Unknown schedule or incompatible assay joins do not qualify. Destructive state assays need randomized/exchangeable diagnostic and endpoint sisters, not the same cell followed after fixation. Observational next-action assignment needs explicit identification assumptions; do not silently call it randomized evidence.

If only endpoint data qualify, first test whether the proposed histories change the relative action choice beyond assay uncertainty. If no meaningful history-dependent contrast exists, there is no demonstrated need for a special history-resolving state in that setting. This is a development gate, not license to select histories from confirmation outcomes.

## Minimum discriminating design

Two authenticated histories x two randomized next actions is the minimum factorial skeleton for a local contrast test. It does not specify adequate sample size or establish transfer to unseen histories. Use independent preparation blocks, common assay/readout, matched scheduling, and adequate overlap in a source-defined state or a small justified state model. Do not manufacture overlap by collapsing an encoder.

Define the first decision time and A/B menu; use one endpoint and dose/time regime. Choose development histories without future confirmation outcomes. Test known-history contrast variation and state noise on development blocks. Freeze state definition, probe selection, model, outcome scale, meaningful equivalence margin, tie/abstention rule and costs before testing reserved preparations/history. Power/precision planning uses source-side repeat variability and feasible decision-loss headroom; no universal replicate count or unattainable margin is imposed.

Use separate blocks for choosing/admitting a relation and for assessing held-history prediction, or predeclare a joint analysis accounting for selection. Failure to reject a history-by-action interaction is not evidence of equivalence. For noisy continuous S, use predeclared coarse strata or a small conditional-contrast model and report its assumptions, overlap and precision.

Randomizing the next action after S identifies effects among eligible preparations at that decision. It does not identify the total effect of H or outcomes in cells eliminated before eligibility. A biological mediation claim would require additional state-targeting intervention evidence.

## Small models and fair comparators

Start with baseline count/growth, recorded history and exposure covariates. Compare a state-only next-action contrast with a state-plus-known-history contrast on common support. Add probes only if they resolve a documented predictive blind spot. Compare:

- direct conditional response/contrast regression with no bottleneck;
- ordinary response-panel ridge/covariance and supervised reduced rank or PLS;
- count/growth/recovery/exposure models;
- DBP or an appropriate mechanism-specific functional probe where the endpoint is apoptosis;
- a fixed minimal probe panel versus the candidate panel at the same actual assay budget.

A categorical unseen history ID is not a meaningful extrapolating comparator; use recorded history descriptors or a declared population-level fallback. GAT is relevant only if transcriptomic inputs are actually present. Do not require GAT, chemistry, spatial or gene inputs when absent from the functional-only task.

The first test is not a new latent architecture. If ridge using the same probes matches the proposed representation, no special representation claim survives. A genuinely new informative measurement or validated biological relation may still matter, but requires biological closest-prior comparison; numerical equivalence alone does not erase that possible contribution.

## Evaluation and staged decisions

Report contrast error/equivalence interval, treatment-choice regret against the supported menu, preference reversal prediction, tie/abstention coverage and risk, and absolute endpoint calibration separately. Cost includes control wells, probes, biological material, repeats and result-availability time. A smaller embedding computed from all assays is not a measurement saving.

Use preparation-block uncertainty; wells and cells within one preparation are not independent samples. Margin and precision must distinguish support, refutation and inconclusive evidence. Freeze metric direction, residualization if any, finite masks, ties, eligible populations and oracle definition; require an independently authored metric implementation before outcome access. A clarification-only post-run arithmetic PASS is not a protocol-conformant independent model replay.

Stage 1: qualify accessible history/action endpoints and test whether a consequential contrast or preference change exists. Stage 2: test whether a cheap measured S accounts for that variation within common support. Stage 3: evaluate a source-frozen rule on independent preparations and reserved histories. A later-action chemotype holdout is a separate claim from holding out the chemicals used to create the history. Never merge them into one generalization label.

Park this candidate if assay uncertainty/poor overlap makes the relation untestable, the contrast does not transport, probes add no useful information relative to cost, or an existing biological profiling method already supplies the claimed capability. Record information failure separately from biological refutation. Do not rescue a failed premise by increasing model size or adding an Agent.

## Conditional cell-to-organoid and Agent extension

An independently supported, scientifically substantive cell-level functional relation may justify a minimal organ-specific extension. Full outcome-distribution equivalence is not an obligatory intermediate gate for a contrast-specific model; its claims must remain bounded. Exceptional drug-discovery value and novelty still require independent evidence before core promotion.

For one organ-specific decision, compare an additive mixture of independently predicted cell functions with the smallest interaction model. Measure composition/context and later organoid function. Omission/add-back, ligand blockade, matrix/flow or exposure interventions must support corresponding interaction claims. Use donor/batch separation when making donor/batch transport claims. Predicting a cell endpoint does not establish organoid function.

After an organoid model has demonstrated its own held-out utility, test an Agent that selects measurements distinguishing intrinsic resistance, local exposure failure and intercellular protection, or requests a justified fidelity change. Compare deterministic VOI/POMDP, BO/active learning and fixed/random design with identical available observations, actions, total assay/time budget and stopping rules. Agent prose cannot revise the biological law or supply unobserved mechanisms. Equal deterministic performance leaves the Agent an operational interface.

## Current status and immediate next action

Decision-focused static surrogate PARKED; action-contrast research DATA_QUALIFICATION_PENDING; Virtual Cell core NOT_ADMITTED; AIVO/Agent DEFERRED.

Next action: audit already located functional resources for history x supported next-action endpoints, controls, schedule and preparation identity; classify them using the tier table. Only then assess whether baseline/probes can support a frozen contrast test. No eligible new dataset or experiment is asserted by this design update. The separate GAT replay repair remains an engineering work item and neither validates nor vetoes the biological route.
