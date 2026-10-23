# Official AssayLoop code static review

2026-10-22. Read root's saved SOURCE_INVENTORY.json metadata and relevant passages of src_assayloop_amortized_rl.body, without importing/executing author code, downloading data/weights, reading biological values or making networkrequests. Source pinned treee7251afacda88c803864896e0d1444196f482471, src/assayloop/amortized/rl.py blob1b77d49c936ef628ebcc07f361d5b1cd3f4531bb,size89349 as supplied by inventory. Root reports gitblob validation; I did not independently recompute that acquisition validation. Read scope: ordinary rollout reward/returnlines310–515, corresponding text rolloutlines635–690, helper_group_advantagelines70–85 and training defaults around1041–1046, plus mode references byrg. Not a full-file or checkpointconfiguration audit.

## Direct branch evidence

Lines397ff select context_delta/context_delta_reset and compute detached fixed no-context reference scores from empty context. Lines459–463 mask those scores with the actual obs_mask, choose torch.topk deterministically and subtract its hitcount from actual chosen hits. Lines468–470 update observations only with actual chosen genes. The reference proposal does not independently remove its own selected items. Therefore the original deterministicreference witness is not merely a limiting stochastic approximation: it directly represents this branch's pool/topk contract, under the small synthetic restriction and appropriate fixed rankings. This is stronger than the earlier source-only uncertainty and differs from Methods4.5's wording that reference batch is sampled.

Lines501–508 construct discounted future returns running=R_t+gamma*running and apply groupnormalization. Thus future reference rewards can depend on prior actual actions and enter earlier remainingreturns. A state-only baseline at the current step does not by itself remove those future terms. However per-step groupnormalization, stdfloor/clipping and KL/entropy modify optimization; the ranking witness does not predict actual finitegroupGRPO gradients or training outcome. Actual policy sampling is GumbelTopk; the baseline branch topk distinction must be explicit.

## Author already implements ordinary alternatives

The code's own documentationlines334–350 states telescope as default, contextdelta as static-reference contrast and adjusted as another comparisonmode. Lines474–480 overwrite telescope reward with the increment of cumulative NVR. Lines496–497 add final NVR for nvr_terminal. Text-policy path similarly implements these branches. Training defaults include gamma1, temperature1 and reward_modetelescope. These are actual existing author operations, not a missing repair invented by MAESTRO. A purported contribution consisting only of terminal objective or telescoping return is even more directly anticipated than our earlier general potential-shaping observation.

At gamma1, no warmstart, the telescope sum equals final cumulativeNVR. With a fixed supplied warmstart, the sum is finalNVR minus its initialwarmNVR, a rolloutconstant for the sharedwarmstart; do not state raw sum always equals finalNVR. For gammaotherthan1, undiscounted telescoping does not automatically prove the discounted returnobjective aligned. Default1 supports the ordinary scoped case but does not identify allconfigs or the paper's reported checkpoint. NVR normalization and rawtotalhit objectives must also be related under the actual fixedlibrary/budgetcontract, not globally conflated acrossscreens.

## Claim change and next boundary

We can now say a released pinned source branch contains the deterministicsharedremainingpool structure and separately already contains ordinary terminal/telescope alternatives. We cannot say the authors' benchmark checkpoint used a specific mode, alltrainingruns are affected, that their observed gains are invalid, or our standardrepair empirically wins. The paper's terminalEF ablation performs worse by authorreport and must remain. Neither sourcecode nor mathematicalalignment settles finitelearningefficiency.

No candidatecore is promoted. Next action should be an accurate sourcecontract record, not another biologicalpilot, newrewardmenu, downloadedcheckpoint or novelshapingclaim. Only a genuinely different costed estimative/credit mechanism with independentreview could justify newmethodwork; none is supplied here. Existing ALMANAC/CCI STOPs and protectedreserves remain.

## Actual peer challenge

I sent frontier the static branch findings and challenged overbroad telescopealignment: warmstartoffset,gamma and normalizedadvantages constrain the conclusion. The ensuing response is recorded in a separate post-reviewexchangeaddendum if received after this reviewseal, keeping chronology visible. This review itself does not claim a peerreply already received.
