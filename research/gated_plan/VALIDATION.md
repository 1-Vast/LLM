# Validation record

Commands actually run in block 4 (2026-09-27, +0800), with their results. Times are approximate, read from tool output or file times. The environment is Windows 11 with Git Bash.
`python` is `C:\Python314\python.exe`. Research modules were run with `PYTHONPATH="D:/MAESTRO;D:/MAESTRO/src"`.

## 1. Commands and results

| # | Time | Command | Result |
|---|---|---|---|
| 1 | 13:32 | `git status --short`; `git log --oneline -5`; `git show --stat HEAD` | `main` at `e5ad68f` (the owner's commit of block 3, 12:55). Untracked: `inspect/`, `reference_0927/`, `research/prompt_review_20260927/`. |
| 2 | 13:33 | Read `~/.codex/sessions/2026/09/27/*.jsonl` (session metadata and user messages only) | Three concurrent Codex sessions: <br>• 12:00-13:49: group-meeting slides; created `inspect/` and `reference_0927/`. <br>• 13:25-13:32: revised the owner's prompt; wrote `research/prompt_review_20260927/`, the source of this brief. <br>• 13:31 onwards: read-only novelty assessment. <br>None touched this folder. |
| 3 | 13:37 | Python: raw SciPlex3 `obs` counts for the 12 conditions absent from `conditions.csv` | All 12 were profiled (6-18 cells per replicate) and dropped by the 20-cell rule. |
| 4 | 13:44 | Python: Murcko scaffolds of SciPlex3 compounds by fold | 12 scaffolds (30 compounds) span folds; 0 of 180 skeletons do. |
| 5 | 13:46 | `python -m research.gated_plan.probes --out outputs/gated_plan_20260927/probes.json` (26 s) | Six results, listed below. |
| 6 | 13:52 | `PYTHONPATH=D:/MAESTRO/src python -m evaluation.cli --public-cases data/evaluation/cases/engagement_v1/public --private-results data/evaluation/cases/engagement_v1/private --capabilities data/evaluation/capabilities/engagement_capabilities_v1.json --manifest data/evaluation/derived/engagement_case_manifest_v1.json --policy repair --mode decision --output outputs/gated_plan_20260927/engagement_replay --state-root outputs/gated_plan_20260927/engagement_replay/state --run-id gated-plan-engagement-20260927` (2.6 s) | 6 cases, 6 offline arms, 0 provider calls. Table in section 2. |
| 7 | 13:48 | `python -m pytest research/protocol_v2 -q -p no:cacheprovider -o addopts=""` | 24 passed (67.8 s) |
| 8 | 13:49 | `python -m pytest tests/test_outcome_decision.py tests/test_audit_regressions.py tests/test_prediction_reliability.py tests/test_engagement_licensing.py tests/test_discriminating_acquisition.py -q -p no:cacheprovider -o addopts=""` | 123 passed (6.1 s) |
| 9 | 13:49 and after the last edit | `python -m pytest tests/test_repository_shape.py -q -p no:cacheprovider -o addopts=""` | 9 passed |

**Probe results (step 5):**
- **Historical claims:** fixed/oracle 63.3-99.4%.
- **GSE70138 cohort:** 686 new compounds, 673 metadata-eligible, 613 units.
- **Menu leak:** `menu_moves_with_outcome: true`.
- **Evidence path:** only a real, condition-matched record eliminates. Two unregistered citations of one experiment count as 2 clusters; with a registered cluster they count as 1. A lysate grant satisfies an engagement premise that names no site.
- **Validator:** an undetected reading eliminated nothing in 2,000 trials; the reference-absence branch eliminates with 2 references.
- **Splits:** 12 scaffolds span SciPlex3 folds.

**Failed attempts, kept for the record:**
- Step 6 without `PYTHONPATH` failed with `ModuleNotFoundError: evaluation`.
- Step 6 with `--costing data/evaluation/costing/real_record_retrieval.json` failed with
  `costing_entry_matches_no_action:orthogonal_context_control`. That overlay belongs to another package; engagement_v1
  prices its own actions (0 wells, 0 days), so the rerun omitted it.

## 2. Engagement replay (step 6)

Verdicts are relative to the package's licensing rules. "Registry verdict" asks what the capability registry makes
reachable.

| Case (context) | fixed_expert | outcome_aware | maestro_core | registry_repair_rule (A1) | registry_expanded_selection (A0a) | registry_repair_random |
|---|---|---|---|---|---|---|
| ABL1 / dasatinib (K562) | continue, 1.0 | continue, 1.0 | continue, 1.0 | **revise_attribution**, 1.0 | continue, 1.0 | continue, 1.0 |
| ATR / VE-821 (K562) | defer*, 2.0 | defer*, 0 | defer*, 0 | revise_intervention, 1.0 | revise_intervention, 1.0 | defer*, 2.0 |
| BRD4 / JQ-1 (K562) | defer*, 3.0 | defer*, 2.0 | defer*, 1.0 | change_intervention_mode, 1.0 | change_intervention_mode, 1.0 | defer*, 3.0 |
| CDK1 / AZD-5438 (K562) | defer*, 3.0 | defer*, 2.0 | defer*, 1.0 | revise_intervention, 1.0 | revise_intervention, 1.0 | defer*, 3.0 |
| MTOR / AZD2014 (MCF7) | defer, 2.0 | defer, 0 | defer, 0 | defer, **2.0** | defer, 0 | defer, 2.0 |
| MTOR / OSI-027 (K562) | defer*, 3.0 | defer*, 2.0 | defer*, 1.0 | revise_intervention, 1.0 | revise_intervention, 1.0 | defer*, 3.0 |
| Mean cost | 2.33 | 1.17 | 0.67 | 1.17 | 0.83 | 2.33 |

\* over-deferral under the registry verdict. All 36 case-arm pairs are "correct" under the menu licensing rule; zero
wrong development actions.

**What this shows:**
- **Registry access changes decisions.** The engagement capability changes 4 of 6 decisions relative to the menu-only
  arms.
- **The repair step adds nothing on these cases.** Given the same capabilities, A1 and A0a agree wherever A1 decides.
- **Where they differ:**
  - ABL1: A1 reaches a different licensed decision (revise_attribution); A0a's decision (continue) is the one the
    independent kinobeads test calls "consistent".
  - MCF7 (AZD2014): A1 spends more and still defers.

## 3. Checks not run, and why

| Check | Why not |
|---|---|
| Full production suite (`tests/`) | No file under `src/` or `tests/` changed. The last full run (block 3): 1,336 passed, 5 failed, all caused by the other session's `inspect/` directory (see `log/20260927/0927/protocol_v2_run_notes.md`). |
| Full research suite (143 tests) | No research module changed; only `research/gated_plan/probes.py` was added, and it is not a test. The `protocol_v2` subset was run. |
| The 516 single-MoA count for GSE70138 | Needs the consumed study's labels. The count is carried from protocol v1's vault run, not re-executed. |
| LINCS 2020, CPJUMP1 and Tahoe-100M census | No download approval (the brief does not authorise downloads). |
| Online resolution of the contribution-card citations | Titles, venues and DOIs of Fikes & Nilsson 1971, Reiter 1987, de Kleer & Williams 1987, Lindley 1956, Howard 1966, Chow 1970, King et al. 2004, Golovin, Krause & Ray 2010, van der Krogt & de Weerdt 2005, Fox et al. 2006 and Chandrasekaran et al. 2024 were **not re-resolved in this block**. Rainforth et al. 2024, Geifman & El-Yaniv 2017 and Ahlmann-Eltze et al. 2025 were resolved in `research/protocol_v2/LITERATURE.md`. Resolve the others before any publication. |
| Blind adjudication of the engagement replay | Not a claim-bearing run; the preregistered adjudication applies to a registered stage-1 run. |
| Registration of E-DATA1 or E-CAL1 | The tree is not clean: the untracked files belong to other sessions and to this folder. Registration requires a commit. |

## 4. Unresolved limits

- **Proxy task.** The historical numbers describe the transcriptomic MoA proxy task only. They do not bear on the
  prerequisite-repair claim.
- **Tiny agent sample.** The only real prerequisite task has 6 cases and 5 target clusters.
- **Unmatched engagement.** The engagement capability is not condition-matched to the phenotype, and `not_engaged`
  has no measured sensitivity.
- **Calibration base.** Calibration evidence rests on two development studies.
- **No boundary against same-user code.** Process separation for sealed data does not exist yet. Controls against
  code running as the same user are detective (digests, logs), not preventive.

## 5. Next justified action

Owner decisions, in order:
1. Commit this folder (and decide on the other sessions' untracked folders) so experiments can be registered.
2. Authorise MINIMAL_IMPLEMENTATION for P0-1 to P0-3, or not.
3. Approve, or refuse, a metadata-only CPJUMP1 and LINCS 2020 census.

Without these, the only runnable next step is E-AG1 stage 0 (a local premise-only census) and E-CAL1 as an
exploratory analysis labelled unregistered.
