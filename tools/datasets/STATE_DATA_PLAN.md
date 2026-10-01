# Acquisition and collection plan after the failed state gate

This is an executable data plan, **not a frozen efficacy experiment**. No test
result is inspected, no model is trained and no state benefit is estimated.
The next step is resolving operational state availability, sample relationships,
actual action coverage and physical independence before designing a comparison.

## Public acquisition priorities

| Candidate and audited original fields | Obtain next | Qualification remains conditional |
| --- | --- | --- |
| [GSE279162](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE279162): untreated WM989, six treated samples and clone links | Original state processing completion/availability and allocation-event times; founder-pool/culture/aliquot map; complete attempts, failures, controls, costs and independently repeated treatment menus; resolve doxorubicin schedule differences | The [author study](https://pmc.ncbi.nlm.nih.gov/articles/PMC13261651/) documents collection before treatment and sister-clone association, not processed state available to a decision agent. Three naive sequencing lanes are not three independent founder populations. |
| [LARRY cytokine data](https://github.com/AllonKleinLab/paper-data/blob/b8658b78c1c288019dfa60b6f50aace270528a29/Lineage_tracing_on_transcriptional_landscapes_links_state_to_fate_during_differentiation/README.md): `Library`, `Cell barcode`, `Time point`, `Cytokine condition`, clone membership | Sequencing/processing availability timestamps, cytokine allocation events, culture/aliquot/randomization and biological batch maps; explain SCF day6 absence and provide complete failure ledger | Destructive day2 profiling and sister-clone membership do not establish the same live cell followed longitudinally. The inspected matrix is clones by cells; explicit axis/row mapping is mandatory. |
| Thunor HTS001, registry and CSV pinned in [source plan](state_public_sources_20261001.json): `upid`, `well`, `time`, `cell.count`, drug/dose | Original pre-dose images/counts, drug-addition and processing events; plate/well/frame map; same-context independent physical batches and complete exclusions | All inspected counts are after treatment. Earliest frame is not a certified pre-treatment state. Each cell line currently has one plate. |
| Local Nyman live data: `time`, replicate `mean/std`, growth/apoptosis `25x60` arrays | Original same-well frame table, time units, dose-event order, well membership under each aggregate and availability logs; reconcile 67 h protein/72 h live endpoints | A real `t=0` exists, but its relation to drug addition and aggregate well membership is unverified. RPPA time points are treatment-relative and destructive. |
| Current STATE | Exact checkpoint training TOML and per-condition/outcome exposure/split manifest; certified feature axis and lawful measured control-population input route | A different local TOML cannot prove the loaded checkpoint's split. New public upload date cannot prove checkpoint nonexposure. No unsupported compound, dose, time or cell context is inferred. |

Run the pinned metadata tool first. Preserve its raw bytes and license/version
receipts; do not download large expression matrices until the missing event and
sample maps can be obtained through the source's normal access route. No author
or provider is contacted automatically. GEO access, article license, code
license and matrix license are separate fields; unknown rights stay unknown.

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -m tools.datasets.state_public_review --out outputs/state_identifiability_20261001/public_metadata_next
```

## Required laboratory export

Export four joined CSV tables and a protocol document. Keep native immutable
record IDs and raw-file SHA256 alongside every derived row. Missing values stay
missing, with a reason; a failed attempt is not an undetected biological response.

| Table | Required fields and evidence |
| --- | --- |
| `state_observations.csv` | question/state/parent/sample IDs; donor or cell line; independently initiated culture batch, passage and lot; modality and feature-axis hash; measured-at, processing-completed/available-at and decision-at with timezone; raw file/hash and source row; state QC and acquisition cost; previous treatments, if any |
| `action_attempts.csv` | question/action/attempt IDs; full legal menu; compound, dose/unit, exposure and endpoint; allocation/decision/start/finish times; actually attempted, skipped/cancelled reason; child/parent sample and randomization record; plate, well, batch; control IDs and shared-control group; all assay failures/QC and source record; measured costs, duration and budget usage |
| `response_observations.csv` | response/attempt/parent IDs; raw sample and file/hash; measured/recorded-at and result-available-at; declared endpoint/unit and observed value; QC version/status/reason; matched control and contrast rule; destructive or live measurement and audited sample relation |
| `checkpoint_exposure.csv` | backend, served/checkpoint version, immutable weights hash and feature-axis hash; actual training/calibration/test source versions and condition/outcome IDs; known/unknown prior local and provider exposure; records supporting those declarations |

For destructive RNA profiling, explicitly sample an aliquot from a known parent
population and randomize the remaining matched sister aliquots to each action.
Do not call those cells the same measured cell. Record culture drift and the lag
between state sampling, processing availability and assignment. A state that
becomes available after assignment fails the operational gate even when it was
physically sampled earlier. For live imaging, preserve same-well pre-dose frames
and addition events directly. An imaging state cannot enter STATE without a
certified existing modality/feature contract; no new learned bridge is proposed.

Use multiple independently initiated cultures or donor batches with the same
candidate menu and within-batch controls. Wells and sequencing lanes are technical
replicates. Do not reuse one physical control sample across nominal batches.
A small collection pilot can expose variance and missingness; choose confirmation
sample size from development-only variance and a prespecified meaningful effect.
No current effect estimate supports a numerical power claim or a required total.

## Only after the gate passes

Freeze one auditable question, all observed action mappings, sample/control graph,
data/checkpoint versions and exposure records before scoring held-out outcomes.
Assign entire independent physical components to development/calibration/test;
chemical scaffold/component generalization is a separate analysis. No test batch
selects thresholds, model, endpoint, planner, preprocessing or abstention policy.
The confirmation phase must use the same lawful candidates, endpoint, QC rules,
measurement budget, costs and refusal permissions in every arm.

Use a simple state-blind forecast and the current callable world backend, plus
the same backend receiving lawful predecision state. Keep identical feature and
condition contracts; removing a required STATE query row is unsupported, not a
valid state-blind intervention. Fix the selection rule for the state comparison;
then compare fixed versus forecast-based selection with the same forecasts.
Use frozen development-only state-shuffle and state-removal controls within the
same context and timing strata. Keep input/output hashes and field visibility at
predictor, selector, repair and evidence boundaries. New biological response
records remain hidden until the selected measurement is revealed.

To estimate the information contribution, acquire state in both matched arms,
charge its acquisition/processing cost in both and mask only its visibility in
the state-blind arm. Separately report a deployment-cost comparison against a
baseline that does not buy state. Do not describe free retrospective state as
net deployment value. Refusal thresholds stay identical; report coverage, risk
on decided/common-decided episodes and costs, without selecting a test-fold
threshold to manufacture coverage parity.

Predeclare reading MAE/RMSE or NLL/Brier where their outcome contract applies,
calibration/interval coverage, forecast availability and refusal; action-rank,
first/subsequent-action change rates; paired terminal utility, correct/wrong/
undetermined/deferred, measurements, days and actual costs; and state-by-policy
interaction. A curated mechanism label is not direct biological truth. Define
terminal utility from an actual prespecified assay/decision endpoint and failure
costs before outcomes; record its range and every arm's attainable missing-action
lower/upper utility, without model imputation. Separate prediction improvement,
selection improvement and endpoint improvement explicitly.

Estimate uncertainty over genuinely independent physical components. Chemical
units answer a different generalization question and cannot replace physical
replication. One connected physical component yields **unable to determine**,
with no physical bootstrap confidence interval. Missing outcomes yield only
prespecified utility bounds. An interval crossing zero does not support benefit.
Improved forecasts with unchanged actions locate an interface bottleneck;
changed actions without improved outcomes locate menu/validator or endpoint
limits; permutation-equivalent selection does not establish content value.

Keep STATE, WorldV2, case-memory and diagnostic oracle outputs separate. Use
WorldV2 only after a verified restorable existing artifact is recovered; its
absence does not authorize fitting a new model or substituting ReferenceWorld.
No backend is promoted on the basis of this data plan.
