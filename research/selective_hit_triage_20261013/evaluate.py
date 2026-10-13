"""One-shot test evaluation: score the locked choices against sealed CTRP v2 confirmation outcomes.

File summary
- Path: research/selective_hit_triage_20261013/evaluate.py
- Purpose: open the test outcomes once, after FREEZE.json and CHOICES_LOCK.json, and score every
  pre-registered arm and contrast in PROTOCOL.md.
- Core points:
  - Primary hypotheses at b = 1 (16 confirmation curves per campaign, 128 in all). Both use
    one-sided sign-flip tests over compounds at alpha 0.025:
    - P1: MAESTRO beats D3_two_way_z;
    - P2: MAESTRO_LOOP beats CONV_LOOP, with the same 32 bought secondaries.
  - Secondary analyses S1-S12 are descriptive or exploratory and carry no confirmatory claim.
  - The memory replay (S8) runs here because it learns from earlier campaigns' revealed outcomes:
    - MEM adds line reliability (as in DEV_EXPLORE3, lambda 1, prior 20) to MAESTRO_LOOP's final
      score;
    - it learns from development outcomes plus the outcomes of its own nominations in earlier
      test campaigns;
    - SHUF permutes the training labels before every campaign.
  - Scientific Decision Review family (R), registered separately at alpha 0.025 each:
    - R1: evidence vetoes in SDR_veto pick compounds that are less often confirmable than the
      compounds it leaves as NEED_MORE_EVIDENCE (one-sided Fisher exact);
    - R2: admitting virtual-cell predictions as replicate evidence (SDR_unverified) produces more
      false NO-GOs than SDR_veto (compound sign-flip);
    - R3: SDR_veto is non-inferior to MAESTRO_LOOP in validated hits (95% bootstrap lower bound
      above -6).
    Decision quality (S13) is reported for every arm. A compound is *confirmable* when any of its
    screen-selective pairs (z_r <= -2) validates.
  - Claim audit (S14): every evidence value in every stored decision record is re-derived from
    features.npz; any mismatch is an unsupported claim.
  - Agent arms are scored only when AGENT_CHOICES.json or SDR_DEBATE_CHOICES.json exists, into
    AGENT_RESULTS.json and SDR_DEBATE_RESULTS.json (each write-once). Otherwise they are
    reported NOT_RUN.
  - Write-once: a rerun recomputes and must reproduce TEST_RESULTS.json exactly.
- Interfaces: `score_arm`, `contrast`, `memory_replay`, `decision_quality`, `audit_records`, `main`.
"""
from __future__ import annotations

import json
import sys

import numpy as np

from arms import load_table, nominate
from census import HERE, ROOT
from dev import labels
from dev_explore2 import K_FRACTION
from dev_explore3 import reliability
from outcomes import ENDPOINT, qualified_outcomes, require_freeze
from test_choose import components, load_choices, loop_scores, pair_id

sys.path.insert(0, str(ROOT))
from tools.evaluation.scoring import cluster_signflip_test  # noqa: E402

NON_INFERIORITY_MARGIN = -6.0
EVIDENCE_VETOES = ("ISOLATED_OUTLIER_UNREPLICATED", "NON_REPLICATING", "PREDICTED_NON_REPLICATING")

ALPHA = 0.025
PRIMARY = {"P1": ("MAESTRO", "D3_two_way_z"), "P2": ("MAESTRO_LOOP", "CONV_LOOP")}
SECONDARY_CONTRASTS = [
    ("S2", "ML", "D3_two_way_z"), ("S2", "VC", "D3_two_way_z"), ("S2", "VC", "ML"), ("S2", "ML+context", "ML"),
    ("S2", "ML+mechanism", "ML"), ("S2", "ML+transcriptional", "ML"), ("S2", "VC+S", "MAESTRO_LOOP"),
    ("S3", "MAESTRO_top", "CONV_LOOP"), ("S3", "CONV_frontier", "CONV_LOOP"), ("S3", "MAESTRO_LOOP", "MAESTRO_top"),
    ("S3", "MAESTRO_LOOP", "CONV_frontier"), ("S3", "CONV_LOOP", "D3_two_way_z"), ("S3", "MAESTRO_LOOP", "MAESTRO"),
    ("S5", "MAESTRO_ALL", "MAESTRO_LOOP"), ("S5", "CONV_ALL", "MAESTRO_LOOP"), ("S5", "MAESTRO_ALL", "CONV_ALL"),
    ("S10", "D3_two_way_z", "zero"), ("S10", "D3_two_way_z", "random"), ("S10", "D3_two_way_z", "D1_magnitude"),
    ("S11", "LOOP_uncertain", "MAESTRO_LOOP"), ("S11", "LOOP_top", "MAESTRO_LOOP")]
LAMBDA, MEMORY_SEED, BOOT, BOOT_SEED = 1.0, 20261013, 10000, 20261013
RESULTS, AGENT_RESULTS = HERE / "TEST_RESULTS.json", HERE / "AGENT_RESULTS.json"


class Truth:
    """Test outcomes keyed by pair id, plus compound facts used by the descriptive analyses."""

    def __init__(self, t: dict, outcomes: dict):
        rows = np.flatnonzero(t["role"] == "test")
        y, ev, pan = labels(t, rows, outcomes)
        self.pairs = [pair_id(a, b) for a, b in zip(t["core"][rows], t["line"][rows])]
        self.index = {p: k for k, p in enumerate(self.pairs)}
        self.y, self.ev, self.pan = y, ev, pan
        self.tgt_mut = t["tgt_mut"][rows] > 0
        self.ctx = t["ctx_pred"][rows]
        self.zr = t["z_r"][rows]
        split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
        self.cores = sorted(split["test"])
        self.family = split["family"]
        self.phase = {r["core"]: r["phase"] for r in json.loads((HERE / "compounds.json").read_text(encoding="utf-8"))}
        self.outcomes = outcomes
        core = t["core"][rows]
        self.confirmable = {c: bool(y[(core == c) & (self.zr <= -2)].any()) for c in self.cores}
        self.has_signal = {c: bool(((core == c) & (self.zr <= -2)).any()) for c in self.cores}

    def hits(self, noms: list[str]) -> np.ndarray:
        return np.array([bool(self.y[self.index[p]]) for p in noms], dtype=bool)

    def per_compound(self, noms: list[str]) -> np.ndarray:
        count = {c: 0 for c in self.cores}
        for p, h in zip(noms, self.hits(noms)):
            count[p.split("|")[0]] += int(h)
        return np.array([count[c] for c in self.cores], dtype=float)


def flat(arm: dict) -> list[str]:
    return [p for camp in arm["campaigns"] for p in camp["nominations"]]


def score_arm(truth: Truth, noms: list[str], bought: int) -> dict:
    h = truth.hits(noms)
    k = np.array([truth.index[p] for p in noms], dtype=int)
    cores_hit = {p.split("|")[0] for p, x in zip(noms, h) if x}
    return {"nominations": len(noms), "validated_hits": int(h.sum()), "hit_rate": float(h.mean()) if len(noms) else None,
            "false_positives": int(len(noms) - h.sum()), "not_evaluable": int((~truth.ev[k]).sum()),
            "pan_active_nominations": int(truth.pan[k].sum()), "compounds_nominated": len({p.split("|")[0] for p in noms}),
            "compounds_with_validated_hit": len(cores_hit),
            "launched_compounds_with_hit": sum(truth.phase[c] == "Launched" for c in cores_hit),
            "hits_with_target_mutation": int((h & truth.tgt_mut[k]).sum()),
            "confirmation_curves": len(noms), "secondary_compounds_bought": int(bought),
            "curves_per_validated_hit": float(len(noms) / h.sum()) if h.sum() else None,
            "secondaries_per_validated_hit": float(bought / h.sum()) if h.sum() else None}


def contrast(truth: Truth, a: list[str], b: list[str], *, family: bool = False, drop: set | None = None) -> dict:
    d = truth.per_compound(a) - truth.per_compound(b)
    clusters = [truth.family[c] for c in truth.cores] if family else list(truth.cores)
    if drop:
        keep = np.array([c not in drop for c in truth.cores])
        d, clusters = d[keep], [c for c, k in zip(clusters, keep) if k]
    st = cluster_signflip_test(d.tolist(), clusters)
    rng = np.random.default_rng(BOOT_SEED)
    if family:
        names = sorted(set(clusters))
        sums = np.array([d[[k for k, c in enumerate(clusters) if c == n]].sum() for n in names])
    else:
        sums = d
    boot = sums[rng.integers(0, len(sums), size=(BOOT, len(sums)))].sum(axis=1)
    return {"difference": float(d.sum()), "p_greater": st["p_greater"], "p_less": st["p_less"], "p_two_sided": st["p_two_sided"],
            "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))], "clusters": st["n_clusters"]}


def verdict(c: dict) -> str:
    if c["difference"] > 0 and c["p_greater"] <= ALPHA:
        return "CONFIRMED"
    if c["difference"] < 0 and c["p_less"] <= ALPHA:
        return "REVERSED"
    return "NOT_CONFIRMED"


def decision_quality(truth: Truth, arm: dict) -> dict:
    """GO / NO_GO / NEED_MORE_EVIDENCE against compound confirmability.

    Arms without decision records read as: nominated compounds GO, compounds without a
    screen-selective pair NO_GO (NO_SELECTIVE_SIGNAL), all others NEED_MORE_EVIDENCE.
    """
    status: dict = {}
    for camp in arm["campaigns"]:
        if "decisions" in camp:
            status.update({k: (d["status"], d["reasons"][0] if d["reasons"] else "") for k, d in camp["decisions"].items()})
        else:
            status.update({p.split("|")[0]: ("GO", "NOMINATED") for p in camp["nominations"]})
    for c in truth.cores:
        if c not in status:
            status[c] = ("NEED_MORE_EVIDENCE", "NOT_FUNDED") if truth.has_signal[c] else ("NO_GO", "NO_SELECTIVE_SIGNAL")
    noms = flat(arm)
    hit_compounds = {p.split("|")[0] for p, h in zip(noms, truth.hits(noms)) if h}
    out: dict = {}
    for s in ("GO", "NO_GO", "NEED_MORE_EVIDENCE"):
        cs = [c for c in truth.cores if status[c][0] == s]
        out[s] = {"compounds": len(cs), "confirmable": sum(truth.confirmable[c] for c in cs)}
    out["GO"]["with_validated_nomination"] = sum(c in hit_compounds for c in truth.cores if status[c][0] == "GO")
    out["NO_GO"]["by_reason"] = {}
    for c in truth.cores:
        if status[c][0] == "NO_GO":
            r = out["NO_GO"]["by_reason"].setdefault(status[c][1], {"compounds": 0, "confirmable": 0})
            r["compounds"] += 1
            r["confirmable"] += int(truth.confirmable[c])
    out["false_no_go"] = out["NO_GO"]["confirmable"]
    out["_status"] = {c: status[c] for c in truth.cores}
    return out


def audit_records(t: dict, choices: dict) -> dict:
    """Every evidence value stored in a decision record, re-derived from the frozen pair table."""
    rows = np.flatnonzero(t["role"] == "test")
    index = {pair_id(a, b): r for a, b, r in zip(t["core"][rows], t["line"][rows], rows)}
    breadth = {c: int((t["z_r"][rows][t["core"][rows] == c] <= -2.5).sum()) for c in set(t["core"][rows])}
    out: dict = {}
    for b, arms in choices["arms"].items():
        for name, arm in arms.items():
            checked = mismatched = 0
            for camp in arm["campaigns"]:
                for c, d in camp.get("decisions", {}).items():
                    e = d["evidence"]
                    r = index[pair_id(c, e["best_line"])]
                    ctx = float(t["ctx_pred"][r]) if np.isfinite(t["ctx_pred"][r]) else 0.0
                    claims = [(e["breadth"], breadth[c]), (e["best_z_r"], round(float(t["z_r"][r]), 3)),
                              (e["best_ctx"], round(ctx, 3)), (e["generic_fraction"], round(float(t["promisc_c"][r]), 4))]
                    if e["best_sec_z"] is not None:
                        claims.append((e["best_sec_z"], round(float(t["sec_auc_z"][r]), 3)))
                    checked += len(claims)
                    mismatched += sum(stored != derived for stored, derived in claims)
            if checked:
                out[f"{name}:{b}"] = {"claims_checked": checked, "unsupported": mismatched}
    return out


def review_family(truth: Truth, choices: dict, noms: dict) -> dict:
    from scipy.stats import fisher_exact
    arms = choices["arms"]["1.0"]
    q = {name: decision_quality(truth, arms[name]) for name in arms}
    veto = q["SDR_veto"]["_status"]
    vetoed = [c for c in truth.cores if veto[c][0] == "NO_GO" and veto[c][1] in EVIDENCE_VETOES]
    open_ = [c for c in truth.cores if veto[c][0] == "NEED_MORE_EVIDENCE"]
    a, b = sum(truth.confirmable[c] for c in vetoed), sum(truth.confirmable[c] for c in open_)
    p1 = float(fisher_exact([[a, len(vetoed) - a], [b, len(open_) - b]], alternative="less")[1]) if vetoed and open_ else None
    r1 = {"vetoed": len(vetoed), "vetoed_confirmable": a, "need_more_evidence": len(open_), "need_more_evidence_confirmable": b,
          "p_one_sided": p1, "alpha_one_sided": ALPHA, "verdict": "CONFIRMED" if p1 is not None and p1 <= ALPHA else "NOT_CONFIRMED"}

    def false_no_go(name):
        st = q[name]["_status"]
        return np.array([float(st[c][0] == "NO_GO" and st[c][1] in EVIDENCE_VETOES and truth.confirmable[c]) for c in truth.cores])

    d = false_no_go("SDR_unverified") - false_no_go("SDR_veto")
    st = cluster_signflip_test(d.tolist(), truth.cores)
    r2 = {"false_no_go_unverified": int(false_no_go("SDR_unverified").sum()), "false_no_go_verified": int(false_no_go("SDR_veto").sum()),
          "difference": float(d.sum()), "p_greater": st["p_greater"], "alpha_one_sided": ALPHA,
          "verdict": "CONFIRMED" if d.sum() > 0 and st["p_greater"] <= ALPHA else "NOT_CONFIRMED"}
    c3 = contrast(truth, noms["1.0"]["SDR_veto"], noms["1.0"]["MAESTRO_LOOP"])
    r3 = {**c3, "margin": NON_INFERIORITY_MARGIN,
          "verdict": "NON_INFERIOR" if c3["ci95"][0] > NON_INFERIORITY_MARGIN else ("INFERIOR" if c3["p_less"] <= ALPHA else "INCONCLUSIVE")}
    ablations = {}
    for bb in ("0.5", "1.0", "2.0"):
        for x, y_ in (("SDR_veto_acquire", "SDR_veto"), ("SDR_acquire", "MAESTRO_LOOP"), ("SDR_full", "SDR_veto_acquire"),
                      ("SDR_unverified", "SDR_veto"), ("SDR_veto", "MAESTRO_LOOP"), ("SDR_veto_acquire", "MAESTRO_LOOP")):
            ablations[f"{bb}:{x}-{y_}"] = contrast(truth, noms[bb][x], noms[bb][y_])
    quality = {name: {k: v for k, v in q[name].items() if k != "_status"} for name in q}
    return {"R1_veto_correctness": r1, "R2_evidence_verification": r2, "R3_hits_non_inferiority": r3,
            "ablations": ablations, "S13_decision_quality_b1": quality}


def memory_replay(t: dict, truth: Truth, choices: dict, *, shuffled: bool) -> dict:
    """Sequential b = 1 replay: line reliability learned from development and from revealed own nominations."""
    drows = np.flatnonzero(t["role"] == "development")
    dy, dev, _ = labels(t, drows, qualified_outcomes("development"))
    use = dev & (t["z_r"][drows] <= -2)
    keys, lab = list(t["line"][drows][use]), list(dy[use].astype(int))
    rng = np.random.default_rng(MEMORY_SEED)
    rows = np.flatnonzero(t["role"] == "test")
    c = components(t, rows)
    noms: list[str] = []
    per_campaign = []
    for ci, camp in enumerate(choices["campaigns"]):
        sel = np.flatnonzero(np.isin(c["core"], camp))
        B, K = len(camp), int(round(K_FRACTION * len(camp)))
        bought, post = loop_scores(c, sel, B, K, "maestro", "frontier")
        assert sorted(bought) == choices["arms"]["1.0"]["MAESTRO_LOOP"]["campaigns"][ci]["bought"]
        y_train = np.array(lab)
        if shuffled:
            y_train = y_train[rng.permutation(len(y_train))]
        rel = reliability(np.array(keys), y_train, np.ones(len(keys), bool), c["line"][sel])
        pick = sel[nominate(post + LAMBDA * rel, c["core"][sel], c["line"][sel], B)]
        got = [pair_id(c["core"][k], c["line"][k]) for k in pick]
        noms += got
        per_campaign.append(int(truth.hits(got).sum()))
        for k in pick:                                  # reveal own nominations only
            if truth.ev[k] and c["zr"][k] <= -2:
                keys.append(c["line"][k])
                lab.append(int(truth.y[k]))
    return {"nominations": noms, "hits_per_campaign": per_campaign}


def calibration(truth: Truth, choices: dict) -> dict:
    out = {}
    for b in ("0.5", "1.0", "2.0"):
        for name in ("MAESTRO_LOOP", "D3_two_way_z"):
            noms = flat(choices["arms"][b][name])
            p = np.array(choices["predicted"][f"{name}:{float(b)}"])
            h = truth.hits(noms).astype(float)
            out[f"{name}:{b}"] = {"expected_hits": float(p.sum()), "realised_hits": int(h.sum()),
                                  "brier": float(np.mean((p - h) ** 2)), "mean_p": float(p.mean())}
    noms = flat(choices["arms"]["1.0"]["MAESTRO_LOOP"])
    p = np.array(choices["predicted"]["MAESTRO_LOOP:1.0"])
    h = truth.hits(noms)
    out["bins_MAESTRO_LOOP:1.0"] = [{"bin": [lo, hi], "n": int(((p >= lo) & (p < hi)).sum()),
                                     "mean_p": float(p[(p >= lo) & (p < hi)].mean()) if ((p >= lo) & (p < hi)).any() else None,
                                     "rate": float(h[(p >= lo) & (p < hi)].mean()) if ((p >= lo) & (p < hi)).any() else None}
                                    for lo, hi in ((0, .2), (.2, .3), (.3, .4), (.4, .6), (.6, 1.01))]
    out["abstention_MAESTRO_LOOP:1.0"] = {str(tau): {"kept": int((p >= tau).sum()), "hits_kept": int(h[p >= tau].sum()),
                                                     "hit_rate_kept": float(h[p >= tau].mean()) if (p >= tau).any() else None,
                                                     "curves_saved": int((p < tau).sum()), "hits_lost": int(h[p < tau].sum()),
                                                     "refusal": "INSUFFICIENT_EVIDENCE"}
                                          for tau in (0.0, 0.2, 0.3, 0.4, 0.5)}
    return out


def evidence_reliability(truth: Truth, noms: list[str], bought: set) -> dict:
    k = np.array([truth.index[p] for p in noms], dtype=int)
    h = truth.y[k]
    strata = {"context_agrees(ctx<=-1)": truth.ctx[k] <= -1, "context_silent_or_against": ~(truth.ctx[k] <= -1),
              "secondary_bought": np.array([p.split("|")[0] in bought for p in noms]),
              "secondary_not_bought": ~np.array([p.split("|")[0] in bought for p in noms]),
              "target_mutation": truth.tgt_mut[k], "no_target_mutation": ~truth.tgt_mut[k],
              "pan_active_compound": truth.pan[k], "not_pan_active": ~truth.pan[k]}
    return {name: {"n": int(m.sum()), "hits": int(h[m].sum()), "rate": float(h[m].mean()) if m.any() else None} for name, m in strata.items()}


def novelty(truth: Truth, a: list[str], ref: list[str]) -> dict:
    ha = {p for p, x in zip(a, truth.hits(a)) if x}
    hr = {p for p, x in zip(ref, truth.hits(ref)) if x}
    return {"hits": len(ha), "hits_not_found_by_reference": len(ha - hr), "reference_hits_missed": len(hr - ha),
            "compounds_with_hit_not_found_by_reference": len({p.split('|')[0] for p in ha} - {p.split('|')[0] for p in hr})}


def build(t: dict, truth: Truth, choices: dict) -> dict:
    res: dict = {"label": "TEST (sealed CTRP v2 outcomes opened once, after FREEZE and CHOICES_LOCK)", "endpoint": ENDPOINT,
                 "test_compounds": len(truth.cores), "compounds_with_outcomes": len(truth.outcomes),
                 "evaluable_pairs": int(truth.ev.sum()), "validated_pairs": int(truth.y.sum()),
                 "base_rate_evaluable": float(truth.y[truth.ev].mean()),
                 "pan_active_compounds": int(sum(o["pan_active"] for o in truth.outcomes.values())),
                 "compounds_with_any_validated_pair": len({p.split('|')[0] for p, v in zip(truth.pairs, truth.y) if v})}
    res["arms"] = {b: {name: score_arm(truth, flat(arm), arm["secondary_bought"]) for name, arm in arms.items()}
                   for b, arms in choices["arms"].items()}
    noms = {b: {name: flat(arm) for name, arm in arms.items()} for b, arms in choices["arms"].items()}
    res["primary"] = {}
    for key, (a, b) in PRIMARY.items():
        c = contrast(truth, noms["1.0"][a], noms["1.0"][b])
        res["primary"][key] = {"arms": [a, b], **c, "alpha_one_sided": ALPHA, "verdict": verdict(c),
                               "family_clusters": contrast(truth, noms["1.0"][a], noms["1.0"][b], family=True)}
    res["secondary"] = {"S4_budgets": {}, "contrasts": {}}
    for b in ("0.5", "2.0"):
        for key, (a, r) in PRIMARY.items():
            res["secondary"]["S4_budgets"][f"{key}@{b}"] = contrast(truth, noms[b][a], noms[b][r])
    for b in ("0.5", "1.0", "2.0"):
        for tag, a, r in SECONDARY_CONTRASTS:
            res["secondary"]["contrasts"][f"{tag}:{b}:{a}-{r}"] = contrast(truth, noms[b][a], noms[b][r])
    res["secondary"]["S1_pan_active_nominations_b1"] = {k: v["pan_active_nominations"] for k, v in res["arms"]["1.0"].items()}
    res["secondary"]["S6_novelty_b1"] = {f"{a}_vs_{r}": novelty(truth, noms["1.0"][a], noms["1.0"][r])
                                         for a, r in (("MAESTRO_LOOP", "CONV_LOOP"), ("MAESTRO_LOOP", "D3_two_way_z"),
                                                      ("MAESTRO", "D3_two_way_z"))}
    res["secondary"]["S7_calibration"] = calibration(truth, choices)
    mem = memory_replay(t, truth, choices, shuffled=False)
    shuf = memory_replay(t, truth, choices, shuffled=True)
    base = noms["1.0"]["MAESTRO_LOOP"]
    res["secondary"]["S8_memory_b1"] = {
        "MEM": {"hits": int(truth.hits(mem["nominations"]).sum()), "per_campaign": mem["hits_per_campaign"]},
        "SHUF": {"hits": int(truth.hits(shuf["nominations"]).sum()), "per_campaign": shuf["hits_per_campaign"]},
        "NO_MEM": {"hits": int(truth.hits(base).sum())},
        "MEM-NO_MEM": contrast(truth, mem["nominations"], base), "MEM-SHUF": contrast(truth, mem["nominations"], shuf["nominations"])}
    bought = {p for camp in choices["arms"]["1.0"]["MAESTRO_LOOP"]["campaigns"] for p in camp["bought"]}
    res["secondary"]["evidence_reliability_MAESTRO_LOOP_b1"] = evidence_reliability(truth, base, bought)
    leak = json.loads((HERE / "LEAKAGE.json").read_text(encoding="utf-8"))
    res["secondary"]["S12_leakage_sensitivity"] = {
        f"{key}:without_{name}": {"dropped": len(drop), **contrast(truth, noms["1.0"][a], noms["1.0"][r], drop=set(drop))}
        for key, (a, r) in PRIMARY.items()
        for name, drop in (("shared_target_gene", leak["test_compounds_sharing_a_target_gene_with_development"]),
                           ("similar_to_development", leak["similar_to_development"]))}
    res["review"] = review_family(truth, choices, noms)
    res["secondary"]["S14_record_audit"] = audit_records(t, choices)
    ran = [n for n in ("AGENT_CHOICES.json", "SDR_DEBATE_CHOICES.json") if (HERE / n).exists()]
    res["agent_arms"] = "NOT_RUN" if not ran else "SCORED_IN_AGENT_RESULTS"
    return res


def score_agents(truth: Truth, choices: dict) -> dict:
    agent = json.loads((HERE / "AGENT_CHOICES.json").read_text(encoding="utf-8"))
    out: dict = {"model": agent["model"], "replicates": agent["replicates"], "spent_usd": agent["spent_usd"], "arms": {}}
    ref = {"AGENT_conventional": "CONV_LOOP", "AGENT_maestro": "MAESTRO_LOOP"}
    for name, reps in agent["arms"].items():
        rows = []
        for rep in reps:
            noms = [p for camp in rep for p in camp["nominations"]]
            rows.append({**score_arm(truth, noms, sum(len(camp["bought"]) for camp in rep)),
                         "refusals": sum(len(camp["refusals"]) for camp in rep),
                         "flags": sum(len(camp.get("flags", [])) for camp in rep),
                         f"vs_{ref[name]}": contrast(truth, noms, flat(choices["arms"]["1.0"][ref[name]])),
                         "vs_D3_two_way_z": contrast(truth, noms, flat(choices["arms"]["1.0"]["D3_two_way_z"]))})
        out["arms"][name] = rows
    flagged = [f for rep in agent["arms"]["AGENT_maestro"] for camp in rep for f in camp["flags"]]
    out["flag_precision"] = {"flags": len(flagged), "flagged_pairs_that_validated": int(truth.hits([f["pair"] for f in flagged]).sum())}
    a1 = [r["vs_MAESTRO_LOOP"] for r in out["arms"]["AGENT_maestro"]]
    out["A1_flags_add_value"] = "CONFIRMED" if a1 and all(x["difference"] > 0 and x["p_greater"] <= ALPHA for x in a1) else "NOT_CONFIRMED"
    return out


def score_debate(truth: Truth, choices: dict) -> dict:
    """R6: the LLM tournament steers only the purchase; GO / NO-GO stay with the verified review."""
    debate = json.loads((HERE / "SDR_DEBATE_CHOICES.json").read_text(encoding="utf-8"))
    arms = choices["arms"]["1.0"]
    out: dict = {"model": debate["model"], "replicates": debate["replicates"], "spent_usd": debate["spent_usd"], "runs": []}
    for run in debate["runs"]:
        arm = {"campaigns": [{"nominations": c["nominations"], "bought": c["bought"], "decisions": {
            k: {**v, "evidence": None} for k, v in c["decisions"].items()}} for c in run]}
        noms = flat(arm)
        q = decision_quality(truth, arm)
        out["runs"].append({**score_arm(truth, noms, sum(len(c["bought"]) for c in run)),
                            "decision_quality": {k: v for k, v in q.items() if k != "_status"},
                            "refusals": sum(len(c["refusals"]) for c in run),
                            "citations": sum(c["citations"]["citations"] for c in run),
                            "unsupported_citations": sum(c["citations"]["unsupported"] for c in run),
                            "vs_SDR_veto_acquire": contrast(truth, noms, flat(arms["SDR_veto_acquire"])),
                            "vs_SDR_veto": contrast(truth, noms, flat(arms["SDR_veto"]))})
    r6 = [r["vs_SDR_veto_acquire"] for r in out["runs"]]
    out["R6_debate_adds_value"] = "CONFIRMED" if r6 and all(x["difference"] > 0 and x["p_greater"] <= ALPHA for x in r6) else "NOT_CONFIRMED"
    return out


def main() -> None:
    require_freeze()
    choices = load_choices()
    t = load_table()
    truth = Truth(t, qualified_outcomes("test"))
    text = json.dumps(build(t, truth, choices), indent=1) + "\n"
    if RESULTS.exists():
        if RESULTS.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
            raise SystemExit("RESULTS_MISMATCH: recomputed results differ from TEST_RESULTS.json")
        print("REPRODUCED TEST_RESULTS.json")
    else:
        RESULTS.write_bytes(text.encode())
        print("WROTE TEST_RESULTS.json")
    for source, target, scorer in (("AGENT_CHOICES.json", AGENT_RESULTS, score_agents),
                                   ("SDR_DEBATE_CHOICES.json", HERE / "SDR_DEBATE_RESULTS.json", score_debate)):
        if (HERE / source).exists():
            agent_text = json.dumps(scorer(truth, choices), indent=1) + "\n"
            if target.exists() and target.read_text(encoding="utf-8").replace("\r\n", "\n") != agent_text:
                raise SystemExit(f"RESULTS_MISMATCH: {target.name}")
            target.write_bytes(agent_text.encode())


if __name__ == "__main__":
    main()
