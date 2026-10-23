# Independent renewal: finite-excitation dynamic updating, no drug-core GO

2026-10-23. **NO_SUPPORTED_CORE / NO_EXPERIMENT_GO**. One2026primary method actually inspected, threeHTTP total under the four-request cap. No current-phase peer report read before this seal. No count/model fitting, old outcome reopening, new biological data or API-model calls. The stopped GI/count/projection leads remain stopped; this is a different observation-contract question.

## New primary and exact reading scope

Trivikram Satharasi et al., **Adaptive Control with Sparse Identification of Nonlinear Dynamics**, arXiv2604.06338v1,7April2026. Before fetching the original, exact-title/ID search across historical Markdown/JSON (excluding this phase) found no hits. Official original https://arxiv.org/html/2604.06338v1 returned200,692119bytes,SHA2568c0acb15dc363bf71a96e3779071501709539b6f6883ca1c908b0881f0827b07. Read problem/Assumptions1–2, integral regression equations5–7, Algorithm1, sparse cost/update equations9–11, Theorem1's statement/ultimate-bound form and simulation/limitations discussion. No author code, complete proof audit or benchmark reproduction. Source text/projection and UTC/status/byte/hash receipts retained.

The method's substantive published addition is a sparsity-promoting integral concurrent learning (SP-ICL) differential-inclusion update integrated with a tracking controller and nonsmooth stability analysis. Integral history reuse/finite excitation itself is explicitly inherited from earlier ICL literature. Thus neither 'remember informative experiments' nor 'learn equations sparsely' is claimed as a new2026primitive.

## The actual operation, beyond static label regression

The system is xdot=Y(x)theta+g(x)u, with fixed unknown sparse theta, known nonlinear library Y, known g, and observable state trajectory. For a windowT the paper forms

    Yf(t) = integral_[t-T,t] Y(x(tau)) dtau,
    Uf(t) = x(t)-x(t-T)-integral_[t-T,t] g(x(tau))u(tau) dtau,
    Uf(t)=Yf(t)theta.

This avoids explicitly differentiating measured states in the identification equation. A bounded history stack stores window observations and constructs normalized Gram H=sum_i Yfi'Yfi/(1+kappa||Yfi||^2) and matching rhs h. Finite excitation requires lambda_min(H)>=y_lower>0 after some finite time. Unlike persistent excitation, sufficiently informative past data may then be reused without perpetual probing. Algorithm1 refreshes a finite memory using minimum-eigenvalue conditions, favoring recent samples once an information threshold is preserved.

The sparse objective is .5 theta_hat'H theta_hat-theta_hat'h+lambda||theta_hat||1. The update adds a tracking-error term Y(x)'e, a memory residual h-H theta_hat and a nonsmooth shrinkage term; only the continuous part is projected onto a bounded parameter set. The paper analyzes a differential inclusion to retain boundedness despite the unprojected sign term. This is an explicit feedback/model-update operator with a conditional stability property, not an ungrounded world-model label. Its control/trajectory contract and nonsmooth boundedness argument are not equivalent merely by naming a static KRR/covariance/ridge family.

However, the memory Gram/right-hand-side and sparse regression are standard sufficient statistics/inference ingredients. A same-information batch/incremental sparse estimator can reuse the same integral windows; no claim that ordinary direct estimation cannot do so is justified. The finite-excitation result is conditional on an informative full-rank history, not proof that sparse labels magically provide it, nor an active experiment-selection sample-complexity guarantee. The routine selects which **already observed windows to retain**, not which drug action to administer by a new information-gain policy.

## Claimed guarantee and material limits

Assumption1 requires g(x)full row rank, hence full/over-actuation m>=n. The certainty-equivalence controller uses its known right inverse. Assumption2 requires positive minimum eigenvalue in the full p-parameter library. Sparsity regularization does not relax that to a sparse restricted-eigenvalue condition in the stated guarantee. Theorem1 establishes ultimate boundedness under gain/excitation/initial-condition restrictions; its radius depends on lambda,parameter dimension and excitation. It is not unbiased exact parameter recovery, finite-sample drug-effect identification or an improved-improver result.

The simulation is a fully observed2-state polynomial system with20dictionary coefficients and g=I2, with known equations/parameter truth for scoring. It studies shrinkage strengths, tracking/model error and sparsity. Reported stronger shrinkage produces chattering and can worsen tracking or remove true terms. These are the author's synthetic results, not our cell evidence. Noise robustness, latent unobserved cell states, unknown drug actuation and cross-task inheritance are not established by the inspected theorem/experiment.

Source precision: Eq6uses a normalized memory Gram, while Algorithm1 displays unnormalized Gram sums; the prose after Eq8says replacement does not decrease the minimum eigenvalue, although retaining a threshold need not preserve its previous higher value. I do not silently equate those statements or rely on monotone-information claims without implementation clarification. The core integral relation and declared assumptions remain clear. This is a reading caveat, not a claim to have disproved the stability theorem.

## One concrete transferable bottleneck for drug-functional feedback

Application worth considering independently of old endpoints: revise a dynamical model of living-cell proliferation/recovery under timed drug pulses so that limited follow-up assays improve predictions of **unseen schedules**, not just the endpoint at an already measured dose. The useful structural question is whether measured input/state windows provide finite information about the changing drug-response dynamics before more closed-loop decisions are made. Repeated trajectories close to a steady response may add many rows while leaving relevant window-regressor directions unexcited. Tracking a target well and identifying how an untested pulse acts are different objectives.

This bottleneck is concrete: inspect the declared window regressor's nuisance-adjusted rank/conditioning and prediction of held schedules, rather than interpreting more labels or agent reflection as new knowledge. Integral windows avoid one numerical derivative burden; an information-preserving memory may permit later model updates after probing ends. Those are potentially useful finite-information/control properties in an existing family, not novelty conferred by applying a surname to cell data.

The present drug mapping fails crucial premises. Typical few-drug interventions do not provide known full-rank actuation over a high-dimensional cellular state; drug efficacy itself is unknown. Destructive transcriptomic snapshots do not automatically supply a continuous same-state trajectory. An observed cell count is not automatically a closed Markov state. A time/dose endpoint table is not a timed-input trajectory and cannot be relabeled as the required Uf observations. No specific public drug-pulse dataset with authenticated input times, tracked functional states and needed repeats is qualified in this phase. Therefore this primary supplies a real technical bottleneck and a fair control, **not a currently executable cell mechanism**.

## Minimal falsifier if an appropriate observation contract is later available

First fix an actually available functional trajectory/input dataset and a small declared state/library/actuation contract using source information only. Do not assume gknown/fullrank to import the theorem; either authenticate those properties for a legitimately low-dimensional endpoint or clearly forgo that guarantee. No extra drug/trajectory observation is free because the model is dynamical. Independently assign whole schedules/replicates as queries, not overlapping time windows across training/query.

Then ask whether the proposed memory/update operation improves unseen-schedule functional prediction or schedule decisions at the same real trajectory/dose/time cost against frozen/direct trajectory models, ordinary batch/incremental sparse identification, RLS/ridge/KRR with the same history features, ordinary forgetting/retraining/continual updates, active-design controls and equal-budget program search. Separate memory-retention gains from actually acquiring more informative perturbations. Charge window computation, dictionary/rank tuning, source training and controller/solver work. Stop if the legal history does not identify the relevant directions, the model needs unavailable state/control measurements, or a simpler same-window ordinary estimator matches utility/cost. A pure simulation with known g=I cannot satisfy the biological observation contract.

This is a future falsifiable capability question, not an instruction to start fitting now. A new drug-specific structural restriction or measurable finite-information advantage would need its own independent evidence/review. No such restriction is supported by the present read. Reusing a history stack or carrying theta to a new run is not RSI; inherited update benefit and improved improvement strategy require separate later-task/common-start tests.

## Decision and resource record

NO_SUPPORTED_CORE. Preserve the usable insight—feedback quality is constrained by dynamic excitation and actual actuation/state observability—without inventing a new cell model or reopening the failed count lead. Familiar components do not automatically invalidate a contribution; here it is the missing drug observation/control premises and absent demonstrated advantage that prevent promotion.

ThreeGETs: two OpenAlex metadata searches200 and one official original HTML200; no fourth request needed. All original bodies/receipts retained. One metadata query returned mostly educational 'active learning' results and was not used as mechanism evidence. Projection initially generated via a local one-off lxml command, with reproducible project.py saved under research; no new dependency install. No new biological values, fits, models, tests, API-model calls or old-array reads. All artifacts here, all scripts under research/grounded_feedback_renewal_20261023/constructive. Native tokens/currency unavailable. Full goal ACTIVE / NOT_ACHIEVED.
