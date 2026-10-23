# Frozen diagnostic: effector death is not necessarily target-count absorption

2026-10-23. Full objective ACTIVE / NOT_ACHIEVED. This is a stipulated mathematical necessary-condition test of the constructive proposal, not biological validation, novel algorithm evidence or an attempt to repair its stopped configuration.

## Model and observations

One effector and one target; t=0,1,2 and actual assay endpoint T=2. At t=1 the effector is observed dead and no target death has yet been observed. All observable history H1 is identical in two equally probable worlds. An UNOBSERVED binary pending-apoptosis state B is Bernoulli(1/2): if B=1 the target dies at t=2 following a prior committed effect; otherwise the target does not die before T. K counts observed target deaths, not lethal-hit initiations. No simultaneous effects, uncertainty in timestamps, survivor selection or other effectors are needed for this counterexample. Physical possibility is the premise being tested against the terminal rule; its rate is not measured or inferred here.

Both methods receive the same constant H1, same stipulated law and, in the finite-source arm, the same complete source episodes. Neither sees query B. A direct predictor cannot condition on latent B. The primary target Y=K2-K1 is therefore Bernoulli(1/2) conditional on H1. At actual T the remaining increment is zero; the observed 1-to-2 increment is still scored. The original effector-death-absorbed rule instead assigns remaining increment zero immediately at t=1.

## Fixed comparisons and claims

Primary proper score is Brier loss (p-Y)^2 for P(Y=1). Enumerate rational expectations exactly, no RNG or optimizer.

1. Original absorption constraint p=0.
2. Ordinary same-information law-aware endpoint predictor p=1/2. This has analytic knowledge shared by both models; its advantage cannot be interpreted as measured training efficiency.
3. Ordinary endpoint empirical mean from m=1,2,4,8 independent source episodes, evaluated on an independent query. Enumerate every source bit sequence and query bit with equal probability. Candidate may receive identical source episodes but its fixed terminal constraint remains p=0. This is an elementary finite-data counterexample, not an equal-compute search or RSI comparison.

Record Brier loss, average predicted probability and count-mean bias. Verify conditional tower identity E[Y|H1]=E[K2-K1|H1]=1/2; zero violates it. Expected theoretical scores .5, .25, and .25+.25/m are predictions to check, not executed findings.

## Decision and boundaries

Falsifier succeeds if the original zero-remaining rule is biased under the stated law and an ordinary same-H method has smaller expected Brier loss for m>1. Stop that instantiated terminal rule. Do not add pending-state modules, change K to lethal-hit initiations or retrofit future information. A target that cannot die after effector death would be a different law; no conclusion that every effector-death absorbing model is wrong. Distributional TD with the same wrong terminal is equally wrong. This test does not validate the existence of a pending state in a particular released assay and does not establish world/agent/inheritance/synergy/RSI benefits.

Implementation: research/sustained_function_task_20261023/delayed_death_check.py. Freeze hashes of this protocol, implementation and critic MATH_PRE_REVIEW before executing the numerical enumeration. No biological values or API calls.
