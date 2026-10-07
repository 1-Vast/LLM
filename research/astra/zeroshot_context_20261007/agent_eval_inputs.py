"""Build frozen evaluation episodes (requires both freezes; evaluation observations built after them).

For each evaluation line and half-menu: candidate rows (labels, wells, y_A, y_B, features, public
metadata) and each world's prior mean/SD from the frozen AGENT_PROTOCOL calibration. Policies only
ever receive y_A of purchased candidates; y_B is read by the runner after flags are committed.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agent_data as ad  # noqa: E402
import world_models as wm  # noqa: E402
from agent_dev import design_matrix, menus  # noqa: E402
from world_dev import panel_keys  # noqa: E402


def main():
    for name in ("WORLD", "AGENT"):
        frozen = json.loads((HERE / f"{name}_FREEZE.json").read_text(encoding="utf-8"))
        if frozen["protocol_sha256"] != hashlib.sha256((HERE / f"{name}_PROTOCOL.json").read_bytes()).hexdigest():
            raise PermissionError(f"{name} protocol changed after freeze")
    protocol = json.loads((HERE / "AGENT_PROTOCOL.json").read_text(encoding="utf-8"))
    world = json.loads((HERE / "WORLD_PROTOCOL.json").read_text(encoding="utf-8"))
    wm.guard(wm.SPLIT["evaluation"])
    ch = world["choices"]
    cal = protocol["calibration"]
    beta = np.array([cal["simple_coefficients"]["intercept"]] + [cal["simple_coefficients"][f] for f in ("zdisp_B", "dev_B", "m0energy_B")])
    panel = wm.Panel(panel_keys())
    wells = ad.menu_labels()
    meta = ad.drug_metadata()
    episodes = []
    for name in wm.SPLIT["evaluation"]:
        rows = ad.heldout_table(name, panel, wells, ch["M0_variant"], ch["M1_family"], ch["krr_lambda"], meta)
        for mi, menu in enumerate(menus(rows, protocol["design"]["menus"])):
            simple = design_matrix(menu) @ beta
            state = simple + cal["state_coefficients"]["intercept"] + cal["state_coefficients"]["root_state_B"] * \
                np.array([float(ad.root(r["state_B"])) for r in menu])
            episodes.append({"line": name, "menu": mi, "cell": ad.cell_metadata(name), "rows": menu,
                             "prior": {"simple": {"mean": simple.tolist(), "sd": [cal["prior_sd"]["simple"]] * len(menu)},
                                       "state": {"mean": state.tolist(), "sd": [cal["prior_sd"]["state"]] * len(menu)}},
                             "obs": [cal["observation_model"]["intercept"], cal["observation_model"]["slope"], cal["observation_model"]["sd"]]})
    out = HERE / "agent_eval_inputs"
    out.mkdir(exist_ok=True)
    (out / "EPISODES.json").write_text(json.dumps(episodes), encoding="utf-8")
    print(json.dumps({"episodes": len(episodes), "candidates": [len(e["rows"]) for e in episodes],
                      "sha256": hashlib.sha256((out / "EPISODES.json").read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
