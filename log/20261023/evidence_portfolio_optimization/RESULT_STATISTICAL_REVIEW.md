# Statistical review of the exposed Jaaks result

2026-10-23. Reviewed `PROTOCOL.md`, `PRE_FREEZE_REVISIONS.md`, `RESULTS.json` and `CROSS_EVIDENCE.md`, together with the independent reviews. This review reads summary records only. It does not independently reconstruct response arrays, choices, costs or bootstrap draws.

## Assessment

The frozen primary endpoint passes its stated development gate. At the declared >0.10 threshold, feedback obtains 919 two-read repeat-positives versus 675 with fixed ranking after the same scouts: +244, a 36.1% increase, with the reported paired SIDM-bootstrap interval [185, 310.025]. The stronger fixed paired-acquisition control obtains 876, leaving a much smaller +43 advantage, about 4.9%, with the reported conditional interval [9, 78]. Every arm is charged 3,234 planned reads, or 22,638 seven-well proxy wells. The gain against direct is about 1.90 repeat-positives per 1,000 planned proxy wells.

This supports one bounded positive observation: ordinary scout sorting can improve acquisition of pairs meeting a chosen two-measurement repeatability criterion on this exposed, selected Jaaks pool. It does not show more single-final-read positives at the same total cost. At >0.10, feedback has 919 positive final reads, whereas direct has 1,037. The primary comparison requires both purchased reads to be positive and is a different utility.

The discarded final-only design was set-dominated before outcomes and correctly replaced before freeze. My earlier `CROSS_STATISTICAL.md` supported that original comparison without detecting its set inclusion; that endorsement is superseded by the evidence review's challenge and the explicit pre-freeze revision. The new result cannot be used to claim success for the discarded final-only task.

## Selection of the scout is part of the endpoint

The scout used to select final nominations is also one of the two measurements required for success. Filtering out a known scout failure can therefore help the repeat-positive utility without the scout carrying any predictive information about the final measurement. This is a legitimate sequential-screening benefit for the declared purchased-repeat utility, but it is not automatically intervention-specific prediction or transferable functional information.

For an illustrative large-pool calculation, suppose scout and final binary positives are independent with homogeneous probability p = 0.6. Screening 0.4K candidates supplies enough scout-positive candidates to nominate 0.2K. Expected adaptive repeats are then approximately 0.2K*p = 0.12K, while fixed acquisition of 0.3K pairs yields 0.3K*p^2 = 0.108K. Adaptive screening wins even though scout status does not predict final status. This is a mathematical example, not a model fitted to the Jaaks data. It shows why the current endpoint alone cannot identify a predictive or world-model mechanism.

In the actual summary, feedback's >0.10 repeat count equals its positive-final count, consistent with every successful nomination already passing the scout criterion. The next controls should test whether scout magnitude adds anything beyond that binary paid gate. A good hit fraction by itself is inadequate because the policies buy different numbers of final measurements.

## Threshold reversal and uncertainty

At the fixed >0 sensitivity threshold, feedback obtains 1,061 repeats versus direct's 1,409: a reversal of 348. This does not invalidate the predeclared >0.10 primary test, and it must not be repaired by threshold tuning. It materially narrows the practical conclusion: screening is useful for this stronger read threshold, whereas broad near-zero positivity is sufficiently common that purchasing more fixed pairs wins. The threshold has no established clinical or latent-effect meaning. Report both outcomes prominently rather than describing an unconditional discovery-efficiency improvement.

The interval [9, 78] is conditional development uncertainty over 78 SIDM clusters and frozen choices. It is not a confidence statement for a new line distribution, a prospectively rerun policy, independent cultures, all drug pairs or a learned mechanism. Shared drugs, original validation selection and assay processing remain limitations. Global scout/final BARCODE separation prevents a specific plate-role reuse; it does not prove independent noise or remove source normalization dependence.

There is also a useful bootstrap interpretation check: resampling SIDM clusters while holding global choices fixed can change each arm's selected read count and hence break exact cost equality inside a bootstrap draw, even though the observed full-pool costs are equal. The reported paired count interval should retain its declared conditional interpretation. A supplemental cost-aware cluster analysis can expose this sensitivity, but should neither replace the frozen primary rule nor be presented as prospective policy uncertainty. Reallocating policies inside a bootstrap would be a different estimand and needs its own contract.

All reported missing counts are zero. Thus this dataset does not empirically test the effect of charged missing measurements; that behavior is supported by software fixtures. Seven wells per read is a declared combination-well proxy, excluding shared controls, usable plate capacity, processing and the turnaround of a two-stage screen. No executable wet-lab cost saving is established. Also report the absolute final nominations: 1,078 for feedback versus 1,617 fixed pairs. Feedback is already at 919/1,078 of its structural repeat-count ceiling, limiting headroom within this allocation budget.

## Tight next diagnostic

Support the root's proposed **explicitly post hoc** ordinary controls, without changing the original primary result:

1. Keep the same original top-S scouts, F final nominations, global plate roles, >0.10 endpoint and total S+F planned cost.
2. Gate on scout >0.10, then rank passing candidates by original score; fill any shortfall from scout failures using the predeclared original ordering.
3. Apply the same binary gate, then rank passing candidates by a fixed hash independent of response magnitude; use the same declared fallback and charges.
4. Persist these new nominations before converting any newly needed final responses. Record that some final outcomes are already exposed from the first run. This is a diagnostic comparison on the same historical pool, not fresh confirmation.

Feedback versus the gated-original policy asks whether magnitude beats simply removing known threshold failures and retaining the old prior. Feedback versus the gated-hash policy asks whether magnitude supplies value beyond threshold screening itself. Both are necessary simple explanations before adding models or agents. If they match or outperform feedback, the supported mechanism is ordinary binary screening. If feedback clearly wins, the result supports incremental magnitude information on this selected task; a later frozen, cross-context comparison against ordinary learned/direct predictors would then be warranted. Stop this line of elaboration if the gain disappears under these controls; do not change threshold, roles or reserve access to rescue it.

No world/direct learned comparison, agent contribution, inherited update, joint benefit, improved-improver effect, latent true-hit certification or FDR guarantee has been demonstrated. The result is worth this small additional diagnostic precisely because its primary gain against the strongest existing control is real in the reported record but modest, task-specific and compatible with a simple screening explanation.
