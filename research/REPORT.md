# MAESTRO Research Report

As of 2026-10-12, MAESTRO maintains a scientific agent and a virtual-cell world model with typed evidence, prediction identity, applicability checks and refusal boundaries. The operational loop is covered by software contracts; those checks do not establish biological validity or scientific decision gain.

## Current conclusions

| Status | Conclusion | Evidence |
|---|---|---|
| `SUPPORTED` | For selective-killer discovery among compounds without an annotated selective mechanism, virtual-cell transfer contributed 17 unexpected hits (95% interval 11 to 23, p=0.00098) across 38 campaigns. This is annotation-relative discovery evidence on one assay and platform. | [Block P](astra/selective_discovery_20261011/README.md); [evidence register](EVIDENCE.md) |
| `SUPPORTED` | Transcriptional transfer predicts selective killing profiles for unseen mechanism classes and adds to a partial screen. Scope is limited to the evaluated PRISM task. | [Block N](astra/mechanism_routing_20261011/README.md); [evidence register](EVIDENCE.md) |
| `ENGINEERING_ONLY` | Typed prediction identity, applicability/refusal, decision authorization, budget accounting, receipts and restart contracts are implemented and tested. | [Core tests](../tests/); [promoted APIs](../src/) |
| `NOT_SUPPORTED` | The agent loop has not shown useful yield beyond a conventional agent-with-tool loop. Feedback adaptation has not beaten the strongest batch design; LLM forecaster, critic, explainer and trust-judge roles add no demonstrated benefit. | [Blocks N and P](EVIDENCE.md) |
| `NOT_SUPPORTED` | STATE does not improve the evaluated Tahoe relative-survival selectivity endpoint over the basal-context prior; the registered gate correctly refuses this use. | [Phenotype-anchored study](astra/phenotype_anchor_20261010/README.md) |
| `EXPLORATORY` | Archived P0 diagnosis improves global prediction error, but not selection utility. It does not release a new feedback policy or Agent study. | [P0 diagnosis](discrepancy_p0_20261012/README.md) |
| `BLOCKED` | Fresh source-repeat qualification, a distinct qualified evidence channel, full data/checkpoint axes, and a newly frozen P0.6 protocol remain prerequisites for further reliability experiments. | [P0 studies](EVIDENCE.md); [blocked assets](../BLOCKED_ASSETS.md) |

## Retained and promoted

The only promoted scientific model capability is scoped `virtual_cell.transcriptional_transfer`. Promoted engineering contracts include condition and source binding, typed authorization, refusal on unsupported scope, bounded execution and receipt-backed audit. Experimental policies and fitted models remain in `research/`.

## Structure change

This refactor created the sole repository inventory at [REFACTOR_INVENTORY.json](REFACTOR_INVENTORY.json), consolidated this file as the cross-study conclusion entry point and kept frozen protocols, study results and dated receipts.

| Decision | Result |
|---|---|
| `KEEP` | Core packages, tools, tests, study evidence, frozen assets and canonical receipts remain in their existing ownership areas. |
| `PROMOTE` | 0 new research capabilities promoted; existing scoped transcriptional transfer remains tested in `src/virtual_cell/`. |
| `MERGE` | README and this report now route to concise project/current conclusions; detailed numerical findings remain in EVIDENCE. The duplicate legacy inventory was replaced. |
| `DELETE` | Removed `Innovation.md`, the unreferenced `targeted_review_20261011.md`, and `RESEARCH_INVENTORY.json`. |
| `BLOCKED` | Data, outputs, temporary research ledgers and tracked presentation files have unresolved experiment/receipt dependencies. Cache/build removal was rejected by the local execution policy. |

The inventory records 18 root directories before and after, and a research-file scope change from 13,405 files / 580,183,721 bytes to 13,404 / 580,160,029 bytes. Its current worktree snapshot contains 26,909 files and 135,068,132,112 bytes; `src/` has 201 files, `tools/` 164, `research/` 13,404 in the non-cache inventory scope, and `tests/` 592. It identifies 706 byte-identical groups and 100 duplicate-function candidates; neither implies semantic redundancy. Of 100 research Markdown links, five point to files absent from retained third-party source copies and remain `BLOCKED`. No experiment was rerun or scientific claim promoted in this refactor.

## Verification and next gate

`compileall` and all 785 default tests pass; the core shape/integration subset passes. `python -m agent --help` passes. Research preflight is `BLOCKED/ASSET_MISSING` for `data/virtual_cell/tahoe_c39_x_hvg_feature_names.json`. Import took 0.707 seconds and the default suite took 69.84 seconds on this checkout; no comparable pre-refactor timing was measured. Before/after counts and unresolved links are in `REFACTOR_INVENTORY.json`. The next minimum gate is to qualify primary repeat endpoints and the full decision menu, then freeze a P0.6 protocol with independent units, controls, exclusions and acquisition costs before execution.

Detailed numerical results and reproduction paths are in [EVIDENCE.md](EVIDENCE.md); study procedures, limitations and receipts are linked from [INDEX.md](INDEX.md). Scientific conclusions remain separate from software behavior, numerical replay, prediction performance, decision gain and causal claims.
