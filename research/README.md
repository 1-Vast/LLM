# Research record

Designs, protocols and analysis for MAESTRO, synchronized as work proceeds. The claim and its
formal decision layer are in [`../Innovation.md`](../Innovation.md); the runnable surface is in
[`../README.md`](../README.md); the task gates are in [`../task.md`](../task.md).

## Contents

| File | Subject | Status |
|---|---|---|
| [`agent_architecture.md`](agent_architecture.md) | Knowledge base, memory registers and star topology, context compression, sub-agents, collaboration protocol, deep reasoning, judgment accuracy | Design; implemented parts marked |
| [`decision_layer.md`](decision_layer.md) | Belief state, action space, value of information, error accumulation, acceptance tests | Design; implemented parts marked |
| [`dynamic_networks.md`](dynamic_networks.md) | Conditional regulatory structure, complementarity, structural redundancy, multimodal and multiscale use | Design |
| [`typed_decision_model.md`](typed_decision_model.md) | TypeSafe Jev integration, its boundary, and the unverified parts of its contract | Implemented |
| [`engineering_record.md`](engineering_record.md) | Literature-grounded optimization pass and the topological analysis of the action and package graphs, with measurements | Implemented and measured |
| [`asrg/`](asrg/00_index.md) | Action-Supported Repair Geometry: audit, data and cost matrix, frozen protocol, decision memo | Research design; go/no-go gates open |
| [`analysis/`](analysis/) | Executable checks: residual non-identifiability, gain identity, reachability bound, synthetic selection | Runs offline |

## Evidence labels

Every claim about the repository is labelled:

- **implemented** — present in `src/` and covered by a contract test.
- **partial** — a mechanism exists but does not yet cover the stated design.
- **design** — specified here, not implemented.
- **unverified** — depends on an external asset or service this environment could not reach.

A design file that asserts a capability without one of these labels is a defect in the file.

## Working rule

Research files are updated in the same change as the code they describe. A design that has
been implemented is re-labelled, not left as a proposal; a design that measurement contradicts
is corrected in place with the contradicting measurement recorded, rather than deleted.
