# Dual-core iteration: run notes (block 7, 2026-09-27)

**File summary**
- **Path:** `log/20260927/0927/dual_core_run_notes.md`
- **Purpose:** the command sequence, timings and integrity checks behind block 7. The report is
  `research/dual_core/README.md`.
- **Core points:** E1's keep rules passed with small effects; E2 found no risk control on held-out units and no
  selected-action gain from the in-context world model; the reference arm reproduced E-DATA1 exactly.

## Sequence (Asia/Shanghai)

| Time | Step |
|---|---|
| 21:55 | Tree and concurrency check: blocks 5-6 uncommitted; the Codex session that wrote this brief made no change after block 6. Hardware inspected (20 cores, 15.8 GB RAM, RTX 4060 present but PyTorch is a CPU-only build) |
| 21:57-22:05 | Six DOIs resolved via bioRxiv and Crossref; State found peer-reviewed in Cell (doi:10.1016/j.cell.2026.07.052); Stack PDF is v2; SCALE v2 exists and was not inspected. Prior-art searches; 17 further identifiers verified |
| 22:04-22:10 | `splits.py` written; split manifest produced. Fold identifiers 0-4 confirmed; no declared unit spans folds; 10 SciPlex3 Murcko scaffolds (26 compounds) do span folds and become a stratum |
| 22:10-22:16 | `transfer.py` and `e1.py` written; 5 synthetic tests pass; execution-only smoke run on L1000 fold 0 (169 s, counts only) |
| 22:17:22 | **`protocol.json` frozen** with code, prepared-data and split hashes, before any E1 score |
| 22:18-22:27 | E1 run: 10 (dataset, fold) jobs, 4 workers, about 9 minutes. Agent side written (`ledger.py`, `world2.py`, `agent.py`, `e2.py`); 10 tests pass |
| 22:27-22:29 | E1 analysed. Both keep rules pass on both datasets, so `rrt_q` and precision aggregation enter E2 |
| 22:29-22:30 | Execution-only E2 smoke runs (L1000 T fold 1, SciPlex3 A fold 2); a prompt-kernel cache added after the first showed repeated recomputation |
| 22:30:12 | **`protocol_e2.json` frozen**, after E1's analysis and before any E2 score |
| 22:30-22:41 | E2 run: 20 tasks, 4 workers, about 11 minutes; 0 problems; 480/480 live abstention checks matched truncation |
| 22:41-22:55 | E2 analysed; reference-arm reproduction check; post-hoc binding-alpha and power analyses |
| 22:55-23:10 | Report, log block 7, index, memory; test suites rerun |

## Integrity checks

- **Reference arm versus the registered run:** 6,601 of 6,601 E-DATA1 `belief` episodes have identical action
  sequences (`outputs/dual_core_20260927/e2/reference_reproduction.json`).
- **Sealed view:** `public_view_problems` and `audit_trace` returned nothing for all 20 tasks.
- **Live abstention equals exact truncation:** 480 of 480 replayed episodes.
- **Strict nesting:** a test spies on every transition fit during the empirical-Bayes search and asserts each uses
  exactly the inner-training folds.
- **Ledger refusals** are exercised for target, future, unpurchased, QC-failed and identity-mismatched prompts.

## Files copied here

- `dual_core_split_manifest.json`
- `dual_core_e1_analysis.json`
- `dual_core_e2_analysis.json`
- `dual_core_e2_posthoc_power.json` (post hoc)
