# Independent constructive operator proposal

2026-10-22. Initial position, sealed before peer current proposals or root API reports. Requested native role identity is not backend attested. I read the entire user objective, current REPORT, prior native_operation root decision/continuation/source reading, and the prior biological position. No protected numerical reserve or new biological outcome scalar was opened.

## One candidate and its scientific necessity

Candidate: **functional contrast projection with explicit assay closure**. The motivation is the authenticated Frangieh CD58 finding: an IFNg/MHC surrogate can fail for immune evasion because an intervention changes a different functional route. The proposed task remains genetic perturbation prioritization under immune co-culture with matched growth controls, not drug efficacy. Existing public data do not yet establish independent later patient tasks. This is a computational reduction of a decision-world posterior, not a claim to identify all true cellular mechanisms.

Newly authenticated frontier foil: *Latent Projection for Latent Planning*, arXiv 2610.26979v1, 19 October 2026. Sections 3–4 derive Sigma=I-AA^T under Gaussian marginals, linear Gauss-Markov transitions and normal A, then retain the k least noisy directions in the planning cost. A is explicitly fit action-free under the generating policy; the encoder, action-conditioned rollout and planner are frozen. This is a specific operation, not just a world-model name. Biological persistent transcriptional directions need not determine immune-specific function; a noisy but informative surface-state direction can be discarded. Destructive population assays also do not supply the same-cell trajectories required for this A fit. Consequently I propose reducing decision contrasts and their available measurements, rather than preserving state solely by temporal persistence.

The literal first construction would retain only the span of candidate functional contrasts D theta and project all measurements into it. Its potential defect is substantive: a molecular reporter orthogonal to D may be informative through posterior correlation with D theta. The ONE allowed revision, already specified here and not to be followed by another patch if it fails, is **assay closure**: retain the joint distribution of all candidate functional contrasts and all still-legal measurement rows. This can preserve indirect functional evidence while discarding thousands of irrelevant molecular coordinates.

## Exact operation

Let a locally linear world have theta~N(mu,Sigma), candidate functional utilities u_a=b_a^T theta and an arbitrary reference a0. Let D have rows b_a-b_a0. Legal paid assay bundle q returns y_q=H_q theta+epsilon_q with epsilon_q~N(0,R_q). R_q includes within-bundle covariance, including shared controls; metadata determines the full cost and batch/replicate unit. No assay is treated as a noiseless molecular surrogate. Parameters, linear maps, covariance and utility are source-fitted and frozen before reserve access; none has been fitted here.

Form Z=[D; all distinct still-legal rows of H]. Compile m=Z mu and V=Z Sigma Z^T once. An assay bundle selects rows J. The complete update is:

    S = V[J,J] + R_q
    m_new = m + V[:,J] solve(S, y_q-m[J])
    V_new = V - V[:,J] solve(S, V[J,:])

Nominate argmax([0,m_new[:number_of_contrasts]]). An agent chooses a legal bundle through any matched acquisition rule evaluated on this posterior and true remaining cost; a small executable comparison will use conditional Gaussian information gain on D theta per cost. This is a diagnostic acquisition, NOT a proof that information gain maximizes functional utility. The proposed biological trial would need decision value/KG and a fixed-budget utility metric registered separately.

This reduction is exact for the declared finite assay menu and fixed linear-Gaussian world. It changes online update dimension from latent parameter dimension p to at most (#contrasts + #distinct assay rows). It does not require normal dynamics, a stationary covariance or longitudinal cell matching. It does not create biological information. If new assays or nonlinear regimes are introduced, the closure must be recomputed from a retained full model; no guessed cross-covariance is admitted. One-time compilation, storage and source fitting count against compute budget.

## Closest ordinary competitors and falsifiers

The strong ordinary comparator is full linear-Gaussian Bayesian design, plus a cached joint Gaussian / dual-space implementation receiving the exact same D,H,R,posterior and assay menu. The latter may recover every line above. That equivalence would not erase a real reduction against dense full-space updating, but it would eliminate an original-algorithm claim if the optimized ordinary implementation also matches the cost. LP's low-noise projection, functional-only projection, direct supervised predictors, ordinary refits and fixed/random design are additional controls; a surrogate-only model is not sufficient proof of novelty. World and agent benefits remain hypotheses until exact utility is compared under equal data/feedback/compute.

Bounded literature search has already located *Coupled Input-Output Dimension Reduction* (2406.13425v2, updated 2025), *Goal-Oriented Sequential Bayesian Experimental Design for Causal Learning* (2507.07359v1), and *Risk-Aware Goal-Oriented Bayesian Optimal Experimental Design* (2609.08023v1). Primary bodies are retained but the necessary method passages are not yet fully inspected. These are strong prior-art risks, not afterthoughts. The initial decision is GO for one synthetic operation audit only; NO biological pilot or method promotion yet.

Minimal falsifier: demonstrate loss of a function-informative noisy direction under LP; demonstrate correlated-reporter loss under functional-only projection; test the one assay-closure revision against full and optimized ordinary posterior/design on identical synthetic observations, including shared-control covariance. If an equally informed cached ordinary method has identical state, nominations, acquisitions and dimensions, stop novelty promotion of this specification. Do not add another mechanism to rescue it.

## World, agent and possible improved improver

The world predicts the joint effects of interventions and possible measurement outcomes. The agent chooses costly functional versus molecular measurement bundles and nominates perturbations. All parts can be conventional and still useful. Inheritance of a calibrated contrast/assay covariance is ordinary model transfer. A possible Level-3 object would be a learned proposal policy that suggests which observable rows to add when held-out source tasks expose a missing functional direction; old/new proposal policies must be compared from the same fresh downstream model and assay menu with equal source training/search/feedback cost. This role does not implement or claim that improvement mechanism, and no Level-3 benefit is established by Gaussian compression.

## Limits

Protected TG later14, AZ413, CiPA8/9 and MSE development/later remain numerically unopened. All old STOPs persist. No API model call, fit, new cell assay or dataset download was performed. Public arXiv metadata/HTML and the LP author README were retrieved with exact receipts; these are source authentication, not validation of author performance. Scientific utility, biological linearity, actual covariance calibration, independent task units and improved-improver value remain untested.
