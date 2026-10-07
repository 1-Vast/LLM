# Phase 2 access log (agent C)

Authorised by the coordinator for this task only: Jaaks outcome columns of the 64 HD lines and `results/mono_labels.csv.gz`. E outcomes must not be read or used.

## How E was kept out

`VERIFY_lib.load_hd` wraps the frozen builder's `_read` (`jaaks.py`). Immediately after the CSV is parsed and before any computation, every outcome column (`SYNERGY_DELTA_EMAX`, `SYNERGY_OBS_EMAX`, `SYNERGY_RMSE`, `LIBRARY_RMSE`, `Synergy`) of rows whose SIDM is in the E partition is overwritten with a constant that passes QC (150,922 rows). E rows are masked, not dropped, because the contract's tie-break uses the line's position in the builder's per-tissue line tuple; dropping E rows would change the HD tie-break ranks. After the panels are built, `assert_e_masked` verifies that every E label is 0 and no E call is True (3,652 / 3,647 / 2,351 rows for Breast / Colon / Pancreas). No E outcome value survives the read. The study's own `access_log.jsonl` was not written; this phase logs to `VERIFY_access_log.jsonl` through the same `open_vault` (freeze hashes intact at every opening: freeze sha256 7223bf7e...).

E-line GDSC2 mono labels sit in `mono_labels.csv.gz`; they were used only to count training-pool membership (`VERIFY_3`) and were never used as features or targets in any analysis. Design columns (SIDM, CELL_LINE_NAME, COSMIC_ID) of the original and validation Jaaks CSVs were read to re-derive the Jaaks identity sets.

## Reads (from `VERIFY_access_log.jsonl`)

| # | Time (+0800) | Source | Purpose / script |
|---|---|---|---|
| 0 | 03:16:57 | Jaaks CSV (HD, E masked) | `VERIFY_1_reproduce.py` simple rankings, D_add |
| 1 | 03:19:50 | `mono_labels.csv.gz` | `VERIFY_3_wiring.py` leakage re-derivation, retrain, own table |
| 2 | 03:20:05 | Jaaks CSV (HD, E masked) | `VERIFY_3_wiring.py` own-mono wiring, poisoning |
| 3-4 | 03:22:57-58 | mono + Jaaks | `VERIFY_5_info.py` information test, regularisation sweep |
| 5-6 | 03:25:28-29 | mono + Jaaks | `VERIFY_6_ceiling_curve.py` first run (aborted on a sampling-size error before any output; no result used) |
| 7-8 | 03:25:41 | mono + Jaaks | `VERIFY_6_ceiling_curve.py` rerun after fixing the history sizes |
| 9-10 | 03:26:20-21 | mono + Jaaks | `VERIFY_7_own_sweep.py` |
| 11-12 | 03:27:25-26 | mono + Jaaks | `VERIFY_7b_own_subset_match.py` |
| 13-14 | 03:28:07-08 | mono + Jaaks | `VERIFY_8_own_full.py` |

Not an outcome read: `VERIFY_4_contrasts.py` uses only `results/s2_dev_records.pkl`, `s2_dev_selection.json`, `s2_dev_summary.json`, `s2_gates.json`.

Nothing outside `decisions/` was written; no API call; no Vis file; no E outcome.
