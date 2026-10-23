# Evidence-portfolio continuation: independent evidence review

2026-10-23. **Decision: retain the decision-level direction; run one small exposed Jaaks observation-allocation diagnostic before expanding certification, models or RSI.** The available census supports such a diagnostic. It does not yet support opening the AZ reserve, declaring anytime-valid biological discoveries, or treating a portfolio as a demonstrated new core.

## Review scope

Read both user attachments, `forward_perspective/PERSPECTIVE.md`, the certified-discovery `START.md`, `PROTOCOL.md`, `CENSUS.json`, and its `common.py`, `prepare.py`, `worldfit.py`, `evalues.py`, `replay.py`, `gate0.py` and relevant `gate1.py` code. Cross-checked the current research report, retained evidence index, Block Q report and AZ paid-reference decision. No source numeric payload, protected/reserve outcome, new download, fit or replay was opened or run by this review. This is source/report/code review, not independent numerical replication.

At inspection, the certified-discovery log contains only START, CENSUS and PROTOCOL. No FREEZE, prepared-data receipt, gate result or final decision is present there. The attachment's account of successful end-to-end synthetic runs and fairness retests is therefore not a recorded real-data result in this directory. Do not infer that the biological gates have run.

## What the existing evidence supports

- Ordinary feedback and transfer can have useful task-level value. The original Block Q report distinguishes its confirmed transfer claim from unconfirmed decision-planner superiority. Its one-anchor RKT comparison is 0.529 against 0.287 generic and 0.510 best single route. This is a bounded transcriptional transfer result, not evidence that a dynamic cell world or agent is necessary.
- The retained evidence index reports Block N/P content value but no established agent gain; it also discloses exposed retrospective follow-ups and source preprocessing. Preserve algorithm-held-out versus independent biological confirmation distinctions. A previous label of sealed does not make today's exposed replay fresh confirmation.
- The AZ paid-reference candidate actually lost to strong direct controls on both frozen endpoints. Its stop is not merely an underpowered positive result. A new endpoint and mechanism may be studied, but must not inherit a success claim from that stopped candidate.
- The perspective usefully shifts attention to paid observations and downstream decisions. Its stronger claim that the research search cannot succeed does not follow: a posterior-mean optimality statement does not rule out useful finite-data, finite-compute structural improvements. Likewise, some earlier gates lacking headroom do not invalidate other well-powered negative results.

## Units and independence

**Jaaks.** The census identifies 9,152 units in the original screen and on at least two distinct validation barcodes; 3,127 have at least three. A unit is `(SIDM, anchor ID, anchor concentration, library ID)`, not a biological task or a generic unordered drug pair. Validation includes 454 barcodes, disjoint from original-screen barcodes. This supports separate recorded plate observations. It does not establish independent cultures, prospective randomization, absence of shared normalization, or independence between units sharing a plate. The pool was validation-selected and enriched by the original study; conclusions apply to this selected exposed pool.

**AZ.** Of 7,864 exposed `(MASTER, sorted pair)` units, 7,478 have one plate, 336 non-control units have two or three, and 50 recurring control combinations have 14--17. The file has combination wells and no negative-control wells. The frequently repeated controls may have a different variance/effect distribution from the sparse non-control units. They cannot automatically supply representative experimental noise.

AZ matrix averages also combine 7x7, 7x5 and 5x7 dose grids. Before treating sorted-pair matrix means as replicates of one effect, check dose values, orientation, endpoint/time and normalization definitions using metadata. A common drug pair and distinct barcode alone do not establish a common matrix-average estimand.

Two hundred reorders of the same observations are not 200 independent biological replications. Four hash-ordered blocks of 413 MASTERs could define retrospective later-task evaluation, but ordering alone does not create chronological evolution, independence or adequate replication. The 413-context MDE asserted in the perspective must be recomputed for the actual clustered endpoint; it cannot be imported into a different certification design.

## Limits of the current Gate 0/1 implementation

1. **Headroom is model-conditional.** The code fits iid Student-t noise and a marginal effect prior to exposed responses, then simulates new effects/reads. AZ's main prospective simulation gives every unit three new reads that are absent for most real units. This is a useful scenario study, not empirical headroom of the available AZ experiment. Bootstrap over simulated replays describes Monte Carlo uncertainty conditional on the fitted simulator, omitting biological sampling, noise/prior estimation and misspecification uncertainty.
2. **The oracle is a named heuristic.** Sorting positive true effects with true-effect bets is not a proved budget-optimal allocation oracle. Certification thresholds, heterogeneous availability and wells/read can change optimal allocation. A small gain cannot establish that every useful policy has insufficient headroom; a large gain is only an opportunity under this simulated world.
3. **Calibration is weaker than validity.** Noise parameters are fitted using the same exposed responses later replayed. Matching a capped statistic to fitted-model simulations is a diagnostic, not a proof that uncapped e-values have null expectation at most one. Pair differences of Student-t reads are not generally Student-t reads. Mirrored inactive combinations are not authenticated nulls: inactive monotherapies do not prove nonnegative interaction. Plate dependence and adaptive use of other units require a conditional observation-law argument; e-BH's tolerance of dependence across valid e-values does not supply that argument.
4. **False failure and false assurance need separation.** Synthetic fairness testing of the gate is useful software/methodology validation. Replacing a fragile check before real outcomes is preferable to a post-result rescue, but the surviving check still has a defined detection range. No finite collection of empirical checks proves validity for arbitrary future self-modification.
5. **Cost needs an explicit proxy.** Seven Jaaks combination wells/read omits shared controls, plate overhead and original-screen information. AZ currently substitutes each unit's most common matrix size for per-read costs. These are acceptable declared development proxies, not measured wet-lab savings. A policy's unused budget and absolute discoveries must accompany any discoveries-per-used-well ratio.
6. **Storage must be corrected before execution.** `common.OUT` and default preparation/gate paths currently put NPZ/CSV data in `log/`. The user's rule requires detailed inputs/derived arrays in `data/`, code in `research/`, and key reports/results/path-hash receipts in `log/`. No implementation is ready for promotion to `src/` or `tools/` from the present evidence.

## Contribution controls that remain absent

The protocol explicitly excludes world/direct, conventional-agent, inherited-updater and improved-improver arms. Its b3 is one adaptive expert-mixture rule, not a test of RSI. The following claims require separate later evidence:

| Claim | Required contrast |
|---|---|
| World contribution | Same observations, budget and update opportunities for a world-based predictor and strong direct predictors; distinguish a static transfer prior from intervention-state dynamics. |
| Agent contribution | Fixed workflow, active learning, ordinary continual/retraining policies and a conventional tool agent; charge all observations, turns, search and fitting. |
| Inheritance/joint value | Reset versus inherited solver and policy, with swaps from common starts; compare the combined system with each component. |
| Strategy improves later improvement | Frozen old/new improvers starting from the same model, data, history and search budget on later tasks; equal-budget ordinary program search is necessary. |

Predictable expert mixtures may protect validity under the appropriate observation law; that does not certify useful discovery gains or unbiased credit. Counterfactual bets can be scored on the same realized read, but counterfactual allocation changes which read is observed. Allocation credit needs actual randomized propensities, positivity and its variance/cost analysis. Selecting the highest of many null-safe experts can still overstate its expected future usefulness. A preserved prior-free component and familiar KL/log-score identities are useful conventional controls, not independent evidence of a new biological or RSI mechanism.

## Minimum justified real-data continuation

The root's proposed **Jaaks-only two-stage diagnostic** is preferable to immediately running the full simulated certification arena:

1. Globally hash validation BARCODEs to scout versus final roles, so the two roles use disjoint plates across all units. Require a metadata-eligible unit to have an observation in each role and choose one per role by a fixed hash independent of response values. Check that BARCODE maps consistently to SIDM. Freeze role salt, unit eligibility, fixed original-score calculation, counts and missingness handling before reading responses.
2. Spend scout reads on the original-score top 40% of eligible units; nominate 20% for a final read. Compare original ranking against scout-read ranking on the same scout set. Add the strong equal-planned-budget original-only policy that spends the full 60% directly on finals. Uniform and a fixed rank mixture may be descriptive; they are not needed to establish minimum feasibility.
3. Primary utility is the number of observed positive final reads per planned well proxy, with fixed `>0` and `>0.10` read thresholds reported separately. Report hit rates and missingness as secondary diagnostics. A missing selected final read is no observed success, with its missing status separately counted; never replace it by a stronger or finite read after looking. The final read is a noisy observation, not an authenticated latent true-hit label or certified discovery.
4. Use one frozen primary replay; alternative hashes are sensitivity analyses. Resample SIDM clusters preserving the units/plates they contain, and disclose the selected-line population and shared-source limitations. Do not treat reordered reads or threshold variants as independent tests.
5. If scout ranking beats the costly fixed-scout policy but loses to original-only allocation, feedback has not paid for itself at this budget. If it wins against both, the result justifies one next frozen development comparison against ordinary learned/direct policies; it does not establish world, agent, certification or RSI gains. If the diagnostic is uninformative, stop this budget/task configuration without altering thresholds or opening a reserve to rescue it.

This continuation tests an actual, bounded resource question on existing observations without a fit, oracle, new dataset, reserve opening or speculative editor/archive implementation. AZ remains structurally qualified but numerically unopened by this continuation. Any subsequent certification or reserve experiment requires its own concrete endpoint, conditional-validity argument, cost model and protected-task protocol.

## Evidence pointers

- [Forward perspective](../forward_perspective/PERSPECTIVE.md).
- [Existing gate protocol](../certified_discovery_gates/PROTOCOL.md), [census](../certified_discovery_gates/CENSUS.json), [exposure disclosure](../certified_discovery_gates/START.md).
- [Current scientific report](../../../research/REPORT.md), [retained evidence index](../../research_records/EVIDENCE.md), [Block Q report](../../research_records/knowledge_transfer_20261012/README.md).
- [AZ scoped stop and control requirements](../../20261022/az_paid_reference_gate/DECISION.md).

No new performance, formal validity, novelty or improved-improver gain is established by this review.

## Pre-freeze correction after inspecting the reduced implementation

The source review of the newly written `study.py` found that Section "Minimum justified real-data continuation" above accepted an impossible final-count comparison. Every scout policy's final set is a subset of the original top S, while the equal-cost direct final set contains the original top S+F. Each common unit uses the same final observation. Direct therefore has at least as many positive finals pathwise at every threshold. A strict feedback win and positive paired lower interval are impossible. The reviewer missed this nesting in the earlier prose proposal and identified it before freeze or numeric outcome conversion. The original support is retained here as history, not a valid experiment recommendation.

Root accepted the correction without opening outcomes. A lawful, distinct pre-outcome redesign is to ask about **purchased two-observation repeat-positive units**: adaptive policies buy S scouts and F paired finals; the fixed repeated comparator buys both selected role observations for the original top D = floor((S+F)/2), with an odd leftover scout still charged. A repeat requires both purchased observations to exceed the fixed threshold; either missing observation is no repeat and remains charged. This removes set dominance because adaptive policies can pair units at original ranks D+1 through S. It changes the endpoint from single final positives to replicate-positive acquisition, and that distinction must remain explicit in protocol, result and decision. The discarded design and all revisions should be recorded before freeze. No true-hit/FDR/world/agent/RSI claim follows.
