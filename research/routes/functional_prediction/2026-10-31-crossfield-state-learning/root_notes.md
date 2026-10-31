# Coordinator source and correction notes

## Primary sources read

- Hafner et al., *Mastering diverse control tasks through world models*, Nature (2025), DOI 10.1038/s41586-025-08744-2. Crossref identity/date and original publisher full HTML retrieved. Reading level P: World model section (RSSM encoder/recurrent/dynamics/reward/continue/decoder equations and three losses), Critic learning opening, Fig.6 learning-signal ablation passage. The paper says reconstruction is predominantly responsible for performance in its ablation. No results reproduced. Thus no claim that task-only latent losses universally dominate reconstruction.
- Elmachtoub & Grigas, *Smart Predict, then Optimize*, Management Science (2022), DOI 10.1287/mnsc.2020.3922; read original arXiv:1710.08005v5 (19 Nov 2020) PDF pp1-5. Crossref identity verified. Decision regret loss, SPO+ surrogate and continuous/symmetric conditional-cost consistency premise read; full proofs not read. Theory is for coefficients of a stated linear objective and feasible set, not a biological causal law. No algorithm run.

Original response bytes, URLs, SHA256, UTC retrieval timestamps and errors are in root_receipts.jsonl/root_sources. Local preprocessing initially lacked bs4 and fitz in maestro; recovered using Python stdlib HTMLParser and already-installed system Python PyMuPDF. No packages installed. This is document reading, not scientific fitting.

## Static replay correction (source inspection, not rerun)

The previous MVP all-arm replay is not a valid all-arm equivalence test as written. Directly reading mvp_run.py and VERIFY_FULL_61/replay_full.py shows:

1. Main runner learns top-five directions separately per option from reference covariance. Replay learns one flattened PCA over all 18 options and removes its first five directions. These are different algorithms.
2. Main runner PCA/random/full-flat arms consume the per-option GAT residual. Replay consumes centered raw signatures for these arms. Again different inputs.
3. Main primary hit precision is overlap between predicted and observed most-sensitive residualized top-10% sets. Replay chooses the largest predicted residual (wrong sign for sensitivity) and counts raw LFC<=-1 rather than observed top-set overlap. Regret shares the reversed choice sign. The identical raw/ridge predictions therefore coexist with mismatched primary metrics.
4. Replay treats zero fingerprints as zero similarity, allowing fallback neighbors, whereas main marks them missing. This explains the stated singleton discrepancy at the implementation level.

These are confirmed static implementation differences, not evidence of biological non-reproducibility. The first verifier's limited PASS remains its recorded scope; full arm reproduction remains unresolved. No frozen artifact or historical VERDICT was overwritten, and no new scientific run was executed. The previous report's sole attribution to protocol ambiguity should be read as superseded by this diagnosis.

## New candidate direction from the transfer

Candidate v1: functional challenge panel as a cell-state observation operator. Start with a finite drug decision menu and later functional outcomes, learn a small panel of standardized diagnostic perturbation responses and a readout of the whole action-outcome vector. The scientific question is whether response-to-challenge carries future susceptibility information that passive state and ordinary equally informed response-panel completion fail to retain, across unseen histories/chemotypes and preparations. This does not claim new PSR, VIB, active learning, or response-panel completion. The vulnerable difference is authenticated state/history closure and transport to a later action, compared with strong direct history/ridge/conditional models.

Constructive reasoning only: two surviving populations can have the same current count and early RNA summary but different recovery after washout or susceptibility to a second drug. A diagnostic response can separate them if it actually differs before the final decision and is measured on exchangeable sister cultures. If all allowed diagnostic responses are the same, the ambiguity persists and no encoder repairs it. Sister-culture exchangeability and perturbation carryover must be tested, not assumed. The same cell cannot receive all mutually exclusive destructive assays; the panel is a preparation/population-level predictive state, not an identified single-cell latent state.
