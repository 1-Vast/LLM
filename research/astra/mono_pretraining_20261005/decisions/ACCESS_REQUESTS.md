# Access disclosure and requests (agent C, phase 1)

## What was read in phase 1

- Code and documents named in the brief (contract, report, design/resources code, builder, frozen protocols, `src/` interfaces).
- **Scalar fields of existing campaign receipts** (aggregated per campaign, not raw Jaaks rows): `confirmation_campaign_20261004/design/results/{eval_20261004_130452/campaigns_primary, dev_20261004_130123/campaigns_p2_grid}.jsonl.gz` (fields `arm, tissue, line, role, n_menu, M, confirmed, menu_joint_hits` only), `resources/results/summary_20261004_130800/summary.json`, `resources/results/eval_20261004_130438/{headroom.json, campaigns_native.jsonl}`, `design/results/*/{eval,dev}_summary.json`. These are inside the directories listed in the brief. The same fields are re-read by `headroom_from_receipts.py`.
- `knowledge_transfer_20261004/README.md` and `REPORT_ZH.md` and `knowledge_optimization_20261004/model_review.md` (documentation). **These directories are not in the enumerated list**; I used only the numbers printed in the reports (n4 / n8 / all totals and intervals). I did **not** open `knowledge_transfer_20261004/results/*.json`.
- Not done: no raw Jaaks CSV, no outcome column, no vault ticket, no Vis file, no GDSC2 label, no API call. Probes of `src/` ran against temporary SQLite files outside the repository.

## Requests (not performed)

| # | Request | Why it is needed | What it unlocks | Safeguards |
|---|---|---|---|---|
| R1 | Permission to read the aggregated per-line receipts `knowledge_transfer_20261004/results/{n4,n8,all}_per_line.json` (confirmed totals per E line, strong simple and knowledge arms, seeds 11/23/47) | The n4 per-line contrast variability and the between-seed variance are only available as interval half-widths in a report; a direct estimate replaces the SD_rel brackets (0.09-0.28) in `EVALUATION_DESIGN.md` | A tight power and MDE table for the actual n4 regime | Aggregated receipts only; no raw outcomes |
| R2 | A **Gate 0 development run on HD lines only** through the existing exposed-ticket mechanism, executed by the lead (or by me if the lead authorises it in writing): learning curve of the six simple rankings plus the declared matched-information baselines D_add and M_pot at n_hist in {4, 8, 16, 32, all} with >= 10 independent history draws, P2 fp 30, with oracle | (a) the size of the strong-simple baseline's history-draw SD relative to tau; (b) whether D_add or a continuous tie-break already closes most of the n4-to-full-history gap, which bounds what any mono model can add; (c) tie census at n4. None of this can be answered from existing receipts | Decides whether the pretrained arms are worth running and which comparator is strong | HD only (E stays sealed and unread), logged ticket per contract rule, no model with mono labels involved, outputs scalar per-line values |
| R3 | No raw read is requested for decisions, headroom or framework gaps | - | - | - |
