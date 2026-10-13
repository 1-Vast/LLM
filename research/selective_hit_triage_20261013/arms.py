"""Triage arms: each turns the pair evidence of a campaign into budgeted nominations.

File summary
- Path: research/selective_hit_triage_20261013/arms.py
- Purpose: one place for every non-LLM arm, used unchanged by the development analysis and by the
  frozen test choices.
- Core points:
  - A nomination is (compound, line). Each arm ranks the campaign's eligible pairs. The top
    ``budget`` pairs are nominated with at most ``CAP`` per compound, so the budget is spent on
    compound prioritisation and context choice together. Ties break by a fixed hash.
  - Zero and random arms: `zero` uses no compound measurement, only the lines' general
    sensitivity over the PRISM library. `random` draws among primary hits (LFC <= -1).
  - Deterministic screen and pharmacology rules:
    - D1 magnitude (most negative LFC);
    - D2 within-compound robust z;
    - D3 two-way residual z (line sensitivity removed);
    - D3f, D3 restricted to primary hits;
    - D4, D3 with selective hits (z_r <= -2) carrying a target-gene mutation first.
  - Learned arms: one fixed gradient-boosted classifier, so arms differ only in the evidence they
    may use.
    - ML: screen features only.
    - VC: screen plus context, mechanism and transcriptional-transfer evidence.
    - VC+S: additionally the bought PRISM secondary dose-response.
  - The MAESTRO decision layer ranks by the VC model's calibrated probability. It may abstain
    below a threshold (`INSUFFICIENT_EVIDENCE`) and may buy secondary dose-response for a
    fixed number of compounds (`acquire_secondary`).
- Interfaces: `load_table`, `nominate`, `deterministic_scores`, `fit_model`, `predict`, `acquire_secondary`.
"""
from __future__ import annotations

import hashlib

import numpy as np

from census import HERE, SPLIT_SALT

CAP = 3
PRIMARY = ("lfc", "z_c", "z_r", "line_med", "line_noise", "promisc_c", "mad_c", "rank_c")
EVIDENCE = PRIMARY + ("ctx_pred", "lineage_pred", "tgt_mut", "tgt_expr_z", "biomarker_pred", "vc_pred", "vc_trust")
SECONDARY = EVIDENCE + ("sec_auc_z", "sec_slope")
FEATURE_SETS = {"ML": PRIMARY, "VC": EVIDENCE, "VC+S": SECONDARY,
                "ML+context": PRIMARY + ("ctx_pred", "lineage_pred"),
                "ML+mechanism": PRIMARY + ("tgt_mut", "tgt_expr_z", "biomarker_pred"),
                "ML+transcriptional": PRIMARY + ("vc_pred", "vc_trust")}
HGB = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=50, l2_regularization=1.0, random_state=20261013)
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


def load_table() -> dict:
    with np.load(HERE / "features.npz", allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def tie(core: np.ndarray, line: np.ndarray) -> np.ndarray:
    return np.array([int(hashlib.sha256(f"{SPLIT_SALT}:tie:{c}:{l}".encode()).hexdigest()[:12], 16) / 16 ** 12
                     for c, l in zip(core, line)])


def nominate(score: np.ndarray, core: np.ndarray, line: np.ndarray, budget: int, *, cap: int = CAP) -> np.ndarray:
    """Indices of the nominated pairs, best first; NaN or -inf scores are never nominated."""
    s = np.where(np.isfinite(score), score, -np.inf)
    order = np.lexsort((tie(core, line), -s))
    taken: dict = {}
    out = []
    for k in order:
        if len(out) >= budget or s[k] == -np.inf:
            break
        if taken.get(core[k], 0) < cap:
            taken[core[k]] = taken.get(core[k], 0) + 1
            out.append(k)
    return np.array(out, dtype=int)


def deterministic_scores(t: dict) -> dict:
    hit = t["lfc"] <= -1.0
    rnd = tie(t["core"], t["line"])
    return {
        "zero": -t["line_med"] + 1e-9 * rnd,
        "random": np.where(hit, rnd, -np.inf),
        "D1_magnitude": -t["lfc"],
        "D2_compound_z": -t["z_c"],
        "D3_two_way_z": -t["z_r"],
        "D3f_two_way_z_hits": np.where(hit, -t["z_r"], -np.inf),
        "D4_target_mutation": -t["z_r"] + 100.0 * ((t["tgt_mut"] > 0) & (t["z_r"] <= -2.0)),
    }


def matrix(t: dict, rows: np.ndarray, features: tuple[str, ...]) -> np.ndarray:
    return np.column_stack([t[f][rows].astype(float) for f in features])


def fit_model(t: dict, rows: np.ndarray, y: np.ndarray, features: tuple[str, ...]):
    from sklearn.ensemble import HistGradientBoostingClassifier
    model = HistGradientBoostingClassifier(**HGB)
    model.fit(matrix(t, rows, features), y.astype(int))
    return model


def predict(model, t: dict, rows: np.ndarray, features: tuple[str, ...]) -> np.ndarray:
    return model.predict_proba(matrix(t, rows, features))[:, 1]


def acquire_secondary(p: np.ndarray, core: np.ndarray, has_secondary: np.ndarray, k: int, rule: str) -> set:
    """Compounds whose secondary dose-response is bought, chosen from pre-acquisition evidence only.

    ``uncertain``: the compounds whose best candidate's probability is closest to 0.5, where a
    dose-response can most change the decision. ``top``: the compounds with the highest best
    candidate (a conventional follow-up of the strongest hits).
    """
    best: dict = {}
    for pk, c, s in zip(p, core, has_secondary):
        if s and np.isfinite(pk):
            best[c] = max(best.get(c, -1.0), float(pk))
    key = (lambda c: abs(best[c] - 0.5)) if rule == "uncertain" else (lambda c: -best[c])
    return set(sorted(best, key=lambda c: (key(c), c))[:k])
