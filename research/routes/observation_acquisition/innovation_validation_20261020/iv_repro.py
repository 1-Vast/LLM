"""Reproduce the identified comparison defects of the pinned predecessor (self_improving_virtual_cell_20261020) from its own code and stored
records, without modifying it. Output: REPAIR_REPRODUCTION.json. Real-data use is limited to nothing: checks use synthetic worlds and stored records."""
from __future__ import annotations

import importlib.util
import inspect
import json
import re
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SVC = ROOT / "research" / "self_improving_virtual_cell_20261020"
sys.path.insert(0, str(SVC))

import svc_evolution as E  # noqa: E402
import svc_programs as P  # noqa: E402
import svc_world as W  # noqa: E402


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def program_identity():
    a = {"phi": [{"t": "global"}, {"t": "class", "a": 0, "b": 1}], "Q": [{"kind": "probe", "frac": 0.5, "rule": "coverage", "cond": None},
         {"kind": "probe", "frac": 0.5, "rule": "witness", "cond": {"coord": 1, "thr": 0.3, "else": "coverage"}}], "f": {"type": "ridge", "inter": [], "lam": 3.0}}
    b = json.loads(json.dumps(a))
    b["phi"] = [a["phi"][1], a["phi"][0]]         # same entries, other order: coord 1 now refers to the global coordinate
    ea, eb = P.entries_of(a), P.entries_of(b)
    return {"same_canonical_key": P.canonical(a) == P.canonical(b), "condition_refers_to": [ea[1], eb[1]],
            "defect_reproduced": P.canonical(a) == P.canonical(b) and ea[1] != eb[1]}


def headroom_oracle():
    src = inspect.getsource(importlib.import_module("svc_run").stage_headroom)
    uses_last = bool(re.search(r"oracle = float\(np\.mean\(\[r\[\"oracle\"\] for r in rr\]\)\)", src))
    in_seed_loop = src.index("for seed in SEEDS") < src.index("oracle = float")
    w = W.make_synthetic("compositional", 1, n_drugs=14, n_cells=24)
    cells = E.split_cells(w.cells, "synthetic")
    memo = E.Memo(w)
    per_seed = []
    for seed in (0, 1, 2):
        rr = E.evaluate({"kind": "zero"}, w, memo, w.static, cells["H0"], cells["H0"], 8, seed, "T", nested=True)
        per_seed.append(float(np.mean([r["oracle"] for r in rr])))
    return {"oracle_assigned_after_seed_loop_from_last_seed": uses_last and in_seed_loop, "per_seed_oracle_synthetic_T": per_seed,
            "last_seed_minus_mean_oracle": per_seed[-1] - float(np.mean(per_seed)), "defect_reproduced": uses_last and in_seed_loop and abs(per_seed[-1] - np.mean(per_seed)) > 1e-9}


def verifier_empty():
    spec = importlib.util.spec_from_file_location("svc_verify_probe", SVC / "svc_verify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as d:
        mod.HERE = Path(d)
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mod.main()
    return {"exit_code_on_empty_directory": rc, "output": buf.getvalue().strip(), "defect_reproduced": rc == 0 and "VERIFY OK" in buf.getvalue()}


def stored_records():
    syn = jload(SVC / "SYNTHETIC_RESULTS.json")["results"]
    real = jload(SVC / "REAL_RESULTS.json")["results"]
    out = {}
    # inheritance comparison: the no-inheritance arm never ran the validation step its competitor ran
    noinh_validated = sum(1 for r in syn for e in r["library"]["evo_noinherit"] if "validation" in e["evidence"])
    full_validated = sum(1 for r in syn for e in r["library"]["evo_full"] if "validation" in e["evidence"])
    out["inheritance_validation"] = {"noinherit_entries_with_validation": noinh_validated, "full_entries_with_validation": full_validated,
                                     "defect_reproduced": noinh_validated == 0 and full_validated > 0}
    # promotion: ties demonstrate
    ties = [(r["world"], r["contract"], r["budget"], r["seed"], e["id"], e["evidence"]["validation"]) for r in real for lib in r["library"].values() for e in lib
            if e["status"] == "demonstrated" and "validation" in e["evidence"] and e["evidence"]["validation"]["wins"] == 0]
    out["promotion_by_ties"] = {"demonstrated_with_zero_wins": len(ties), "example": ties[0] if ties else None, "defect_reproduced": len(ties) > 0}
    # checkpoints use incumbent_after recorded before later validation/rollback
    stale = 0
    example = None
    for r in syn + real:
        for arm, lib in r["library"].items():
            status = {e["id"]: e["status"] for e in lib}
            for g in r["generation_records"][arm]:
                if status.get(g["incumbent_after"]) == "retired":
                    stale += 1
                    example = example or (r["world"], r["contract"], r["budget"], r["seed"], arm, g["gen"], g["incumbent_after"])
    out["checkpoint_rollback"] = {"checkpoint_programs_that_were_later_retired": stale, "example": example, "defect_reproduced": stale > 0}
    rc = jload(SVC / "SERIALIZATION_RECEIPT.json")
    primary = jload(SVC / "FREEZE.json")["config"]["primary"]
    out["serialization_contract"] = {"receipt_note": rc["note"], "primary_contract": primary["contract"], "defect_reproduced": "contract E" in rc["note"] and primary["contract"] == "T"}
    return out


def latent_basis():
    """The SVD basis of released residuals carries arbitrary sign/rotation; a program that names 'latent 1' means a different coordinate under another history."""
    worst, rows = 1.0, []
    for kind in ("low_rank", "null_anchor", "compositional"):
        for seed in range(3):
            w = W.make_synthetic(kind, seed, n_drugs=14, n_cells=24)
            cells = E.split_cells(w.cells, "synthetic")
            p1 = P.fit_prior(w.history(cells["H0"] + cells["D1"]))
            for drop in range(3):
                keep = (cells["H0"] + cells["D1"])
                p2 = P.fit_prior(w.history(keep[: len(keep) - 1 - drop]))
                c = [float(np.corrcoef(p1.V[:, j], p2.V[:, j])[0, 1]) for j in range(2)]
                rows.append({"kind": kind, "seed": seed, "drop": drop, "corr": c})
                worst = min(worst, min(c))
    return {"minimum_signed_column_correlation": worst, "n_comparisons": len(rows), "n_below_0.9": sum(1 for r in rows if min(r["corr"]) < 0.9),
            "n_sign_flipped": sum(1 for r in rows if min(r["corr"]) < 0), "defect_reproduced": worst < 0.9}


def zero_for_unknown():
    w = W.make_synthetic("compositional", 0, n_drugs=14, n_cells=24)
    st = w.static
    entries = [{"t": "global"}, {"t": "class", "a": 0, "b": 0}]
    prior = P.fit_prior(w.history(E.split_cells(w.cells, "synthetic")["H0"]))
    other_class_pair = int(np.nonzero(st.pair_class != st.classes.index((0, 0)))[0][0])
    z = P.state_vector(entries, prior, st, [other_class_pair], [0.2])
    return {"state_when_class_never_probed": z.tolist(), "defect_reproduced": float(z[1]) == 0.0}


def main():
    out = {"program_identity": program_identity(), "headroom_oracle": headroom_oracle(), "verifier_empty_evidence": verifier_empty(),
           **stored_records(), "latent_basis": latent_basis(), "unknown_coordinate_as_zero": zero_for_unknown()}
    out["all_reproduced"] = all(v.get("defect_reproduced") for v in out.values() if isinstance(v, dict))
    (HERE / "REPAIR_REPRODUCTION.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    for k, v in out.items():
        if isinstance(v, dict):
            print(k, v.get("defect_reproduced"))
    print("all_reproduced", out["all_reproduced"])


if __name__ == "__main__":
    main()
