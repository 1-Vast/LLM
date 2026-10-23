# Evidence map before this study (2026-10-19)

Sources read: `research/EVIDENCE.md`, `log/DIRECTIONS.md`, `log/RESEARCH_PROGRAM.md`, `research/maestro_far_20261019/README.md`,
its `REPORT.md` and `audit_20261019/REPORT.md`, the EG-RPT draft summary, and the replicate loaders of
`program_revision_20261017` / `indication_triage_20261016` / `anchor_purchase_20261016`. All numbers below are quoted from
those records; none was rerun here except where marked.

## What has actually worked (development grade unless stated)

| Result | Where | Scope limit |
|---|---|---|
| L1000 transcriptional transfer predicts PRISM killing profiles of unseen compounds (+0.116 over targets on 421 sealed drugs; RKT +0.218 over generic on sealed GSE70138) | Block N, Block Q | One assay/dose; the sealed tiers are now exposed |
| Item-specific measured feedback ("exploit-first": measure the model's top items, re-rank) | Beat AML context transfer (confirmed once, +0.073), feedback attribution, FAR (+0.033 over no assay) | Gains belong to feedback on the same item, not to the basal-RNA prior or procedure choice |
| Ranking follow-ups by calibrated P(hit) instead of the standardised prediction (55 -> 77/141) | Collaboration limits (fresh GCP lines) | Calibration slope did not transfer (.45 fresh vs .80 dev) |
| Assay + fixed gate repair (+0.039 test, +0.047 reused vault) | FAR | Not FAR-specific; reference contracts not strictly isolated (audit) |
| Fixed sparse designs and exploit-first beat VOI/lookahead/agent-searched acquisition | Block Q, acquisition program, feedback attribution | Hindsight headroom of acquisition choice is small (+7% held-out) |
| Certified discovery on NCI-ALMANAC combinations (FDR/yield certificates valid) | Certified discovery | Combination task only |

## Proposed contributions that were not supported

LLM agents (planner, critic, forecaster, proposer, bridge picker): null or harmful in every matched comparison. Learned
procedure transfer / policy memory: value labels unidentified (13 records). FAR failure signatures: AUROC 0.47-0.52; learned
expected-benefit model cross-fit r about 0. Knowledge graph beyond mechanism-class membership: gene-relabel null reproduces
the gain. Low-rank state model vs drug-specific ridge on Beat AML (G1 failed). Program revision / seed library (corrected
contract: NOT_CONFIRMED). kNN-analogue feedback propagation (not replicated). PRESAGE pathway adapter (NO_GO).

## Results with evaluation or independence limitations

* Everything local is exposed: PRISM 19Q4 primary and secondary, L1000 GSE92742/GSE70138 (including the former sealed
  tiers), Beat AML, GCP, Tahoe, MIX-Seq. New splits are development evidence.
* FAR: search used select outcomes as references; test folds trained each other; four slices were not equal drug counts;
  secondary MoA labels crossed folds; results depend on library versions/threads (audit).
* Program revision: the development bench trained on reserved query outcomes; replay contract defects (seed attribution).
* Indication triage: utility was a re-read of probed cells (99.7%).
* Many grading contracts score a policy on the same noisy screen that produced its inputs or on one replicate.
* Repeated finding of overconfidence on *selected* actions: forecasts 1.6-2x low on selected actions, card P(wrong) 2-19x low,
  agent-stated probabilities ~5x overconfident, conformal BH FDP above nominal on exposed triage.

## Important capabilities that remain untested

1. How much of the "model error" used to grade policies and failure detectors is replicate noise of the grading read.
2. Decision evaluation against an independent physical replicate that no policy used, and a cross-run check.
3. Calibration of a Virtual Cell posterior *on selected candidates* when noise is identified from replicates.
4. Dose/condition transfer (the secondary screen's 8-dose ladder) - deferred in DIRECTIONS.
5. Independent confirmation (no unexposed local tier; PRISM 24Q2 remains sealed/unauthorised).
6. Mechanism (no measured references locally).

## Pre-protocol observation made in this study (disclosed)

Before any method was written, a descriptive pass over all 1,394 HTS002 2.5 uM cores (all roles; no method comparison)
measured: replicate-plate correlation of raw log2FC 0.87; of the selective residual 0.52; per-compound selective profile
replicate correlation median 0.41 (0.62 for strongly active, 0.29 for weak compounds); primary-vs-secondary selective
correlation 0.34; noise SD 0.62 against selective SD 0.89. This motivated the selected direction and is exposure of every
partition at the level of replicate agreement only.
