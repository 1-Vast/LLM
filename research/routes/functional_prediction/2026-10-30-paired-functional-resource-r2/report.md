# Paired-resource and literature-transfer audit (2026-10-30)

## Decision

The R2 candidate is not currently testable with an eligible matched proxy/function dataset. The available 684-row transcriptome--PRISM bridge fails the condition and provenance contract. Keep the bridge for exploratory association or an ordinary predictive baseline only. Current status is `DATA_UNAVAILABLE / NO_EXPERIMENT / NO_PROMOTION`.

## Transferable operations

1. Use a cheap molecular proxy to prioritize candidates, but keep the functional endpoint separate and measure it on a matched experimental unit.
2. Record each model or agent revision against the observed functional feedback and preserve the prior rule for comparison.
3. Let an agent propose direct measurement, local model update, or abstention only after comparing against ordinary uncertainty sampling and cost-aware value-of-information baselines.

The literature review shows that proxy-plus-phenotype feedback, model revision, and uncertainty-driven experiment selection each have prior art. The narrow remaining candidate is a predeclared decision rule that chooses between direct functional measurement and local virtual-cell update, then improves functional outcomes or reduces assay burden under equal budget on untouched compounds and backgrounds. This is a hypothesis, not an established novelty or result.

## Bridge contract

| Requirement | Result |
|---|---|
| Drug and cell identity | Partial: 296 compounds and A549/MCF7/PC3 are connected across sources, not shown to be the same experimental unit. |
| Dose | Fail: transcriptomic side encodes 10,000 nM; PRISM AUC summarizes multi-dose curves. |
| Exposure time | Fail: transcriptomic side encodes 24 h; matched PRISM time is absent. |
| Vehicle/control | Fail: the bridge drops a matched control key. |
| Preparation/plate | Fail: PRISM raw plate/well fields are not carried through and transcript preparation cannot be traced. |
| Independent replicate | Fail: MTS010 is a technical redo and bridge rows lack biological replicate IDs. |
| Independent function | Fail: pooled viability is not an orthogonal endpoint such as recovery, clonogenicity, apoptosis, or secretion. |
| Target/genetic reference | Fail: MoA/target are annotations rather than matched engagement or genetic intervention. |
| Raw provenance | Fail: prepared transcript files and PRISM curve-parameter provenance are unavailable alongside the bridge. |

The detailed bridge and source-field audit is in [bridge_audit.md](bridge_audit.md). Literature precedent and minimum falsification gates are in [prior_challenge.md](prior_challenge.md).

## Narrow candidate: durable-function gate

Retain the design question: after a low-cost proxy ranks compounds, should the system directly measure a durable functional endpoint, update only a local virtual-cell state, or abstain? A valid test needs paired conditions and independently repeated function, a frozen decision rule, equal-budget baselines, and whole-drug/whole-background holdouts. A cross-assay join does not satisfy this design.

## Execution boundary

No new experiment, model training, or mechanism claim is authorized by this audit. The existing bridge is already development-exposed. Do not use it as independent confirmation, do not call discordance a localizable biological error, and do not infer savings from retrospective ranking alone. Reopen only when an eligible matched dataset or prospective experimental plan is available.
