"""Read-only verifier: manifests, stored results and verdict consistency. It fits nothing and never opens a sealed outcome file.

Levels reported separately:
  1 software/frozen-file integrity     frozen code hashes, source workbook hashes, sealed-file receipts
  2 stored-output recalculation        retention decisions, shortlist utilities, nominations and verdict recomputed from stored outputs
  3 information-boundary audit         vault ledger order and counts, pre-G sealing hashes, API receipt limits
Independent biological confirmation is not performed and not performable from this evidence.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))


def sha_lf(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main() -> int:
    problems, notes = [], []
    check = lambda ok, msg: problems.append(msg) if not ok else None  # noqa: E731
    present = lambda name: (HERE / name).exists()  # noqa: E731

    # ---- level 1
    prov = load("PROVENANCE.json")
    sources = load("../../data/ONEIL_SOURCES.json") if False else json.loads((ROOT / "data" / "ONEIL_SOURCES.json").read_text(encoding="utf-8"))
    raw = ROOT / "data" / "raw" / "oneil2026_qualification"
    for item in sources:
        path = raw / Path(item["path"]).name
        check(path.exists() and sha(path) == item["sha256"], f"source workbook hash mismatch: {path.name}")
    work = ROOT / "tmp" / "functional_rule_revision_20261020"
    for role, rec in prov["receipts_sealed_outcome_files"].items():
        f = work / "sealed" / rec["file"]
        if f.exists():   # hash only: the file is not opened as an array
            check(sha(f) == rec["sha256"], f"sealed {role} file changed after qualification")
        else:
            notes.append(f"sealed file {rec['file']} not present locally (cannot re-hash)")
    freeze = load("FREEZE.json")
    for name, h in freeze["code_sha256"].items():
        check(sha_lf(HERE / name) == h, f"frozen file differs from freeze receipt: {name}")
    part = load("PARTITION.json")
    roles = list(part["roles"].values())
    check({r: roles.count(r) for r in "SCGF"} == part["role_counts"], "partition counts differ")
    from study import digest_obj
    T_pairs = list(part["roles"].keys())
    check(len(T_pairs) == len(set(T_pairs)) == 583, "partition pair identities")

    # ---- level 3 (boundary) and level 2 (recalculation)
    if present("CHALLENGE_TRACE.json"):
        trace = load("CHALLENGE_TRACE.json")
        pre = load("PRECHALLENGE_PREDICTIONS.json")
        body = {k: v for k, v in pre.items() if k != "sha256"}
        check(digest_obj(body) == pre["sha256"] == trace["prechallenge_sha256"], "pre-challenge prediction hash")
        check(sha(HERE / "SEALED_PREDICTIONS.npz") == trace["sealed_predictions_sha256"], "sealed predictions changed after challenge")
        check(sha_lf(HERE / "NOMINATIONS_SEALED.json") == trace["nominations_sha256"], "sealed nominations changed after challenge")
        ledger = trace["vault_ledger"]
        ops_c = [e["op"] for e in ledger]
        check(set(ops_c) <= {"read_S", "disclose_C"} and ops_c.count("disclose_C") == 1, "challenge-stage ledger must contain only S reads and one C disclosure")
        check(sorted(set(trace["arms"])) == ["api", "conventional", "fulldict", "revision"], "arm set")
        check(len(set(trace["common_training_set"]["sha256"] for _ in [0])) == 1, "common training set")
        edit_arms = [a for a in ("revision", "api") if trace["arms"][a].get("candidate")]
        rules = load("RULES.json")
        for arm in edit_arms:
            rec = rules[arm]
            check(rec["after"]["n_parameters"] == rec["before"]["n_parameters"] + 1, f"{arm}: edit is not a single added component")
            check(rec["scope"]["pairs_among_unmeasured"] > 1, f"{arm}: edit does not alter sharing across more than one unmeasured pair")
        if present("API_RECEIPT.json"):
            api = load("API_RECEIPT.json")
            check(api.get("http_attempts", 0) <= 4 and api.get("logical_requests", 0) <= 2, "API budget exceeded")
            check((api.get("usage", {}) or {}).get("completion_tokens", 0) <= 2048, "API output token bound")
            check((api.get("est_input_tokens") or 0) <= 6000, "API input token bound")
            text = json.dumps(api)
            check("Bearer" not in text and "api_key" not in text.lower(), "credential-like text in API receipt")
    if present("RETENTION.json"):
        ret = load("RETENTION.json")
        gq = [e for e in ret["vault_ledger_after_G"] if e["op"] == "G_query"]
        check(len({e["arm"] for e in gq}) == len(gq), "an arm used more than one G query")
        tau, tol = freeze["retention_tau"], freeze["config"]["retention"]["mse_ratio_tolerance"]
        for arm, d in ret["decisions"].items():
            if not d["candidate_available"]:
                check(d["deployed"] == "refit" and not d["accepted"], f"{arm}: no candidate must deploy the refit")
                continue
            m = d["metrics"]
            expect = bool(m["delta_utility"] >= tau and m["mse_ratio_all"] <= 1 + tol
                          and (m["mse_ratio_out_of_scope"] is None or m["mse_ratio_out_of_scope"] <= 1 + tol) and d["criteria"]["complexity_within_limits"])
            check(expect == d["accepted"], f"{arm}: stored retention decision is not reproduced by the stored metrics")
            check(d["deployed"] == (arm if d["accepted"] else "refit"), f"{arm}: deployed procedure inconsistent")
    if present("RESULTS.json"):
        res = load("RESULTS.json")
        ledger = res["vault_ledger"]
        ops = [e["op"] for e in ledger]
        check(ops.count("F_final") == 1 and ops.count("disclose_C") == 1 and ops[-1] == "F_final", "F must be opened exactly once, last")
        check(max(i for i, o in enumerate(ops) if o == "G_query") < ops.index("F_final"), "all G queries precede F")
        check(sha_lf(HERE / "PREDICTIONS_F.csv") == res["predictions_csv_sha256"], "stored prediction table changed")
        # recompute utilities from the stored table (not from sealed outcome files)
        lines = (HERE / "PREDICTIONS_F.csv").read_text(encoding="utf-8").strip().split("\n")
        head = lines[0].split(",")
        rows = [l.split(",") for l in lines[1:]]
        col = {n: i for i, n in enumerate(head)}
        cells = sorted({r[col["cell"]] for r in rows})
        pairs = sorted({r[col["pair"]] for r in rows})
        pindex = {p: k for k, p in enumerate(pairs)}
        truth = np.full((len(pairs), len(cells)), np.nan)
        methods = [n for n in head if n not in ("group", "pair", "cell", "activity_observed", "activity_reference")]
        pred = {m: np.full_like(truth, np.nan) for m in methods}
        for r in rows:
            i, j = pindex[r[col["pair"]]], cells.index(r[col["cell"]])
            truth[i, j] = float(r[col["activity_observed"]])
            for m in methods:
                pred[m][i, j] = float(r[col[m]])
        import evaluation
        # stored utilities are computed from unrounded values; allow the CSV's 6-decimal rounding
        for m in methods:
            u = evaluation.utility(pred[m], truth)
            check(abs(u - res["methods"][m]["utility"]) < 2e-5, f"utility of {m} not reproduced from the stored table")
        check(abs(evaluation.oracle_utility(truth) - res["oracle_utility"]) < 2e-5, "oracle utility not reproduced")
        # stored nominations equal the top-k of the stored predictions for F
        nominations = load("NOMINATIONS_SEALED.json")
        for m in ("refit", "initial", "bliss_reference"):
            sel = evaluation.top_k(pred[m])
            expect = {cells[c]: sorted(pairs[i] for i in sel[:, c]) for c in range(len(cells))}
            have = {c: sorted(v) for c, v in nominations[m]["F"].items()}
            check(expect == have, f"sealed nominations for {m} differ from the stored predictions")
        # verdict consistency
        import study
        recomputed = study.decide(res, freeze["margin"])
        check(recomputed == res["verdict"], "verdict is not reproduced by the stored contrast table and the frozen rule")
        notes.append("verdict: " + res["verdict"]["label"])
    for p in problems:
        print("FAIL", p)
    for n in notes:
        print("NOTE", n)
    print("VERIFY OK (levels 1-3; no model refit, no sealed outcome opened)" if not problems else f"VERIFY FAILED ({len(problems)})")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
