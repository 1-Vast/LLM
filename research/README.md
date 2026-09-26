# Research record

Designs, protocols and analysis for MAESTRO, synchronized as work proceeds. The claim and its
formal decision layer are in [`../Innovation.md`](../Innovation.md); the runnable surface is in
[`../README.md`](../README.md); the task gates are in [`../task.md`](../task.md).

## Contents

| File | Subject | Status |
|---|---|---|
| [`agent_architecture.md`](agent_architecture.md) | Knowledge base, memory registers and star topology, context compression, sub-agents, collaboration protocol, deep reasoning, judgment accuracy | Design; implemented parts marked |
| [`decision_layer.md`](decision_layer.md) | Belief state, action space, value of information, error accumulation, acceptance tests | Design; implemented parts marked |
| [`judgment_stability.md`](judgment_stability.md) | Reproducibility as an admission test: the Brier decomposition, the averaging law, and the gate that needs no outcome | Implemented and measured |
| [`dynamic_networks.md`](dynamic_networks.md) | Conditional regulatory structure, complementarity, structural redundancy, multimodal and multiscale use | Partial; conditioned retrieval and planning diagnostics implemented |
| [`framework_optimization.md`](framework_optimization.md) | Conditioned biological assertions, agent/Jev evidence context, modality contributions, costs and live verification | Implemented; biological utility remains unvalidated |
| [`agent_research_20260925.md`](agent_research_20260925.md) | Report verification, primary agent literature, task-state loss reproduction, bounded repair and paired API probe | Targeted research complete; context repair implemented and tested; scientific utility unvalidated |
| [`typed_decision_model.md`](typed_decision_model.md) | TypeSafe Jev integration, its boundary, and the live-verified HTTP contract | Implemented and verified |
| [`engineering_record.md`](engineering_record.md) | Literature-grounded optimization pass and the topological analysis of the action and package graphs, with measurements | Implemented and measured |
| [`asrg/`](asrg/00_index.md) | Action-Supported Repair Geometry: audit, data and cost matrix, frozen protocol, decision memo | Research design; go/no-go gates open |
| [`analysis/`](analysis/) | Executable checks: residual non-identifiability, gain identity, reachability bound, synthetic selection | Runs offline |
| [`local_verification/`](local_verification/README.md) | Protocol, fixtures and scripts for the checks that need a machine with credentials and local assets | Protocol; offline half runs anywhere |
| [`biological_depth/`](biological_depth/README.md) | Pre-registered test of whether the virtual cell and the agent carry perturbation-specific biology: literature anchors, systematic-shift-centered metrics, JEPA-style latent world models, an agent probe, and the SciPlex3 label-offset finding | Measured 2026-09-26; see its README |
| [`dynamic_world_model/`](dynamic_world_model/README.md) | Pre-registered test of whether scenario cards, a time-aware policy, a learned population transition model or language-model planners choose measurements that separate mechanisms better than the current magnitude tie-break; SciPlex3 24 h and 72 h, validator, case study and closed-loop replay | Measured 2026-09-26; negative for promotion, see its README |
| [`acquisition_link/`](acquisition_link/README.md) | Audit of the link from world-model prediction to measurement choice (priorities dropped on the power-aware path, per-hypothesis forecasts reduced to one number, borrowed exposure times, deleted low-support actions), the distribution-aware selector that repairs it, and its pre-registered evaluation on the block-2 episodes | Implemented (opt-in) and measured 2026-09-26; INCONCLUSIVE, not promoted |

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
