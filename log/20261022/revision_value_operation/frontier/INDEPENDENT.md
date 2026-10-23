# Independent operation audit: revision value needs contrast support and honest evaluation

2026-10-22. **NO_CANDIDATE for a new algorithmic core.** One concrete operator was examined: directly estimate the functional utility difference induced by a proposed world-model revision, restricting measurement effort to actions whose acquisition probability changes. It has a useful weaker support requirement, but its estimator is exactly the difference of ordinary doubly robust policy-value scores. A distinct unresolved problem is adaptive selection of the revision using the same feedback used to evaluate it. A finite exact counterexample shows known propensities and full action support do not by themselves remove that bias.

Read the full mandatory goal at the start of this stage. No current-stage peer file/message was read before this draft. Old AssayLoop, AR-BED and DABS primary bodies were reused; no new data, weights, network or model API requests. HEAD 47a0e2dea5a7dd42379fa17eb3621caf6bd0114c; existing tracked changes are log/README.md and research/REPORT.md, untouched. User Karpathy guidelines apply; rg found no on-disk AGENTS.md. All stopped reward-shaping, CCI projection and ALMANAC anchor-transfer routes remain stopped.

## The specific scientific estimand

At a history h of legal observations in a new functional screen, a fixed incumbent world model M and a proposed update U produce acquisition distributions pi0(a|h) and piU(a|h). Define the *one-next-assay* revision value

    Delta(U,h) = sum_a [piU(a|h)-pi0(a|h)] * mu(a,h),

where mu is expected measured functional utility of a legal assay bundle in this biological context. The candidates, dose/time/context, outcome definition and full physical bundle cost must be fixed first. This is a policy consequence of a model revision; it does not establish that the world model uniquely identifies cellular mechanisms, nor that model-state improvement itself is a useful decision metric.

This conditional one-step estimand is deliberately narrower than the total downstream discovery value. After the branches acquire different results their histories and candidate pools diverge. Summing the displayed local differences along only the incumbent's histories generally does not identify the revised policy's whole trajectory value. That requires sequence support/sequential causal assumptions, branch rollouts on a qualified complete table, or an authenticated counterfactual outcome model. An extra name for model revision supplies none of them.

## Exactly one attempted operation and its strongest faithful counterpart

Let d(a)=piU(a)-pi0(a), and log one evaluation action A drawn using known q(a|h) and functional outcome Y. Fit a mean predictor m from independent source/pre-evaluation information. Before observing A,Y, freeze U, d, m and the current h. Then use

    psi = sum_a d(a)*m(a) + d(A)/q(A) * [Y-m(A)].

Require q(a)>0 wherever d(a)!=0. Actions with d(a)=0 may have q(a)=0: their identical policy mass cancels. With q correct, conditional expectation of psi is Delta even if m is wrong. A cross-fitted/direct or ordinary learned predictor can be m; a mechanistic world model receives no privilege. Logged randomness must be independent of potential outcomes conditional on the recorded history. This rule is not advertised as a new invention: it is a linear policy-value contrast with a standard augmented inverse-propensity correction.

The strongest faithful conventional counterpart computes V_DR(piU)-V_DR(pi0), using the *same log record and same fitted m*. Every summand is identical, including the cancellation of common unsupported actions. Its online arithmetic can also exploit sparse d and share cached source predictions. Comparing to two independently sampled value estimates or an implementation that unnecessarily recomputes all actions would manufacture variance or compute headroom. A policy-directed logging allocation such as q proportional to |d| times a residual-scale estimate is also ordinary optimal importance allocation; it is not a second proposed mechanism.

The plausible distinction from AssayLoop is a feedback contract, not yet a methodological contribution: it evaluates revision credit from one observed action rather than freely looking up the labels of both actual and reference batches in a completed retrospective table. The plausible distinction from AR-BED/DABS is that m is not allowed to declare its own unobserved predictions ground truth. These restrictions matter scientifically, but they do not distinguish psi from an equally informed ordinary estimator.

## Executed exact falsifiers

The independent standard-library executable is research/revision_value_operation_20261022/frontier_exact_audit.py; results are EXACT_AUDIT.json. All numbers are constructed rational toy probabilities, never biological records.

1. **No contrast support means no identification.** Two actions have means (1/2,0) or (1/2,1). A logger always measures action 0; old policy chooses 0, revised policy chooses 1. Both worlds have the same full observed-data law, but Delta is -1/2 versus +1/2. Any estimator or update rule receiving only those observations, the same source history and the same prior model has identical input distributions in both worlds. A confident sign claim cannot be justified without additional structural information. This does not prove real data lack overlap; it proves an exact necessary gap for this contract.

2. **Only contrast support is required; ordinary DR gets the same benefit.** pi0=(1/2,0,1/2), piU=(0,1/2,1/2), q=(1/2,1/2,0). Neither absolute policy value is identified from this logger without assumptions on arm 2, but their difference is. Across 216 exact combinations of three mean values per arm and binary fitted means, psi expectation equals Delta and equals the difference of ordinary DR scores pointwise. Thus a universal requirement to observe every arm used by either policy would be too strong for this *fixed conditional contrast*. Conversely presenting cancellation as a new core fails the faithful comparison.

3. **Same-feedback revision selection biases even a fully supported known-propensity estimate.** Both actions have true mean 1/2. Logger draws A uniformly, Y is Bernoulli(1/2), incumbent is uniform. Select a revised policy that chooses A when Y=1 and the other action when Y=0. Its true next-assay value increment is always zero. With m=0, reusing that same (A,Y) in the displayed score yields exact expectation 1/2. Evaluating the selected policy on a fresh independent uniform action/outcome yields expectation zero. Four source possibilities and 16 source/audit pairs are enumerated exactly. Propensity correction does not turn adaptive model/program selection into honest evaluation.

These checks address identification and estimator equivalence, not efficiency bounds, confidence intervals or observed functional performance. No larger toy or neural benchmark is needed to reject novelty for this literal estimator.

## What the existing 2026 sources actually supply

Exact excerpts and hashes are saved in SOURCE_PASSAGES.json. The original papers remain in the prior phase's frontier/sources directory; they were previously authenticated by official arXiv receipts.

- AssayLoop arXiv2609.11877v1, Methods 4.5, explicitly computes hits in both the selected and context-free reference batches and trains on completed historical screens. The previously authenticated official rl.py statically gathers hits_b for reference top-k and can calculate auxiliary held-out-gene BCE. Such source training is legal when historical outcomes are available and charged as source information. It is not an estimator that obtains the unchosen batch's measured utility from a sparse live log. Source roles do not become independent physical assays merely because a replay program hides labels.
- AR-BED arXiv2610.20832v1, Methods 4.1–4.2 and Appendix D.6, specifies an external fixed likelihood oracle and sums over hypotheses and outcomes for Rao–Blackwellized expected information reward. It explicitly says the reward is exact for its specified finite model, not necessarily the full target hypothesis space. For functional drug utility, a calibrated external response law would be an additional assumption; substituting the model under revision as its own judge creates a different estimand.
- DABS arXiv2607.16927v1, Section 3.2 and limitations, integrates continuous effects/noise under conjugate spike-and-slab assumptions to target activity-support information. This is exact model marginalization under a chosen generative family, not recovery of unknown counterfactual drug outcomes under an arbitrary selective logger. These priors can be helpful predictors; they do not eliminate the two-world support counterexample without an explicit, warranted restriction excluding one world.

Source-excerpt extraction initially selected the TOC and then an appendix occurrence of a repeated phrase; the selector was corrected before sealing to the unique literal 'RL fine-tuning. The supervised policy'. No unsupported conclusion rests on a heading-only match.

## Realistic feedback contract and honest next gate

A feasible *retrospective* starting point exists in the official AssayLoop documentation: completed CRISPR screen libraries and binary functional labels. A separate root qualification would have to verify actual physical independence, usable phenotype, legal library, study groups, missingness and labels. A precommitted randomized reveal mechanism can create known q for a replay; that q is an algorithmic masking design over pre-existing observations, not the original wet-lab propensity or evidence of fresh sequential experiments. Public hit labels cannot automatically stand in for drug treatment benefit, and the author's curated test set was selected partly using outcome and LLM-performance conditions.

A genuine sparse real-assay contract would log all pre-action context, candidate legality, the randomized sampling probability of each actual purchasable bundle, dose/time/cell identity, control/replicate costs, measured functional utility and missingness. Freeze each candidate update before its independent evaluation feedback; for adaptive campaigns use predictable policies plus valid sequential evaluation, or separate whole-study folds where the update is refit without the evaluation group's outcomes. Shared controls and pooled-screen interference require evaluating the physical bundle/joint sampling design rather than treating each gene as an independent free assay. No such new contract was authenticated this stage.

The minimal future gate is not 'train the estimator': it is to specify whether the intended target is fixed one-step contrast, value of an adaptive update *algorithm*, or full multi-step discovery. Then establish support on the relevant differences and enough independent evaluation units to avoid revision selection bias. If those hold, standard paired DR, IPW, direct modeling, cross-fitting/holdout, ordinary contextual update-rule learning and sequential off-policy evaluation are mandatory equal-information competitors. A novel candidate would have to beat their attainable precision/cost under a stated extra structural property, rather than quietly receiving counterfactual labels, discarding selection cost or assuming an oracle likelihood.

## Decision and inheritance limits

Stop novelty promotion for the displayed estimator because the faithful conventional operation is exactly equal. Retain the weaker contrast-support fact and the same-feedback selection counterexample as constructive qualification requirements. The concrete unresolved gap is a useful, statistically honest estimate of the *adaptively chosen update rule's* later functional value with limited logged overlap and physical assay bundling, without uncharged oracle labels. No new estimator overcoming that gap has been provided here; adding a learned model or another selection layer does not solve it automatically.

Learning U from such valid scores could be ordinary metaoptimization and may still be valuable. Model revision alone is adaptation. Inherited update-rule benefit needs held-out tasks. Operational Level 3 needs later common-start improved-improver comparisons; none follows from an unbiased single policy contrast. World, agent, inheritance, joint and recursive functional gains remain NOT_ESTABLISHED. The full objective is not achieved, and this local NO_CANDIDATE does not declare it globally blocked.

Resources this stage: local primary-source reads, one exact rational audit, zero API/network calls, zero biological scalar/array reads, zero protected-response access, zero author-code execution. No old sealed file was changed.
