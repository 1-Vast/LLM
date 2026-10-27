"""E060: numerical audit of SYNTHESIS.md against the source result files.

Every figure quoted in the consolidation document is re-read from the JSON that produced it.
No new computation. Pre-registered in PROTOCOL_E058.md.
"""

from __future__ import annotations

import json
from pathlib import Path

R = Path(r"D:\MAESTRO\research")
EP = "2026-10-27-agent-cell-identifiability-"


def load(ep):
    return json.load(open(R / (EP + ep) / sorted((R / (EP + ep)).glob("E0*_RESULTS*.json"))[0].name,
                          encoding="utf-8"))


def get(d, *path, default=None):
    cur = d
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        elif isinstance(cur, list) and isinstance(k, int) and k < len(cur):
            cur = cur[k]
        else:
            return default
    return cur


checks = []


def chk(name, claim_text, ok, detail=""):
    checks.append({"name": name, "claim": claim_text, "ok": bool(ok), "detail": detail})


# ---- C24: unseen drug, rho 0.200, AUC 0.682, R2 0.029
d = load("r29")
s = get(d, "summary", default={})
rho = get(d, "summary", "rho_model", "median")
chk("C24_rho", "unseen drug rho 0.200", rho is not None and abs(rho - 0.200) < 0.01, f"source={rho}")
r2 = get(d, "r2_baseline", "r2_model_median")
chk("C24_r2", "R2 0.029", r2 is not None and abs(r2 - 0.029) < 0.005, f"source={r2}")
auc = get(d, "summary", "auc_model", "median")
chk("C24_auc", "AUC 0.682", auc is not None and abs(auc - 0.682) < 0.01, f"source={auc}")

# ---- C25: unseen cell rho median 0.502, tissue +0.0247
d = load("r30")
s = get(d, "summary", default={})
med = get(d, "summary", "rho_all", "median")
chk("C25_rho_median", "unseen cell rho median 0.502", med is not None and abs(med - 0.502) < 0.01, f"source={med}")
diff = get(d, "summary", "rho_diff", "median")
chk("C25_tissue_diff", "tissue +0.0247", diff is not None and abs(diff - 0.0247) < 0.002, f"source={diff}")

# ---- C26: cross-screen 0.6888
d = load("r31")
v = get(d, "cross_screen", "pearson")
chk("C26_cross_screen", "cross-screen 0.6888", v is not None and abs(v - 0.6888) < 0.005, f"source={v}")

# ---- C27: 1.43% -> 6.50% at k=20
d = load("r33")
base = get(d, "audit", "synergy_rate")
k20 = get(d, "by_k", "20", "precision_syn", "exploit")
chk("C27_base", "base 1.43%", base is not None and abs(base - 0.0143) < 0.002, f"source={base}")
chk("C27_k20", "exploit 6.50% at k=20", k20 is not None and abs(k20 - 0.065) < 0.01, f"source={k20}")

# ---- C29: feedback gain -7.4 pp
d = load("r34")
fg = get(d, "feedback_gain", "mean")
chk("C29_feedback", "feedback -7.4 pp", fg is not None and abs(fg + 0.074) < 0.01, f"source={fg}")

# ---- C34: rho +0.0064, p10 -0.0074
d = load("r44")
pr = get(d, "summary", "paired_rho", "mean_diff")
pp = get(d, "summary", "paired_p10", "mean_diff")
chk("C34_rho", "hier rho +0.0064", pr is not None and abs(pr - 0.0064) < 0.002, f"source={pr}")
chk("C34_p10", "hier p10 -0.0074", pp is not None and abs(pp + 0.0074) < 0.002, f"source={pp}")

# ---- C35: inversion +0.56
d = load("r46")
sp = get(d, "inversion", "spearman_d_rho_vs_d_p10")
chk("C35_inversion", "inversion +0.56", sp is not None and abs(sp - 0.56) < 0.05, f"source={sp}")

# ---- C28: crossovers
d = load("r51")
c20 = get(d, "crossover", "20")
c50 = get(d, "crossover", "50")
chk("C28_cross20", "k=20 crossover 1000-3000", c20 == [1000, 3000], f"source={c20}")
chk("C28_cross50", "k=50 crossover 3000-10000", c50 == [3000, 10000], f"source={c50}")

# ---- C36: +9.33, +2.79, 6/6
d = load("r53")
sec = d["secondary_analysis"]
e = get(sec, "predicate_minus_exploit", "diff")
m = get(sec, "predicate_minus_mix", "diff")
chk("C36_vs_exploit", "+9.33 pp", e is not None and abs(e - 0.0933) < 0.002, f"source={e}")
chk("C36_vs_mix", "+2.79 pp", m is not None and abs(m - 0.0279) < 0.002, f"source={m}")
chk("C36_six_of_six", "6/6 best fixed", get(sec, "matches_best_fixed_at_all_sizes") is True,
    f"source={get(sec, 'matches_best_fixed_at_all_sizes')}")

# ---- C38: 50% / 62.5%
d55 = load("r55")
d56 = load("r56")
a55 = get(d55, "decisions", "agreement_rate")
a56 = get(d56, "decisions", "agreement_rate")
chk("C38_r55", "50% agreement", a55 is not None and abs(a55 - 0.50) < 0.01, f"source={a55}")
chk("C38_r56", "62.5% agreement", a56 is not None and abs(a56 - 0.625) < 0.01, f"source={a56}")

# ---- C33: -0.173, Q4-Q1 -10.29 pp
d = load("r57")
sp = get(d, "analysis", "spearman_rho_vs_diff")
gap = get(d, "decisions", "quartile_gap")
chk("C33_spearman", "-0.173", sp is not None and abs(sp + 0.173) < 0.01, f"source={sp}")
chk("C33_gap", "Q4-Q1 -10.29 pp", gap is not None and abs(gap + 0.1029) < 0.003, f"source={gap}")

# ---- cross-check the synthesis text quotes those same figures
syn = (R / "SYNTHESIS.md").read_text(encoding="utf-8")
quoted = {
    "0.502": "C25_rho_median", "0.0247": "C25_tissue_diff", "0.200": "C24_rho",
    "0.029": "C24_r2", "0.682": "C24_auc", "1.43%": "C27_base", "6.50%": "C27_k20",
    "0.0064": "C34_rho", "0.0074": "C34_p10", "0.56": "C35_inversion",
    "0.173": "C33_spearman", "10.29": "C33_gap", "62.5%": "C38_r56",
    "9.33": "C36_vs_exploit", "2.79": "C36_vs_mix",
}
for text, name in quoted.items():
    chk("quoted_" + name, f"SYNTHESIS quotes {text}", text in syn, f"present={text in syn}")

n_ok = sum(1 for c in checks if c["ok"])
out = {"kind": "numerical_audit_of_synthesis", "n_checks": len(checks), "n_ok": n_ok,
       "all_pass": n_ok == len(checks), "checks": checks}
(R / (EP + "r60") / "E060_RESULTS.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
for c in checks:
    print(("OK   " if c["ok"] else "FAIL ") + c["name"] + " | " + c["claim"] + " | " + str(c["detail"]))
print("\n%d/%d pass" % (n_ok, len(checks)))
