# Dose-window principle scout: findings and handoff

Date: 2026-10-30. Source reuse only; no new network acquisition. Requested runtime configuration inherited; effective model, effort, token usage and cost unknown.

## Finding and useful operation

The inspected donors support **task-informed calibration before choosing a compound**, but do not supply an identified biological invariant or a new predictive algorithm. A practical learner could use a small, fixed, source-selected panel of measured drug/dose responses to characterize a new background, then predict unmeasured drug-pair differences in a specified supported dose/time window. Ordinary hierarchical curves, regression and multi-output/kernel GPs already cover this conditional-prediction operation. Their same-information comparison is decisive.

The constructive scientific hypothesis is conditional anchor sufficiency. Write the observed growth response as R(b,j,c,t), and a fixed calibration panel as z(b) = [R(b,a_1,c_1,t_1), ..., R(b,a_m,c_m,t_m)] plus allowed vehicle/baseline information. For a new background, hypothesize that the conditional mean pair difference E[R(b,j,c,t)-R(b,k,c,t) | z(b), baseline] is stable across background identity within the represented population. This preserves dose-specific rank reversals; it does not posit a global drug order. Its practical output is a selected drug, predicted pair difference, and a refusal when calibration/window support is inadequate.

The panel must be fixed using source-only cross-validation on **selection loss**, with an explicit number of wells, doses and readout times. A panel selected to reconstruct all responses or maximize latent variance can spend its budget on changes irrelevant to the particular choice. Choosing probes for the final decision is the useful donor principle. The current continuation does not authorize a new adaptive acquisition algorithm or an Agent.

**What would distinguish this relation from pooled curves?** Under whole-background holdout, the calibration measurements must identify which dose window changes the best compound, and predict pairwise signs/crossings not supplied by pooled drug curves or vehicle growth alone. Randomly mismatching complete calibration vectors between backgrounds should remove that improvement. This establishes dependence on measured functional context, not a biological mechanism.

**What would distinguish it from an ordinary GP with the same anchors?** Conditional anchor sufficiency alone cannot: a GP can represent it. A new learning-mechanism claim needs a stronger, prespecified restriction and a discriminating prediction. An illustrative restriction is a common background-specific log-dose shift across drug curves, R(b,j,c,t)=g_j(log(c)+s_b,t), with s_b inferred only from calibration drugs. It predicts that the same shift aligns held-out drug curves and their rank-crossing locations, rather than allowing arbitrary drug-specific warps. This is an ordinary shape-invariant/nonlinear mixed-effects hypothesis and may be biologically false across drug mechanisms; it is not a recommended new method or a source-established biological fact. Closest aliases require checking before any novelty claim: curve registration, parallel-curve bioassay, potency scaling, nonlinear mixed effects, multi-task dose-response, functional fingerprints and cold-start response prediction. No source here establishes their absence from the target literature.

**One decisive falsification test.** Freeze a small anchor panel, one set of measured concentration/time windows and a whole-background split. Give every model exactly the same anchors and baseline inputs. Compare the candidate against pooled/hierarchical curves, ordinary anchor-conditioned ridge/kernel regression and a multi-output/conditional GP using measured growth-unit compound-selection loss. The useful operation fails if anchor conditioning supplies no headroom over pooled/vehicle-only curves. A distinct donor mechanism fails if its apparent gain is matched by the ordinary models given the same information, or the claimed stronger curve restriction fails on held-out drugs. If ordinary calibration succeeds, retain that useful result and stop a novel-mechanism claim. This scout has executed none of these checks.

## Source-native mechanism and broken mappings

### 1. Poke and Strike — task relevance, rather than complete identification

Original: *Poke and Strike: Learning Task-Informed Exploration Policies*, arXiv:2509.00178v1 (2025; local library first-public date 2025-08-29). [Official original](https://arxiv.org/html/2509.00178v1). Local source: `D:/MAESTRO/reference/papers/arxiv-2509.00178/paper.html`. P reading: §2 and §4.1 complete; first 2700/3208 characters of §4.3; first 2700/3063 characters of §4.4. No proof, experiment or code reproduction.

Exact mechanism passages: §4.1 assumes physical properties remain “constant throughout the episode.” §4.3 trains an estimator with errors obtained from “the difference between the ground truth physical property values” and estimated values. §4.4 computes thresholds “from task performance sensitivity,” perturbing one true property while keeping others correct, and explicitly assumes “the impact of each property on task performance is independent of the others.”

Mapping: safe exploratory motion -> measurements on a fixed calibration panel; physical properties -> a predictive functional background descriptor; task success -> correct drug choice in the specified window. This changes **panel selection and the endpoint**: source-only choice loss should determine what needs to be measured, rather than latent reconstruction error. It does not require RL for a fixed panel.

Required data: source backgrounds with both candidate anchor responses and queried drug outcomes; sufficiently stable background/preparation state across the separately treated wells; supported calibration/query doses and readout times. The major mismatch is lack of ground-truth biological properties, simulator counterfactual parameter perturbations, and proven separability of property effects. Drug treatment can itself alter the state. Thus the source's sensitivity-threshold mechanism cannot be imported literally.

Strongest simpler explanation: the panel is a correlated covariate vector for ordinary conditional response regression. A gain over pooled curves alone is compatible with this explanation. The decisive same-anchor GP comparison above is required.

### 2. Learning-To-Measure — context-conditioned inference has explicit sampling assumptions

Original: Kobayashi et al., *Learning-To-Measure: In-Context Active Feature Acquisition*, ICML 2026/PMLR 306, official-main PDF. [Proceedings original](https://proceedings.mlr.press/v306/kobayashi26a.html). Local source: `D:/MAESTRO/reference/papers/pmlr-v306-kobayashi26a/paper.pdf`. P reading: PDF p1; pp3-4, first 4400 characters each. Theorem and method continuation/proofs not audited.

Exact passages: PDF p3, §3: tasks are sampled from a probability measure over a family of tasks, and “the features are time-invariant, i.e., the values of X do not evolve over time.” PDF p4, Assumptions 3.1-3.3 require MAR, No Direct Effect and Positivity. The explanatory text states “measuring a feature does not directly affect the target variable.” Section 4.1 conditions query prediction on “Context Samples” from the same task distribution.

Mapping: one task -> one biological background/preparation distribution; context samples -> measured calibration responses; query targets -> unmeasured drug/window responses. This confirms the initial note's distinction between descriptor-only, fixed-panel and queried-drug partial-curve tasks. They require separate protocols and matched costs.

Failure: a treatment is not a passive feature reveal in the same cell population. Separate aliquots can avoid directly changing the queried well, but do not certify stable culture state or MAR/positivity. Different time points are not static features automatically. The source's CMI objective reduces target uncertainty; it need not reduce wrong-compound selection loss. The usable portion is context conditioning, already supplied by ordinary regression/GP. No sequence pretraining or new model is justified by this paper in the current small panel.

### 3. SPI-Active — excitation/identifiability limits interpretation

Original: *Sampling-Based System Identification with Active Exploration for Legged Robot Sim2Real Learning*, arXiv:2505.14266v1, 2025-05-20. [Official original](https://arxiv.org/html/2505.14266v1). Local source: `D:/MAESTRO/reference/papers/arxiv-2505.14266/paper.html`. P reading: first 6500/8960 characters §3; §§4 and 7 complete; Appendix A.5 complete. No code/result reproduction.

Exact passages: §3 Eq1 identifies parameters of a specified state-action transition f using observed state-action trajectories. §4 Eq6 minimizes tr(F^-1) for excitation; its Eq7 approximation assumes Gaussian process noise and uses the currently estimated parameter in place of truth. Appendix A.5 says the unexpectedly large inertia estimates suggest “overfitting or parameter coupling due to insufficient excitation,” even though the fitted model improves task transfer.

Implication: a calibration panel must distinguish the response alternatives relevant to choice; duplicate technical wells reduce noise but need not identify an unobserved response regime. Good prediction does not identify a biological parameter or mediator. Counts do not supply the known simulator, observed state or ground-truth physical parameters that enable literal SPI. This confirms the initial map's observability gate and supplies concrete contrary evidence against interpreting a fitted latent descriptor mechanistically.

### 4. GVALID — useful decision alignment, incompatible optimum assumption

Original: Wan et al., *Active Policy Optimization for Individualized Dosing via Gradient Variance Minimization*, ICML 2026/PMLR 306. [Proceedings original](https://proceedings.mlr.press/v306/wan26l.html). Local source: `D:/MAESTRO/reference/papers/pmlr-v306-wan26l/paper.pdf`. P reading: PDF p1; pp3-4 first 4300 characters each; targeted Assumptions 4.1-4.2 on p3 and B.1-B.4 beginning on p14. No proof or experiment audit.

Exact passages: p3 §3 permits one intervention per individual and defines final-policy regret in Eq3. Assumption 4.1 on p3 requires 0<mu<=-d²f/dt²<=L, not just unspecified smoothness. P4 Eq6 assumes the posterior-mean optimal dose lies in the interior. Theorem 4.1 bounds regret using posterior gradient variance at that estimated optimal dose. Appendix B states consistency, ignorability and positivity assumptions.

Mapping: covariates -> observable background descriptors; policy value -> measured growth outcome of the final selection. The operative principle is to optimize final decision quality instead of global curve RMSE. The critical mismatch is that choosing among different compounds at a user-specified window is not estimating a strongly concave response's interior optimal dose. Growth suppression can be monotone or saturating, with optimal values at the boundary. The source gradient-regret bound therefore does not transfer. Its GP surrogate is also a strong ordinary baseline, not evidence for an Agent.

### 5. Decision-focused sequential design — decision disagreement can matter more than error norm

Original: Wan et al., *Decision-Focused Sequential Experimental Design: A Directional Uncertainty-Guided Approach*, arXiv:2602.05340v1 (2026-02-05). [Official original](https://arxiv.org/html/2602.05340v1). Local source: `D:/MAESTRO/reference/papers/arxiv-2602.05340/paper.html`. P reading: §§2.1-2.2 complete. No guarantees/proofs or experiments audited.

Exact passage: §2.1 Example 2.1 shows that larger prediction disagreement can leave the optimizer unchanged, while smaller disagreement can change it. §2.2 Algorithm1 samples according to directional disagreement over a confidence set, records acquisition probabilities, and uses importance-weighted SPO loss.

This supports comparing choices and their growth loss, already in the initial note. It does not license importing directional uncertainty: drug choice is invariant to an added common response component whereas cost-vector angles can change, and complete compound cost vectors/confidence-set calibration may be unavailable. No adaptive sampling is needed for the fixed-panel operation. Its contribution here is confirmation of decision alignment, not a changed biological rule.

### 6. Active multiple matrix completion — a prior threat with the wrong sampling unit

Original: *Active multiple matrix completion with adaptive confidence sets*, arXiv:2605.02458v1 (2026-05-04). [Official original](https://arxiv.org/html/2605.02458v1). Local source: `D:/MAESTRO/reference/papers/arxiv-2605.02458/paper.html`. P reading: §2.1 first 2000/2520 characters; §2.3 complete; §2.4 first 2000/3912 characters.

Exact passages: §2.1 assumes independent noise and uniformly sampled entries of a low-rank matrix. §2.3 constructs error estimates using entries “observed twice.” §2.4 lets the learner choose which matrix to sample, after which an entry is chosen uniformly at random. Technical well repeats do not create independent biological units, and an entire unseen row without descriptors/anchors is unidentifiable. The source does not choose arbitrary informative drug/dose entries. Rebranding the target as active matrix completion would not resolve these mismatches; this is an ordinary-structure prior threat, not a preferred donor.

### 7. Direct target prior: PIMOGP already borrows latent response functions

Original: *Permutation invariant multi-output Gaussian Processes for drug combination prediction in cancer*, arXiv:2407.00175v1 (older direct prior). [Official original](https://arxiv.org/html/2407.00175v1). Local source: `D:/MAESTRO/reference/papers/arxiv-2407.00175/paper.html`. P reading: first 2500/6955 characters of Background/Multi-output GPs; Datasets/Prediction setting and hyperparameters complete; Conclusion complete.

Exact passages: Eq8 writes each output as a linear combination of shared independent latent GP functions. Its evaluation is leave-triplet-out while other examples may contain “the same cell line, or the same drugs.” Its conclusion states “we were not yet able to beat the simple (Bliss) baseline for this dataset” and proposes omics covariances for new cell lines as future work.

Implication: shared latent dose-response borrowing and uncertainty are existing operations. This paper did not validate unseen-background transfer, and its failure against Bliss is in a drug-combination dataset, not a result on HTS001. It supports including ordinary multi-output/kernel competitors and prevents treating latent sharing as new. LMC, intrinsic coregionalization, multi-task GP, curve borrowing and cold-start response prediction are immediate alias/prior checks for the investigator.

## Exposure, decision change and process evidence

The saved `initial_structural_mapping.md` precedes source acquisition and prior-scout reading. Its premise was: “Learn a task-specific function from a small observed context set,” while ordinary models might already perform the operation. Initial source reading was candidate-unexposed. A later coordinator message disclosed three tentative alternatives: background descriptors only, fixed-dose calibration with a shared within-drug curve relation, and early trajectories predicting later suppression. All subsequent development, including the constructive anchor-sufficiency formulation and Poke/PIMOGP reading, is **co-development, not an independent candidate challenge**.

Traceable changes: one added future design detail, choose the fixed calibration panel using source-only drug-selection loss rather than full-response/latent reconstruction, follows from Poke §4.4. This refines the initial context-learning hypothesis; no prior fixed panel existed to reverse. Exact GVALID curvature/interior assumptions rule out importing its gradient guarantee into a fixed-window compound choice. The other passages confirm existing input, support and identifiability boundaries. Zero models, panels or experiments were executed or adopted; zero target gains established.

Actual usage: **0 donor-directed network requests, 0 completed body bytes, 0 new queries/passes consumed by this scout**. All six requests and 5,000,000-byte allocation remain unused and can return to the coordinator's shared budget. Seven distinct existing original works had method passages inspected (all P, none F); no duplicate version counted. Two local parser imports failed (`bs4`, `fitz`); stdlib/lxml and installed pypdf recovered the reads without installing dependencies. No raw counts, HTS003/031 treatment payload, candidate draft, model fitting, shared-library/index edit, contact, upload or subdelegation occurred. Only files in this scout output directory were created.

No new donor query was necessary because the existing originals supplied both the constructive task-informed operation and its decisive mismatch. This bounded reuse is not broad coverage of all relevant 2025-2026 donors or target aliases, and supplies no novelty evidence. The coordinator's target investigator still owns the closest dose-transfer literature and data-design audit.
