# Independent content review: functional-data priority update

Date: 2026-10-31 (Asia/Shanghai).

Initial verdict: **SCOPED REVISION REQUESTED**. The maintained design follows the requested research priority and preserves the inherited evidence limits. Two small scientific-scope clarifications below were requested before a text-level PASS. This review does not require another experiment or a larger initial data contract.

## Scope and sources

Read in full: `NEXT_ROUND_DESIGN.md`; `../2026-10-31-decision-focused-selection-mvp/REPORT.md`; its `VERIFY_61_SUPPLEMENT.md`; and `../2026-10-31-crossfield-state-learning/CHALLENGE.md`, including its action-contrast addendum. Line references below refer to the reviewed text before any subsequent revision.

This is an independent scientific/content review of these documents, not empirical verification, a new closest-prior literature search, or an audit of fit implementation. No models, numerical arrays, network requests, or core/source edits were used. Only this review file was created.

## Required textual fixes

**R1: Keep the state/history contrast non-vacuous.** `NEXT_ROUND_DESIGN.md:47` calls baseline growth/viability **and recorded history/exposure** the first candidate state. Line 65 similarly combines these inputs immediately before comparing state-only with state-plus-history. If S contains H itself, or an identifier/descriptor that uniquely encodes H, conditioning additionally on H supplies no new information: the displayed invariance is true by definition, and it cannot demonstrate a history-resolving measured state. The common-support warnings elsewhere help but do not remove this ambiguity.

Suggested precise clarification: baseline growth/viability are the first candidate measured S; recorded history/exposure are available comparator and stratification covariates. If selected transferable exposure descriptors are included in S, freeze them explicitly, preserve overlap across distinct histories, and do not treat an encoding that determines history identity as evidence of invariance. Distinguish the S-only and S-plus-history input contracts in the small-model comparison. History descriptors may still support useful prediction; that is a different claim from demonstrating that a measured functional S absorbs history effect modification.

**R2: Bound choice utility to the tested action contrasts.** Line 17 allows a menu containing A and B, and line 79 asks for regret against the supported menu, while the scientific restriction only covers A minus B. The challenge addendum explicitly states that one invariant pair does not certify a larger menu (`CHALLENGE.md:78`).

Suggested precise clarification: the initial actionable menu and its regret oracle are exactly {A, B}. If a larger menu is evaluated later, require the relevant contrasts against a declared reference action and evaluate them on their supported populations before claiming whole-menu choice utility. The existing two-by-two skeleton already supports this small scope; extra actions are not an admission requirement for the initial test.

## Checks that pass within this review

- The parked arm is accurately described as binary top-set ridge under one static input contract. Its saved-run numbers match the source report. The text does not generalize its negative direction to decision-focused learning or SPO as a field.
- Original verifier FAIL, clarification-based arithmetic PASS, and scientific INCONCLUSIVE remain separate. The supplement is not promoted to model-fit certification or confirmation. Earlier GAT mismatch remains an unresolved engineering comparison, not biological refutation.
- The main target is conditional next-action contrast invariance. Common absolute-outcome shifts may cancel. Magnitude equivalence, sign/preference preservation, and absolute efficacy/safety/tail prediction are distinguished. Full-distribution sufficiency does not gate contrast research or a suitably bounded later extension.
- The resource tiers permit endpoint-only history/action testing before measured-state sufficiency. An early-state join is required only for the state claim; independent reserved preparations/history blocks are required for its transport validation. Static endpoint resources cannot be relabeled as sequential evidence.
- Two histories by two randomized next actions is correctly treated as a factorial skeleton, not a powered design or proof of unseen-history transport. Preparation blocks, sibling exchangeability, schedule/carryover, eligible-population limits, overlap, outcome scale, equivalence margin, and precision are addressed. Observational assignment is explicitly distinguished from randomized evidence.
- The candidate probe count is optional. Single-cell omics, spatial assays, ECM, proteomics, chemistry, and GAT are not prerequisites to the inexpensive endpoint census or a functional-only initial test.
- Preparation-chemistry holdout and later-action chemotype holdout are distinguished. Source-only freezing, disjoint admission/validation blocks or selection-aware joint analysis, and avoidance of significance-as-equivalence are explicit.
- Ordinary contrast regression, panel ridge, simpler growth/exposure inputs, and appropriate DBP are retained as fair rivals. Representation advantage, informative measurement, biological relation, and assay-cost reduction are not conflated.
- Organoid and Agent extensions remain conditional. No eligible new dataset, successful experiment, novel mathematical principle, biological mechanism, or independent empirical result is invented.

After R1 and R2, the document can receive a **text-level scoped PASS** for the requested priority update. That would authorize no numerical run, empirical conclusion, core promotion, or claim that suitable data have been qualified.

## Revision reread

R1 is **RESOLVED** on rereading the revised `NEXT_ROUND_DESIGN.md`: the primary-question section now explicitly keeps S and H distinct, states the tautology from putting full H into S, and requires prespecified descriptors with nontrivial cross-history overlap; resource triage now identifies measured growth/viability as the first S and history/exposure as design/comparator information. The small-model section is read subject to that explicit contract.

At the first reread, R2 remained pending: the primary question still said a menu containing A and B and evaluation still said regret against the supported menu. The requested remedy was a scope sentence, not additional experimental requirements.

At the final reread, R2 is **RESOLVED**: the primary question defines the initial action menu and selection-regret oracle as exactly {A,B}, requires every relevant contrast against a declared reference for expansion, and explicitly rejects whole-menu certification from one invariant pair. Evaluation's supported-menu language is bounded by that definition.

**Final verdict: TEXT-LEVEL SCOPED PASS.** Both initial objections are resolved in the maintained design. The inexpensive, staged action-contrast research priority is coherent with the four reviewed documents. This verdict certifies only the reviewed text and its claim boundaries; it does not certify numerical results, fit implementation, eligible data, biological invariance, novelty, transport success, or readiness for a numerical run/core promotion.
