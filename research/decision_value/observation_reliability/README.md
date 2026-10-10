# Observation reliability before active acquisition

This P0.5 study preserves frozen STATE predictions and every V3 source/result.
It authenticates the original data coordinates needed by the existing 39-gene
projection, then audits conditional sampling variation in the preselected DMSO
controls. It does not train a new feedback model or release P2 acquisition.

`CONTROL_PLAN.json` preserves the earlier row selections and corrects the
all-32 variance interpretation: group sizes are 32, 32, 30, 28, 32, 32, 32, 32.
The denominator is each group's actual observed size. The historical endpoint
is the equal-positive-weight average of 39 expression changes, not a program
with gene-specific positive and negative apoptosis weights. The exact source
definition is in `ENDPOINT.json`.

The first frozen control-only axis audit is complete and independently
reconstructable: 448 DMSO cells from two sources, disjoint from the 250 noise
cells, received within a 20 MB authentication cap. Unique matching passes for
27/39 coordinates in c40 and 34/39 in c44. Sparse/all-zero control trajectories
leave several identities unidentifiable. The all-39 certificate therefore fails;
the planned 2 MB noise payload remains unread, and no real 39-gene noise estimate
is reported. Failure to identify an unexpressed coordinate does not establish
that the historical coordinate definition was wrong or that feedback is useless.
Offline verification reconstructs all 78 coordinate checks from the retained
HTTP bytes. A separate metadata probe finds no ordered HVG reference in the
selected HDF5 files. Stored X contains normalized expression; "raw X" in the
matching equation denotes that stored source matrix, not raw UMI counts.

`axis/` first searches the old identity asset; if it cannot be recovered, it
freezes an exact-byte, control-only raw-X to X_hvg identity audit. Its controls
are disjoint from the 250 later noise cells. Only uniquely matched endpoint
coordinates may be named; other coordinates stay null. Dataset coordinate
identity does not authenticate the separate STATE checkpoint output axis.

The runner refuses network access unless the source revision, endpoint
definition and authenticated mapping are hash-bound. After an axis pass, freeze
the noise study before downloading its 2 MB payload:

```powershell
python -m research.decision_value.observation_reliability.run freeze
python -m research.decision_value.observation_reliability.run run --out outputs/decision_value/observation_reliability
python research/decision_value/observation_reliability/verify.py --out outputs/decision_value/observation_reliability
python -m pytest research/decision_value/observation_reliability/test_reliability.py
```

Producers refuse to overwrite outputs. The first two commands require a valid
axis certificate and all frozen input assets. The audit compares full scalar
variance with diagonal-only weighted-gene variance, divides both by actual n_g,
and bootstraps complete cell vectors within each group. These intervals assume
conditional exchangeability of sampled cells. They are not independent culture
intervals or evidence that DMSO explains A/B disagreement. The old mean variance
over 2,000 genes is reported separately because its endpoint and scale differ.
Do not add this sampling variance again to observed residual moments.

`shadow.py` routes typed evidence gaps to axis authentication, controls, matched
treated repeats, a paired information trial, or a direct-B/stop proposal. Every
recommendation has zero purchases and unknown predicted benefit. A source
receipt is required, and private evaluator outcomes are forbidden. This is a
deterministic baseline and a control contract for a future scientific agent;
it is not an experiment demonstrating an LLM advantage.

`literature/` verifies primary sources and specifies the P0.6 paired-repeat
design. Publication status, model assumptions and author-reported effects stay
separate from MAESTRO's own results. No RNA endpoint is interpreted as viability,
apoptosis, causal mechanism or net monetary decision value.

The new source qualification authenticates the original Tahoe global 24-hour
protocol and authors' plate6/14 biological-repeat description, with exact
sample/plate/condition joins. These are fresh provenance findings; they do not
rewrite the earlier unknown-duration receipt. Eight planned control strata
correspond to four pooled samples, and two cell-line partitions do not double
experimental replication. Per-sample timing, new culture independence and a
third confirmation source remain separate requirements.

The primary paper excludes NCI-H661 from subsequent analyses because of low
counts. This does not invalidate every NCI-H661 cell, but motivates a prospective
P0.6 source-quality guard. `literature/UPDATED_SENTINELS.json` selects SW 1088
and SW 1271 instead, requires 50 full-QC cells per available stratum, and proposes
six paired treatments with 32 cells sampled per stratum: 6.144 MB future RNA.
No treated RNA has been opened. This is a design, not a frozen executed study
or decision-gain result. The first metadata proposal remains preserved.

Software checks: 20 focused counterexamples and the 653-test default suite
pass. The shadow router returns `authenticate_axis` on the current failed
certificate, with zero purchases. The variance module is verified synthetically;
the real 250-cell variance experiment has not been released.
