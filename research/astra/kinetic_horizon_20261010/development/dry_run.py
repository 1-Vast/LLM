"""Pre-freeze dry run of evaluate.py on development data only (no sealed value is read).

Sealed loaders are monkeypatched: the 24 MIX-Seq development lines are split 12/12 into fake
"development" and "confirmation"; mix_sealed -> mix_development; A_treated_sealed -> A_treated_dev;
D_treated -> D_control relabelled DMSO_ -> Tram_ (a null time course); Tahoe confirmation ->
Tahoe development. Numbers are meaningless; only code paths are exercised.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import evaluate as EV  # noqa: E402
import horizon_data as H  # noqa: E402
import mixseq_panel as MP  # noqa: E402

real_split, real_load_late, real_units, real_hsplit = MP.split, H.load_late, MP.load_units, H.split


def fake_split():
    s = real_split()
    dev = s["pool_A_development"]
    s["pool_A_development"], s["pool_A_confirmation"] = dev[:12], dev[12:]
    s["pool_D"] = [d for d in s["pool_D"]]
    return s


def fake_late(tier):
    if tier == "mix_sealed":
        return real_load_late("mix_development")
    if tier == "confirmation":
        return real_load_late("development")
    return real_load_late(tier)


def fake_units(units):
    mapped, relabel = [], False
    for u in units:
        if u == "A_treated_sealed":
            mapped.append("A_treated_dev")
        elif u == "D_treated":
            mapped.append("D_control"); relabel = True
        elif u == "C_treated":
            mapped.append("C_control")
        else:
            mapped.append(u)
    out = real_units(mapped)
    if relabel:
        out["hash_tag"] = np.array([h.replace("DMSO_", "Tram_") for h in out["hash_tag"]])
    return out


def fake_hsplit():
    s = real_hsplit()
    s["confirmation"] = s["development"]
    return s


MP.split, H.load_late, MP.load_units, H.split = fake_split, fake_late, fake_units, fake_hsplit
EV.MP.split, EV.H.load_late, EV.MP.load_units, EV.H.split = fake_split, fake_late, fake_units, fake_hsplit
EV.NBOOT = 50
EV.T.B = 50
cfg = json.loads((HERE.parent / "GATE.json").read_text())["config"]
store = {}
out = {}
for name, fn in (("M", lambda: EV.domain_m(cfg, None, store)), ("T", lambda: EV.domain_t(cfg, None)), ("K", lambda: EV.domain_k(cfg, None, store))):
    try:
        res = fn()
        out[name] = "ok"
        print(name, "ok", list(res)[:8])
    except Exception as exc:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        out[name] = f"FAIL {type(exc).__name__}: {exc}"
# poisoning invariance on the dry-run data
store2 = {}
EV.domain_m(cfg, 7, store2); EV.domain_k(cfg, 7, store2)
same = {k: bool(np.array_equal(store[k], store2[k], equal_nan=store[k].dtype.kind == "f")) for k in store}
out["poison_invariance"] = same
print(json.dumps(out, indent=1))
