# Context discrimination: exploratory protocol, 2026-10-13

## Question and exposure

Can source-grounded reasoning improve the choice of a second cell-line measurement
after a fixed RKT hub measurement, to find recorded context-dependent transcriptional
activity? This is an exploratory development study, NOT independent confirmation.
All 702 Block Q compounds and their outcomes were previously evaluated. Before this
protocol, we inspected aggregate activity rates, prediction rows, historical campaign
results and all pairwise activity-discordance counts (289/702 compounds have both
active and inactive lines). No new-policy outcomes or LLM choices were evaluated.

## Endpoint and resources

Population: all 702 eligible compounds, including entirely inactive compounds.
Primary endpoint: fraction with two acquired observations on opposite sides of the
line-specific 95th-percentile vehicle response-norm threshold, at 10 uM / 24 h.
This is recorded transcriptional activity discordance, not viability selectivity,
mechanism discrimination or a statistical test of a biological interaction.
Sensitivity endpoint: active norm >1.2 threshold and inactive norm <0.8 threshold.
Every policy has two profile-retrieval slots per compound. These are offline replay
slots, not new laboratory wells or independent biological replicates. Fixed policies
need one simulated round, feedback policies two; actual elapsed lab time is zero.

## Policies

The first line is the strongest outgoing-transfer hub from reference-only RKT maps.
All unavailable lines are excluded using metadata. Fixed choices may use availability.

- sparse_hub: two best transfer hubs, the validated practical fixed baseline.
- fixed_pair: reference-only highest-discordance pair (task-specific strong fixed control).
- empirical: hub then line with highest reference conditional discordance given the
  observed hub label, with Beta(1,1) smoothing.
- empirical_knn: hub then reference-neighbour activity prediction (20 nearest hub
  response-norm ratios, uniform weights, Beta(1,1) smoothing); same objective.
- rkt: hub then maximize predicted opposite activity, using the frozen RKT certifier.
- C agent only: literature/annotation-grounded two-stage hypothesis/revision workflow,
  with empirical probabilities but without RKT predictions.
- D conventional LLM + VC: same information and two calls, ordinary hypothesis and
  tool-selection instructions, with RKT tools exposed as a compact evidence table.
- E integrated: same information and two calls, explicit competing explanations,
  evidence gaps, RKT failure critique and revisable research memory.

The LLM pilot is the first 84 compounds sorted by SHA256('context-pilot:' + key),
in 12 batches of seven. No activity filtering. Each LLM arm receives identical
annotations, reference probabilities, source limitations and hub feedback. C has
RKT fields removed. Two calls per batch: hypotheses before feedback, second-line
selection after feedback. Maximum 72 calls, deepseek-flash only, temperature zero,
cached requests, no more than USD 1 conservative budget accounting (below user $10).
Invalid selections fall back to empirical and are counted. No post-result repair
of scientific hypotheses. CaseStore persists selected real observations and plans.

## Analysis and gates

Deterministic feasibility on 702 compounds precedes paid calls. Stop if oracle
headroom over best fixed policy <0.05, or reliable margin-discordance ceiling <0.10.
No tuning to the 702 outcomes. Report all policies, threshold sensitivity, compound
bootstrap 95% intervals (10,000 replicates, seed 1310). LLM inference additionally
clusters by its 12 prompt batches; use exact sign-flip and 98.75% bootstrap intervals
for four planned contrasts: E-C, E-D, E-strongest deterministic, and interaction
(E-C)-(B-A), with B=rkt and A=empirical on the same pilot. Holm adjusts these four
one-sided p-values. These remain exploratory regardless of p-value.
Promote nothing from this exposed-data study. LLM benefit requires E to beat the
strongest practical deterministic/fixed arm, not merely a positive interaction.

## Scope and independence

RKT predicts directions and activity under the existing L1000 contract. Its weights
remain unchanged. New policy code stays here. Query outcomes are physically masked
from the atlas until a selected hub observation is revealed. The evaluator alone
reads second-line outcomes after actions are saved. Offline lookahead is reported
only as an unattainable ceiling. Unknown culture/plate dependence and unvalidated
activity thresholds prevent calling discordance a causal or replicable mechanism.
Independent confirmation requires a separately audited, unexposed source and frozen
protocol; existing PRISM and GSE70138 exposures do not satisfy that condition.
