# Research findings and evidence

Read the [integrated research report](RESEARCH_REPORT.md) for the current scientific position, quantitative findings, historical hypotheses, negative results, corrections and inherited next steps. It distinguishes exploratory studies, maintained software and formal communication outputs. The research objective remains ACTIVE / NOT_ACHIEVED.

| Question | Report chapter |
|---|---|
| Updated Agent–virtual-cell objective and latest completed CXCL9 test | [Joint-learning objective](RESEARCH_REPORT.md#agent-virtual-cell-joint-learning-to-discover-and-revise-biological-intervention-rules-2026-10-30) |
| Latest CDI retrospective pilot and intervention-gated candidate | [Joint-learning objective](RESEARCH_REPORT.md#agent-virtual-cell-joint-learning-to-discover-and-revise-biological-intervention-rules-2026-10-30) |
| Latest Agent/virtual-cell audits, ten directions and four conditional mechanisms | [2026-10-27 research](RESEARCH_REPORT.md#latest-agent-and-virtual-cell-research-2026-10-27) |
| Latest paid-repeatability result and threshold correction | [Current result](RESEARCH_REPORT.md#current-paid-repeatability-result) |
| Knowledge, ordinary feedback and decision value | [Knowledge](RESEARCH_REPORT.md#knowledge-and-decision-value), [feedback](RESEARCH_REPORT.md#functional-feedback-and-acquisition) |
| Mechanisms, inheritance and scoped stops | [Mechanisms](RESEARCH_REPORT.md#mechanisms-inheritance-and-self-repair) |
| Source identity and task qualification | [Sources](RESEARCH_REPORT.md#source-and-task-qualification) |
| Literature findings versus engineering checks | [Literature](RESEARCH_REPORT.md#literature-and-source-access) |
| Current use, restoration and remaining research | [Reproduction and next work](RESEARCH_REPORT.md#reproduction-and-next-work) |

The [study index](STUDY_INDEX.tsv) preserves per-study findings, exact numbers and amendment/source identities. It distinguishes reconciled findings from attributed source excerpts and missing final records. Later explicit amendments govern interpretation; maintenance records are not scientific findings. `research/STUDIES.json` combines the study registry, storage state and selected conclusion/evidence/decision relations without a separate database.

## Exact evidence and historical restoration

### Published key sources

The Git release includes the report, study index, maintained code and
`SOURCE_MANIFEST.json`. Key historical protocols, implementations and findings
are bound to fixed Git blobs; new or changed key texts absent from that Git
version are retained in a small exact-byte supplement. Read them with
`python -m tools.retained_records --published --show SOURCE_ID`. A clean checkout
uses this published manifest automatically when the local record store is absent.

Git blob bytes can differ from local original bytes through LF/CRLF normalization;
the manifest records both identities where applicable. This verifies the stated
source representation, not the bytes of an excluded local archive. A shallow
checkout must fetch the manifest's fixed `source_commit` using
`git fetch origin COMMIT` before reading historical Git sources.

Datasets, models, numeric payloads and large research packages are not uploaded.
Their local location/hash is a dependency record, not proof they are available in
a fresh clone. The software suite validates published key sources without those
assets. `MAESTRO_VERIFY_ARCHIVES=1` additionally checks local package integration;
once enabled, missing packages are failures. Neither test level establishes the
scientific verdict or a complete experimental replay.

### Complete local records

`data/processed/research_records/` contains exact former reports, protocols, reviews, corrections and logs. `data/processed/research_packages/` contains three verified packages of retired experimental code, detailed numerical assets and historical workbench files. Protected payloads and current dependencies stay in place. Original relative paths identify sources; they do not promise executable old interfaces.

```powershell
python -m tools.retained_records --show log/20261022/almanac_feedback_pilot/DECISION.md
python -m tools.retained_records --list packages/historical_experiments/research/acquisition_program_20261018
python -m tools.retained_records --restore packages/historical_experiments/research/acquisition_program_20261018 --destination D:/temporary-verification
```

The reader verifies retrieved content hashes. Restore selected sources into an explicit isolated destination, assemble their declared dependencies and lawful inputs, and use the required environment before historical replay. The destination follows source IDs, including a `packages/` prefix; it does not automatically recreate a runnable project. A retained verifier is not immediately runnable solely because its source exists. Recorded modes/times/content hashes are not a full NTFS ACL/ADS backup.

[Experimental implementations](../research/README.md), [data inventory](../data/README.md), and [storage policy](STORAGE_POLICY.md) describe separate responsibilities. No new scientific experiment was authorized by organization.
