# Minimal collection specification after the new source search

This directory contains **empty acquisition templates**, not observations or a
qualified task. Do not fill a missing event with a scheduled time. The associated
`collection_protocol.json` proposes a one-platform RNA pilot for the registered
STATE domain and explicitly lists the unresolved prerequisites. That pilot is
not executable against STATE until the input route and treatment protocol are
authenticated.

## Closest-source pilot that can actually be collected

For DeepCellControl, use one E. coli CcaSR-GFP strain and one mother-machine
fluorescence platform. Follow the original [author acquisition
code](https://gitlab.com/dunloplab/pycromanager/-/blob/ef7507fb6c5b896618a0aed63502eb9450015b69/scripts/Lugagne_Blassick_Dunlop_bioRxiv_2022/moma_training.py)
and its original microscopy protocol; no custom agent controls hardware here.
The code specifies 300-second acquisition cycles, phase/GFP camera exposures of
85 ms, constant green LED background and a 60-ms red DMD channel. These are
settings, not incurred costs. Keep the strain/medium, illumination intensity,
camera and feature definitions identical across arms. Use a separate inoculum,
independently started culture and chip for each batch. An initial three-batch
pilot checks the export and estimates development variance; it supplies no
confirmation power claim.

1. Assign immutable culture/chip/position/chamber/mother IDs before imaging.
   Save the original frame and chamber mask hashes and a native-ID-to-array-row
   table. Record mother loss, replacement, division and neighboring chambers.
   Every field and chamber in a chip shares its batch/control component.
2. Recover under red illumination for the protocol's recorded recovery period.
   Save each raw image, acquisition timestamp and actual illumination events.
   Extract fluorescence, area, chamber count/mean/std and sharpness from the
   current/past images only. Save processing-start, completion and the moment
   the feature packet becomes available. Save the packet itself before making
   the decision. Do not use reverse tracking or eventual track survival to
   construct the state stream.
3. For a first minimal question, use a prespecified decision cycle following
   recovery, identical in every batch. After state availability, randomize
   spatially separated, pre-enrolled chamber groups to two executed actions:
   red DMD pulse with green background, or green background without a red
   pulse. Keep reference red/green groups and blank/illumination controls in
   each chip. Preserve randomization probabilities and reference membership.
   Log both queued commands and hardware acknowledgement, actual start/end,
   exceptions, fallback/default patterns and skipped/cancelled reasons.
   A mother's two counterfactual responses are not both observed; the experimental
   question is a randomized within-batch group contrast, with predeclared
   spatial interference handling. It is not an exact per-mother policy replay.
4. Record all enrolled chambers at the next and prespecified later cycles,
   including tracking losses and assay failures. Use raw GFP fluorescence as
   the sole endpoint, with fixed camera calibration. An RNA or resistance
   phenotype is not inferred from this reporter. Store response frame IDs and
   hashes, outcome availability and QC reasons. Keep next-frame stimulation
   at index `j+1` associated with state history through `j`; acquisition code
   and hardware logs must verify this alignment.
5. Export `questions.csv`, `actions.csv`, `attempts.csv`, `state_samples.csv`
   and `response_samples.csv` with native source IDs, source rows and hashes.
   For live imaging, record the same verified live sample; for an RNA pilot,
   use the separately documented parent/sister aliquot relation. All statuses,
   missingness, technical repeats, shared controls and cost denominators remain
   explicit. Include labor, microscope runtime, acquisition/processing, media,
   chip, actuation and failed-attempt costs in a common currency with rate version.
6. Sign off the event/sample/attempt graph and checkpoint input/exposure manifest
   before assigning entire connected culture/chip/control components to folds.
   Collect confirmation batches only after freezing the endpoint/horizon,
   action probabilities/menu, QC, budgets, costs, utility, refusal, predictors,
   selector, permutation controls and statistical analysis on development data.

This specification repairs missing data provenance; it does **not** make optical
features legal STATE inputs. A fluorescence world model must be named separately
and its checkpoint authenticated. For the user-requested current STATE experiment,
the RNA pilot in `collection_protocol.json` remains the appropriate route:
NCI-H596, destructive parent aliquot for state, randomized sister treatment
aliquots, exact registered trametinib condition labels and the certified ordered
RNA axis. Measure and process the state before deciding or starting treatment;
record the delay and culture drift. Recover the registered exposure protocol
before dosing. Removing STATE's required basal population is not a blind arm;
certify a fixed development-only, context-matched basal-population replacement.

## Frozen comparison requirements after a pilot qualifies

Acquire state in both information-comparison arms and charge its costs in both;
mask only visibility. Separately compare deployment against a blind policy that
does not buy state. Freeze a simple context-only baseline, identical STATE
backend with lawful visible/blind basal inputs, identical action selector and a
development-chosen fixed action. Use all measured actions for evaluation but
reveal only chosen measurements to the decision agent.

Report prediction MAE/RMSE and calibration/coverage; action changes; correct,
wrong, undetermined and refusal counts using a development-frozen target rule;
measurement counts, elapsed time, costs, terminal utility and refusal utility.
Use within-context state permutation and log predictor/selector/evidence field
visibility. Missing actions get only preregistered biological utility limits
minus known incurred costs, never model-filled outcomes. No physical confidence
interval is reported without independently initiated physical components.

The proposed RNA endpoint is an EGR1 transcriptomic shift, a surrogate only.
Its scale, target boundary, QC thresholds, resource budget and cost normalization
must be locked using the pilot before confirmation. The empty fields in the
protocol identify required development decisions; they are not numerical values
to invent from the unqualified public sources.
