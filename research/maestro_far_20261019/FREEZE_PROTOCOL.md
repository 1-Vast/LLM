# MAESTRO-FAR dev-arena realisation: frozen before the test folds (written 2026-10-19 after search and select)

Amends `PROTOCOL.md` for the arena built in `far_data.py` (PRISM 19Q4 primary x L1000 landmark signatures x ECFP4; 848 dev drugs, 242 chemistry/MoA-connected
families, 5 family folds). Search = folds 0,1; select = fold 2; test = folds 3,4 (references 0,1,2 and the other test fold; test outcomes were never read
before this file). Everything is exposed PRISM data: internal development assessment only.

Search/select facts already observed (not test): failure signatures (domain distance, neighbour dispersion, model disagreement) have held-out AUROC 0.47-0.50;
a gradient-boosted expected-benefit model had cross-fit correlation ~0; on fold 2, FAR (signature model) minus exploit-first = -0.013 [-0.028, -0.004], FAR-v2
(benefit model) minus exploit-first = -0.020 [-0.038, -0.007]; strongest baseline on select = exploit-first.

Frozen test decisions (all proposed gates now fixed):
* Primary repair = `gate` (transfer if top L1000 similarity >= tau=0.258, else base). Equal cost: 4 of 16 equal-size slices (25% of the pool) for every policy.
* Phase 1 gate: >= 2 of 3 signatures with test AUROC lower 90% bound > 0.60 (family-cluster bootstrap, 600 draws).
* Phase 2/3 primary contrasts, family-cluster bootstrap (4,000 draws, stratified by fold), practical threshold 0.010 utility (log2FC of selective killing per
  nomination, about 25% of the random-slice assay+repair gain seen in search), one-sided 95% lower bound: C1 = far.gate - exploit.gate, C2 = far2.gate - exploit.gate.
  Holm over {C1, C2}. FAR is "supported in this arena" only if a contrast passes.
* Secondary (descriptive, no claim): each FAR policy vs random/coverage/poh; assay+repair vs none; repair variants; all-slices ceiling; split-line oracle (slice value
  reproducibility); hits per nomination.
* If neither primary contrast passes: no agent phase (Phase 4), no 2x2 (Phase 5), no transfer claim (Phase 6). Phase 7 = one reused-vault check only (block-N drug names;
  opened once by block N, so not independent).
No LLM, no paid call is used in this realisation.
