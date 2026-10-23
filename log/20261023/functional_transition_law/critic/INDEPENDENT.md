# Independent critic: temporal innovation transport versus inherited dynamics knowledge

2026-10-23. Full goal read in full and previous feedback_law_discovery/DECISION read. Objective ACTIVE / NOT_ACHIEVED. Prior consistency configuration remains STOP; no gamma/width/step rescue, old growth-clock equivalence or old mechanistic branch reopened. One concrete temporal feedback operation is attempted below. No biological labels/fit, author code or reserve accessed.

Independence scope: candidate, retrieved primary and exact check were completed before receiving source's mechanism summary. That peer summary arrived before this written seal; it is not used in this independent candidate. Root also supplied release names/README-only metadata, not numerical evidence; it does not support the candidate's dynamics assumptions.

## Concrete operation and application

Application is short-duration actual live-count feedback updating a late viable-count forecast at a fixed intervention/dose. Let z(t)=log(N(t)/N(0)); measured control trajectories are separate observed inputs, not assumed perfect clocks. Over a declared bounded window, approximate forecast discrepancies by velocity and acceleration basis b(t)=(t,t(t-1)/2). The acceleration term is a local net-growth curvature, not identified cell death, resistance, intracellular dose or metabolic yield. This is a distinct operation from stationary GR recalibration, but the polynomial dynamics family is ordinary.

From a common initial predictor theta0=(r0,k0), measured early log-count discrepancies e=y-H theta0, and source-estimated between-task correction covariance C, apply

    U_C(theta0,H,y) = theta0 + C H^T (H C H^T + R)^(-1) e.

H contains actual time basis rows; R describes observation noise. Late forecasts recompute b(t)^T theta_new, and multiple doses could share a predeclared covariance structure only if source evidence warrants it. Inheritable object C specifies how early functional innovations revise a late trajectory rather than merely recomputing a stationary rate. A learned optimizer can implement this matrix map exactly; no claim is made that it cannot. For sequential feedback the posterior covariance and observation history must update too; reusing a fixed gain while double-counting old observations is not this operation.

## Executed exact finite-sample witness

The standalone Fraction script temporal_innovation_check.py computes population moments, not fitting/Monte Carlo or biology. Stipulated truth z(t)=r*t+k*t(t-1)/2; independent zero-mean r,k with variance1; early observations at times1,2 have independent unit-variance errors; target is latent late z(3)=3r+3k. Initial predictor zero, H=[[1,0],[2,1]], C=R=I. Gain K=[[1/4,1/4],[-1/4,1/4]], late predictor is (3/2)*y2.

Ordinary unregularized joint refit yields 3*y2-3*y1 and expected late error18. The inherited innovation rule has expected error9/2. This is a genuine finite-sample risk calculation in a stipulated distribution. However ordinary same-prior Bayesian regression and a direct conditional predictor give exactly the identical 9/2 and identical predictions. Source knowledge can help without a different learning algorithm. Keeping the inherited gain while changing target curvature variance from1to9 gives risk45/2, worse than refit's18. Thus the claimed advantage needs stable correction statistics; temporal information alone does not guarantee transfer. Independent late measurement noise would add the same irreducible term to all risks under the specified measurement model.

This is not a new biological positive, not an assertion that actual counts have Gaussian log errors or quadratic dynamics, and not a refutation of a nonlinear ordinary dose-time model. It provides an explicit attempted operator, finite-sample rationale, exact strongest counterpart and falsifying shift condition. Shared time curvature would need support beyond an individual curve fit.

## What could be novel, and what currently is not

For linear-Gaussian restrictions the WHOLE stated operation is standard conditional/MAP adaptation, not merely a member of the same broad family. Narrow new-operation novelty is therefore STOP. This is not a veto on useful constrained biological models: if a genuinely supported restriction linking early innovation types to later dose/time responses were found, it could still yield a finite-resource contribution, tested against the identical restriction in empirical Bayes and direct prediction. None has yet been identified in this independent check. Adding count/CTG features or learned covariance does not remove that requirement.

Candidate source-only hypothesis, not a new experiment authorization: repeated actual count trajectories across line/drug tasks might show low-dimensional, task-stable velocity/curvature correction statistics that transfer late-count improvements from few early observations. Strong same-information Bayesian covariance adaptation, joint six-parameter refit, shrinkage trajectory models and direct episodic time/dose prediction must receive those statistics and the same feedback. An independent early→late CTG channel cannot be generated from counts: ATP per cell may change, so the cross-channel measurement law requires actual paired data/validation and a separate direct control. Do not add a death state, latent dose or a CTG calibration gate after a failure.

## Inheritance and RSI separation

Retaining source C in a fixed Bayesian solver is inherited dynamics-distribution knowledge. Retaining an initial mean trajectory is predictor knowledge. Retaining K derived from C is not automatically a changed algorithm; for this operation it is a cached statistical prior. If a learned update procedure U_eta is later proposed, ordinary Bayesian/joint-refit controls must inherit the same learned C/dynamics representation. Compare common predictor mean, common dynamics prior/noise assumptions, common feedback and equal source/search budget, with only the update procedure varying. A parameter-prior × update-procedure factorial is necessary; reset predictor mean alone does not isolate updater inheritance.

Zero-shot direct conditional prediction remains a strong alternative: storing a function of support history may emulate system identification without fitting target weights. Its information/budget cannot be weakened merely to manufacture an updater distinction. World contribution additionally needs matched direct time/dose/history input versus a state-transition model. Agent contribution needs policy improvement beyond fixed/standard acquisition. Source learning U once is not improved-improver RSI: G1 must produce better subsequent U programs than G0 from common U/model/history under equal total cost on later independent tasks.

## New primary reading and bounded requests

Three purposeful GETs, all200: broad official arXiv web search; targeted exact meta-learning AND system-identification search; full original https://arxiv.org/html/2610.13411v1, *In-Context Learning for System Identification: Probabilistic Formulation, Long-Sequence Handling, and Benchmark Validation*. Local duplicate search found this ID previously present in update_law_search/skeptic/SEARCH_ENTRIES.json; it was a historical index hit, not claimed a previously unknown paper. This pass read the original conditional meta-model formulation, probabilistic NLL Eq6, source-training description, and Eq31 uncertainty-weighted synthetic regularization. Receipt/body/text retained. Other search abstracts are leads only, not authenticated methods.

Primary explicitly meta-trains a context→future output distribution approximator; Eq6 minimizes conditional negative log-likelihood. Eq31 fits a classical predictor with real-data loss plus uncertainty-weighted synthetic predictions. Thus emulating identification without target fitting, and using source-conditioned future predictions as regularization, are concrete occupied operations. Source synthetic calibration/generalization and reported benchmarks are author claims, not independently reproduced. A learned conditional future map is not necessarily a changed updater. No foreign code executed and no synthetic model output substituted for measured biological feedback.

## Decision

NO_NEW_CORE_GO. The proposed temporal innovation rule is simple, operational and differs from the stopped stationary growth-clock update, yet its whole linear-Gaussian implementation is ordinary Bayesian identification. Its exact gain over unregularized refit proves only useful source prior information in the stipulated finite-data model and vanishes against a same-prior direct/Bayesian control. Preserve it as a necessary ordinary comparator and inheritance attribution test. Later review may nominate a biologically supported non-equivalent restriction or finite-cost gain; this report does not authorize data fitting or declare RSI unsupported universally.
