# Recovery of the interrupted working snapshot

The workspace reverted to an earlier snapshot during the user's “keep” message. Raw-well, matched-repeat and initial RNA results survived; the dependency matrix, seven biological-arm outputs, static-control outputs and report changes did not. This run reconstructs those missing files from the configurations and tool outputs already visible in this conversation. It is a rerun of known outcomes, not an untouched or newly preregistered evaluation.

Preserved earlier results: raw no-fit correlation 0.5835883163; split-history residual 0.3788965703. Previously executed but lost biological outputs: simple P2 3.25; hotspot, dependency, pair-target dependency and binary RNA each 3.2857142857; shuffled dependency/targets also 3.2857142857. The post hoc zero-feature static-prior control gave 3.2857142857 with identical confirmed sets for four true-information arms.

Reconstruct exactly the substantive design: 111 nonrepeat history cells, 14 target cells, same strict 4519-action menu, binary historical Synergy label, 5 tissue-wise cell folds with seed 20261005. Ridge lambdas [1000000,1000,100,10,1]; rank blend alpha [0,.25,.5,1], ties prefer fallback, lower alpha then stronger shrinkage. Seven simple baselines: same_y, same_p, both_y, mean_p, product_p, min_p, joint_p. Select by development top20% positives. Tissue order and sorted cell order fixed.

Seven biological arms: hotspot542, hotspot-cell-shuffle, dependency61, dependency-cell-shuffle, pair-target dependency6, target-gene-shuffle, RNA14 binary objective. Dependency6 is Amean,Amin,Bmean,Bmin,Amean*Bmean,Amin*Bmin. Compound regimens use union of component targets. All-zero-data cells retain baseline ranking; train-only imputation/scaling. State shuffles only within available rows of each train/validation/target tissue partition. Target gene mapping uses seed+20. All original target outcomes remain excluded from fitting/selection; the research as a whole is exposed and exploratory.

Zero-feature control is explicitly post hoc, with alpha chosen in the same history folds; it blends the selected simple score and same_p. No new biological hypothesis or extra hyperparameter search is introduced in recovery.

Fixed P2: M=ceil(.2N), screen=floor(.7M), verify only R1 positives up to remaining budget; confirm iff R1 and R2 positive. Save every candidate score and selected set. Report 14-cell stratified paired bootstrap; fixed-selection cell×pair sensitivity and seven-arm simultaneous bands. These are conditional diagnostics, not external validation or general 5% exclusion.

Do not change any surviving freeze. Compare recovered point estimates and confirmed sets with the recorded earlier run. Preserve a recovery receipt instead of fabricating the missing original freeze files or timestamps. Do not open Vis or change production code.
