"""Stage 2: confirm every frozen edit on held-out compounds x held-out lineages in ONE masked transfer read; write RECORDS.json once.

Requires FREEZE0 and FREEZE1. The hidden evaluator lives in this function; arms never see it.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import obs_seal  # noqa: E402

warnings.filterwarnings("ignore")


def main():
    obs_seal.check(0)
    obs_seal.check(1)
    out = HERE / "RECORDS.json"
    if out.exists():
        raise SystemExit("RECORDS_EXIST (write-once)")
    import masked_interface as M
    import obs_core as O

    W = O.build_world()
    idx = {n: i for i, n in enumerate(W.names)}
    edits = json.loads((HERE / "EDITS.json").read_text(encoding="utf-8"))["edits"]

    def hidden(role, decisions):
        return [{**{k: e[k] for k in ("family", "arm", "variable", "sign", "magnitude", "p")}, "meta": e.get("meta", {}),
                 **O.confirm(W, e["family"], idx[e["variable"]], e["sign"], e["magnitude"])} for e in decisions]

    iface = M.MaskedOutcomeInterface(hidden, HERE / "ACCESS_LEDGER.jsonl", freeze_check=lambda: (obs_seal.check(0), obs_seal.check(1)))
    recs = iface.query("transfer", edits)
    out.write_bytes((json.dumps(recs, indent=1) + "\n").encode())
    print("records", len(recs), "confirmed", sum(r["confirmed"] for r in recs))


if __name__ == "__main__":
    main()
