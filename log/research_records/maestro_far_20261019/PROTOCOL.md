# MAESTRO-FAR protocol (PROPOSED; DRAFT; not frozen; nothing executed)

Falsification-Aware Research with Virtual Cells. Every number in `[P]` is a **proposed** gate, to be checked for statistical and operational fit on the qualified data and then frozen (hashed, LF-normalised) before any `D_test` read. Evidence status of the premise: see `AUDIT.md`.

## 1. Question (revised)
Can a research agent identify where a Virtual Cell (VC) fails, choose a discriminating orthogonal assay, and apply a bounded local repair that raises downstream decision utility on held-out chemistry and context, beyond strong simple baselines? Three claims are kept separate: (C1) deterministic falsification-plus-repair adds utility; (C2) an LLM adds to C1 over same-budget non-LLM search; (C3) experience transfers across tasks (EG-RPT, deferred). The evidence only licenses *testing* C1: feedback is the supported ingredient (+1.056 over prior), whereas latent-state priors, R1 repair, lookahead and typed-edit agents did not add decision utility in the studied arenas.

## 2. Hypothesis record and roles
Record (all required): claim; affected slice; competing explanation (including a strong simple baseline); predictions under each; discriminating experiment from the allowed set; repair primitive; numeric rejection condition. Reuse `ResearchEdit.validate`. The LLM may propose these fields; it may not certify biology, set weights or thresholds, see `D_test`, or override the deterministic evaluator. Response patterns are not causal mechanisms; certificates must not claim mechanism.

## 3. Interface and baselines
VC interface = predict(drug, context, assay) → value, uncertainty, model disagreement, domain/OOD flag, supporting evidence list, `apply_repair(spec)`, `abstain()`. Model set: item mean, ridge, drug-specific ridge, gradient-boosted trees, plus at most two modern VCs whose inputs match the data (candidate: the repository's transcriptional-transfer model; STATE only where its input contract is met). No foundation-model training, no raw imaging.
Design baselines: random; fixed coverage/A-optimal; exploit-first; probability-of-hit; BATCHIE-like sequential (simplified implementations exist; the papers are not ported); robust Bayesian design where feasible.
Repairs: none; retrain/recalibrate; conditional residual expert; mixture/gating; abstain/fallback. Agent comparators: grammar enumerator, random/evolutionary search.

## 4. Phases and gates (all gates [P]; a failed gate retires that component, not the programme)
* **Phase 0 qualification.** Edge needs ≥300 perturbations and ≥8 independent MoA/compound groups; audit compound, cell, dose, time, protocol, provenance, overlap. *Observed so far (labels only):* PRISM–L1000 passes identity counts; JUMP blocked (empty directory); <2 outcome edges, so run the bounded pilot on PRISM–L1000 + DepMap and report the limitation. Remaining Phase 0 work: dose/time covariate model and structure-level identity check (no outcomes).
* **Phase 1 failure atlas.** ~40 search + ~30 internal-held-out campaigns [P]; failure signatures defined on search data only; folds = MoA-family and lineage held-out. Gate: ≥2 signatures with held-out AUROC lower bound >0.60 and association with terminal decision error [P]. Pre-step: split-noise reliability test (two independent probe-noise draws), because the campaign-level 131-vs-100 gap is noise-consistent. Fail → revise failure representation; no agent.
* **Phase 2 orthogonal falsification.** ≤4 auxiliary assay actions per campaign. Rank by conservative expected terminal utility (LCB − cost − model-risk); distinguishability only as tie-break. Gate: FAR utility − strongest baseline has positive lower bound and exceeds a predeclared practical threshold [P]. Derive the threshold from Phase 1 noise, not from the earlier 0.1875 (carried floor, to be re-checked).
* **Phase 3 repairs.** Fixed predeclared procedures, same evidence budget, no agent tuning. Admit only if LCB of utility gain > threshold and calibration and false-progression do not worsen beyond tolerances [P].
* **Phase 4 agent increment.** Only after deterministic FAR beats baselines. 20-30 episodes, hard cap 300-500 LLM calls (planning cap, not an estimate; deepseek-flash only; spend needs your authorisation). Gate: ≥10% over same-budget non-LLM search with positive LCB [P]. Fail → withdraw the LLM-specific claim, keep deterministic FAR if it stands. Note prior agent power: the agent-vs-enumerator contrast had SE ≈0.025, so 20-30 episodes may be underpowered; compute power first and declare the phase descriptive if so.
* **Phase 5 2×2.** Agent falsification × VC repair; δ = U11 − U10 − U01 + U00 with cluster bootstrap; claim synergy only if LB>0. Prior note: interaction contrasts needed ~38-82k compounds under conservative assumptions; likely descriptive.
* **Phase 6 transfer / EG-RPT.** Only with a uniform certificate schema and enough independent certificates. Compare no memory, retrieval-only, explicit transfer policy on new scaffolds/lineages/edges. Targets [P]: equal utility at ≥20% lower cost, or ≥10% higher utility at fixed cost, without negative transfer.
* **Phase 7 external confirmation.** Blocked until an independent, unexposed source is cleared and authorised; freeze first, one evaluation, no post-test change reported as confirmatory.

## 5. Splits, statistics, outputs
`D_search → D_select → D_test` with masked-interface role caps. Clusters: scaffold/MoA, cell lineage (or patient), source/batch; noise draws are not replicates. Family-cluster bootstrap (4,000 draws), Holm or predeclared ordered testing. Report four layers: VC correctness (per-perturbation metrics, calibration, OOD, interval coverage); decision utility (hits per 64, false progression/rejection, regret, actions to target); research efficiency RE = (U_after − U_before)/cost with the cost definition and interval; epistemic quality (hypothesis precision and calibration, negative transfer, search-selection-test gap, unsupported causal statements).

## 6. Certificate schema (Proposed)
failure signature and slice; hypotheses with predictions; chosen assay and itemised cost; observed outcome; repair spec (fixed); held-out utility change with cluster interval; calibration and false-progression change; data tier (exposed/independent); dependence group; verdict. Negative and refused certificates are first-class.

## 7. Resources and prohibited actions
CPU-only, ~24-32 cores / 96-128 GB. No wet-lab, no foundation-model training, no raw imaging download, no sealed access, no paid calls without your authorisation, no commits or pushes. Phases 0-3 are LLM-free.

## 8. Not run, not claimed
No FAR analysis beyond the Phase 0 label counts; no VC was trained or evaluated; no atlas, no falsification experiment, no repair, no agent arm; no claim that MAESTRO-FAR or EG-RPT is validated.
