# Independent initial review of H_MEAN.v1

2026-10-29. Written before receiving any coordinator rebuttal or empirical result. Role: scientific challenger, not diagnostic proposer. Requested model/effort: Sol/high; effective runtime settings, tokens and cost are not independently exposed. Fresh task context contained the review brief and file locators, with no desired numerical outcome. No raw HTS001 file, response value, author code, network, paid API, experiment, installation, core file or project index was accessed or changed. Only this review file is added. The general research objective remains NOT_ACHIEVED.

## Initial finding

The proposed raw-mean prediction comparison is scientifically interpretable within its explicitly conditional scope. It does not establish that the exponential mean is adequate, even if preferred, and it cannot validate white observation error, homogeneous latent rates, molecular killing or agent benefit. One small but execution-relevant inconsistency must be resolved in a preserved pre-access clarification: the design requires INCONCLUSIVE when original point and bootstrap-stability signs conflict, whereas protocol_v1's decision branches omit that guard. Because both documents declare themselves canonical together, a program should not silently choose one rule. Apart from this clarification, no essential redesign of the stated conditional comparison is needed before eligible control-count access.

After that clarification is frozen, narrowly execute the one specified control-only comparison, with the frozen split, raw objectives, deterministic fitting, all-nuisance refits, 500 complete row-block draws and declared stop rules. Do not expand the run into covariance diagnostics or rate inference. A failed fit/draw, unavailable resource budget, material optimizer ambiguity or disagreement with independent verification must remain INCONCLUSIVE rather than trigger an unregistered repair run.

## Frozen identity and reading scope

Computed SHA256 values matched protocol_receipt.json for all three files it freezes:

| File | SHA256 observed in this review |
| --- | --- |
| protocol_v1.md | cfcbb224496ffab372f2a5ed0b212c5794788d3ad29d44976367d7f1a16699b0 |
| design_worker/recommended_design.md | 01df5ee1aef8916dc1c36cf55f9d64945d7445588eff55bee0f0a25bafcbcf46 |
| metadata_qualification.json | 84709d091437495c2ec49d1ad7787185a3f4a3f6fe69c4d54e87f9735cda8ce0 |
| protocol_receipt.json itself | 6467e5b91e5c111a83d412d60b18a4ce16374a2a625244926921ffbf3d844fe7 |

Read record.md, protocol_v1.md and recommended_design.md in full. Inspected metadata_qualification.json's scope/provenance fields and programmatically checked every cell's plate, well roster and complete trajectory time coordinates without response access. All seven cells have the exact B–O by 02/23 roster, 28 trajectories and a common time grid within plate. Eligible frame counts are BR1 11, DS3 13, DS7 13, DS8 13, DS9 11, MGH 9, PC9 15. The file reports count_values_accessed=0 and independent_culture_or_technical_nesting_certified=false. This is a metadata assertion and roster verification, not an audit of the raw count source or proof of physical preparation independence.

Read the parent root_derivation.md; saved Wu published-primary Sec27–29 passages with DOI 10.1038/s41540-025-00560-8 and recorded original-JATS hash 002ff6e2add18dfecc65faf95316a623a753ca6b712dd4d9f02d8b7d77beb889; and BESTDR original JATS sections s2-1 and s4. Read installed innovation-research SKILL.md and its relevant independent-review rules in discovery.md, research-team.md and quality-gates.md. No new prior-work search was performed; no novelty conclusion is attempted.

## Objections, affected claims and resolutions

### T-MEAN-01 — essential pre-access decision-rule clarification

Affected claim: deterministic classification of the single frozen test. The design's outcome 3 explicitly includes "point/stability signs conflict". protocol_v1 instead classifies from the empirical 5th/95th percentiles and numerical checks alone. A skewed bootstrap distribution can have a positive 5th percentile while the original Delta is negative, or the converse. This possibility need not occur to make the current executable contract ambiguous.

Resolution required before count access: preserve both frozen documents and freeze a short explicit precedence/clarification that specifies the treatment of this case, including zero. The existing design's conservative conflict-to-INCONCLUSIVE rule is already a specified option; implementing it does not require choosing new models, thresholds or splits. Record exactly which rule the primary and verifier will share. Do not resolve this after seeing the signs. No other scientific specification change is requested by this ticket.

### T-MEAN-02 — relative prediction cannot certify exponential adequacy or equivalence

Affected claim: the broad record's question whether trajectories support a homogeneous model "strongly enough to justify its use as feedback", and any informal "as well as" interpretation. Delta compares two fitted predictors, not either model against an absolute adequacy criterion. Two badly wrong curves can have similar loss. A negative or unstable Delta can reflect limited power, estimation cost of curvature, or the rival's inadequacy. Without a predefined effect margin and calibrated inferential design, failure to find gain is not equivalence. Positive conditional gain is evidence to stop treating this exponential predictor as the default in this particular task; it is not a calibrated rejection of a biological homogeneous-growth null.

Resolution/status: substantially controlled by the narrow protocol and its explicit nonvalidation language. Keep that language in the actual report. Report the fitted predictions, losses/contributions and observed-grid scope; do not upgrade the outcome labels into a population hypothesis test. No extra comparator or absolute-adequacy analysis is required for the narrowed test.

### T-MEAN-03 — exchangeability and unobserved dependence limit the estimand

Affected claim: expected prediction loss for a new well from the same preparation, plus the connection from heldout gain to a mean-model prerequisite. The exact split balances the two observed columns and keeps all times of a well, and both same-row wells, in one role. It is not a randomized split. Training rows B,D,F,H,J,L,N and validation rows C,E,G,I,K,M,O differ by one row position on average. A row gradient, checkerboard allocation, acquisition drift or cross-role shared disturbance can therefore produce or mask gain. Alternation does not establish a shared mean preparation. One plate per cell leaves plate and cell inseparable; 196 wells are not 196 independent cultures.

Resolution/status: unknown and not repairable from counts alone. The frozen documents acknowledge it adequately for a descriptive within-plate operational comparison. Treat "new well" as a conditional working interpretation requiring shared preparation; the directly observed result is loss on the specified validation wells. A positive result can block the operational default without identifying biological curvature. Population rate interpretation would need genuine preparation/dependence information and a separate design, irrespective of this result.

### T-MEAN-04 — conditional resampling is a sensitivity calculation, not an uncertainty certificate

Affected claim: a reproducible positive stability tail implies a scientifically significant mean violation. Sampling seven row pairs per role retains all temporal dependence within a trajectory and the two columns within a selected row. Independent train/validation resampling does not preserve unknown cross-role spatial covariance or common plate/time effects. Keeping seven fixed plates does not sample cell lines or independent cultures. Seven blocks and 500 draws also leave finite resampling resolution. A sign fraction is not a posterior model probability, and the 5th/95th percentiles are not calibrated biological confidence limits.

Resolution/status: controlled for the stated use by explicit conditional wording. Describe exactly what variation is perturbed, and preserve the tail cutoff as a prechosen operational decision rule. Do not call the interval a confidence interval or imply the unrepresented dependence has been estimated. No bootstrap redesign is needed for this stated sensitivity question.

### T-MEAN-05 — nonlinear fitting/nestedness checks do not prove optimization adequacy

Affected claim: comparison of the exponential and quadratic-logmean model classes. Starting the rival at the fitted baseline with curvature zero gives a feasible nested initialization, and the frozen SSE tolerance can detect an obvious optimizer failure. However, least_squares with an analytic Jacobian, tight tolerances and a single start can still converge locally or terminate without finding the best class fit. Nested SSE alone does not establish global optimality. Identical implementations agreeing can reproduce the same local solution; independent arithmetic verification is not a theorem of global convergence.

Resolution/status: acknowledged by the design and acceptable for a comparison of these precisely specified fitting procedures. Record solver termination, parameters and objective, apply finite-value/nestedness checks to every fit and draw, and flag material ambiguity. Keep any substantive conclusion at the predictor-procedure level. Do not add starts, bounds, clipping or selective draw deletion after inspecting outcomes. An actual unresolved ambiguity prevents stronger model-class conclusions and, under the frozen stop rule, makes the scientific comparison INCONCLUSIVE.

## Checks that do not expose a new blocker

The estimand uses arithmetic count means. Fitting exp(beta0+beta1*u) by raw-count squared error does not fit mean log counts or exponentiate an estimated E[log Y]. The quadratic describes log of the modeled arithmetic mean, not an average log response. Consequently there is no Jensen correction to add to the specified objective. With shared homogeneous r and zero-mean observation error, a random initial population still has E[Y(t)]=E[X(t0)]exp(r(t-t0)); heterogeneous r or time-dependent observation bias can violate that implication. Curvature therefore remains a nonmechanistic rival.

The raw squared-loss difference is algebraically fair to individual-well loss. At any frame, for either fitted mean m, the average heldout well loss equals (heldout arithmetic mean minus m)^2 plus heldout within-frame variance. The latter cancels exactly when subtracting the two model losses, even without independence. Training least squares on equal-sized frame means likewise has the same minimizing curve as least squares on all 14 training wells at the same frames. The arithmetic averaging does not secretly penalize the baseline through a different information budget for this mean-loss task. Training-only s_c squared is a count-magnitude normalization; it is neither residual variance nor validation leakage. Equal plate/frame weights define the target and do not estimate independence.

Every bootstrap draw must refit both mean functions, the training-only scale and heldout means. Holding the original net rate, amplitude or normalization fixed would change the frozen question and understate the specified perturbation. Repeated rows must contribute with multiplicity and both columns must stay together. Resampling individual frames or mixing roles would violate the design.

Ordinary full continuous multitime likelihood is the strong direct scientific alternative if the eventual objective is latent-rate inference. Wu Sec27–29 explicitly uses additive independent N(0,c^2 I) observation noise and a joint multitime covariance model, and warns that aggregate heterogeneous counts need not be Markov. BESTDR s2-1 uses time-homogeneous Markov transitions and count variance to distinguish rates; s4 acknowledges observation-noise/rate confounding and early transients. These inspected sources support the necessity of checking assumptions, not the outcome here. The current diagnostic does not compare against those full inference procedures, cannot claim their information is unavailable, and cannot establish that an agent or proposed statistic beats them. Such benchmarking is outside this one prerequisite check.

## Legitimate next decision

A consistent, numerically sound conditional curvature gain changes one legitimate choice: stop using the simple exponential predictor as an unqualified default for this fixed control-grid task, and do not carry its common-rate factor into covariance-to-rate interpretation on that basis. This is a conservative operational stop, not identification of which biological or imaging assumption failed.

Preference for the exponential only retains it as the better of these two fitted predictors on this conditional comparison. An inconclusive result leaves even that relative choice unresolved. Both outcomes still stop mechanistic promotion. None provides white-error, latent-rate or drug-specific validation; any later covariance study requires a separately frozen question and stronger assumptions/data qualifications. Thus the test has decision value without supplying a route to claim the broad co-learning objective achieved.

This initial assessment is preserved without coordinator response. It requests one pre-access rule clarification and otherwise permits only the narrow computation described above. No positive consensus or empirical win is required.
