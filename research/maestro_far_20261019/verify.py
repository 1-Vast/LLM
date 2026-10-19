"""Verify MAESTRO-FAR: files, freeze hashes, DECISION.json recompute from saved atlas/contrasts, one contrast recomputed from the saved records, registry, no stray paths."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))


def main():
    fail = []
    for f in ("AUDIT.md", "PROTOCOL.md", "FREEZE_PROTOCOL.md", "REPORT.md", "DEVIATIONS.json", "EDGES.json", "FREEZE.json", "records_test.npz", "records_vault.npz", "DECISION.json"):
        if not (HERE / f).exists():
            fail.append("missing " + f)
    from far_run import sha
    for f, h in json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))["hashes"].items():
        if sha(HERE / f) != h:
            fail.append("freeze mismatch " + f)
    from far_decide import decide
    if decide() != json.loads((HERE / "DECISION.json").read_text(encoding="utf-8")):
        fail.append("DECISION.json does not recompute")
    import far_analyse
    r = far_analyse.contrast("test", ("far", "gate"), ("exploit", "gate"), "U")
    saved = json.loads((HERE / "CONTRASTS_test_U.json").read_text(encoding="utf-8"))["contrasts"]["far.gate-exploit.gate"]
    if abs(r["diff"] - saved["diff"]) > 1e-9 or abs(r["ci95"][0] - saved["ci95"][0]) > 1e-9:
        fail.append("C1 test contrast does not recompute")
    if json.loads((HERE / "DECISION.json").read_text(encoding="utf-8"))["verdict"] != "FAR_NOT_SUPPORTED":
        fail.append("unexpected verdict")
    reg = json.loads((ROOT / "research/STUDIES.json").read_text(encoding="utf-8"))["studies"]
    if not any(s["path"] == "maestro_far_20261019" for s in reg):
        fail.append("not registered")
    st = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True).stdout.replace("\\", "/").splitlines()
    ok = ("research/maestro_far_20261019", "research/STUDIES.json", "log/DIRECTIONS.md", "research/EVIDENCE.md")
    stray = [l for l in st if not any(a in l for a in ok)]
    if stray:
        fail.append(f"unexpected paths {stray}")
    print("VERIFIED" if not fail else "FAILED: " + "; ".join(fail))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
