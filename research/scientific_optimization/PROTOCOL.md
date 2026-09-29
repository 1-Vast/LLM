# Signed RNA readout pilot and scientific interpretation regressions

This is an **unregistered development experiment**, specified before its new fits and scores.
The SciPlex3 prepared data and historical predictions have already been exposed. The checkout
contains a pre-existing uncommitted reorganisation. Neither a new commit nor rerunning this
experiment would turn it into unopened external confirmation.

## Questions and fixed analysis

1. Can the learned serving interface preserve opposite RNA directions that have identical RMS,
   with exact vehicle behaviour and descriptive ensemble disagreement? Software tests answer this.
2. Does a simple endpoint-directed model predict signed gene-set shifts better than the existing
   model and strong trivial baselines? A retrospective biological pilot answers this narrower question.
3. Can duplicate hypothesis identities or overlapping interpretation rules produce an arbitrary
   scientific verdict? Fail-before regression tests and the production suite check the fix.

Data: existing `outputs/biological_depth_20260926/prepared` and five `cv/fold*.npz` archives.
Endpoints: all 50 previously frozen, explicitly restricted Hallmark sets in `gene_sets.json`.
They measure **mean RNA shift**, not target activity. No endpoint selection after scoring.
Keep all 2,250 available conditions; report compounds and independent structure-identity groups.
The historical `skeleton` is an InChIKey connectivity block, **not a Murcko scaffold**. Existing
outer folds were stratified using pathway annotations. This pilot is therefore neither a new
metadata-only benchmark nor evidence of scaffold/study generalisation. Use identical outer folds
for comparability with stored predictions, and disclose the limitation.

Candidate: Morgan-2048 fingerprints crossed with cell identity and gated by log dose; ridge
regression directly to 50 signed RNA endpoints, no SVD target compression. Inner validation
uses the existing outcome-independent hash of training connectivity groups (15%). Choose one
global alpha from {1,10,100,1000}, using equal-group mean endpoint MSE. Refit on the outer
training data. No held-out response is passed to the fit function. Training weights also give
each connectivity group equal weight. This changes both the target objective and weighting;
an improvement is not attributable solely to the projection interface.

Comparators: stored out-of-fold zero, cell/dose training mean, chemistry ridge, chemistry kNN,
existing MLP, PCA and JEPA response predictions, all projected onto the same endpoints.
Primary diagnostic: paired equal-connectivity-group MSE difference against each comparator,
with 2,000 group bootstrap draws (seed 20260927). Negative differences favour the candidate.
These are descriptive development intervals, not multiplicity-corrected confirmatory tests.
Also report overall endpoint MSE and target sign agreement; zero predictions count as abstentions
for sign agreement and sign rate is descriptive because small shifts can be measurement noise.

A candidate is only eligible for *further prediction research* if its upper paired 95% interval
is below zero against zero, training mean, chemistry ridge and kNN. Otherwise retain the simpler
default. Even passing this screen never promotes action selection: calibration, assay validity,
selected-action risk and decision benefit remain separate unmet gates.

There is no new engagement label, no causal mechanism endpoint, no provider call and no assay
execution. Do not fabricate a repair × world-model interaction result. Existing premise-task
NOT_READY and selected-action calibration failures continue to constrain biological claims.

Outputs are write-once per run directory and include protocol/code/input hashes, environment,
outer predictions, validation selections, metrics and explicit limitation flags. Software test
fixtures are never included in biological metrics.
