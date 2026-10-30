# Independent initial challenge — before source review or discussion

2026-10-28. Inputs read: BRIEF.md, CANDIDATE_v1.md, PROTOCOL_exact.md only for this round. No scout or coordinator conclusions received. Requested role: independent challenger. Effective model: unknown (no runtime metadata). No experiments executed.

## Algebraic assessment

The two-world construction is correct. Write q for the probability of choosing AB. Under B=I the regret is (1-q)/2; under B=S it is q/2. Their maximum is at least 1/4, achieved at q=1/2. This is worst-world expected simple regret for one choice of program, after the common exact source information and before any additional experiment. It is not a cumulative-regret result and does not include measurement or query costs. Deterministic choice has worst-case regret 1/2.

The source output of A is e1 in both worlds and source output of B is μ in both. AB has values 1 and 0, VB has 1/2 in both. Thus existing complete single-step marginal outputs do not identify the optimal choice across these two worlds.

## Conditions that must be explicit before code validation

1. Source and purchased observations must be specified per action and per channel. The valid matrix for action a is M_a, containing only initial distributions actually paired with an observed a output. A global M shared by all actions is invalid unless every required action was queried at every row. The present toy can query B at μ and e1 and thereby obtain rank two for B.
2. End-function-only observations give M_a P_a f, not M_a P_a. They generally identify an action on f rather than the entire kernel. Exception: in this exact two-state toy, f=(1,0) plus row normalization determines the other output coordinate. T3 must state whether it uses complete output distributions or this special two-state equivalence. Do not generalize the kernel-recovery assertion.
3. Span membership is sufficient for linear extrapolation of complete output distributions under exact known rows and a common invariant kernel. It is not a necessary condition for identification under stochastic constraints, restricted model classes, or task-specific values. Indeed the toy's μA=e1 and strictly positive μ already force both rows of A to equal e1 by nonnegativity, despite rank(M)=1. Any universal 'outside span means unidentifiable' assertion is false even inside the toy.
4. A prefix produces a lawful new input cohort only if identical independent preparations can be allocated to prefix-measurement and prefix-continuation groups, with state distributions exchangeable and the continuation action following the assumed Markov law. The prefix AB outcome is itself a task outcome purchase. It is neither a free state reset nor a novel source of information beyond testing that program.
5. A readout-defined state bin must actually be sufficient for the transition and terminal value; arbitrary RNA/readout bins do not guarantee a closed Markov kernel. A population distribution over independently treated cultures must not be confused with the within-culture distribution of interacting cells. Adding history to state can restore a formal model but may destroy cross-prefix sharing and available coverage.
6. Exact cohort means require a population oracle or an explicit idealization of infinite/noiseless observation. Zero observation noise does not itself remove sampling variability for a stochastic kernel. The identity/swap toy remains a valid algebraic construction, but is not a finite-sample biological protocol.

## Prior-art exposure and likely verdict

This currently establishes a correct, small, decision-relevant nonidentifiability example and a lawful experimental-information contract. Finite-state linear inversion with active rank completion is standard controlled system identification / indicator-feature operator fitting / experimental design. A fair baseline can query AB and directly compare its functional value against known VB=1/2; no full-kernel update is necessary. T4 should not assert agreement with every EDMD/OED method: specify indicator features, exact input/output moment regression, the same feasible prefix-query set, and the same rank-based design rule, then compare those concrete operations.

Unresolved prior-art checks: controlled-system rank excitation conditions; EDMD/OED equivalence under exact indicators and controlled inputs; PSR tests/linear predictive sufficiency; value equivalence and task-conditioned representation. A generic 'POMDP can represent it' statement is not a substantive novelty critique. The actual overlap is the observable linear prediction/experimental-design operation and the distinction between identifying full transition and identifying tested values.

Initial recommendation: proceed only as a corrected mathematical capability-boundary test; do not treat its execution as algorithm validation. A promising research direction would need an additional nonstandard constraint or operation and a decision-benefit separation from direct program testing and the same-information controlled-identification baseline. That separation is not yet present.
