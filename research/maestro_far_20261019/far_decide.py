"""Apply frozen gates without side effects on import; the CLI writes DECISION.json."""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
J = lambda f: json.loads((H / f).read_text(encoding="utf-8"))
THR = 0.010


def decide():
    out = {"practical_threshold": THR, "stages": {}}
    for st in ("select", "test", "vault"):
        at = J(f"ATLAS_{st}.json")["signatures"]
        n_ok = sum(v["lcb90"] > 0.60 for v in at.values())
        c = J(f"CONTRASTS_{st}_U.json")["contrasts"]
        C1, C2 = c["far.gate-exploit.gate"], c["far2.gate-exploit.gate"]
        # Preserve the original conservative two-contrast (Bonferroni-type) rule.
        p1 = C1["ci95"][0] > THR; p2 = C2["ci95"][0] > THR
        out["stages"][st] = {"phase1_signatures_with_lcb90_gt_0.60": n_ok, "phase1_gate": n_ok >= 2,
                             "C1_far_minus_exploit": C1, "C2_far2_minus_exploit": C2,
                             "C1_pass": bool(p1), "C2_pass": bool(p2),
                             "assay_plus_repair_vs_none": c["far.gate-far.none"], "slice_value_reproducible_split_line_oracle_minus_random": c.get("oracle_split.gate-random.gate"),
                             "all_slices_minus_random": c.get("all.gate-random.gate")}
    t = out["stages"]["test"]
    out["verdict"] = ("FAR_NOT_SUPPORTED" if not (t["C1_pass"] or t["C2_pass"]) else "FAR_SUPPORTED_IN_ARENA")
    out["agent_phase"] = "NOT_RUN (frozen rule: no deterministic FAR advantage)"
    return out


if __name__ == "__main__":
    out = decide()
    (H / "DECISION.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "stages"}, indent=1))
    for st, v in out["stages"].items():
        print(st, v["phase1_gate"], v["C1_pass"], v["C2_pass"], round(v["C1_far_minus_exploit"]["diff"], 4), round(v["C2_far2_minus_exploit"]["diff"], 4))
