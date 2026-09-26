# Run notes, 2026-09-26

Chronological notes for the day record `log/20260926/README.md`. Times are local (+0800).

## 11:58 Orientation

- A Codex session edited this repository until 11:50 and then finished; the Codex processes
  still running at 11:59 were working on `D:\SASG`. Its uncommitted changes were kept as found.
- Full suite on the working tree as found: 1266 passed, exit 0.

## 12:05-12:14 Data directory merge

- `data` was a directory junction to `dataset`; every asset was reachable under two names.
  Code named `data/...` 64 times and `dataset/...` in no executable path.
- The junction was removed with `rmdir` (link only), `dataset` was renamed `data`, and seven
  junctions in the ignored verification clone `outputs/local_verification/upstream/dataset/`
  were retargeted to the new paths.
- Four byte-identical duplicates were moved (not deleted) to
  `D:/MAESTRO_data_archive_20260926/` with `_ARCHIVE_MANIFEST.json`: a second copy of the
  2.29 GiB SciPlex3 h5ad and its provenance file (SHA-256 of both copies equals the recorded
  `bde2420c...`), and two stray copies of chemCPA's own downloader scripts.
- The chemCPA source checkout moved to `data/external/chemCPA/`.
- Inventory check: 1224 files after the merge equals 1228 before minus the four archived files,
  sizes identical. Suite after the merge: 1266 passed.

## 12:15-12:28 Data exploration and pre-registration

- Downloaded the HGNC complete set and MSigDB Hallmark v2024.1 with provenance files under
  `data/external/`.
- Structures resolved for 188 of 188 compounds; three duplicate skeletons merged into one split
  unit each (185 units).
- Protocol frozen at 12:28:14; hashes in the day record.

## 12:31-12:46 First preparation and a fold-0 timing run (both later invalidated)

- The first preparation stopped by name (`unresolved_structure`) on a salt suffix the shared
  name folding missed; fixed in `common.py` and rerun (12:38, 2250 conditions).
- Fold 0 of the cross-validation stopped twice before finishing: once because `mlp_existing`
  projected all rows through its SVD while held-out responses are set to NaN (the leakage guard
  working as designed; fixed to project training rows only), once on a float64 weight array.
  The third attempt finished in 242 s; no metric was computed from it.

## 12:42-12:50 The SciPlex3 release's gene labels are offset by one row

- A dry run of the agent probe printed one compound's signature: olfactory receptors,
  pseudogenes and lncRNAs, which is not what a drug response looks like. The 30 genes with the
  highest vehicle expression were likewise implausible (SACM1L, GRIN3A, LRIG2, ...).
- Each of those Ensembl identifiers sits one row before a gene that should top the list:
  GRIN3A (ENSG00000198785) before MT-ND5 (...198786), LRIG2 before MT-CO1, SACM1L before MT-RNR1,
  MIR9-2HG before NEAT1. The feature table's first entry is a stray header row,
  `id gene_short_name`, so the gene in column j is the label in row j + 1.
- Confirmed with cell-identity markers under both alignments (vehicle cells, 24 h):
  as published, no marker is line-specific and MALAT1 reads 0.00; realigned, HBG1/HBG2/HBZ/GATA1
  peak only in K562, TFF1/KRT19/GATA3/ESR1 only in MCF7, AKR1C1/AKR1B10/NQO1/ALDH3A1 only in A549,
  and MALAT1 and NEAT1 are high everywhere. The chemCPA subset used by the existing tests is
  correctly aligned (9 of 9 markers at offset 0).
- Consequences: the 12:38 preparation and the fold-0 run used wrong gene identities (the MT-
  exclusion and every anchor gene pointed at the wrong column), so both were renamed
  `INVALID_label_offset_*` and are not used. `src/evaluation/model_validation.py` read the same
  labels; its predictive metrics are label-independent, but the gene identifiers it recorded
  were wrong.
- Added `src/virtual_cell/identity_markers.py` (the markers choose the alignment or the reader
  refuses by name) with `tests/test_identity_markers.py` (7 tests, one against the real file),
  and routed both `research/biological_depth/prepare.py` and `model_validation.py` through it.
- Pre-registration status: the protocol's gene rule is unchanged; only which column carries
  which gene was corrected. Seen before the correction: one observed signature and the
  vehicle-expression ranking, both under wrong labels. No model output was scored.

## 12:48-12:57 Corrected preparation, cross-validation and agent probe started

- Preparation with the marker gate (434 s): offset +1 chosen with 12 of 12 markers in their
  line (offset 0: 5 of 11; offset -1: 3 of 11). 2473 genes, 2250 conditions, 31 replicate
  groups excluded below 20 cells. Most expressed vehicle genes are now MALAT1, KRT8, NEAT1,
  GAPDH, KRT18 and long intron-rich genes, as expected for sci-RNA-seq3 nuclear reads.
- One implementation clarification made before any outcome existed: each encoder view averages
  1, 2 or 4 disjoint chunks, so pseudobulk inputs (about 130 cells) stay within the depth range
  the encoder was trained on (a single chunk averages about 16 cells).
- Five-fold cross-validation started 12:55 in the background.
- Agent probe dry run with corrected labels: the first item's MCF7 decrease list is the estrogen
  receptor program (GREB1, ESR1, GFRA1, CCND1, TFF1, XBP1) and its A549 list the NRF2 program.
  Live probe started 12:56.
- 12:57 `research/biological_depth/calibration_spec.json` written before any out-of-fold
  prediction or metric was read; SHA-256
  `2c92bd17b502c7d8d03f066ada716617125f92de9a59844b2ae400a1f307f90d`. It is an addendum for
  deciding whether a served rung may claim calibrated intervals, not part of the frozen protocol.

## 12:56-12:59 Agent probe (live DeepSeek and Jev)

40 compounds, 17 pathway classes, chance 0.059, frequency prior 0.150. Accuracy is agreement
with the vendor annotation, with compound-bootstrap 95% intervals:

| Arm | Accuracy |
|---|---|
| retrieval tool alone (measured profiles of other compounds) | 0.500 [0.350, 0.650] |
| DeepSeek, signature only | 0.100 [0.025, 0.200] |
| DeepSeek, signature plus retrieval card | 0.425 [0.275, 0.575] |
| Jev, signature only | 0.075 [0.000, 0.175] |
| Jev, signature plus retrieval card | 0.475 [0.325, 0.625] |

- Primary (registered): the card adds +0.325 [0.175, 0.500] to DeepSeek; it adds +0.400
  [0.250, 0.575] to Jev. DeepSeek with the card minus the tool alone: -0.075 [-0.175, 0.000].
- Jev answered the same unchanged state identically in 0.933 of repeat pairs (first 10 items).
- Unaided, DeepSeek recognised textbook programs (HSP induction for luminespib, FKBP5 for
  triamcinolone acetonide, a p53/CDKN1A reading for a CDK inhibitor) but over-attributed any
  movement of the MCF7 estrogen program to nuclear-receptor drugs, and was right about
  meprednisone for the wrong reason (it cited estrogen-receptor targets, not glucocorticoid ones).
- No failures or refusals. Spend: DeepSeek $0.0227 over 80 calls (provider ledger
  `outputs/biological_depth_20260926/agent_probe/deepseek_spend.json`); Jev 127,093 input tokens,
  about $0.0053 at $0.042 per million.
- Reading: neither language model reads mechanism from an anonymised 24 h signature; the
  mechanism information in this task sits in the measured reference library, and the models'
  contribution is to follow it, slightly less accurately than the tool itself.

## 13:00-13:16 Retrieval tool built while the cross-validation ran

- `src/virtual_cell/signature_retrieval.py`, `tools/signature_retrieval/` and 7 tests; the three
  tests that pin the tool set were updated deliberately.

## 13:16-13:22 Audit (first reading of any model result)

- First run stopped on a division by zero in the BCR-ABL anchor for the zero arm (guarded; a
  zero-magnitude arm fails that anchor). Results are in the day record and `scorecard.md`.
- The zero arm scored 0.130 on B1, which exposed that centering alone rewards predicting a
  smaller-than-average response. Post-hoc direction metric added (`posthoc.py`), labelled.
- Anchor details showed SciPlex3 names with trailing whitespace; aminoglutethimide (A10) and
  prednisone (exploratory) had been skipped. Identity folded, an unmatched anchor compound now
  stops the audit by name, audit rerun; no conclusion changed.

## 13:22-13:28 Calibration and serving

- Cross-conformal coverage passed for every arm (0.803 to 0.805 at 0.80), but no Hallmark
  readout was narrower than the average-response arm's; only the response magnitude was
  (`knn_chem` width ratio 0.730). The rung serves that readout alone and refuses the rest by name.
- Library (`data/virtual_cell/sciplex3_signature_library/`, arrays SHA-256 `9378b050...`) and
  calibration built; end-to-end check: luminespib's own profile, excluded, retrieves HSP90 at
  cosine 0.70 (null 95th percentile 0.065); vorinostat, absent from SciPlex3, receives a
  calibrated magnitude prediction; panobinostat and a Hallmark readout are refused.
- Backend `sciplex_response` and CLI `--structures` added; `VirtualCellQueryTemplate` gained
  optional dose, dose unit and time.
- Full suite: 1297 passed (the 31 new tests are this session's: 7 identity markers, 7 retrieval,
  17 rung).

## 15:03-15:20 Second block: measurement choice for mechanism discrimination (orientation and freeze)

- A Codex session in this repository was used from 14:34 to 14:51 to draft the two task briefs of
  this block; it wrote nothing under `src/`, `tests/`, `tools/` or `research/` after 13:31.
  Full suite on the tree as found at 15:03: exit 0 (no failures).
- Audit finding that sets the block's scope: the Figshare SciPlex3 release also holds a **72 h**
  A549 cohort (47 compounds and vehicle, four doses, two replicates on plates 49 to 52, vehicle
  wells on each plate; 82,110 cells). Every 72 h condition also exists at 24 h. Cells are never
  observed twice, so the pairing is by condition, not by cell.
- Other local resources checked: `data/external/lincs_l1000_phase1/subset48/` (51,293 matched
  6 h / 24 h L1000 condition pairs, 978 genes, no mechanism annotation joined) and
  `data/raw/combination_sources/combo_sciplex.h5ad` (A549 drug pairs); neither is used here.
- 15:17 first preparation run finished its streaming pass and then stopped on a tuple key while
  writing its manifest; its output was renamed `FAILED_manifest_*` and the run repeated. No
  expression value was printed or read from it.
- **15:19:45 protocol frozen** (`research/dynamic_world_model/`), before any 72 h expression value,
  detection statistic, validator outcome or transition-model output was computed:
  - `PROTOCOL.md` SHA-256 `21590b1f2094de4991aa77253e9089d55c462c4dc19884ef90f0e6fe7edb05b0`
  - `protocol.json` SHA-256 `9cc1d331880f98ab5f3c60235566bae12351862bd342164743eb67cb455eb422`

## 15:20-15:28 Preparation and the registered episodes

- `prepare_time.py` (215 s): the 2250 frozen 24 h conditions reproduced to a maximum absolute
  difference of 2.8e-7; 182 A549 72 h conditions; identity guard 12 of 12 markers under the
  corrected labels; 45 wells below 20 cells excluded by name (14 at 72 h, all high-dose
  cytotoxicity: bisindolylmaleimide IX, dacinostat, mocetinostat, panobinostat).
- Detection thresholds from the vehicle-well null (frozen rule): A549 24 h 0.157, K562 0.107,
  MCF7 0.187, A549 72 h 0.297. The 72 h null has only 16 well pairs, so its 0.99 quantile is its
  maximum and 72 h detection is conservative.
- Implementation clarification made before any episode ran: the protocol's "wrong-elimination
  rate of at most 0.05" for calibrating the floor and margin is computed **among eliminations**
  (wrong / (correct + wrong)), the stricter of the two readings.
- A smoke test on three tier-A episodes printed only that it ran. The first full launch stopped
  on a syntax error from a string escape in a patch; nothing had run. The relaunch finished
  67,392 policy runs in 54 s (tier B 2160 contrasts, tier A 336; random averaged over 20 seeds).

## 16:01-16:12 Registered results, transitions and dyn_model

- P1 (tier B, separation minus magnitude): -0.044 [-0.083, -0.004], the opposite of the
  registered direction. P2 (tier A, dyn_ref minus magnitude): +0.054 [-0.039, 0.152]; dyn_ref
  minus fixed -0.190 [-0.292, -0.092].
- Post-hoc diagnostics, labelled: on episodes where separation did not defer it ties magnitude
  (tier B +0.004); its deferrals (13% of tier B, 22% of tier A) are where the loss comes from; a
  fixed 24 h then 72 h protocol beats magnitude in tier A by +0.244 [0.128, 0.372]; per class,
  DNA methyltransferase and BET inhibitors are never decisive at 24 h and mostly decisive at 72 h.
- `transition.py` (238 s): P3 met (gene ridge minus persistence, 72 h cosine +0.283
  [0.227, 0.336]); the forecast's nearest-template class is no better than persistence's.
- `dyn_model.py` (186 s): dyn_model minus dyn_ref +0.003 [-0.009, 0.018] in tier A.

## 16:07-16:30 Provider arms, and two defects they exposed

- Smoke run: DeepSeek 2 calls ($0.0014), Jev 16 calls (47,840 input tokens).
- The first full launch stopped in `deepseek_base` on a missing similarity score in the prompt
  formatter (a fold whose validator never eliminates carries none); 51 DeepSeek calls were
  logged. The relaunch was stopped at 16:14 because `agent_arms.py` never called
  `SpendLedger.write()`. The carry-in was reconstructed with
  `evaluation.provider_spend.price_usage` from the logged usage ($0.016066 over 53 calls) plus 12
  possibly in-flight calls at their $0.004 reservation, and the ledger is now written after
  every call. Aborted responses are kept as `responses_aborted_runs_1614.jsonl`.
- 16:17 relaunch: the three DeepSeek arms finished by 16:19. `jev_cards` then stopped on
  `http.client.RemoteDisconnected` raised out of `TypeSafeJevClient.evaluate`, whose contract says
  a transport failure is a refusal. Neither provider client caught connection-level errors.
  Fixed in `src/agent/typesafe.py` and `src/agent/llm.py` (retried, then refused or raised as the
  client's own transport error) with `tests/test_provider_transport_failures.py` (4 tests). The
  Jev arms were rerun with a carry-in of every logged Jev call (5,530,754 input tokens) plus one
  failed call's allowance (4,000); the results of the stopped launch were lost with its exception.
- P4 (both tiers, deepseek_cards minus deepseek_base): +0.006 [-0.058, 0.069]. DeepSeek without
  cards chose 72 h after an undetected 24 h result in 19 of 19 tier-A episodes and beat magnitude
  there by +0.190 [0.048, 0.333]; with cards it followed their refusals away from 72 h. Jev with
  cards chose the separation action sequence in 166 of 177 episodes and reached its outcome in
  all 177 (242 of 251 states stable); Jev without cards deferred in 63% of tier-B episodes.
- Repeatability: DeepSeek agreement 0.978 over 30 states asked four times.
- Spend for this block: DeepSeek $0.3955 in total (ledger, carry-in included), Jev 13,665,111
  input tokens ($0.5739). Laboratory cost: none; everything is retrospective.

## 16:18-16:33 Card audit, case study and report

- `card_audit.py` (about 20 min): served cards under-predict (tier B 0.231 predicted against
  0.303 realised, ECE 0.101; tier A ECE 0.154); refused actions were scored with a one-reference
  shadow estimate that is better calibrated (ECE 0.053), so the refusal protected nothing. P5 met:
  multi-branch minus single-mean log loss -0.599 [-0.774, -0.422] (tier B).
- `case_study.py`: anchor 1 held, anchors 2 and 3 failed as registered. In the closed-loop replay
  both DNA methyltransferase inhibitors were undetected at 24 h (retained at implementation
  scope, nothing eliminated) and matched each other's 72 h template (HDAC eliminated) under the
  fixed planner; the magnitude planner ended undetermined and dyn_ref deferred. Raw counts were
  re-extracted from the release for every executed assay and reproduced the prepared shifts
  (maximum difference 1.4e-7). Panobinostat at 72 h, 10 uM, lost both wells: `result_qc_failed`.
- Post hoc: a nearest-class reader with no gates would eliminate the true hypothesis on 26% of
  measurements (validator 1.3%); reading absence as "the perturbation failed" would be wrong on
  29% of measurements.
- `report.py` generated `measurement_choice_report.md`; `test_validator.py` 9 of 9 pass,
  including a rerun of one fold that reproduces its recorded episodes exactly.
- Full suite after the block: 1301 passed (the four added tests are
  `tests/test_provider_transport_failures.py`); `tests/test_repository_shape.py` passes with the
  two-block day record and the 21 new index entries.

## Block 3 (18:22 onward): prediction-to-measurement link

- 18:27 Working tree clean except `reference/` (untracked); block 2 was committed by the user as
  2b4b17c at 18:13. The latest Codex session on this repository (18:05-18:22) committed and
  pushed that block and drafted this task brief; it wrote nothing after 18:22.
- Baseline before any change: full suite 1301 collected, exit 0; subsystem tests (acquisition,
  selection, orchestration, world-model integration, outcome, cases, response rung) 113 passed;
  `research/dynamic_world_model/test_validator.py` 9 passed.
- Phase B, `research/acquisition_link/falsify.py --label before` (old code, synthetic inputs,
  no SciPlex3 outcome): power-aware selection ignored swapped predictions; a card reduced to
  detection power chose a p_wrong 0.3 action over a p_wrong 0 one; the magnitude tie-break chose
  the loud non-separating action; cost order kept a 72 h action out even with a large priority;
  a 72 h action's query stated 24 h and took its priority; a one-reference card left the
  objective. The new regression tests failed at import (the interface did not exist).
- Post hoc, from block-2 records only: step-2 wrong shares among eliminations were magnitude
  0.19, separation 0.12, dyn_ref 0.09, and 0.26 for the 234 step-2 choices driven by the
  `dyn_model` forecast, whose `p_correct` counted any elimination, wrong ones included.
- After the repair: the new file's 16 tests pass; full suite 1317 passed (1301 + 16).
- 18:59:44 Protocol frozen before any episode with the repaired selector or one-reference
  forecasts: `research/acquisition_link/PROTOCOL.md`
  sha256 69303c075b0efd0f3fc12e181c9fdb9cea8317a1b2a1b2720d215a58528a0c95,
  `research/acquisition_link/protocol.json`
  sha256 d858370810984ce700755e50c08ed82bee5e54f71a14323d4c44bdeb9e4f0fda.
- 19:02-19:03 Registered run, `research/acquisition_link/evaluate.py`: 29,952 episode records
  (12 arms including the oracle, 2,496 episodes) and 28,608 step-1 menu rows in 85 s. All seven
  consistency checks passed before any result was read (`production_before` = `cost_only`,
  `production_after` = `magnitude`, and `ec_cards_2ref`, `fixed`, `oracle`, `magnitude`,
  `cost_only` equal to block 2 episode for episode).
- Results: P-A (`da` minus `magnitude`, correct decisions) tier B -0.019 [-0.053, +0.017],
  tier A +0.033 [-0.030, +0.089]; wrong eliminations -0.012 and +0.018; served v2 forecast ECE
  0.058 and 0.085. Frozen verdict: INCONCLUSIVE. S1 (magnitude wired into the power-aware path):
  utility tier B +0.298 [+0.205, +0.388], tier A +0.060 [-0.086, +0.199], wrong eliminations tier B
  +0.044: the keep rule (both tiers excluding zero) is not met.
- 19:05 Following that rule, the orchestrator again leaves magnitude out of the power-aware path
  (it had been wired in by default before the run) and now logs `selection_path` and
  `prediction_priorities_used`; `DiscriminationPlan.payload` gained the rejection reasons. The
  wiring test was rewritten to pin the decision (18 tests in the file).
- 19:06 `falsify.py --label after`: the 72 h action is now queried at 72 h and gets no borrowed
  priority; power-aware magnitude stays unused by design.
- 19:07-19:09 Evaluation rerun on the final code: episodes and menu audit byte-identical to the
  registered run (kept under `outputs/acquisition_link_20260926/run1_before_payload_change/`);
  report and summary identical.
- 19:11-19:13 Result records copied to `log/20260926/0926/acquisition_link_*` and declared in the
  index. Four working copies found with CRLF endings were normalised to the LF `.gitattributes`
  declares, and `log/INDEX.md`, briefly rewritten with CRLF by this block, was restored to LF.
  The report writer now writes LF; a quoting slip in that edit broke `analyze.py` once (syntax
  error, nothing written), and the regenerated report equals the log copy byte for byte.
- 19:20 Review of the runtime diff: a skipped foreign-context query is now logged by name
  (`virtual_cell_query_not_built`), the per-session discrimination plan is consumed once read, and
  the orchestrator summary names the option; one test added (19 in the file).
- Final checks: full suite 1320 passed (1301 + 19); `research/acquisition_link/test_acquisition_link.py`
  4 of 4 (including a one-fold rerun); `tests/test_repository_shape.py` passes with the
  three-block day record. No provider or API call was made in this block.

## Block 4 (21:52 onward): stopping gap and independent sequence validation

- 21:52 Orientation. The HEAD is `97c8e28`. The Codex follow-up (20:31-21:01) is uncommitted in
  `research/acquisition_followup/` and in seven modified files, and was kept as found. A Codex
  session active at 21:52 was working on a remote server, not this tree. The follow-up's recorded
  source hashes match the current files.
- 21:58-22:01 `diagnose.py`: all 2,496 recorded plans per arm were recomputed with the follow-up's
  own `plan_two_step`, with 0 mismatches. Every stop after a neutral first reading was
  attributed. In tier A, 106 of 147 stops broke down as 52 thin support, 37 no paired references,
  8 wrong risk and 9 no gain. By two-step path, the fixed sequence's +0.274 was +0.140 from
  neutral stops, +0.074 from deferrals and +0.018 from QC stops.
- 22:10 `diagnose.py` now imports the audit functions from `policies.py`. Its outputs are
  byte-identical, with the same SHA-256 before and after.
- 22:11-22:14 Phase 2 matched replay, 39,936 records. The five arm-rule pairs whose original
  rules already matched reproduce the original records, 2,496 of 2,496 each. Two-step minus fixed
  in tier A was -0.259 [-0.360, -0.161] under `continue` and -0.250 under `stop`.
- 22:15-22:17 `lincs_prepare.py` (metadata and cache only). The first run stopped on perturbagens
  absent from `pert_info` and wrote nothing. The rerun found 21 LT classes, 344 compounds and
  6,880 episodes, and 15 T classes, 218 compounds and 3,052 episodes. Cache-versus-official
  signature strength: Spearman 0.595. The six GEO metadata files match GEO's SHA-512 sums.
- 22:19-22:21 `test_sequence_audit.py`: 18 tests pass, including the ported planner against the
  original on every contrast of two SciPlex3 folds.
- 22:23:12 Protocol frozen (`freeze.json`). No L1000 validator reading, forecast or decision had
  been computed, and the revision had not run anywhere.
- 22:24-22:27 `lincs_evaluate.py`: the gate passed in 5 of 5 folds in both tiers. It wrote 79,456
  records and 61,144 menu rows, and every record passed `audit_record`.
- 22:26-22:28 SciPlex3 exploratory replay with the revision: 44,928 records.
- 22:28 `lincs_analyze.py`: fallback minus two-step utility in LT was +0.0013 [+0.0002, +0.0026],
  and wrong eliminations +0.0001 [0.0000, +0.0005]. Fallback minus fixed was +0.014
  [-0.012, +0.041]. Frozen verdict: SHADOW.
- 22:31-22:36 Post-run review.
  - 32 LT episodes stopped after a fallback first measurement although the audit found a
    supported positive continuation. A new test pins this behaviour; the rule was not changed.
  - The first version of that test built the wrong scenario, failed, and was rewritten.
  - Added: a one-fold L1000 rerun (identical records) and the record audit over every L1000
    record.
- 22:37 Final checks.
  - `test_sequence_audit.py`: 21 of 21.
  - Related research tests: 43 of 43.
  - Full suite: 1,326 passed, in the `maestro` env.
  - The follow-up's README is Chinese (51 lines); it would fail
    `test_project_markdown_has_no_chinese_prose` once tracked. Recorded, not changed.
- No provider or API call was made in this block, and laboratory cost is 0.
