"""Workstream C, task 3: leakage and time-order checks (verifier's own code).

(a) STATE forecasts used only basal, full-QC DMSO rows: static check of state_infer.py plus a
    data-level check on all 50 contexts: every receipt's basal source rows must be basal,
    full-QC rows of that plate's DMSO group; the SHA-256 of the basal tensor rebuilt from
    rows.npy must equal the receipt; basal_mean_by_plate in the forecast npz must equal the
    mean of that tensor; the npz digest must equal the receipt; paired_delta must equal
    predicted_mean - dmso_predicted_mean of the same plate.
(b) The observation denominator uses only 'reference' controls (study observation npz vs the
    verifier's own reference / basal statistics) and basal and reference rows are disjoint
    (every plan, every control group), with no file row in two groups.
(c) File timestamps: freezes older than evaluation observation receipts, EVAL_RESULTS.json
    and EPISODES.json.
(d) Protocol SHA-256 equals the freeze records; code hashes in the protocols vs current files.
(e) SPLIT.json follows its hash rule.
Writes task3_leakage_timeorder.json.
"""
import hashlib
import json
import os
import re
from datetime import datetime, timezone

import numpy as np

S = r"D:\MAESTRO\research\astra\zeroshot_context_20261007"
C = r"D:\MAESTRO\data\external\tahoe_zeroshot_20261007"
V = os.path.join(S, "verification")
DMSO = "[('DMSO_TF', 0.0, 'uM')]"
FILES = [f"c{i}.h5ad" for i in range(50)]


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def plan_of(f):
    return load_json(os.path.join(C, "extract", "plans", f + ".plan.json"))


def slots_of(f):
    z = np.load(os.path.join(C, "extract", f, "slots.npz"))
    return {int(g): int(s) for g, s in zip(z["group"], z["start"])}


# ---------------------------------------------------------------- (a) static code check
def static_state_infer():
    path = os.path.join(S, "state_infer.py")
    src = open(path, encoding="utf-8").read()
    m = re.search(r"def basal_sets\(.*?\n(.*?)\ndef run\(", src, re.S)
    body = m.group(1) if m else ""
    checks = {
        "basal_sets_skips_non_control_groups": 'if not g["control"]:\n            continue' in body,
        "basal_rows_require_role_basal_and_full": 'role == "basal" and full' in body,
        "row_index_is_control_group_slot_plus_local": 'index = [start[g["group"]] + local[i] for i in pick]' in body,
        "rows_read_only_via_index": body.count("rows[") == 1 and "rows[index]" in body,
        "treated_groups_only_contribute_label_and_plate": 'jobs.append((g["group"], g["label"], g["plate"]))' in src,
        "rows_npy_opened_only_in_basal_sets": src.count('rows.npy"') == 1,
    }
    return {"sha256": sha_file(path), "checks": checks, "pass": all(checks.values())}


# ---------------------------------------------------------------- (a) data-level check
def state_data_check(protocol):
    out = {"files": 0, "plates": 0, "problems": [], "with_replacement_plates": [],
           "max_abs_basal_mean_diff": 0.0, "paired_delta_max_abs_diff": 0.0,
           "receipt_hash_vs_protocol_mismatch": [], "npz_digest_mismatch": [],
           "basal_tensor_sha_mismatch": 0, "refused_total": 0}
    for f in FILES:
        rpath = os.path.join(S, "state_forecasts", f + ".receipt.json")
        receipt = load_json(rpath)
        if sha_file(rpath) != protocol["state_forecast_receipts_sha256"].get(f + ".receipt.json"):
            out["receipt_hash_vs_protocol_mismatch"].append(f)
        npz_path = os.path.join(C, "state_forecasts", f + ".npz")
        if sha_file(npz_path) != receipt["sha256"]:
            out["npz_digest_mismatch"].append(f)
        if receipt.get("treated_rows_read") is not False:
            out["problems"].append([f, "receipt treated_rows_read not False"])
        out["refused_total"] += len(receipt.get("refused", []))
        plan = plan_of(f)
        slots = slots_of(f)
        rows = np.load(os.path.join(C, "extract", f, "rows.npy"), mmap_mode="r")
        treated_rows = set()
        for g in plan["groups"]:
            if not g["control"]:
                treated_rows.update(g["rows"])
        z = np.load(npz_path)
        dplates = [str(p) for p in z["dmso_plates"]]
        ctrl = {g["plate"]: g for g in plan["groups"] if g["control"]}
        for plate, rec in receipt["basal"].items():
            g = ctrl[plate]
            pos = {r: i for i, r in enumerate(g["rows"])}
            basal_full = {r for r, role, ok in zip(g["rows"], g["control_role"], g["full"]) if role == "basal" and ok}
            reference = {r for r, role in zip(g["rows"], g["control_role"]) if role == "reference"}
            src = rec["source_rows"]
            if len(src) != 256:
                out["problems"].append([f, plate, "basal set size %d" % len(src)])
            if not set(src) <= basal_full:
                out["problems"].append([f, plate, "source rows outside basal full-QC DMSO rows"])
            if set(src) & treated_rows:
                out["problems"].append([f, plate, "source rows include treated rows"])
            if set(src) & reference:
                out["problems"].append([f, plate, "source rows include reference rows"])
            if rec["available_basal_full"] != len(basal_full):
                out["problems"].append([f, plate, "available_basal_full mismatch"])
            if rec["with_replacement"]:
                out["with_replacement_plates"].append([f, plate, len(basal_full)])
            idx = [slots[g["group"]] + pos[r] for r in src]
            tensor = np.asarray(rows[idx], dtype=np.float32)
            if hashlib.sha256(tensor.tobytes()).hexdigest() != rec["sha256"]:
                out["basal_tensor_sha_mismatch"] += 1
                out["problems"].append([f, plate, "basal tensor sha256 mismatch"])
            bm = z["basal_mean_by_plate"][dplates.index(plate)]
            out["max_abs_basal_mean_diff"] = max(out["max_abs_basal_mean_diff"],
                                                 float(np.abs(tensor.mean(0) - bm).max()))
            out["plates"] += 1
        dm = {p: z["dmso_predicted_mean"][i] for i, p in enumerate(dplates)}
        recon = z["predicted_mean"] - np.stack([dm[str(p)] for p in z["plate"]])
        out["paired_delta_max_abs_diff"] = max(out["paired_delta_max_abs_diff"],
                                               float(np.abs(recon - z["paired_delta"]).max()))
        out["files"] += 1
    out["pass"] = (not out["problems"] and not out["receipt_hash_vs_protocol_mismatch"]
                   and not out["npz_digest_mismatch"] and out["paired_delta_max_abs_diff"] == 0.0
                   and out["max_abs_basal_mean_diff"] < 1e-5)
    return out


# ---------------------------------------------------------------- (b)
def disjointness_all_plans():
    out = {"plans": 0, "control_groups": 0, "problems": []}
    for f in FILES:
        plan = plan_of(f)
        seen = {}
        for g in plan["groups"]:
            for r in g["rows"]:
                if r in seen:
                    out["problems"].append([f, "row %d in groups %d and %d" % (r, seen[r], g["group"])])
                    break
                seen[r] = g["group"]
            if g["control"]:
                out["control_groups"] += 1
                roles = set(g["control_role"])
                if not roles <= {"basal", "reference"}:
                    out["problems"].append([f, g["plate"], "unexpected roles %r" % roles])
                if len(g["control_role"]) != len(g["rows"]) or len(g["full"]) != len(g["rows"]):
                    out["problems"].append([f, g["plate"], "per-row arrays misaligned"])
                b = {r for r, role in zip(g["rows"], g["control_role"]) if role == "basal"}
                ref = {r for r, role in zip(g["rows"], g["control_role"]) if role == "reference"}
                if b & ref:
                    out["problems"].append([f, g["plate"], "basal and reference overlap"])
                if g["label"] != DMSO:
                    out["problems"].append([f, g["plate"], "control label %r" % g["label"]])
        out["plans"] += 1
    out["pass"] = not out["problems"]
    return out


def denominator_check(files):
    """Study observation npz control statistics vs the verifier's reference/basal statistics."""
    out = {"files": {}, "problems": []}
    for f in files:
        plan = plan_of(f)
        slots = slots_of(f)
        rows = np.load(os.path.join(C, "extract", f, "rows.npy"), mmap_mode="r")
        z = np.load(os.path.join(C, "observations", f + ".npz"))
        cp = [str(p) for p in z["ctrl_plate"]]
        rec = {"plates": 0, "ctrl_n_equals_reference_n": 0, "max_abs_mean_diff_vs_reference": 0.0,
               "min_max_abs_mean_diff_vs_basal": None, "min_max_abs_mean_diff_vs_all_full": None}
        for g in plan["groups"]:
            if not g["control"]:
                continue
            full = np.asarray(g["full"], bool)
            role = np.asarray(g["control_role"])
            X = np.asarray(rows[slots[g["group"]]:slots[g["group"]] + len(g["rows"])], dtype=np.float64)
            ref, bas = full & (role == "reference"), full & (role == "basal")
            i = cp.index(g["plate"])
            rec["plates"] += 1
            if int(z["ctrl_n"][i]) == int(ref.sum()):
                rec["ctrl_n_equals_reference_n"] += 1
            else:
                out["problems"].append([f, g["plate"], "ctrl_n %d vs reference %d" % (int(z["ctrl_n"][i]), int(ref.sum()))])
            cm = z["ctrl_mean"][i].astype(np.float64)
            rec["max_abs_mean_diff_vs_reference"] = max(rec["max_abs_mean_diff_vs_reference"],
                                                        float(np.abs(cm - X[ref].mean(0)).max()))
            db = float(np.abs(cm - X[bas].mean(0)).max())
            da = float(np.abs(cm - X[full].mean(0)).max())
            rec["min_max_abs_mean_diff_vs_basal"] = db if rec["min_max_abs_mean_diff_vs_basal"] is None else min(rec["min_max_abs_mean_diff_vs_basal"], db)
            rec["min_max_abs_mean_diff_vs_all_full"] = da if rec["min_max_abs_mean_diff_vs_all_full"] is None else min(rec["min_max_abs_mean_diff_vs_all_full"], da)
        out["files"][f] = rec
    out["pass"] = (not out["problems"]) and all(r["max_abs_mean_diff_vs_reference"] < 1e-5 for r in out["files"].values())
    return out


def code_static_observations():
    src = open(os.path.join(S, "observations.py"), encoding="utf-8").read()
    wm = open(os.path.join(S, "world_models.py"), encoding="utf-8").read()
    checks = {
        "control_stats_from_full_and_reference": 'ref = full & (np.asarray(g["control_role"]) == "reference")' in src
                                                 and "n, mean, var = _stats(block[ref])" in src,
        "basal_rows_only_stored_as_basal_mean": src.count("block[basal]") == 1,
        "delta_uses_ctrl_mean": 'delta = obs["mean"].astype(np.float64) - obs["ctrl_mean"][ci]' in wm,
        "noise_uses_ctrl_var_and_ctrl_n": 'np.mean(obs["ctrl_var"][ci], 1) / np.maximum(obs["ctrl_n"][ci], 1)' in wm,
    }
    return {"checks": checks, "pass": all(checks.values())}


# ---------------------------------------------------------------- (c)
def times():
    def t(path):
        st = os.stat(path)
        return {"path": path, "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                "ctime_utc_windows_creation": datetime.fromtimestamp(st.st_ctime, timezone.utc).isoformat(),
                "_m": st.st_mtime, "_c": st.st_ctime}
    freezes = {k: t(os.path.join(S, k)) for k in ("WORLD_FREEZE.json", "AGENT_FREEZE.json")}
    later = {}
    for f in ("c31.h5ad", "c12.h5ad", "c26.h5ad"):
        later["observations/%s.receipt.json" % f] = t(os.path.join(S, "observations", f + ".receipt.json"))
        later["CACHE observations/%s.npz" % f] = t(os.path.join(C, "observations", f + ".npz"))
    later["world_eval/EVAL_RESULTS.json"] = t(os.path.join(S, "world_eval", "EVAL_RESULTS.json"))
    later["agent_eval_inputs/EPISODES.json"] = t(os.path.join(S, "agent_eval_inputs", "EPISODES.json"))
    newest_freeze_m = max(v["_m"] for v in freezes.values())
    newest_freeze_c = max(v["_c"] for v in freezes.values())
    order = {k: {"after_both_freezes_by_mtime": v["_m"] > newest_freeze_m,
                 "after_both_freezes_by_creation": v["_c"] > newest_freeze_c,
                 "seconds_after_last_freeze_mtime": round(v["_m"] - newest_freeze_m, 3)} for k, v in later.items()}
    wf = load_json(os.path.join(S, "WORLD_FREEZE.json"))
    af = load_json(os.path.join(S, "AGENT_FREEZE.json"))
    er = load_json(os.path.join(S, "world_eval", "EVAL_RESULTS.json"))
    internal = {"WORLD_FREEZE.frozen_utc": wf["frozen_utc"], "AGENT_FREEZE.frozen_utc": af["frozen_utc"],
                "EVAL_RESULTS.created_utc": er["created_utc"],
                "eval_created_after_freezes": er["created_utc"] > max(wf["frozen_utc"], af["frozen_utc"]),
                "freeze_flags_evaluation_lines_read": [wf.get("evaluation_lines_read"), af.get("evaluation_lines_read")]}
    # pre-freeze artefacts of the evaluation lines (raw rows and STATE forecasts) - context only
    pre = {}
    for f in ("c31.h5ad", "c12.h5ad", "c26.h5ad"):
        pre[f] = {"extract_rows_npy_mtime_utc": t(os.path.join(C, "extract", f, "rows.npy"))["mtime_utc"],
                  "state_forecast_npz_mtime_utc": t(os.path.join(C, "state_forecasts", f + ".npz"))["mtime_utc"]}
    for d in list(freezes.values()) + list(later.values()):
        d.pop("_m"), d.pop("_c")
    ok = all(v["after_both_freezes_by_mtime"] and v["after_both_freezes_by_creation"] for v in order.values()) \
        and internal["eval_created_after_freezes"]
    return {"freezes": freezes, "later": later, "order": order, "internal_timestamps": internal,
            "pre_freeze_evaluation_line_artifacts": pre, "pass": bool(ok)}


# ---------------------------------------------------------------- (d)
def hashes():
    wp, ap = os.path.join(S, "WORLD_PROTOCOL.json"), os.path.join(S, "AGENT_PROTOCOL.json")
    wf, af = load_json(os.path.join(S, "WORLD_FREEZE.json")), load_json(os.path.join(S, "AGENT_FREEZE.json"))
    er = load_json(os.path.join(S, "world_eval", "EVAL_RESULTS.json"))
    w_sha, a_sha = sha_file(wp), sha_file(ap)
    agent = load_json(ap)
    world = load_json(wp)
    code = {}
    for name, proto in (("WORLD_PROTOCOL", world), ("AGENT_PROTOCOL", agent)):
        mism = {}
        for fn, h in proto.get("code_sha256", {}).items():
            actual = sha_file(os.path.join(S, fn)) if os.path.exists(os.path.join(S, fn)) else None
            if actual != h:
                mism[fn] = {"protocol": h, "current": actual}
        code[name] = {"files": len(proto.get("code_sha256", {})), "mismatches_now": mism}
    split_sha = sha_file(os.path.join(S, "SPLIT.json"))
    dev_sha = sha_file(os.path.join(S, "world_dev", "DEV_RESULTS.json"))
    res = {
        "WORLD_PROTOCOL_sha256": w_sha, "WORLD_FREEZE_protocol_sha256": wf["protocol_sha256"],
        "world_match": w_sha == wf["protocol_sha256"],
        "AGENT_PROTOCOL_sha256": a_sha, "AGENT_FREEZE_protocol_sha256": af["protocol_sha256"],
        "agent_match": a_sha == af["protocol_sha256"],
        "EVAL_RESULTS_protocol_sha256_matches": er["protocol_sha256"] == w_sha,
        "AGENT_PROTOCOL_world_protocol_sha256_matches": agent.get("world_protocol_sha256") == w_sha,
        "WORLD_PROTOCOL_split_sha256_matches_SPLIT": world.get("split_sha256") == split_sha,
        "WORLD_PROTOCOL_dev_results_sha256_matches": world.get("development_results_sha256") == dev_sha,
        "code_hashes": code,
    }
    res["pass"] = bool(res["world_match"] and res["agent_match"] and res["EVAL_RESULTS_protocol_sha256_matches"])
    return res


# ---------------------------------------------------------------- (e)
def split_rule():
    sp = load_json(os.path.join(S, "SPLIT.json"))
    toml = open(os.path.join(S, "sources", "ST-HVG-Tahoe_zeroshot_generalization.toml"), encoding="utf-8").read()
    documented = sorted(re.findall(r'"tahoe_holdout\.(.+?)" = "test"', toml))
    names = sorted(sp["files"].keys())
    digests = {n: hashlib.sha256(("zeroshot-context-20261007:" + n).encode("utf-8")).hexdigest() for n in names}
    order = sorted(names, key=lambda n: digests[n])
    file_ok = {}
    for n, f in sp["files"].items():
        census = load_json(os.path.join(S, "census", f + ".json"))
        file_ok[n] = census.get("cell_names") == [n]
    res = {"digests": digests, "recomputed_order": order, "split_order": sp["order"],
           "order_matches": order == sp["order"],
           "development_matches": order[:2] == sp["development"],
           "evaluation_matches": order[2:] == sp["evaluation"],
           "documented_test_cell_types": documented,
           "split_names_equal_documented": sorted(names) == documented,
           "file_to_cell_name_matches_census": file_ok}
    res["pass"] = bool(res["order_matches"] and res["development_matches"] and res["evaluation_matches"]
                       and res["split_names_equal_documented"] and all(file_ok.values()))
    return res


def main():
    protocol = load_json(os.path.join(S, "WORLD_PROTOCOL.json"))
    res = {}
    res["a_static_state_infer"] = static_state_infer()
    res["a_static_state_infer"]["protocol_code_sha256"] = protocol["code_sha256"]["state_infer.py"]
    res["a_static_state_infer"]["code_matches_frozen_protocol"] = \
        res["a_static_state_infer"]["sha256"] == protocol["code_sha256"]["state_infer.py"]
    print("a static done", flush=True)
    res["a_state_data"] = state_data_check(protocol)
    print("a data done", flush=True)
    res["b_static_observations"] = code_static_observations()
    res["b_disjointness"] = disjointness_all_plans()
    print("b disjoint done", flush=True)
    res["b_denominator"] = denominator_check(["c31.h5ad", "c12.h5ad", "c26.h5ad", "c20.h5ad", "c27.h5ad", "c0.h5ad", "c36.h5ad", "c39.h5ad"])
    print("b denominator done", flush=True)
    res["c_times"] = times()
    res["d_hashes"] = hashes()
    res["e_split"] = split_rule()
    res["pass"] = {k: v["pass"] for k, v in res.items()}
    with open(os.path.join(V, "task3_leakage_timeorder.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res["pass"], indent=1))


if __name__ == "__main__":
    main()
