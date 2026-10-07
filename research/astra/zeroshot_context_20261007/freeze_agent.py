"""Write AGENT_PROTOCOL.json (final calibration from development data only) and AGENT_FREEZE.json.

Run after agent_dev.py and before any evaluation-line observation is built. Calibration:
  simple prior    OLS on all training contexts (leave-one-out tables), root-scale features
  STATE prior     simple prior + OLS on the two development held-out lines: y_B - simple ~ 1 + root(state_B)
  observation     y_A = a + b * y_B + e on the two development held-out lines (same depth as evaluation)
  prior SDs       residual SDs on the development held-out lines, per world
  correlation     Ledoit-Wolf shrunk residual correlation across the 146 menu labels (training contexts)
LLM arms are enabled only if the registered development gates passed (see agent_dev.py).
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agent_data as ad  # noqa: E402
import world_models as wm  # noqa: E402
from agent_dev import DESIGNS, FEATURES_SIMPLE, design_matrix, fit_ols, ledoit_wolf  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if (HERE / "AGENT_FREEZE.json").exists():
        raise FileExistsError("agent protocol already frozen")
    dev = json.loads((HERE / "agent_dev" / "AGENT_DEV_RESULTS.json").read_text(encoding="utf-8"))
    tables = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (HERE / "agent_dev" / "tables").glob("*.json")}
    held_names = [n.replace("/", "_").replace(" ", "_") for n in wm.SPLIT["development"]]
    train = {k: v for k, v in tables.items() if k not in held_names}
    held = [r for n in held_names for r in tables[n]]
    labels = sorted(ad.menu_labels())
    rows = [r for v in train.values() for r in v]
    beta = fit_ols(design_matrix(rows), np.array([r["y_B"] for r in rows]))
    resid = {}
    for k, v in train.items():
        if [r["label"] for r in v] == labels:
            resid[k] = np.array([r["y_B"] for r in v]) - design_matrix(v) @ beta
    corr, shrink = ledoit_wolf(np.array(list(resid.values())))
    simple = design_matrix(held) @ beta
    yB = np.array([r["y_B"] for r in held])
    yA = np.array([r["y_A"] for r in held])
    state = np.array([float(ad.root(r["state_B"])) for r in held])
    coef = fit_ols(np.column_stack([np.ones(len(held)), state]), yB - simple)
    b, a = np.polyfit(yB, yA, 1)
    gates = dev["gates"]
    primary = "half"
    g_simple, g_state = gates[f"{primary}|heldout_dev|simple"], gates[f"{primary}|heldout_dev|state"]
    g0 = bool(all(dev["G0_state_coefficient_nonzero"].values()) and abs(float(coef[1])) > 0)
    enabled = bool(g_simple["G1_changes_flags"] and g_state["G1_changes_flags"] and g_simple["G2_kg_improves"]
                   and g_state["G2_kg_improves"] and (g_simple["G3_remainder_at_least_delta_agent"] or g_state["G3_remainder_at_least_delta_agent"]) and g0)
    protocol = {
        "study": "zeroshot_context_20261007", "created_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_lines": wm.SPLIT["evaluation"], "design": {"name": primary, **DESIGNS[primary]},
        "menu": {"labels": len(labels), "well_roles": "label/plate hash; A = first-profile well, B = replicate well",
                 "half_menus": "drugs assigned by sha256('menu:'+drug) order alternately"},
        "endpoint": "y = sign(z) sqrt(|z|), z = depth-corrected deviation energy of the line from the panel mean in the same well",
        "score": "V = sum of y_B over the m flags (replicate well, read after commitment); hits in the menu's top 15% by y_B secondary",
        "calibration": {"simple_coefficients": dict(zip(("intercept",) + FEATURES_SIMPLE, beta.tolist())),
                        "state_coefficients": {"intercept": float(coef[0]), "root_state_B": float(coef[1])},
                        "observation_model": {"intercept": float(a), "slope": float(b), "sd": float(np.std(yA - (a + b * yB)))},
                        "prior_sd": {"simple": float(np.std(yB - simple)), "state": float(np.std(yB - simple - coef[0] - coef[1] * state))},
                        "development_rows": len(held), "training_rows": len(rows)},
        "correlation": {"labels": labels, "matrix": corr.tolist(), "ledoit_wolf_shrinkage": shrink, "contexts": len(resid)},
        "policies": {"deterministic": "one-step knowledge gradient on the top-m sum of posterior means (64 common normals); stops when no positive gain",
                     "llm": "DeepSeek via agent.llm.DeepSeekChatClient.complete_json, temperature 0, max_tokens 400; chooses next screen or stop; invalid or failed answers fall back to the knowledge-gradient choice",
                     "controls": "no acquisition in each world; purchase-swap replay"},
        "arms": {"A": ["simple", "kg"], "B": ["state", "kg"], "C": ["simple", "llm"], "D": ["state", "llm"],
                 "noneA": ["simple", "none"], "noneB": ["state", "none"]},
        "interaction": "(D - C) - (B - A) on mean V per episode; per-line values and an episode bootstrap are reported; lines (n = 3) are the independent units",
        "delta_agent": dev["delta_agent"], "development_gates": gates, "G0_state_coefficient_nonzero": g0,
        "llm_arms_enabled": enabled,
        "api_ceiling": {"max_calls": 400, "max_output_tokens_per_call": 400, "deadline_seconds_per_episode": 1800},
        "agent_dev_results_sha256": sha(HERE / "agent_dev" / "AGENT_DEV_RESULTS.json"),
        "alternative_objective_checks_sha256": {"excess": sha(HERE / "agent_dev" / "EXCESS_OBJECTIVE_CHECK.json"),
                                                "profile": sha(HERE / "agent_dev" / "PROFILE_DECISION_CHECK.json")},
        "world_protocol_sha256": sha(HERE / "WORLD_PROTOCOL.json") if (HERE / "WORLD_PROTOCOL.json").exists() else None,
        "code_sha256": {p.name: sha(p) for p in sorted(HERE.glob("*.py")) if not p.name.startswith("test_")},
        "evaluation_observations_built_before_freeze": False,
    }
    (HERE / "AGENT_PROTOCOL.json").write_text(json.dumps(protocol, indent=1), encoding="utf-8")
    freeze = {"protocol_sha256": sha(HERE / "AGENT_PROTOCOL.json"), "frozen_utc": datetime.now(timezone.utc).isoformat(),
              "evaluation_lines_read": False}
    (HERE / "AGENT_FREEZE.json").write_text(json.dumps(freeze, indent=1), encoding="utf-8")
    print(json.dumps({"llm_arms_enabled": enabled, "calibration": protocol["calibration"], "G0": g0, **freeze}, indent=1))


if __name__ == "__main__":
    main()
