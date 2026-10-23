# Cross-review of the cached repair-menu STOP decision

2026-10-22. Reviewer: frontier_distinct, taking the opposing interpretation role. Decision: **support STOP of this frozen saved-menu routing configuration; no diagnostic collection, router fit or RSI escalation on its behalf**. This is a bounded exposed-data development decision, not independent confirmation or a theorem about world models.

I read `UPPER_BOUND_PROTOCOL.md`, its `FREEZE.json`, and the already generated `UPPER_BOUND_RESULT.json`. I also inspected existing independent-recomputation output and exchanged objections with recursive_distinct. I did not rerun either implementation, recompute any result, train a model, decode raw biological data, call an API or download a source. Numbers below are transcribed from existing results, not a fresh numerical experiment.

## 1. The newly resolved question

The original Q already evaluated common-support head-only, trajectory-only, joint and no-update procedures. Its fixed-arm means did not directly determine the pointwise best selection among them. The new envelope resolves that previously unreported finite-menu question without learning a router. It therefore adds useful negative evidence rather than merely repeating the original average negative.

The primary final table contains seven lineages, one stock each, twenty saved arms. All arms use their recorded common support and target contract. The frozen endpoint is precision@5 on target drugs, and the useful margin is 0.09 precision@5, equivalently 0.45 hits per five nominations. This is not the separate end-to-end 0.40-hit margin.

| Saved primary menu | Existing oracle precision@5 | Existing difference from fixed B1:none | Interpretation |
| --- | --- | --- | --- |
| R: no update / functional-head / molecular-trajectory / joint | 18/35 | -1/5 | Even label-informed repair selection loses to B1. |
| R + B1 fallback | 5/7 | 0 | Fallback does not hide a missed positive repair subgroup. |
| R + B1 + Cmol fallback | 5/7 | 0 | Adding this standard measured-state predictor does not open more room. |
| All twenty saved arms | 27/35 | 2/35 = 0.057142857... | The optimistic broad saved menu still misses 0.09. |

Fixed B1:none is 5/7; fixed Cmol is 24/35. The stored all-twenty envelope exceeds Cmol by 3/35 = 0.085714285..., also below 0.09, although that particular comparison is close to the threshold. The primary B1 comparison is the clearer stopping reason. The fixed B1:kernel2 comparator is weaker here; beating it cannot replace the frozen stronger B1 requirement.

Most decisively, in every recorded final background each of the four R actions is no better than B1. At HCC38, no-update and molecular-only tie B1 while functional-only and joint lose; the other six backgrounds have no R action tying or beating B1. Thus the R+B1 result is not an average cancellation that a better residual diagnostic could remove. No selection rule over those saved actions can create a positive precision@5 improvement over B1 on these seven recorded tasks. The all-twenty extra opportunities are at HCC1187 and HCC38 and can be achieved by conventional kernel actions; they cannot be attributed to state repair or an agent.

This does not mean all R predictions, probability vectors or selected drug sets are identical. It means their recorded top-five hit counts supply no positive action choice over B1. A diagnostic could distinguish harmful from neutral R actions and still fail the useful-gain requirement. We have not tested whether residuals contain information for some other outcome.

## 2. Strongest opposing objections, and where they apply

**Objection: B1 was selected because it looks strong, so this is an unfairly moving baseline.** The new protocol fixes B1:none before the new scalar decoding; it does not select it from this new final envelope. B1's historical choice as a strong conventional comparator used the old development/selection process. That history makes population claims and renewed confirmation inappropriate, but does not invalidate the conditional pointwise inequality against the named fixed B1 column. The same-table envelope remains a genuine upper bound for any selector restricted to the saved actions. Dropping B1 now in favor of a weaker comparator would instead change the scientific target after seeing the result. Baseline selection uncertainty would matter if estimating how a source-trained comparator-selection procedure generalizes to a new asset; that is not what this calculation establishes.

**Objection: there are only seven exposed lineages and noisy labels.** Correct. The calculation is not a statistical population impossibility result and supplies no prospective guarantee. It does not show that a repair could never help an eighth lineage or a different measurement. However, lack of population identification does not justify fitting a high-dimensional router to this sample after its target-label oracle fails. The max already has access to target labels and is favored by selection noise. A small conditional sample upper envelope is sufficient for the predeclared development resource decision, not for a universal rejection.

**Objection: the fitted model is weak, so better training would change everything.** Plausible and unresolved. These actions depend on the historical width-16 ppODE, recorded training regime, checkpoint, update steps/rate, loss weighting, support drugs and masked 24 h measurements. The original initialization/seed and architecture caveats remain. A better initialized or larger model, different molecular scale handling, new coupling or new training objective could produce a different action table. That would be a new candidate experiment with its own hypothesis and cost, not evidence that this saved-menu gate passed. We do not establish the causal reason for the current dominance.

**Objection: the saved state-only action is not the proposed state-parameter repair with both losses.** Correct and explicitly recognized by the frozen protocol. Historical molecular-only means trajectory parameters plus molecular-only loss. Historical functional-only means head parameters plus functional-only loss. A trajectory-parameter update using joint molecular and functional loss, a different order of updates, an alternating optimizer or an entirely different executable improver is outside R. The current result must never be described as testing those unexecuted procedures.

**Objection: a mixture of two weak scores can outperform each score.** Correct. Per-background selection of one saved score is different from a new per-drug blend, calibrated combination or ranking. The all-twenty envelope bounds selecting a saved action, not constructing a score from several actions. In particular, repair1's useful exposed blend signal remains on its different model/pool/process contract; it is neither disproved nor a legal rescue of this original-Q envelope. Any proposed new blend remains subject to strong direct predictors and source-tuned simple mixing controls.

**Objection: residuals might predict probability accuracy even when precision@5 is unchanged.** Correct. The present result does not bound Brier improvement, calibration, AUROC, molecular loss, uncertainty estimation or downstream utility at another k. We have not computed those new envelopes and should not do so to rescue a failed primary endpoint. A compelling different clinical/experimental utility would need to be declared as a new objective with a justified useful margin and data contract. It cannot retroactively convert this precision@5 STOP into GO.

**Objection: a different observation policy or cheaper procedure might still have practical value.** Correct within a new contract. This envelope is conditional on saved supports and outputs. It excludes new support selection, additional experiments, earlier feedback, different doses/times and policies that learn new actions or use individual target-drug feedback. It also does not establish a total-cost impossibility theorem. The oracle was optimistically exempted from search costs, making its failure informative for the frozen useful-gain target, but the result cannot rule out every future cost-saving objective. Q precision@5 after three dual-modality support assays is not five target confirmations inside the original five-unit screening budget.

None of these valid scope objections supplies an action in the frozen table whose utility exceeds its maximum. They constrain the wording of the STOP; they do not overturn it.

## 3. Selection tables are separate descriptive checks

The saved selection tables each cover five lineages and six stocks. The 20-arm table's recorded all-arm envelope is 43/50, with +1/25 over its fixed B1=41/50; the 26-arm grid table's envelope is 9/10, with +2/25 over B1. Both are below the same 0.09 precision@5 margin over B1, but they are not additional independent final evidence. Their arms and model-training context differ from the final table. The historical final-training regime saw selection labels, so combining all selection/final rows into twelve supposedly held-out backgrounds would be invalid.

The 26-arm grid does show that larger updates can change selection-stage action outcomes, which is one concrete reason not to claim that repair is intrinsically immutable or universally useless. It does not add those unrun grid configurations to the final saved menu. Some secondary selection comparisons exceed weaker comparators such as Cmol; that does not pass the primary fixed-B1 gate.

## 4. Actual opposing exchange and one reporting distinction

I asked recursive_distinct whether historical B1 selection could invalidate the current STOP and invited a stronger counterexample. The reviewer agreed that B1 was fixed before the new decode and that historical selection limits confirmation/population extrapolation rather than the same-table pointwise bound. Their independent Fraction recomputation matched the primary implementation. They identified new blended probabilities/rankings and trajectory parameters with joint loss as genuine out-of-menu possibilities, consistent with the objections above.

The reviewer also flagged a labeling distinction worth preserving: `UPPER_BOUND_RESULT.json` field `versus_hindsight_best_fixed` subtracts the **entire table's** best fixed arm, not necessarily the best fixed arm inside each menu. Consequently its R-only final value is -1/5. It must not be labeled R's within-menu switching gain. The existing independent result explicitly reports within-menu switching gain, which is zero for R on the final table. These are different legitimate summaries, not an arithmetic disagreement; the frozen gate uses named-baseline contrasts and is unaffected.

There is no unresolved disagreement on stopping this saved menu. The remaining disagreement one might reasonably have is about the value of a genuinely different future action/model/asset, for which this review supplies no new performance evidence. No such follow-up should be described as having passed the present gate.

## 5. Bounded final decision

Stop fitting a residual router or escalating to agent evolution/RSI for these original-Q saved actions. Stop the broader twenty-action saved selection route at the stated 0.09 precision@5 usefulness target as well. Retain the new result as an exposed finite-menu necessary-bound failure, with model/task/endpoint/menu and source provenance attached.

The diagnostic learnability hypothesis was **not fit or directly falsified**. It was screened out because the corresponding action menu has insufficient useful decision opportunity on the recorded tasks, even for a label-informed selector. We should not turn this into “state+function residuals contain no information,” “no agent can improve,” “no world model adds value,” or “RSI is impossible.” The full research goal remains ACTIVE / NOT_ACHIEVED. Metadata-only source discovery in the separate follow-up does not reopen this old configuration or restore blinded status to PTV.
