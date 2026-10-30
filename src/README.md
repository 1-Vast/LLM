# Runtime source


Keep maintained application and library implementations here. Develop experimental implementations and research tests in [research](../research/README.md).

Promote research code only after validation relevant to its intended use. Record the validated scope, evidence, limitations and promotion decision in [log](../log/README.md); passing repository structure or storage checks alone is insufficient. Store datasets and model artifacts in [data](../data/README.md).

See the [storage policy](../log/STORAGE_POLICY.md). The October 23 consolidation promoted no experimental implementation.

## Current scope and evidence boundary

`src/` is the maintained runtime surface. The `agent`, `maestro`, and `virtual_cell` packages are retained as current interfaces and are covered by the default software tests. Their existence and test coverage do not establish a scientific result. Experimental study code remains under `research/` until an explicit promotion record names its evidence, scope, limitations, and consumers.

Current package roles:

- `maestro`: campaign contracts, evidence/decision review, acquisition, and replay infrastructure.
- `agent`: planning, memory, procedure selection, tool runtime, and orchestration.
- `virtual_cell`: state, panel, calibration, response, transfer, and combination abstractions.

No package is marked as a validated drug-discovery mechanism. Do not delete a module solely because a corresponding study stopped; historical replay and import consumers must be checked first.
