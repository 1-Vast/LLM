# mono_pretraining_20261005 — study plan (append-only; lead agent owns this file)

Question: does public single-drug (GDSC2 fitted LN_IC50) supervision supply transferable *action-comparison*
information for ranking anchor x library combinations in a new cell line when combination history is sparse,
beyond (a) a development-selected strong simple ranking, (b) the same architecture trained from scratch,
(c) mono-pretraining with drug- or cell-mapping permuted?

Ownership (no agent edits another's folder):
- `literature/`  agent A  - related-work matrix, novelty assessment, evaluation-design lessons
- `data_s0/`     agent B  - S0 metadata/identity/unit/QC/overlap contract; NO label values read
- `decisions/`   agent C  - decision-space headroom, matched-budget arms, verification plan
- lead           - integration, freeze, model/experiment code (`src_*.py`), report, promotion

Hard rules: no GDSC2 LN_IC50/AUC/RMSE/Z_SCORE value read before `FREEZE.json` exists; no Vis outcomes; no commits;
no secrets in logs; every outcome read goes through a logged access (`access_log.jsonl`).
