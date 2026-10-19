"""Write FREEZE.json (write-once) before the single kb_run.py run. Digests are sha256 over bytes with CRLF normalised to LF."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AS = ROOT / "research/action_substitution_20261019"
KL = ROOT / "data/external/klaeger2017_chembl"
FILES = ["PROTOCOL.md", "kb_run.py", "mapping.py", "MAPPING.json", "fetch_klaeger.py", "freeze.py"]
REUSED = ["lofo.py", "cas_data.py", "repro.py", "CENSUS.json", "lofo_units_SYNERGY_DELTA_AUC.csv", "LOFO_SYNERGY_DELTA_AUC.json"]


def digest(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    out = HERE / "FREEZE.json"
    if out.exists():
        raise SystemExit("FREEZE.json exists (write-once)")
    as_freeze = json.loads((AS / "FREEZE.json").read_text(encoding="utf-8"))["files"]
    for f in ("lofo.py", "cas_data.py", "repro.py", "CENSUS.json"):
        assert digest(AS / f) == as_freeze[f], f"{f} differs from the action-substitution freeze"
    fr = dict(frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              scope="kb_run.py before any binding correlation, kernel prediction or test statistic was computed",
              eol="sha256 over bytes with CRLF normalised to LF",
              files={f: digest(HERE / f) for f in FILES},
              reused_from_action_substitution={f: digest(AS / f) for f in REUSED},
              data={p.name: digest(p) for p in (KL / "klaeger2017_CHEMBL3991601_kd.csv", KL / "molecules.json")},
              smoke=("kb_run.py --smoke: binding matrix 243 x 320, 31 mapped drugs with a profile row, 435 finite pairs; "
                     "reproduction gate PASS (1,950 units, 0 unmatched, max |diff| 1e-16); 27 implementations, K finite. "
                     "Measured-binder counts per mapped drug inspected (Dactolisib 0) -> primary restricted to defined "
                     "profiles before this freeze. No metric printed."))
    out.write_text(json.dumps(fr, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(fr, indent=1))


if __name__ == "__main__":
    main()
