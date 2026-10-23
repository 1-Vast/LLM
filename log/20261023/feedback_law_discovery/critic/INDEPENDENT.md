# Independent critic: diagnostic identification of update rules

2026-10-23. Full objective remains ACTIVE / NOT_ACHIEVED. Prior scoped STOPs remain in force. This report was written without reading same-round peer reports. A source peer message arrived before sealing, but its mechanism has not been incorporated here; independence is therefore limited to the candidate developed before that message, not blindness to all peer text.

## One concrete candidate

Retain a small set of update operators compatible with current functional feedback; purchase the permissible measurement whose predicted functional outcomes disagree; choose the compatible operator and update a freshly reset predictor. The inherited object is the operator hypotheses and diagnostic selection procedure. Predictor weights, optimizer transient state, and zero-shot predictions reset identically in every arm. A frozen residual prediction head is not an updater just because it is renamed.

Different tasks can require different updates because the same currently measured functional response can arise from distinct parameter corrections with opposite consequences on a future endpoint. This is an observability claim, not evidence that such a distinction exists in the available biological data. No biological relationship or useful diagnostic has yet been authenticated here.

## Executed necessary-condition check

`observability_check.py` uses exact fractions. Two truths (1,0) and (0,1), common predictor (0,0), and support measurement x=(1,1), y=1 give identical gradient (-1,-1). Query x=(1,-1) has truth +1 or -1. Minimum-norm support fit (1/2,1/2) predicts 0, squared error 1. More generally any support-only query prediction z has equal-prior risk ((z-1)^2+(z+1)^2)/2=z^2+1 >=1, including a randomized procedure after expectation.

One paid diagnostic x=(1,0) distinguishes the truths. Selected operator then gives error 0. Ordinary Bayesian two-model discrimination with the identical diagnostic and budget also gives exactly 0. This establishes a missing-information requirement and explicitly does NOT establish superiority, novelty, biological utility, or RSI. The measurements are stipulated linear operators, not drugs or doses. With only the support measurement legally available, no inherited rule can identify the task.

## Strongest ordinary controls and falsifiable claim

Immediate counterpart is Bayesian active model discrimination, active meta-learning, episodic conditional prediction, and a mixture of experts with identical probes. Learned optimizers already condition updates on gradient history. An honest finite-budget claim would be: a specified compressed diagnostic/updater procedure learned on source tasks reduces held-out functional decision regret under the same permissible observations, assay costs, compute and candidate-search budget compared with all these controls. No such advantage has been measured, and a generic two-mode implementation is already matched exactly in the witness.

Necessary comparison arms: strongest direct predictor with identical sequential feedback; ordinary retraining and continued training; active learning with identical diagnostic pool; Bayesian model selection; simple mixture; learned optimizer; equal-budget program search. Match source data, task exposures, feedback, hyperparameter selection and all exploration cost. Separate inherited operator from inherited weights by resetting predictor/state and testing both inheritance objects factorially. Source-trained updater transfer is not RSI. An improved-improver claim requires a learned generator G1 to produce better subsequent update programs than G0 from the same starting programs, task histories and total budget, on fresh tasks.

Stop the narrow mechanism claim when a same-information ordinary method implements the identical operation, as happens in the toy. Continue only for an independently specified biological restriction or an experimentally supported finite-resource advantage. Do not add agent layers to compensate for an absent update-law advantage.

## Primary evidence and retrieval accounting

Three purposeful GETs used: two official arXiv API searches failed HTTP503; one HTTP200 reinspection of a previously read primary, https://arxiv.org/html/2610.09604v1, *Lightweight and Versatile Learned Optimization by Recombination of Gradient History*. This is not newly discovered prior art. Receipts, body and parsed text retained locally. It dynamically recombines gradient-history averages with learned per-group coefficients; this directly occupies history-conditioned update construction. Functional conditioning alone is not a novel operation. Author-reported compute/performance is not reproduced. No author code was run. No further source request, biological fit, protected label access or new split was performed.

## Decision

Candidate is reviewable as a diagnostic observability hypothesis, but generic operation novelty is unsupported and its exact minimal example is matched by ordinary Bayesian discrimination. No numeric biological GO. Next useful evidence is a legally measurable distinction between recurring functional failure types that predicts a transfer update under strong direct controls. Until that exists, this proposal is a concrete negative boundary and research question, not a promoted core mechanism.
