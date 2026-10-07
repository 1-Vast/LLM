"""Single frozen evaluation of the world-model ladder on the three evaluation lines.

Refuses to run unless WORLD_FREEZE.json matches WORLD_PROTOCOL.json and refuses to overwrite a
result. Every choice is read from the frozen protocol; errors are depth-corrected as in development.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import world_models as wm  # noqa: E402
from world_dev import components, contrast, panel_keys, se_model  # noqa: E402

OUT = HERE / "world_eval"


def main():
    protocol_path = HERE / "WORLD_PROTOCOL.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    names = wm.SPLIT["evaluation"]
    wm.guard(names)
    OUT.mkdir(exist_ok=True)
    target = OUT / "EVAL_RESULTS.json"
    if target.exists():
        raise FileExistsError("evaluation already run; results are immutable")
    started = time.perf_counter()
    ch = protocol["choices"]
    v, dk, gk, gs, gs21, lam = ch["M0_variant"], ch["M1_family"], ch["gamma_K"], ch["gamma_S"], ch["gamma_S_on_M1"], ch["krr_lambda"]
    gctl = ch["gamma_for_controls"]
    panel = wm.Panel(panel_keys())
    raw = {n: wm.target(n, panel) for n in names}
    ev = {n: components(panel, t, lam) for n, t in raw.items()}
    for i, n in enumerate(names):
        other = ev[names[(i + 1) % len(names)]]
        okeys = {k: j for j, k in enumerate(other["keys"])}
        ev[n]["devS_swap"] = np.array([other["devS"][okeys[k]] if k in okeys else np.zeros(2000) for k in ev[n]["keys"]])
        rng = np.random.default_rng(protocol["permutation_seed"])
        strata = {}
        for j, k in enumerate(ev[n]["keys"]):
            strata.setdefault((wm.dose_of(k), k[1]), []).append(j)
        perm = np.arange(len(ev[n]["keys"]))
        for members in strata.values():
            perm[members] = rng.permutation(members)
        ev[n]["devS_perm"] = ev[n]["devS"][perm]
        ev[n]["permutation_changed"] = int((perm != np.arange(len(perm))).sum())
    M0 = lambda c: se_model(c, v)
    nochange = lambda c: np.mean(c["obs"] ** 2, 1) - c["noise_L"]
    models = {"no_change": nochange, "M0": M0,
              "M1": lambda c: se_model(c, v, dk, gk=gk),
              "M2": lambda c: se_model(c, v, gs=gs),
              "M21": lambda c: se_model(c, v, dk, gk=gk, gs=gs21),
              "M2_controls_gamma": lambda c: se_model(c, v, gs=gctl),
              "M2_lineswap": lambda c: se_model(c, v, gs=gctl, state_term=c["devS_swap"]),
              "M2_permuted": lambda c: se_model(c, v, gs=gctl, state_term=c["devS_perm"]),
              "STATE_direct": lambda c: np.mean((c["S"] - c["obs"]) ** 2, 1) - c["noise_L"],
              "STATE_raw_direct": lambda c: np.mean((c["S_raw"] - c["obs"]) ** 2, 1) - c["noise_L"],
              "STATE_panel_mean": lambda c: np.mean((c["state_mean"] - c["obs"]) ** 2, 1) - c["noise_L"]}
    R = {"created_utc": datetime.now(timezone.utc).isoformat(), "protocol_sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
         "evaluation_lines": names, "eligible_groups": {n: int(len(c["obs"])) for n, c in ev.items()},
         "permutation_changed": {n: c["permutation_changed"] for n, c in ev.items()},
         "mean_corrected_se": {m: {n: float(fn(c).mean()) for n, c in ev.items()} for m, fn in models.items()}}
    C = {"M2_minus_M0": contrast(ev, models["M2"], M0), "M1_minus_M0": contrast(ev, models["M1"], M0),
         "M21_minus_M1": contrast(ev, models["M21"], models["M1"]),
         "M2c_minus_M0": contrast(ev, models["M2_controls_gamma"], M0),
         "M2c_minus_lineswap": contrast(ev, models["M2_controls_gamma"], models["M2_lineswap"]),
         "M2c_minus_permuted": contrast(ev, models["M2_controls_gamma"], models["M2_permuted"]),
         "STATE_direct_minus_M0": contrast(ev, models["STATE_direct"], M0),
         "M0_minus_no_change": contrast(ev, M0, nochange)}
    R["contrasts"] = C
    h1 = C["M2_minus_M0"]
    criteria = {"improvement_at_least_delta_min": -h1["mean"] >= protocol["delta_min"],
                "ci_excludes_zero": h1["ci95_drug_clustered"][1] < 0,
                "positive_in_every_line": all(x < 0 for x in h1["per_line"].values()),
                "beyond_M1": C["M21_minus_M1"]["ci95_drug_clustered"][1] < 0,
                "context_specific_vs_lineswap": C["M2c_minus_lineswap"]["ci95_drug_clustered"][1] < 0}
    R["H1"] = {"criteria": criteria, "supported": bool(all(criteria.values())), "delta_min": protocol["delta_min"],
               "gamma_S": gs, "note": "gamma_S = 0 would make M2 identical to M0; H1 could not then be supported."}
    R["seconds"] = round(time.perf_counter() - started, 2)
    target.write_text(json.dumps(R, indent=1), encoding="utf-8")
    print(json.dumps(R, indent=1))


if __name__ == "__main__":
    main()
