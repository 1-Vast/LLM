# Final bounded follow-up: candidate-specific context interaction

Adaptive exploratory follow-up after seeing both earlier studies. The motivating
gap is precise: context-neighbour weights were shared by all drug pairs and no
candidate-specific context-response mapping was learned. This study learns that
mapping; it does not establish biological causality or temporal cell dynamics.

Reuse the same 125 SIDMs, all/4/8 histories, seeds, HD/E, P2 fp30 and HD-selected
simple comparator from stage1. Verification ordering remains that comparator.
No more model revision in this session after this follow-up E output.

Cell state: 14 PROGENy coordinates standardised on each permitted history only;
771 TF coordinates standardised on history, then PCA with min(5,n_history-1)
components, also fitted only on history and whitened using history variance.
Each block is divided by sqrt(number of its coordinates), then concatenate and
divide by sqrt(2). No scaling or PCA uses the target line.

Pair features: eigenfeatures of the frozen symmetric pair kernel from stage1;
keep the top min(16,n_pairs) positive eigenvalues, row-normalise feature vectors.
This fixed low rank is the same for drug-ID and signed-network representations.

Predictor: Kronecker product of pair features and cell state. Target vector has
four distinct coordinates: SV screen call, SV verification call, SV continuous
response and VS continuous response. Fit a multi-output ridge with lambda=10 to
residuals from the original pair-history means. Centre both features and residuals
within each history line to remove a global line offset and learn relative action
differences. Add predicted residuals to original means; clip only binary-call heads
to [0,1]. Swap orientation heads for VS. Compute the same simple ranking functional
(C_mean, S_both or C_prod) on predictions. No new synergy definition.

Arms: ID-by-context, network-by-context, network-by-shuffled-context. Same feature
rank, ridge, labels and blend search {0,.5,1}; choose with HD yield only, ties zero.
Shuffled context uses the stage2 within-tissue, within-HD/E permutation. A global
cell offset cannot improve the pair-relative training target; synthetic checks
verify its removal. All drug pairs retained, even when target genes are unresolved.

Report all arms and regimes, selected weights, line-stratified bootstrap10000 and
line-by-pair sensitivity5000 for network vs simple / ID / shuffled. No family-wise
or untouched-data significance claim. A gain must be attributable beyond the
controls; otherwise retain the simple rank. This is the final model trial here.
