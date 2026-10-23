# Independent functional-decision frontier: selection-aware reliability is not efficacy

2026-10-23. **NONE_NEW_CORE / NO_BIOLOGICAL_NUMERICAL_GO.** New primary sources supply two concrete direct comparators and finite-budget contract questions. The one considered continuation is a selection-aware, assay-escalation decision rule using real functional feedback. It is not promoted: a decision guarantee under sparse paid measurements and a hard assay cap is not established by either source, and no additional MAESTRO-specific restriction is yet supplied. This is not a rejection based on conventional algorithm family membership.

Zero old73pair analyses, state microdiagnostics, raw/functional/reserve numerical access, data downloads, fits or author-code execution. No peer new report opened before sealing. One unsolicited source-agent summary arrived near completion; it was not used to select or assess these mechanisms. All old STOPs remain.

## Three purpose-bound GETs and exact versions

1. Official arXiv Atom query on2025–2026decision-focused/risk-control methods,25results. Bounded local Markdown duplicate search found no matching titles/IDs before this report; not exhaustive novelty clearance.
2. Capitaine etal., **Online Decision-Focused Learning**, arXiv2505.13564v3, article header07Mar2026. Full HTML1063875bytes, SHA2569dfd0af6c2fb6191fa76d9a62416d9bb7e518a644bfacdf3df348eb35d6afa1b. Read online setup/assumptions, Algorithms1/2, approximate-oracle discussion, and theorem statements; no claim of author experiment reproduction or full proof audit.
3. Xu, Guo and Wei, **Selective Conformal Risk Control**, arXiv2512.12844v2, article header27Apr2026. Full HTML307947bytes, SHA25697839a1d6fb56601666e3063535a91388b800df6732f15689397f560f3453cb1. Read selective setup, conditional exchangeability, transductive selection and Theorem2/CRC rule. No independent proof verification or benchmark replication.

Receipts preserve URLs/statuses/bodies/hashes; all3HTTP200. Initially reported HTTP Last-Modified August dates to parent as revision dates; corrected in a subsequent message and here using manuscript version headers. HTTP server metadata is not the manuscript date. HTML projected by standard-library parser, no external source executed.

## Primary1: decision-focused model revision has a real feedback/oracle price

OnlineDFL defines a predictor g(theta,X), decision `w*(theta,X)=argmin_w <g(theta,X),w>` and actual cost vector c_t. It smooths the inner decision to define differentiable surrogate losses `f_tilde_t(theta)=<c_t,w_tilde_t(theta)>`; a perturbed-leader update is

`theta_(t+1)=O_xi(sum_(i<=t) f_tilde_i(theta) - <sigma_t,theta>)`,

with coordinate exponential perturbations sigma and an approximate offline optimization oracle O_xi. It also derives a dynamic-regret procedure. Full source Algorithm1 line4 explicitly reveals **the complete true cost vector** after a round, not merely the chosen action outcome. Assumptions include bounded parameter/prediction/gradient quantities and a cost-margin condition; the near-global offline oracle has an approximation error in the guarantees. These are actual limitations to check, not computationally free modules.

Therefore directly using this update with unmeasured drug outcomes inside the surrogate would leak the very assays a sparse-feedback agent must purchase. Replacing the vector by a learned world-model estimate changes the feedback/theorem contract; treating oracle calls as one cheap gradient step changes its cost contract. The paper supplies a strong full-information decision-focused baseline, not a sparse-drug guarantee. Its nonstationarity analysis does not make a shifting patient drug panel observable. This does not rule out bandit/partial-feedback variants; none is authenticated or derived in this pass.

## Primary2: finite-sample accepted-population risk requires selection symmetry

SCRC considers a source-trained predictor, confidence h(X), accepted inputs and nested prediction sets C_lambda(X). Its transductive form chooses a feature-dependent acceptance threshold symmetrically across calibration and new test features. For a fixed admissible symmetric first-stage choice, let I be accepted calibration cases, m=|I|. The printed Eq15 has the CRC threshold

`lambda2_hat = inf{lambda2: sum_(i in I) loss(C_lambda2(X_i),Y_i) <= ceil((m+1)*alpha)-1}`,

for a bounded[0,1]loss nonincreasing in lambda2. Under its stated exchangeability and symmetric-selection assumptions, Theorem2 gives expected loss conditional on acceptance<=alpha. The manuscript prose near Eq15 says “largest feasible” while its displayed formula says inf; this review uses the printed formula and does not silently resolve the discrepancy. Monotone set construction, feasible boundary handling and small accepted m need explicit implementation before any use. Its inductive variant instead has PAC-style statements, not the same exact transductive guarantee.

The specific finite-sample issue is relevant: taking only the apparently reliable outputs of a newly updated cell model and then applying a calibration statement for the unselected population can invalidate the intended decision reliability. Symmetric selection is a concrete restriction beyond merely using an uncertainty score. But this property is already supplied by the source and standard selective calibration; it is not our new primitive. No blanket statement that all ordinary uncertainty methods fail is justified.

## One considered functional mechanism and its legal endpoint

At a fixed information checkpoint, an episodic predictor receives baseline/context metadata plus a **fixed purchased probe panel and paid control bundle**. It predicts a finite-catalogue utility vector. Calibrated action sets or abstention determine whether additional assays are required before nominating a drug. The inherited object would be a calibrated rule for **when an updated prediction is safe enough for a particular measured decision**, rather than another RNA-MSE correction. Updating a predictor, recalibrating its selection and improving a research strategy remain distinct levels.

An actual authenticated endpoint exists locally without reopening a missing identity search: the malignant-serous-effusion resource qualified in log/20261022/contrast_gate_check/DECISION. It has135samples/95patient groups and65common actions after metadata-defined design exclusion, with24h unscaled `RCN=1-malignant_count_drug/median(malignant_count_control)` and `RCF=1-malignant_fraction_drug/median(malignant_fraction_control)`. These are image-classified retained non-apoptotic phenotypes, not healthy-cell survival or clinical efficacy. Full-panel-extrema-scaled sheets are illegal for sparse replay. Control composition is measured in parallel24hDMSO, not zero-timeRNA. No new pairedRNA is authenticated; it cannot support a claimed RNA-world-model advantage by relabeling composition. This review reads only that prior task decision, not response values or another menu.

One finite research target could predefine bounded utility U in[0,1] from joint RCN/RCF shortlist success, using source-only thresholds with explicit interpretation and no clinical claims. If Y is the fixed-tie-broken best true unmeasured action, a prediction set C could be calibrated for `loss=1[Y notin C]`. **That only controls missing the best action**, not the quality of an unmeasured action chosen from C. A legal escalation policy would physically assay every newly selected action in C and then choose by observed utility; it must pay all of those observations. A fixed capK may force rejection or truncation. Truncation can destroy coverage; size-based acceptance can destroy the required selection symmetry. A valid hard-cap/set-loss selection rule would need a separate actual derivation or calibration, not a claim that Theorem2 automatically covers it. Unknown/noisy assay targets additionally change what the label means.

Adaptively chosen probe outcomes also change the patient-episode information distribution. Freeze one source-trained probe policy or replay the exact policy identically for every calibration/test patient; changing model/policy after calibration does not preserve exchangeability for free. Patient repeats must remain grouped. A small fixed source/calibration split, classifier drift and limited accepted cases can make the rule vacuous; neither theoretical validity nor a small set alone implies useful discovery.

## Executed minimal operation check and its consequence

`check_decision_contract.py` executes an exact two-action boundary: true utilities A1/B0, predicted A.4/B.9, prediction set{A,B}. Set miscoverage is0, but predicted argmax picks B with regret1. Assaying all set actions allows choosing A, but costs2when the stated assay budget is1. This **does not refute** a conformal theorem or estimate drug efficacy. It refutes the attempted interface shortcut “a covered best-action set certifies the single nominated action at no further assay cost.” No simulated biological labels are treated as experimental evidence.

Hence no currently executable functional-advantage test follows simply by wrapping calibrated sets around RNA correction. A positive RNA reconstruction, source-state attenuation coefficient or ordinary support-conditioned mean prediction does not establish the downstream risk contract. The missing contribution is a precise, low-cost functional decision restriction whose benefit is not already provided by a strong same-information calibrated direct model.

## Fair minimal test if that contract is later supplied

Before new endpoint conversion, freeze actual patient groups, checkpoint information, probe/control costs, bounded utility definition, accepted-population target, hard catalogue/assay cap, calibration/training isolation and an independently meaningful useful margin. Then test worst failure modes first: policy/selection dependence, acceptance rate, actual cap compliance, patient-level risk versus calibrated target, and utility/cost versus a direct decision policy. Refuse an algorithm that passes average coverage only by abstaining almost everywhere or assaying the whole panel. Uncertainty and abstention are charged and reported, not free wins.

Comparators receive identical probes, composition/state, controls, source outcomes and total compute/search budget: episodic direct predictor, ordinary conditional multivariate completion/refit, replay/continual update, active-learning/value-of-information policies, simple mixture, same selective-CRC wrapper, decision-focused refit where its actual full-feedback costs are charged, and equal-budget program search. A claimed RNA correction must beat the same functional direct predictor/calibrator and a raw-state/no-state contrast; no source here authenticates that additionalRNApayload. Isolate predictor revision versus selection/escalation; later inheritance uses common-start tasks, and RSI uses changed versus unchanged improvers from identical model/history/budget. Fixed calibration or a better frozen policy alone is not recursive improvement.

## Disposition

Retain OnlineDFL and SCRC as exact feedback-/selection-aware direct baselines, and retain the operation check as a concrete efficacy/budget boundary. **NONE** as a new verified MAESTRO functional mechanism. No new biological fit, MSE task launch, asset hunting, threshold/menu search, functional/core/world/agent/inheritance/RSI GO. The conclusion is conditional and empirical: a concrete same-information finite-cost correction could still be valuable, but neither source or this review currently supplies the required distinctive contract and evidence.
