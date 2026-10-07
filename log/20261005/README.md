> **File summary**
> - **Path**: `log/20261005/README.md`
> - **Purpose**: record the mono-pretraining study (public single-drug supervision for new-line combination ranking), run on already-opened Jaaks 2022 data with three review subagents and one independent verifier.
> - **Core points**: frozen protocol; GDSC2 contains the Jaaks lines, so exclusion is fold-wise; pretrained head weaker than tissue-mean/ridge on held-out mono; combination gain zero under a fair shrinkage grid; own-mono ceiling +0.002 Spearman; E never evaluated; no agent headroom; nothing promoted to src/tools.

# Experiment record: 2026-10-05

- **Study directory:** `research/astra/mono_pretraining_20261005/` (report: `REPORT_ZH.md`; manifest: `RUN_MANIFEST.json`).
- **Start:** 01:23 +0800, git HEAD `0f7a999`; the uncommitted tree from 2026-10-04 (knowledge study, imports) was preserved. No file modified after 23:20 on 10-04 by another session was found at start. Nothing committed or pushed.
- **Agents (distinct ownership):** A literature (`literature/`), B data S0 (`data_s0/`), C decisions then independent verification (`decisions/`). Lead: model, freeze, runs, report.
- **Order of events:** S0 (no label read) -> `PROTOCOL_V1.md` and `FREEZE.json` (02:39 label read begins) -> S1 mono (checks, config, 127 pretrainings, G1 pass) -> S2 dev v1 (03:09; G2 and G3 fail, E sealed) -> post-hoc ceiling and reliability diagnostics -> independent verification (exact reproduction; grid unfair to learned arms) -> `PROTOCOL_V1_1.md` repair (grid only) -> S2 dev v1.1 (04:13; G1 and G2 pass, G3 fail, E sealed).
- **Results (HD, 64 lines, exploratory):** see report sections 5.1-5.4. Pretrained within-cell mono ranking 0.729 vs tissue mean 0.759 and ridge 0.746; pre_h6 - S1 combination gain +0.000008 Spearman and 0 confirmed (120.8 vs 120.8) with all arms selecting near-zero weight; own-mono ceiling +0.0023 [+0.0009, +0.0040]; orientation-reproducible residual share about 19%.
- **Retained negatives:** v1 results (HARM class from an under-regularised grid; reported with the line x pair interval that makes it UNRESOLVED) remain in `results/` and `archive_v1/`.
- **Costs:** 0 API/LLM calls; about 13 MB public metadata plus 198 PubChem queries; CPU only (v1.1 dev about 41 min with 3 workers).
- **Disclosed deviations:** D1 fold-wise Jaaks exclusion; D2 rotation-invariant features; v1.1 post-outcome grid repair; agent B's accidental view of aggregate published statistics for 2-3 breast combinations; HD-fold mono pretraining used E lines' GDSC2 mono labels (not combination outcomes).
- **Framework:** no src/ or tools/ change; 12 production-interface gaps listed in `decisions/FRAMEWORK_GAPS.md` (none blocked the research harness).


## 1. Record control

Added on 2026-10-06 without changing the original day-record prefix. The original mono study above remains its chronological record.

## 2. Research questions and hypotheses

The original question was public single-drug transfer to combination selection. The repeat-study follow-up is indexed in the next day record.

## 3. Materials, data and computational environment

Original environment and source details remain in the mono study run manifest.

## 4. Experimental design and controls

Original v1 and development-only v1.1 are retained. This appended structure creates no new preregistration.

## 5. Experiment register and results

Actual mono results and test receipts remain in research/astra/mono_pretraining_20261005/REPORT_ZH.md and RUN_MANIFEST.json.

## 6. Deviations, failures and corrections

Clarification: the earlier residual-orientation value near 0.19 is a correlation, not an authenticated variance ceiling. E combination evaluation was not run, but E mono data were partially used. Public API queries occurred despite zero LLM inference calls.

## 7. Interpretation and claim boundaries

The follow-up repeat study measures same-condition consistency separately from orientation transport; neither correlation nor its square is an established learning ceiling.

## 8. Reproduction and artifact ledger

See research/astra/repeat_optimization_20261006/README.md for safe snapshot verification; historical mono replay remains isolated.

## 9. Open items and next experiments

The current experiment design is maintained in research/astra/repeat_optimization_20261006/NEXT_EXPERIMENT.md.

## 10. Curation provenance

Original bytes were retained as a prefix; the new run manifest records its size and SHA256.
