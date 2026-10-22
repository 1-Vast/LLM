"""Independent founder-level exact arithmetic; no biological inputs or peer imports."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PEER = ROOT / "log/20261022/renewal_application/skeptic"
OUT = ROOT / "log/20261022/renewal_application/advocate/COUNTEREXAMPLE_CHECK.json"


def founders(change):
    cells = [("A", "A", 1)] * 198 + [("B", "B", 1)] * 198
    if change:
        return cells + [("A", "B", 2), ("A", None, 0),
                        ("B", "B", 2), ("B", None, 0)]
    return cells + [("A", None, 0)] * 2 + [("B", "B", 2)] * 2


def observe(cells):
    offspring = [(origin, destination, int(number == 2))
                 for origin, destination, number in cells for _ in range(number)]
    return {
        "initial": Counter(origin for origin, _, _ in cells),
        "joint": Counter((state, generation) for _, state, generation in offspring),
        "flow": Counter((origin, state) for origin, state, _ in offspring),
        "divisions": sum(number == 2 for _, _, number in cells),
        "deaths": sum(number == 0 for _, _, number in cells),
        "total": len(offspring),
    }


def main():
    # These are hand-written synthetic founders, not a call to the peer implementation.
    selection, change = observe(founders(False)), observe(founders(True))
    expected = Counter({("A", 0): 198, ("B", 0): 198, ("B", 1): 4})
    peer = json.loads((PEER / "SELECTION_TRANSPORT_RESULT.json").read_text(encoding="utf-8"))
    freeze = json.loads((PEER / "SELECTION_TRANSPORT_FREEZE.json").read_text(encoding="utf-8"))
    checks = {
        "frozen_files_match": all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                                  for name, digest in freeze["files"].items()),
        "initial_exact": selection["initial"] == change["initial"] == Counter(A=200, B=200),
        "endpoint_joint_exact": selection["joint"] == change["joint"] == expected,
        "totals_exact": selection["total"] == change["total"] == 400,
        "division_events_exact": selection["divisions"] == change["divisions"] == 2,
        "death_events_exact": selection["deaths"] == change["deaths"] == 2,
        "mass_balance": all(x["total"] == 400 + x["divisions"] - x["deaths"]
                            for x in (selection, change)),
        "hidden_A_to_B_exact": (selection["flow"]["A", "B"], change["flow"]["A", "B"]) == (0, 2),
        "origin_A_total_differs": (sum(v for (a, _), v in selection["flow"].items() if a == "A"),
                                   sum(v for (a, _), v in change["flow"].items() if a == "A")) == (198, 200),
        "cycling_fraction_exact": Fraction(sum(v for (_, g), v in expected.items() if g), 400) == Fraction(1, 100),
    }
    weights = {s: Fraction(sum(expected[s, g] for g in (0, 1)), 400) for s in ("A", "B")}
    cycling = {s: Fraction(expected[s, 1], sum(expected[s, g] for g in (0, 1))) for s in ("A", "B")}
    mixture = {(s, g): 400 * weights[s] * (cycling[s] if g else 1 - cycling[s])
               for s in ("A", "B") for g in (0, 1)}
    checks["mixture_exact_not_truncated"] = all(v.denominator == 1 and v == expected[k] for k, v in mixture.items())
    own_joint = {s + "|" + str(g): expected[s, g] for s in ("A", "B") for g in (0, 1)}
    checks["saved_peer_joint_matches"] = own_joint == peer["observed"]["endpoint_state_generation"]
    checks["saved_peer_flow_matches"] = all(
        {a + ">" + b: x["flow"][a, b] for a in ("A", "B") for b in ("A", "B")} == peer["hidden_flows"][name]
        for name, x in (("selection_only", selection), ("state_change", change)))
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
              "endpoint_joint": own_joint,
              "cycling_given_state": {s: str(v) for s, v in cycling.items()},
              "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "peer_result_sha256": hashlib.sha256((PEER / "SELECTION_TRANSPORT_RESULT.json").read_bytes()).hexdigest(),
              "biological_reads": 0, "HTTP": 0, "fits": 0}
    with OUT.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps(result))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
