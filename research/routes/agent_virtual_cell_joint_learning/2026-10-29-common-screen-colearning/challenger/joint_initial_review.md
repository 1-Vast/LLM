# Independent initial review: conditional_next_test.md v1

This assessment was recorded before receiving developer rebuttals or reading source-worker final prior prose. I am the same independent reviewer who checked the unrelated T001 propagation formula; I was not a proposer or co-designer of this candidate. Inputs were the frozen v1 packet, its exact preparation/action menu, and the raw `research/2026-10-29-functional-joint-discovery/metadata_result.json`. I did not read response counts, developer working drafts, coordinator derivations, or new prior-work summaries. Requested configuration remains gpt-6.1-sol/high; effective configuration is unknown. No network, paid API, installation, simulation, author-code execution, or extra experimental work occurred.

The central conditional identification result is sound. The two-pulse example and the signed-pair algebra are sound. The universal D-1 wording needs a nondegeneracy qualification, and two assertions about the HTS001 preparation/replacement contract exceed what the inspected metadata certifies. These are bounded corrections, not reasons to discard the symmetry result. No new algorithm, empirical benefit, or historical novelty is established.

## 1. Full adaptive history, not just matching marginals

An explicit coupling proves the claim. For each fresh balanced well, draw n/2 independent unit exponential death thresholds. Under any time-varying exposure to its one permitted drug, apply that drug's cumulative hazard to these thresholds. The observed count is n/2 plus the number of thresholds not crossed. Assigning these n/2 sensitive cells the opposite latent type changes no count path. Couple observation noise by its stipulated identical label-insensitive joint kernel, and couple policy randomization identically. Histories then match pathwise, so the next adaptive action matches; further observations or dose changes on that same one-drug well continue to match. Induction covers arbitrary finite histories, including interleaved tracking of several wells.

This is stronger than equality of individual endpoint marginals. For a policy with an almost surely finite history-based stopping time, its stopped transcript is also identically distributed. If an infinite transcript is allowed, equality follows from equality of its finite-dimensional distributions for the usual measurable path/transcript construction; a rule that never returns a decision cannot claim a decision-error guarantee.

The equal-prior 1/2 error statement is correct when the binary correct answer is opposite in S and C and the policy must return one of those answers. It is an identification lower bound for this menu and expected-count decision target. It is not an error lower bound for all biological experiments, nor for a policy supplied correlated composition fluctuations, lineage information, shared susceptibility anchors, joint exposures, or a trusted mechanistic prior that excludes one world. The preparation assumptions deliberately remove those information sources.

The construction concerns variation between cells within one population. It cannot be transferred without argument to patient-level drug-response heterogeneity or to a mixture that changes independently or jointly between biological preparations. Shared technical noise does not rescue identification under the stipulated identical label-insensitive joint law; a shared biological composition variable correlated across treatment arms is a different assumption.

## 2. Sequential example and shared object

For one pulse, a resistant cell survives with probability 1 and a sensitive cell with probability s. With no conversion or carryover and memoryless killing, AA and same-orientation AB both have expected fraction (1+s^2)/2. Complementary-orientation AB has expected fraction s. Their difference is (1-s)^2/2. At s=1/4, these values are 17/32 and 1/4, while both monotherapies give 5/8. The threshold 0.30 separates the two expected-response decisions exactly as claimed. AB and BA agree in this construction, so absence of order asymmetry cannot exclude complementarity.

For unequal survivals, q_i(z)=a_i+b_i x_i z gives E[q_i q_j]=a_i a_j+b_i b_j x_i x_j because E[z]=0 and E[z^2]=1. This independently confirms the C_ij formula. It is an expectation over the balanced within-population types and independent killing, not a statement that all noisy finite wells equal C_ij. Sequential and simultaneous exposures agree under the stated fixed additive hazards; actual simultaneous drug interactions or schedule-dependent phenotypes are outside the proof.

One joint condition has different distributions in the two worlds, but one physical realization does not guarantee identification. Even with exact count instrumentation, individual cell deaths remain stochastic. A matched AA/vehicle/calibration design and sufficiently precise replication may support a statistical decision; these are additional purchased wells and preparation requirements. Calling a response continuous does not make its expectation exactly observed.

## 3. Specific objections and required corrections

### J001 — D-1 is conditional on active contrasts

**Affected claim:** D-1 pair conditions are necessary and sufficient for all pair means.

**Evidence:** The packet allows surviving fractions s_i with no explicit global restriction s_i<1. If a drug has s_i=1, then b_i=0 and all its pair means are known from marginals regardless of its orientation. For D=3 with b_1,b_2>0 and b_3=0, one edge (1,2) recovers every pair mean, contradicting an unconditional D-1=2 necessity claim. Flipping a disconnected component containing only inactive drugs changes no cross-component mean.

**Resolution needed:** State all b_i>0 for the D-1 theorem, or let m be the number of active drugs (b_i>0) and state max(m-1,0) informative pair conditions for all pair means. A spanning tree must connect the active vertices. Under this qualification the necessity proof is valid: each query joins at most two components, and an unresolved relative component sign changes some active cross-component pair mean. The sufficiency proof follows by multiplying edge signs along the unique tree path. Adaptive noiseless edge choice does not remove the disconnected-component ambiguity.

This is a count of distinct pair conditions providing exact expectations, conditional on known marginals and the exact model. It is not a physical-well lower bound, a noisy sample-complexity theorem, or the minimum cost of one target decision. Degenerate decision thresholds or restricted target sets can require fewer conditions even when recovering every pair mean would require a tree.

### J002 — Metadata supports a failed intervention contract, not a certified per-well protocol

**Affected claims:** HTS001's replacement is established as same-drug replenishment, and its two wells are established as technical wells.

**Evidence:** The inspected metadata contains only `drug1`, concentration, identity/time/well fields and no certified second-drug or switch schedule. It reports two wells for 980 non-control metadata conditions, `independent_cultures_verified:false`, and `drug_replacement_72h:"repository-description-level; per-well time certification not established"`. It does not itself certify technical-versus-biological replication or exact drug identity at a replacement for each well.

**Resolution needed:** Use the supported wording: the qualified export does not establish matched AB/AC/BC exposures, independent preparation nesting, or certified per-well replacement histories. Report two wells per ordinary metadata condition with independence unverified. If the stronger same-drug/technical characterization is retained, provide the precise original methods/repository passage and preserve its description-level versus well-level scope. The decision not to open counts is already justified without those stronger claims: the required intervention contract is absent from inspected metadata.

### J003 — A mean relation is not yet a calibrated predictive distribution

**Affected claim:** The future falsifier freezes a full predictive distribution and is executable once a short list of assay inputs is obtained.

**Evidence:** The packet defines the ideal killing model and mean relation, but does not yet specify a calibrated technical-noise kernel, independent-preparation variation, actual initial-count distribution, uncertainty construction, or a powered replication allocation. The metadata certifies none of them. The ideal fixed-n model does determine intrinsic death-count distributions, but it does not determine those added experimental variations.

**Resolution needed:** Retain this as a conditional design until the measurement/preparation model, decision margin, nesting and precision/power contract are fixed. Distinguish a prediction interval for a new noisy well from a confidence interval for the mean structural residual. An interval for R does not by itself supply a full count predictive distribution. This does not require extra computation now.

## 4. Triangle falsifier

When the relevant b values are positive, set Delta_ij=C_ij-a_i a_j. The model gives Delta_AB Delta_AC=b_A^2 b_B b_C x_B x_C, so the proposed BC prediction and R identity are algebraically correct. If b_A is small, division by b_A^2 amplifies calibration error; an almost inactive anchor supplies little information. A single pair with a precisely estimated normalized residual away from both +1 and -1 already rejects the exact law. With two accepted informative edges, a third edge supplies the smallest cycle consistency check. Edges alone impose no cycle constraint on a tree.

An untouched BC assay is a valid audit, provided AB/AC are not selected or reinterpreted after seeing it and all calibration/estimation uncertainty is propagated. The packet's practical-margin criterion is a sensible planned falsifier, but cannot be assigned a false-rejection rate without J003's sampling contract. Passing one triangle is compatible with many other latent-factor/overlap mechanisms; it does not prove the two fixed subtypes, molecular identity, transport across doses/backgrounds, or higher-order response law. AA/BB/CC duration controls can also reject the pulse assumptions before the graph relation is useful.

## 5. Strongest simpler rivals and contribution boundary

The elementary signed-graph solver exactly realizes the ideal transfer guarantee. A rank-one susceptibility model on residual pair means provides the same predictions. The direct continuous BC assay is a decisive rival for a single BC decision; compare total wells, calibration, controls, delay and replication rather than counting only learned edges. Classical ordinary experimental design can allocate noisy measurements without an agent label.

Bliss/marginal multiplication chooses C_ij=a_i a_j; this is an additional cross-drug dependence assumption in this construction. The two worlds differ from that value by opposite b_i b_j terms. This algebra does not establish historical novelty of susceptibility overlap. Patient-level independent-action literature addresses a different unit unless an explicit mapping is supplied.

BATCHIE and other combination factor/Bayesian acquisition methods are appropriate operational comparators, but neither their exact capabilities nor the candidate's historical difference can be established from their names. No primary BATCHIE/Bliss/Palmer–Sorger text was newly inspected in this zero-network pass. I therefore withhold a novelty judgment and any claim that a particular named baseline already has, or lacks, a specified guarantee. The candidate already acknowledges that its central graph mechanism is elementary and does not support a distinct agent claim.

The useful retained result is a precisely scoped monotherapy nonidentification construction plus an ordinary separating intervention. The biological shared-law hypothesis remains unvalidated. With the present metadata, execution of its empirical falsifier is not justified and the core empirical scientific goal remains unachieved.
