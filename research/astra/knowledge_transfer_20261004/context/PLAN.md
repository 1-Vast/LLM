# Follow-up: cheap biological context

This is an adaptive follow-up after the complete stage-1 outcome analysis. Stage 1
found no worthwhile benefit from static target/network transfer. Nothing in this
follow-up is confirmatory, and stage-1 choices/results remain immutable.

New information: public GDSC basal-RNA footprints from saezlab/GDSC_footprints,
commit 0dd01090977b9171d54dee284007a320e1ca6b38. All 125 benchmark lines map by SIDM.
The 14 PROGENy and 771 CollecTRI/ULM scores are derived expression signatures, not
direct enzyme activity measurements or within-cell-line dynamic-state observations.
The upstream script derives them from untreated 2022-06-24 RNA and contains no
combination-response fitting. Its numeric output is reused, not independently
recomputed from the original RNA. Knowledge available at the current date is used.

Question: does a cheap cell-context representation improve candidate-relative
action value in unseen lines of the known drug library, under unchanged P2 costs?

Use the stage-1 HD-selected simple rank in each history regime as the comparator:
all=C_mean, n4=S_both, n8=C_prod. Keep verification ordering identical to that rank.
For each target, standardise the 14 or 771 context coordinates using its allowed
history lines only. Drop near-zero-variance coordinates. TF scores additionally use
the first min(5, history_lines-1) PCA directions fitted solely on that history.
Use Gaussian similarity exp(-squared_distance / median_positive_history_pair_distance).
No nearest-neighbour count or bandwidth search. Apply these weights to each pair's
historical orientation means/call rates. Shrink with k0=2 to the same unweighted
pooled mean as the original rank, using Kish effective sample size of weights.

Arms: pathway; TF; shuffled pathway; shuffled TF. Shuffle line-to-feature mapping
within tissue AND within HD/E partition, using fixed seed20261004. All four choose
blend with the frozen simple comparator from {0,0.5,1}, using HD leave-one-line-out
campaign yield only, ties to smaller blend. Alpha0 is an exact fallback. No model,
feature, bandwidth, rank or hyperparameter revisions after seeing follow-up E.

History regimes and seeds remain all / 4 / 8 lines and 11/23/47. Average orientations
and seeds within biological line. Main metric confirmed yield; report screen and
verification measurements and line bootstrap10000; line-by-pair sensitivity5000.
Inference is conditional on fitted histories and upstream features; it does not
include development selection or upstream feature uncertainty. All candidates stay.

This can test transport of baseline context and changed action ranking, not causal
mechanism identification, within-line feedback or new-drug generalisation. A positive
result must exceed the simple and shuffled controls before a larger model is justified.

Budget: public file downloads and local CPU only. No paid model calls, new experiments,
Vis outcomes, or modification of any existing frozen file.
