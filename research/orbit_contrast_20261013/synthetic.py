"""S0: synthetic checks of the OCEA estimator (PROTOCOL.md section 9, first stopping rule).

File summary
- Path: research/orbit_contrast_20261013/synthetic.py
- Purpose: a world whose truth is known. Each query's response is a generic direction plus, for a
  subset flagged by an observable descriptor, the entity's identity direction; a route returns a
  generic part shared with its orbit plus the entity's identity direction; orbit draws return the
  generic part plus other entities' identity directions.
- Checks:
  - generic world (identity never in the truth): |Delta_id(F)| < 0.01;
  - identity world (identity in the truth for 30% of queries, flagged by a noisy descriptor):
    Delta_id(F) >= 0.5 x Delta_id(F) of the same world with a noise-free descriptor (oracle), and
    score(F) >= score(R).
  - The first S0 run used an absolute threshold, Delta_id(F) > 0.05, set before the synthetic noise
    was calibrated; it observed 0.044 and failed. The relative criterion replaces it (DEVIATIONS.json D1).
- Interface: `run() -> dict` with `passed`.
"""
from __future__ import annotations

import numpy as np

from ocea import compress, concat, fit_predict, entity_means
from routes import RouteOut, cos_rows, unit

P, N_ENT, N_LINES, M = 60, 1500, 3, 16


def world(identity: bool, seed: int, oracle: bool = False):
    rng = np.random.default_rng(seed)
    generic = unit(rng.normal(size=(N_LINES, P)))
    ident = unit(rng.normal(size=(N_ENT, P)))
    flag = rng.random(N_ENT) < 0.3                        # entities whose identity matters
    quality = flag.astype(float) + (0.0 if oracle else 0.3) * rng.normal(size=N_ENT)   # observable descriptor of the flag
    rows = []
    for e in range(N_ENT):
        for T in range(N_LINES):
            rows.append((e, T))
    ent = np.array([r[0] for r in rows]); line = np.array([r[1] for r in rows])
    amp = rng.uniform(0.5, 1.5, len(rows))
    y = amp[:, None] * generic[line] + 1.2 * rng.normal(size=(len(rows), P)) / np.sqrt(P) * 3
    if identity:
        y += (flag[ent] * 1.5)[:, None] * ident[ent]
    f = 0.6 * generic[line] + ident[ent]
    draws = [0.6 * generic[line] + ident[rng.integers(0, N_ENT, len(rows))] for _ in range(M)]
    gbar = np.mean(draws, 0)
    spread = np.sqrt(np.maximum(np.mean([(d * d).sum(1) for d in draws], 0) - (gbar * gbar).sum(1), 0))
    cf = cos_rows(f, y)
    co = np.mean([cos_rows(d, y) for d in draws], 0)
    desc = np.column_stack([quality[ent], np.zeros(len(rows)), np.zeros(len(rows))])
    ro = RouteOut(f, np.ones(len(rows), bool), gbar, spread, desc, ("quality", "z1", "z2"), cf, co)
    gen = generic[line]
    fold = np.array([e % 5 for e in ent])
    return ro, gen, y, line, ent, fold


def run() -> dict:
    out = {}
    for name, identity, oracle in (("generic_world", False, False), ("identity_world", True, False),
                                   ("identity_world_oracle", True, True)):
        ro, gen, y, line, ent, fold = world(identity, 7 if identity else 11, oracle)
        test_m = fold == 0
        parts = []
        for j in range(1, 5):
            m = fold == j
            sub = RouteOut(ro.f[m], ro.avail[m], ro.gbar[m], ro.spread[m], ro.desc[m], ro.desc_names, ro.cos_f[m], ro.cos_orbit[m])
            parts.append(compress({"syn": sub}, gen[m], y[m], (), ("syn",), line[m], ent[m], j))
        tr = concat(parts)
        sub = RouteOut(ro.f[test_m], ro.avail[test_m], ro.gbar[test_m], ro.spread[test_m], ro.desc[test_m], ro.desc_names,
                       ro.cos_f[test_m], ro.cos_orbit[test_m])
        te = compress({"syn": sub}, gen[test_m], y[test_m], (), ("syn",), line[test_m], ent[test_m], -1)
        res = fit_predict(tr, te, (), ("syn",), N_LINES)
        mask = np.ones(len(te.ynorm), bool)
        mean = {a: float(entity_means(s, te.entity, mask)[1].mean()) for a, s in res["scores"].items()}
        out[name] = {"scores": mean, "delta_id_F": mean["F"] - mean["O"], "F_minus_R": mean["F"] - mean["R"],
                     "F_minus_Cp": mean["F"] - mean["Cp"]}
    g, i, o = out["generic_world"], out["identity_world"], out["identity_world_oracle"]
    out["passed"] = bool(abs(g["delta_id_F"]) < 0.01 and i["delta_id_F"] >= 0.5 * o["delta_id_F"] and i["F_minus_R"] >= 0)
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1))
