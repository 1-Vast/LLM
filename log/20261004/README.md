> **File summary**
> - **Path**: `log/20261004/README.md`
> - **Purpose**: record the reproducible-allocation study (screening, verification and stopping under a fixed budget), run on already-opened Jaaks 2022 data with three subagent workstreams.
> - **Core points**: an equal-budget repair of the verification comparison, corroborated (not authenticated) repeat provenance, a feedback correction without action gain, a static reproducibility-aware predictor gain from history information, no scheduler or LLM contribution, and a blocked 2x2 with an executable protocol.

# Experiment record: 2026-10-04

## 1. Record control

Work started at 2026-10-03 23:44 +0800 in the session that ran the feedback-validation study, and
continued after midnight. Git HEAD was `23f9e60` with an uncommitted tree from earlier blocks
(certified discovery, feedback validation, direction exploration); all of it was preserved.

- **Study directory:** `research/astra/reproducible_allocation_20261003/`, created at 23:48.
- **File-ownership plan:** `protocol/STUDY_PLAN.md`, written at 23:50 before any parallel edit:
  - parent: protocol, report, manifest;
  - `repeats/`: provenance and model identification;
  - `allocation/`: budget and resource accounting;
  - `review/`: statistics, data qualification, agent contribution, novelty.
- **Usage-limit stop:** the three subagents stopped at about 23:51 before writing anything and were
  resumed at 02:12.
- **Earlier freezes:** intact (feedback validation 15/15 files, certified discovery all files).
- **Nothing committed or pushed.**

## 2. Research questions and hypotheses

Primary: can reproducibility-aware predictions improve how a fixed budget is split between screening,
independent verification and stopping, beyond strong simple policies?

Sub-questions:
- **Phase 1:** does the earlier verify-hits advantage (+16%) survive equal budget consumption?
- **Phase 2:** does purchased-screen feedback carry signal that predicts an independent measurement?
  The model is a static prior plus lambda x feedback, with lambda = 0 allowed.
- **Phase 3:** do predictor and scheduler each contribute?

## 3. Materials, data and computational environment

- **Data:** Jaaks et al. 2022 fitted release (SHA-256 `1188968c...a278`), EXPOSED, used for
  exploratory analysis only.
- **Downloaded on 2026-10-04** (design columns only; intensities and viabilities never read):
  - the authors' raw plate records (figshare 19141916, 60.7 MB) and day-1 plates (figshare 19141919);
  - Europe PMC full text and supplements of the Jaaks paper;
  - the BATCHIE pair screen (Zenodo 13871987, 24.7 MB).
- **Environment:** maestro, Python 3.11.16, numpy 2.4.6, pandas 2.3.3, scipy 1.17.1,
  scikit-learn 1.9.0.
- **Frozen code:** the TransferWorld world model and the feedback-validation builder and bootstrap
  were imported unchanged.
- **Provider calls:** none (USD 0 of the USD 3 cap).

## 4. Experimental design and controls

- **Outcome access:** every reading goes through `common.exposed_ticket`. It verifies the earlier
  freeze and appends to the study's `protocol/access_log.jsonl`, which has 8 entries.
- **Plans before readings:** each workstream wrote its plan before its own outcome readings. Post hoc
  additions have their own plan files and are labelled.
- **Units:** cell lines, stratified by tissue, with a line-stratified bootstrap (10,000 resamples,
  seed 20261003). Role assignments, plates, seeding events and seeds are never counted as units.
- **Zero arms:** screen-only (zero verification) and random ranking.
- **Strong baselines:** full-feasible-budget paired measurement; a development-selected fixed split;
  verify-hits with a reserved terminal verification round; historical confirmation probability per
  cost.
- **Information control:** the S_both ranking uses the same history data as R without modelling
  confirmation.

## 5. Experiment register and results

All results are EXPLORATORY; intervals are 95% line-bootstrap intervals.

1. **Reconciliation.** The original totals reproduce exactly (3,958 vs 3,762 measurements; 238.5 vs
   205.0 verified discoveries).
   - Paired lost 196 units: 48 unavoidable (odd budgets) and 148 avoidable (no carry-over).
   - The original verify-hits left 64.5 final-round hits unverified.
2. **Equal-budget replay (125 lines).**
   - Verify-hits with a terminal round found 252.5 confirmed discoveries, against 214.5 for
     full-budget paired: +17.7% [13.1, 23.1].
   - Against the fixed split (231.5): +9.1% [5.4, 13.5].
   - Against confirmation-probability-per-cost (268.0): -5.8% [-9.3, -2.1].
   - The terminal round adds +5.9% [3.8, 8.3].
   - The wells budget gives the same ordering.
   - Verify-hits needs 5 rounds; paired gets its result in 1 and the fixed split in 2. At 2 rounds
     the fixed split wins (-9.1% [-14.3, -3.4], post hoc).
   - Custom plates differ by up to 2.2x between arms, so equal wells is not equal plates.
3. **Repeat provenance: CORROBORATED_NOT_AUTHENTICATED.**
   - Plate -> seeding date and culture expansion comes from documented raw fields for 3,106/3,106
     plates; 107 plates lack a day-1 plate.
   - Whether a seeding event is the paper's biological replicate is unknown.
   - In 9 of 14 repeat lines, all repeats come from one culture expansion.
   - Each plate carries 216-254 control wells, against 200 documented.
4. **Scalar feedback correction.**
   - lambda_U is 0.26-0.30 on the role-swapped target and 0.24-0.36 on the same-condition target. No
     fold selected lambda near zero.
   - Role-swapped: squared error -0.71 [-1.10, -0.34] of 44.3; concordance -0.0006 [-0.0020,
     +0.0008]; no top-k gain.
   - Same-condition (14 lines): concordance +0.0065 [0.0029, 0.0101], but the squared-error
     interval includes 0, so the stop rule fired.
   - Full-weight feedback (lambda = 1) is clearly worse than none.
   - "Screen hits first" beats lambda-shrunk verification ordering.
   - No latent effect blocks were added.
5. **Post-hoc R2 correction.** The earlier "-0.03 to -0.05" was a variance ratio. The squared-error
   R2 is -0.08 to -0.14.
6. **Predictor x scheduler (post hoc).**
   - Predictor effect under verify-hits: +6.5% [2.6, 10.6].
   - Scheduler effect: -0.8% [-4.0, +2.5] and -0.4% [-0.95, 0.0]; interaction null.
   - Information-matched ranking: S_both - S is +4.4% [2.0, 6.8], and R - S_both is +2.1% [-1.6,
     +6.1].
7. **Review.**
   - No dataset qualifies for an untouched 2x2.
   - tau = 5% is recommended at fixed rounds and wells (a judgement). It needs about 150-180 lines
     with two role assignments.
   - LLM arm: DO_NOT_RUN.
   - Novelty: every method component is covered by prior art.

## 6. Deviations, failures and corrections

- **Usage limit:** the subagents stopped at about 23:51 and resumed at 02:12.
- **Accidental data row:** one row of the fitted release, outcome columns included, was printed by
  the repeats workstream before its first ticket. The data were already exposed.
- **Repeats corrections:** a figshare ID correction (19141922 is the validation raw data); a
  time-zone bug in the provenance addendum, corrected in v2.
- **Review timestamps:** estimated times were typed at first and then corrected to file times,
  labelled in the files.
- **Post hoc additions:** the time-matched replay and allocation addenda 2 and 3, each planned before
  its own reading.
- **Europe PMC timeout:** the first supplementary-files download timed out after 300 s; the second
  attempt succeeded.
- **Corrections to `research/astra/feedback_validation_20261003/REPORT.md`** (that file is unchanged):
  - its +16% was not budget-matched;
  - its post-hoc R2 was a variance ratio.

## 7. Interpretation and claim boundaries

- **Nothing here is confirmation.** Every outcome number comes from an already-opened screen.
- **Where the predictor gain comes from.** It is mostly richer history (both orientations of other
  lines), not modelling of reproducibility.
- **What target-line feedback does.** It shifts per-line levels but does not reorder candidates on
  the role-swapped measurement.
- **What drives verify-hits' advantage.** It depends on extra rounds.
- **What the same-condition repeats are.** They are re-seedings, mostly of one culture expansion;
  they are not independent biological experiments.
- **What this is not.** No STATE, mechanism or cheap-predecision-state claim is made.
- **No physical experiment was performed.**

- **Continue:**
  - verify-hits with a terminal verification round, when rounds are cheap; a development-selected
    fixed split when only 2 rounds are available;
  - static reproducibility-aware history, always alongside the S_both information control;
  - physical accounting by branch.
- **Change:**
  - declare the binding resource and fix rounds across arms;
  - use a development-fitted feedback weight (about 0.3), not 1.
- **Stop:**
  - more complex feedback models;
  - the index scheduler;
  - LLM arms for this problem.

## 8. Reproduction and artifact ledger

- **Report:** [REPORT.md](../../research/astra/reproducible_allocation_20261003/REPORT.md).
- **Manifest:** [RUN_MANIFEST.json](../../research/astra/reproducible_allocation_20261003/RUN_MANIFEST.json),
  with hashes of all study files, commands, runtimes, seeds, the access log and the downloads.
- **Executable protocol:**
  [NEXT_PROTOCOL.json](../../research/astra/reproducible_allocation_20261003/NEXT_PROTOCOL.json).
- **Blocking receipt:** `research/astra/reproducible_allocation_20261003/receipts/phase3_blocking.json`.
- **Tests:**
  - study suite 52 passed (synthetic data, 282 s);
  - core default 354 passed;
  - repository shape 22 passed;
  - the five new test files are registered under the research test scope in `pyproject.toml`.

## 9. Open items and next experiments

- **Qualify an untouched release:**
  - complete anchored menu;
  - verification on separate seeding events, with date-stamped raw plate records;
  - other lines measured in both roles;
  - 150 or more lines with two role assignments.
- **Then:** freeze and run `NEXT_PROTOCOL.json`, with primary contrast (R+V) - (S+V) at fixed rounds
  and tau = 5%.
- **Not yet run:**
  - a plate-budget replay;
  - a native-plate replay that credits co-measured orientations.
- **Blocked:**
  - authentication of biological replicates (no published plate -> replicate table);
  - the DREAM data (account required).

## 10. Curation provenance

Written by the parent session from the three workstream hand-backs and the parent audits:
- the purchase-log audit of the replay;
- the recomputation of the repeats contrasts from per-line records;
- the dry runs of the protocol runner.

Every number above is in the cited result or receipt files.


## Research direction exploration (2026-10-04)

Three specialist agents and a parent receipt audit narrowed the continuation to an information-matched predictor comparison under a resource/deadline contract. The report documents terminal-screen expenditure, the distinction between budget caps and consumption, and the small same-condition feedback signal with its stronger comparator. Historical outcomes remain exploratory; intervals were read rather than refitted. No production code, new model experiment, API call, commit or push occurred.

- Exploration: [REPORT.md](../../research/astra/direction_exploration_20261004_v1/REPORT.md)
- English continuation: [NEXT_PROMPT.md](../../research/astra/direction_exploration_20261004_v1/NEXT_PROMPT.md)
- Source hashes and independently extracted values: [EXPLORATION_RECEIPT.json](../../research/astra/direction_exploration_20261004_v1/EXPLORATION_RECEIPT.json)



## Confirmation-campaign study (2026-10-04)

A bounded study ran on exposed Jaaks 2022 data, so every result is EXPLORATORY. It used three subagents with disjoint folders: design, resources and independent verify.

- **Contract.** The campaign contract was frozen at 12:43:42, before any outcome read. Its v2 adopts all 21 items of an independent pre-freeze challenge.
- **Primary.** Under identical two-orientation history, a two-round deadline and a 20% measurement cap, R (shrunk joint-call rate) against the development-selected C_mean gave 110.5 vs 117.5 on 61 held-out lines: -5.96% [-13.36%, +1.67%]. Verdict EXPLORATORY_WORTHWHILE_EXCLUDED, so STOP. The verify agent reproduced it independently, campaign by campaign.
- **Information package.** Two-orientation history against one-orientation history: +13.4% [8.4%, 18.8%].
- **Feedback.** EXPLORATORY_NO_RELATIVE_FEEDBACK_VALUE. Matched static controls absorb the apparent ordering gains.
- **Stopping.** Not buying screens that cannot be verified by the deadline keeps the yield and saves 20% of measurements and 31% of custom plate starts. Two rounds beat one.
- **Scheduler and agent.** No headroom; no API calls.
- **Untouched data.** One release qualifies conditionally (Vis et al. 2024 cross-run repeats). It is kept sealed under the stop rule.
- **Tests.** 481 study tests, 354 core and 22 shape tests passed.
- **Records.** Nothing committed. Report: [REPORT.md](../../research/astra/confirmation_campaign_20261004/REPORT.md); manifest: [RUN_MANIFEST.json](../../research/astra/confirmation_campaign_20261004/RUN_MANIFEST.json); blocking receipt: `research/astra/confirmation_campaign_20261004/receipts/evaluation_blocking.json`.


## Constructive solution exploration (2026-10-04)

Three agents investigated solutions rather than extending the previous stop conclusion. The selected next task is native plate-set acquisition with fixed predictions and first-round purchases, followed by independent raw-response recovery and a bounded potency/efficacy predictor. Parent checks confirmed the 2–7 components per side and the local raw intensity schema. Vis author endpoint code was inspected; fitted evaluation values and supplementary outcome tables remain unopened. No campaign/model experiment, API inference, source change or Git publication occurred.

- [Solution report](../../research/astra/solution_exploration_20261004/REPORT.md)
- [English execution prompt](../../research/astra/solution_exploration_20261004/NEXT_PROMPT.md)
- [Exploration receipt](../../research/astra/solution_exploration_20261004/EXPLORATION_RECEIPT.json)


## Biological knowledge optimization and second curation (2026-10-04)

Imported the 83-file supplied knowledge package without changing its bytes. Three agents reviewed model/pretraining, data contracts and maintenance. Added an explicit read-only datasets query tool; opposite protein/transcription signs remain distinct, unknown applicability/structure remains unknown. Added non-overwriting import and 49,424-campaign verification, with the external partition CRLF/LF difference recorded rather than refrozen.

The original 14 synthetic checks and four new query tests pass; related structure/collection checks bring the executed range to 45 passing tests. No model training, Vis outcome access, paid inference, src change or Git publication. Local GDSC2 metadata supports a staged 14-pathway mono-pretraining design; metadata coverage is not QC or sample independence.

- [Optimization and curation report](../../research/astra/knowledge_optimization_20261004/REPORT_ZH.md)
- [Current maintenance and reproduction entry](../../research/astra/knowledge_optimization_20261004/README.md)
- [Pretraining design](../../research/astra/knowledge_optimization_20261004/PRETRAINING_PROTOCOL.json)
- [Run manifest](../../research/astra/knowledge_optimization_20261004/RUN_MANIFEST.json)
