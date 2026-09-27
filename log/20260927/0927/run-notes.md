# Run notes, 2026-09-27 (external-validation block)

All times are local (+0800). File modification times in `research/external_validation/` confirm
the order.

**Before the freeze:**
- **23:54 (2026-09-26): state of the tree.** The tree was clean at `d011fcd`, where the owner had
  committed blocks 1–4 and the Codex sparse-value work.
  - The active Codex session was working in `D:/SASG-ST`.
  - The Codex session that touched MAESTRO (drafting this brief) completed at 23:53 and left
    nothing uncommitted.
- **00:00–00:08: local candidates for an unseen study.**
  - Tahoe subset `c39.h5ad`: only its obs metadata was read, never its expression.
  - sciPlex-GxE: only the text sample sheets were read.
  - The Tahoe-100M licence (CC0 1.0) and the GSE70138 and GSE92742 file listings were read from
    their public pages. Nothing was downloaded.
- **00:10: `protocol.json` written.** `firewall.py` was also written then.
- **00:15: package layout.** Naming the module `statistics.py`, as the brief asks, would shadow the
  standard library for `src/maestro/tool_analysis.py` and `src/virtual_cell/pathway_readout.py`.
  The directory became a package run with `python -m`.
- **00:18: first smoke check failed on L1000.** `episodes.lab_cost` carries SciPlex3's day table
  and raised `KeyError: 6.0`. It was replaced by the same well rule without the day table (two
  wells per measurement, four shared vehicle wells per new line and time).
  - The re-run gave 87 records per task and 0 violations.
  - Only counts were printed.
- **00:23: manifests written.** They passed schema checks, and no compound or group crosses a fold.
- **00:25: contract tests.** 24 passed and 2 skipped (freeze, reproduction). They assert structure
  only.

**The freeze and the registered run:**
- **00:27:22: `freeze.json` written.** It holds 56 file digests.
  - Git head was `d011fcd`; the new module was uncommitted.
- **00:27–00:32: registered replay.** 20 tasks, 29 arm settings, 8 workers: 360,412 records and 0
  integrity problems.
- **00:28–00:30: descriptive report code written** (`risk_audit`, `calibration_audit`,
  `paired_ablation`, `report`), while the replay ran and before any result was read.
- **00:33: `report.py` applied the frozen gates.**
  - Overall REJECTED: SciPlex3 B and L1000 T REJECTED, SciPlex3 A and L1000 LT INCONCLUSIVE.
  - The external comparator frozen in `baseline_selection.json` is `fixed`.
  - Newton overflow warnings came from logistic calibration fits in small, perfectly separated
    strata; those strata's intercepts and slopes are unreliable.

**Checks after the run:**
- **00:34: cross-checks against earlier independent runs.** All reproduce exactly:
  - fixed in SciPlex3 A: 0.640 / 0.057 / 1.63 (block 4);
  - production in SciPlex3 B: 0.172, and magnitude there: 0.558 (block 3);
  - sparse two-step in L1000 LT: 851 of 6,880 correct and 27 wrong (Codex sparse-value).
- **00:35: tests.**
  - External-validation tests: 26 of 26 passed, including freeze verification and an exact rerun
    of L1000 T fold 1.
  - Research tests: 68 passed.
  - Full suite: 1,325 passed and 1 failed, `test_project_markdown_has_no_chinese_prose`. It fails
    on the two committed Chinese READMEs (`research/acquisition_followup/README.md`,
    `research/sparse_value/README.md`) from the Codex session. They are reported and left
    unedited.

No provider call was made. Laboratory cost was 0 wells.

# Run notes, 2026-09-27, block 2 (belief planning and the first external test)

**Audit (02:59-03:10):**
- **02:59: brief received.** A Codex thread wrote it (02:57-02:59) and the owner pasted it.
- **03:00-03:05: state of the tree.** `git status` and the Codex session logs in
  `~/.codex/sessions/2026/09/27/` show three Codex turns from 00:59 to 02:56 (the last was
  interrupted). Among the files they touched:
  - `freeze.json`, regenerated at 02:53:48;
  - `l1000_T_1.jsonl.gz`, rewritten at 02:52:44;
  - six frozen block 1 files.
  Nothing was reverted.
- **03:07-03:16: GSE70138 downloaded.**
  - The metadata came first.
  - Then the Level 5 file (5.37 GB, 313 s, 12 range connections). Its SHA-512 matches the
    series list.
  - 03:10: `sig_metrics` was loaded once to list its column names only.
- **03:17-03:36: GSE92742 Level 5 downloaded** (21.3 GB, SHA-512 match), for the strict-design
  feasibility check only.

**Development iterations** (development data only; outputs in `outputs/belief_planning_20260927/dev/`):
- **03:18-03:33 v0** (fixed priors):
  - belief against fixed: A 0.509 vs 0.640; B 0.584 vs 0.582; LT 0.126 vs 0.106; T 0.219 vs 0.230;
  - the virtual cell masked equals on.
- **03:45 v1.** Per-fold empirical-Bayes fit, and unit-left-out readings (which moved pooled rates
  by under 0.005).
- **03:59 v2.** Factorised world model: worse (A 0.464, B 0.558), not used.
- **04:05 v3.** Anchoring: the anchored agent equals fixed on SciPlex3.
- **04:07-04:26: strict cross-study design checked on Phase I.** 266 complete labelled compounds,
  4 pool classes, 96 episodes; not run.
- **04:13: external manifest written** from metadata. 1,053 references; 673 new test compounds
  (613 units); 0 identity overlap with development; no shared batch.
- **04:05-04:20 v4.** All controls.
  - The first start crashed: a permuted-feedback substitute could be an eliminating label. The
    control was fixed to use compatible (non-eliminating) partner readings.
  - The rerun was stopped at 04:20 once the design was clear.

**Freeze and the registered runs:**
- **04:20-04:35: final tests before the freeze.**
  - Production: 1,341 pass.
  - Belief-planning contract tests: 10 pass, including every registered arm on a synthetic
    external study with invented measurements and labels.
- **04:35:20: `research/belief_planning/freeze.json`** (54 digests).
- **04:35:36-04:55:44: registered development replay.** 298,272 records, 0 problems.
- **04:35:44: vault opened.** 04:35:44-04:38:53: study opened. Pool of 11 classes, of which 38
  test compounds are eligible (380 episodes).
- **04:38:53-04:40:39: external replay, once.** 9,120 records, 0 problems.
- **04:4x: frozen analysis on the external records.** `belief` vs `fixed`: -0.024
  [-0.074, +0.011], INCONCLUSIVE.

**Checks after the runs:**
- **About 05:00: reproducibility.**
  - SciPlex3 A fold 1 reruns identically in Python 3.11.16 and 3.14.4 (maximum difference
    3.1e-15).
  - The external replay reruns identically from its pickle.
- **About 05:00: research suite.** 117 of 119 pass. The 2 failures are block 1 tests, broken by
  the coherence fix to the Codex function (its post-hoc freeze lists `acquisition.py`; the
  rewritten fold's `decision_sensitive_edv` records moved: 65 of 588).

**Costs.** No provider call was made. Laboratory cost was 0 wells.
