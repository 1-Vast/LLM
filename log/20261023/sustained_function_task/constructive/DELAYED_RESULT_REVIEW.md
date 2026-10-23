# Constructive independent review of delayed-target-death result

2026-10-23. Read DELAYED_DEATH_PROTOCOL.md, DELAYED_DEATH_RESULT.json and delayed_death_check.py after the frozen run. **ACCEPT_STOP_THIS_EFFECTOR_DEATH_ABSORBED_TARGET_COUNT_RULE.** This is independent analytic/static result review, not a rerun, new experiment, statistical fit or biological validation.

## Independent algebra

Both methods observe identical H1, not hidden query B. Under the stipulated law, Y is Bernoulli(1/2). For any independent source-based forecast p, expected Brier loss is

    E[(p-Y)^2] = 1/4 + Var(p) + (E[p]-1/2)^2.

Thus the hard absorbed forecast p=0 has loss1/2 and mean-count bias-1/2. The ordinary law-aware p=1/2 has loss1/4. The empirical mean of m independent Bernoulli source episodes has mean1/2 and variance1/(4m), giving loss1/4+1/(4m). The reported m=1,2,4,8 values1/2,3/8,5/16,9/32 and source/query assignment counts4,8,32,512 agree exactly with these identities. For m=1 the empirical predictor ties the absorbed rule; strict expected advantage begins at m>1, as the protocol states. No latent query-state observation is needed by the ordinary predictor.

The script statically enumerates every source bit sequence and both independent query outcomes with weights1/2^(m+1). Its calculations implement this population without RNG, learning or an oracle B feature. I did not import/run it or claim an independent execution audit. The ordinary law-aware score is an analytic comparator, not evidence that source training acquired the law cheaply. The finite-source comparison is an elementary risk calculation under declared iid episodes, not measured assay sample efficiency or equal-compute program search.

## Relevance to the original target rule

The original sealed proposal counted **observed target deaths**, yet treated NK death as a boundary with no future target-count increment. The stipulated pending-target construction is directly relevant: a lethal influence can precede NK death while the observable target death follows it. At t=1, no target death has been observed, so K2-K1 still includes a possible later target death. At actual endpoint T the *remaining* increment is zero, but this does not erase the observed interval1-to-2 increment. Those are different boundaries.

This falsifies the proposed hard death-absorption constraint for the declared outcome under this law. It does not claim that every neural model trained with some terminal targets must output exactly zero in every implementation; p=0 is the explicit semantic constraint being tested. A learner allowing later deaths after NK death would already have relaxed that constraint. Redefining K as lethal-hit initiations would change the observable target and require separate measurement authentication, rather than repair the original test. No pending-state module or such relabeling is proposed here.

Ordinary distributional TD with the same incorrect terminal boundary shares the defect. The result therefore validates the earlier substantive critic objection rather than arguing that an unfamiliar model family is wrong or an ordinary method is inherently correct. A full-history functional forecast can mathematically handle hidden B by predicting its conditional probability; it need not identify B in an individual cell.

## Limits and stop

Bernoulli pending status, its1/2probability, source independence and event timing are stipulated. The calculation does not authenticate delayed apoptosis in the selected source, estimate its prevalence, establish per-NK death attribution, or overcome unavailable public event/censoring data. It is not a new biological positive or performance replication. A different measured law with no delayed attributable target death could justify another death-terminal estimand; this result is no universal rejection of all absorbing effector models.

Accept the fixed terminal-rule STOP and retain the broader untested question of predicting sustained target death and effector loss at the actual assay endpoint under lawful history. No new fit, parameter menu, additional search or revised candidate follows. World-model, agent, updater-inheritance, joint and G1-over-G0 benefits remain unestablished.
