# Live API results, 2026-10-01

The actual DeepSeek and Jev calls verified provider integration and exposed a
useful boundary: legal typed output can still choose the wrong next step. This
pilot does **not** demonstrate biological superiority over the registered
baselines. DeepSeek exactly matched the public-forecast one-step optimizer in the
biological episodes; the observed L1000 saving came from deferral. The independent
`ModelAuditAgent` reports formal defects without repairing or choosing actions.

This is the original frozen result. Subsequent support-contract corrections and
fresh validation are reported separately in [POST_FIX_RESULTS.md](POST_FIX_RESULTS.md).
Four one-unit reading intervals are formally removed in the archived
`uncertainty_correction/corrected_summary.json`; no original estimate, path or
API response is overwritten.

## Population and information

The frozen comparison comprises 24 constructed scenarios (six contract families
with four variants), 48 blinded clean/defective proposal cards, and 12 biological
episodes (six SciPlex3 B and six L1000 LT, spanning each existing fold). Biological
episodes have at most two purchased measurements. Fixed ordering, the one-step
forecast optimizer and the API arm use the same registered menu, budget, QC,
endpoint and executor. This optimizer is explicitly a **one-step** comparator;
the earlier frozen audit supplies the current baseline-planner comparison.

Provider cards contain public conditions, candidate hypotheses, frozen
ReferenceWorld forecasts, and already purchased observation categories. Evaluator
truth, unpurchased readings and held-out annotation joins are concealed. Forecasts
never enter terminal evidence. The hosted providers' pretraining exposure is
unknown; public compound identifiers remain visible. ReferenceWorld is the
existing case-based reading forecaster, not production STATE or WorldV2. Its
hyperparameters and validators were restored without training or refitting.
All biological artifacts were previously exposed: this is an internal pilot,
not external validation or a new chemical/context generalization result.

The raw/gated/typed-review contract comparisons reuse the same DeepSeek proposal.
Jev is report-only and therefore leaves the gated action unchanged by construction.
Neither its unchanged action nor the auditor's finding is biological evidence.

## General contract and defect tests

| Arm | Legal actions / 24 | Objective-adherent choices / 24 |
| --- | ---: | ---: |
| Fixed ordering | 24 | 20 |
| Public-forecast one-step optimizer | 24 | 24 |
| DeepSeek raw proposal | 24 | 20 |
| DeepSeek with contract gate | 24 | 20 |
| Jev report-only arm | 24 | 20 |

The four API failures all belong to the unsupported-forecast family: the model
selected a legal measurement instead of the declared objective's required defer.
The local formal auditor correctly accepted these proposals' shape/legality;
formal contract compliance does not certify forecast availability or optimality.
There were no raw illegal proposals in this action population, so gating supplied
no observed action gain. Family-resampled API success is 0.8333 with conditional
interval [0.5, 1.0]; the paired success difference versus fixed is zero. These
constructed-family intervals describe this probe, not a biological population.

The saved arithmetic forecast regret is zero for every arm. It assigns zero
value to unavailable-forecast actions and consequently misses the unsupported
family's objective violation. It must be read alongside objective adherence and
support status, and cannot certify zero real decision regret.

Known defects comprise six terminal-authority claims, six unregistered actions,
six missing required fields, and six non-object proposals, paired with 24 clean
controls. Labels were withheld from provider-visible cards.

| Reviewer | TP | FP | FN | TN | Precision | Recall | False-positive rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Read-only local auditor | 24 | 0 | 0 | 24 | 1.0000 | 1.0000 | 0 |
| DeepSeek batch review | 24 | 0 | 0 | 24 | 1.0000 | 1.0000 | 0 |
| Jev typed batch review | 23 | 1 | 1 | 23 | 0.9583 | 0.9583 | 0.0417 |

The paired-then-family bootstrap accuracy for Jev is 0.9583 [0.9167, 1.0]. Local
and DeepSeek review are perfect on these deliberately explicit inserted defects;
that result is not a guarantee of arbitrary model-bug discovery. No reviewer
fixes a model, changes a threshold or mutates the input. The initial two-call
smoke also retained a Jev semantic false positive: an empty-evidence state was
labelled measured at probability 0.51. A structured answer is no correctness
certificate.

## Biological replay and costs

Totals are across six episodes per task. Terminal utility is `+1` correct, `-2`
wrong, and `0` undetermined/deferred. Net utility subtracts `.02` **per attempted
measurement**; assay days are a separate budget.

| Task | Arm | Correct | Wrong | Undetermined | Deferred | Measurements | Days | Mean terminal U | Mean net U |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SciPlex3 B | Fixed | 5 | 0 | 1 | 0 | 8 | 48 | 0.8333 | 0.8067 |
| SciPlex3 B | One-step optimizer | 5 | 0 | 1 | 0 | 8 | 48 | 0.8333 | 0.8067 |
| SciPlex3 B | DeepSeek gated | 5 | 0 | 1 | 0 | 8 | 48 | 0.8333 | 0.8067 |
| L1000 LT | Fixed | 1 | 0 | 5 | 0 | 12 | 67.5 | 0.1667 | 0.1267 |
| L1000 LT | One-step optimizer | 1 | 0 | 0 | 5 | 2 | 12 | 0.1667 | 0.1600 |
| L1000 LT | DeepSeek gated | 1 | 0 | 0 | 5 | 2 | 12 | 0.1667 | 0.1600 |

Both tasks have six chemical units in this selected population. Each paired
terminal-utility difference versus fixed is zero. The conditional bootstrap
output [0, 0] reflects identical observed deltas, and establishes neither
equivalence nor zero uncertainty on future biological tasks. The selected menus
have no flagged reachable source gaps, so the pilot's source bounds collapse to
its registered observations; the earlier unresolved source records remain
unresolved. Physical plate/batch dependence remains one connected component per
task; no physical-cluster confidence interval can be estimated.

SciPlex3 has four changed action sequences out of six; all four retain the same
terminal outcome, and total measurements/days are unchanged. This is consistent
with a menu/validator limitation for these episodes. L1000 has six changed
sequences; one preserves the exact final string, while five change undetermined
to deferred. **All six preserve correctness and terminal utility.** The mean
measurement difference is -1.6667 [-2, -1], mean day difference -9.25
[-11.25, -5.25], and mean net-utility difference +0.0333 [0.02, 0.04]. These are
conditional chemical-unit resampling outputs; the gain is avoided spending on
five refused episodes, not improved biological correctness.

On common-decided episodes, SciPlex3 has five pairs and L1000 one pair. Both
policies have risk 0 and correct rate 1 in each intersection. SciPlex3 mean cost
is 1.2 measurements/7.2 days for both. L1000 uses two measurements for both;
the API arm takes 12 days versus fixed's 11.25. Common-decided matching here is a
descriptive intersection, not a calibrated selective-risk guarantee.

Selected-reading quality uses per-episode means followed by equal chemical-unit
means. SciPlex3 fixed NLL/Brier are 0.9569/0.4834; API and optimizer are
0.5455/0.2849. The **same ReferenceWorld** supplies both, and selected
actions/histories differ; this is selection composition, not a backend accuracy
improvement. L1000 fixed selected NLL/Brier are 0.1741/0.0996 across six units;
API/optimizer values are 0.6689/0.5103 on only **one** measured unit. Its raw
bootstrap interval is degenerate and provides no meaningful reading-quality
uncertainty interval or fair matched-population backend comparison.

## Actual serving and efficiency

The formal comparison used 40 logical calls per provider, below the declared
49-call cap: 24 action probes, one batched defect review, and 15 biological
decisions. The initial smoke adds two calls per provider. There were no observed
transport errors; existing bounded retry policies were retained. The receipts
report logical completions and end-to-end transport latency, not independent
server-request counts under hypothetical retries.

| Provider | Served identifier | Formal usage | Median latency | p95 latency |
| --- | --- | --- | ---: | ---: |
| DeepSeek | deepseek-flash | 71,569 prompt + 1,296 completion = 72,865 total tokens | 0.6166 s | 1.0678 s |
| Jev | jev-1.13.0 | 113,712 input + 8,127 output tokens | 0.9089 s | 1.0200 s |

Recorded account charges/pricing receipts are unavailable, so monetary billing
is unknown. Token usage is observed, not a bill estimate. The separate warmed
local timing receipt reports fixed 0.874 microseconds, one-step optimizer 1.955
microseconds, and optimizer-plus-auditor/hashes 19.906 microseconds per card
(three trials, 24,000 operations each). These test different workloads from a
network completion; they support routing already structured numerical decisions
through deterministic code, not a matched hardware/model throughput claim or a
STATE acceleration claim.

## Reproduction, failures and recovery

The original preregistration freezes 522 retained inherited records and 134
current executable sources. Four independently verified runtime changes are
recorded with old/current hashes. The population, prompt, threshold and outcomes
were not tuned after execution. Every raw provider receipt has request/response
hashes, served identifier, usage and latency; every biological trace retains
readings/QC, action path, terminal/cost and selected forecast quality.

The first freeze stopped before any API call when the inherited ledger mixed
executable sources with inputs. The fresh formal freeze retained every inherited
hash except the exact authorized four-file source allowlist. The actual formal
run then completed all requests/replays but strict artifact serialization rejected
a registered validator's `-inf` score. Both failed directories and failure
receipts remain preserved; original source bytes are archived.

The serialization-only recovery represents nonfinite scores as the existing
`{"nonfinite":"-inf"}` sentinel, without numerical imputation. It reconstructs
all biological rows from unchanged data and saved proposals/reviews: 15/15 cards
and gates match exactly, source/input hashes are checked before and after, and
network transports plus ReferenceWorld fitting are patched to raise. Recovery
makes **zero new API calls**. It writes a fresh directory and copies original
receipts byte-for-byte.

```powershell
& D:\anaconda\envs\maestro\python.exe -m research.dual_core_live.benchmark recover --from-run outputs/dual_core_live_20261001/fixed_benchmark_v1 --out outputs/dual_core_live_20261001/fixed_benchmark_recovered
```

The write-once command refuses an existing output directory; use a new output
path to reproduce the offline recovery. The original live `freeze`/`run` commands
and settings are saved in `API_DESIGN.md` and the original preregistration. The
recovery command is sufficient for an offline result reconstruction.

| Provenance item | SHA256 |
| --- | --- |
| Original preregistration | fd30716bfee888fc7db18bf0f89c1914a009ff2b78be0dc7105ee0f58d87a19d |
| Recovery preregistration | 151847b7704af5e08e590b6ea072d36bebf8e2e9b924da8a89ab1ce4a39a9efa |
| Original benchmark source | 3ef641713bb5152268dd05aa8c1b637b555d12468d629ad8ea7de00297de00b4 |
| Recovery benchmark source | 4c59e8b950e38905d830caceb158835d736dd6fe39215241086a26a53b7cb858 |
| Recovered summary | 5d212f64bb11104dbe2f354d4d15e31ffd7d12548532b4162d979d64f08a91a5 |
| Recovered artifact ledger | 3d7de07f13312cb56def1695844224d03480cb923b66c740f8ef994ee0bde885 |

The recorded code parent is `8271e8a119138d0e9c60fd9938f0abe11e081a79`;
source hashes identify the then-uncommitted new scripts and runtime fixes.
Python/environment/package metadata and exact commands accompany the artifacts
under `outputs/dual_core_live_20261001/`. The observed conclusion is a defensible
engineering boundary and a null biological benefit against the strong comparator.
External deployment value still requires prospectively available state,
independent batches and broader unrevealed task families. The present tests do
not justify a general-superiority claim, prompt selection on these folds,
or promotion of an oracle to an executable strategy.
