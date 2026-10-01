# Independent raw-data state-identifiability review

This is a source audit performed in D:/MAESTRO on 2026-10-01. No model,
checkpoint tensor, new utility experiment, fitting routine or API was run.
No production or existing frozen file was changed. The reviewer does not repair.

The hard gate fails for all 12 inspected task families. This conclusion concerns
real decision-time state gain. The L1000 historical policy comparison separately
requires utility intervals because of unresolved source joins. It does not
satisfy the state-gain gate by having an interval-valued historical result.

The reviewed evidence comprises 42 source receipts, complete raw metadata
schemas, and 8,036 raw record/slot/design locators. Whole-file hashes were freshly
verified for SciPlex3, SciPlex2, SciPlex4 and registered Tahoe c39; response matrix
values were not used as pre-action state. Source locators retain original obs
indices and ZIP member/row indices. Matrix slots and design rows are explicitly
marked and never treated as completed, successful experiments.

| Candidate | Raw state and action evidence | Blocking fields |
| --- | --- | --- |
| SciPlex3 B | obs compound/dose/cell/time/plate/well/replicate; time=24h endpoint | pre-action measured/available/decision times, sample relation, complete attempts |
| L1000 I LT | sig_id/distil_id to inst_id/rna_plate/rna_well; exposure duration | basal sample/time relation, all attempts; four well and five plate differences unresolved |
| L1000 II | inst_id/det_plate/det_well and exposed Level5 history | same chronology/attempt gap; not untouched external data |
| LINCS2020 | metadata signature/plate/well/QC field names; instance file absent | instance-stage denominator and pre-action matched state |
| SciPlex2 | 24,262 cells, 192 sample-sheet wells; actual raw well groups retained | time and dose unit, biological batch, pre-action state relation |
| SciPlex4 | 98,437 cells, plate_id/well_id, two intervention dose tokens | pre-action timing/lineage, raw attempt completeness, independent cultures |
| Tahoe c39 | 30,394 registered NCI-H596 endpoint cells, plate/sample fields | control endpoint is not predecision state; checkpoint-specific training manifest |
| Nyman RPPA/live phenotype | RPPA post-exposure minutes; live phenotype includes t=0 | t0 relative to drug, availability, well memberships of mean/std, sample/batch linkage |
| Hill RPPA | 0min records and raw UACC812 RPPA batch files | inhibitor preincubation, destructive sample matching, availability and balanced independent batches |
| DepMap/PRISM | basal expression and viability share cell-line identity | same experimental culture/passage/lot and chronology; collapsed attempts |
| GxE GSM7056149 | plate/well hashes, sgRNA identities; 72h endpoint protocol | missing exact treatment hash metadata; pre-action measured state and sample pairing |
| JUMP Target1 | Batch/plate/time-delay/anomaly design metadata | raw per-well trajectories, time-specific map, availability and same-culture lineage |

## Non-obvious findings

- Hill complete sixth metadata column is manuscript inclusion; core sixth is QC
  exclusion. They have opposite meanings. Complete 0min counts are 93 BT20,
  110 BT549, 109 MCF7 and 111 UACC812. Those records already have inhibitor
  labels. They cannot be labeled untreated/pre-action merely because Timepoint=0.
  UACC812 batch 1 and 2 have different inhibitor menus, so those two batches do
  not supply a balanced independent replication of all candidate actions.
- Nyman main.m defines RPPA realtime in minutes as 10,27,74,180,540,1440,2880,4020.
  4020 is 67h; a nearby comment calls the last time 72h. That discrepancy is
  preserved. Incucyte has t=0,3,...,72 and rep1/2/3 mean/std arrays of 25x60.
  This early live phenotype candidate is acknowledged, not discarded by calling
  every local timepoint post-treatment. Timing relative to drug addition and
  actual imaging availability remain unidentified; per-well identities are lost
  from the aggregate structure. Shared DMSO controls and late-time normalization
  cannot be reused as supposedly available pre-action state.
- SciPlex2/4 source partitions include 529/40 unknown-identity cells in separate
  raw groups. Sheet rows are design, not completed-action evidence. Six hash
  rows per SciPlex2 condition do not prove six biological replicates.
- LINCS2020 2026-09-27 provenance is historical. Its global metadata-only wording
  is superseded by the 2026-09-29 Level5 acquisition/evaluation manifest. This
  audit additionally viewed all siginfo column names and its first row including
  that row's QC metadata, and records that exposure. It read no further QC
  values and no Level5 response vector. The original never_read declaration and
  all old files remain unchanged.

The reviewed registry supports currently registered exposed Tahoe conditions;
it is not evidence of unseen compound, time, dose or SciPlex support. Backend
condition-level training/outcome exposure remains unavailable as a complete
checkpoint-specific manifest. WorldV2 historical training/replay exposure and
missing serialized transitions remain separate from STATE and ReferenceWorld.

## Artifacts and checks

- raw_source_review.json: 42 path/hash/schema receipts, 12 task assessments,
  timing/QC/cost/endpoint/exposure/physical-unit gaps and hard gate.
- raw_action_rows.jsonl: 8,036 raw locators; each is tagged as observed deposited
  cells/sample, source design only, or matrix slot only. No new result utility.
- action_mapping_specs.json: delimiters, members, original row-index semantics,
  grouping columns and warnings for tools/datasets construction.
- nyman_live_candidate_addendum.json: the t0 imaging candidate and source hashes.
- review_validation.json: raw-cell partition/hash checks, estimand separation,
  intentional temporal nulls and artifact/environment receipt. All seven pass.

Next data acquisition should request measured_at, available_at, decision_at,
well/sample/culture relationships, attempted/failed/not-executed status and
reason, measured costs and independent culture batch for at least one same-menu
problem. For Nyman/Hill the protocol and original imaging/RPPA sample sheets
are a smaller first request than downloading more endpoint matrices. A valid
state-blind arm requires the same matched samples and common rule permissions.
No prediction, action-choice or terminal-utility state improvement is estimated.
