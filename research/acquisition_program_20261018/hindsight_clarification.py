"""Recompute the campaign-level hindsight selector of feedback_propagation_20261018 from its public records.

File summary
- Path: research/acquisition_program_20261018/hindsight_clarification.py
- Purpose: `D_hindsight` of the predecessor chooses, per compound, the model with the lower squared error on
  unmeasured cells (a model-fit criterion read from the hidden side), not the list with the higher terminal decision
  utility. This script instead chooses, per complete 64-compound campaign, the better of the ridge and R1
  nomination lists by realised hits. It is an unavailable hindsight diagnostic (it reads the outcome), never a policy.
- Reads only records/E_fold{2,3,4}.json of the predecessor; writes HINDSIGHT_CLARIFICATION.json (write-once).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REC = HERE.parent / "feedback_propagation_20261018" / "records"
out = HERE / "HINDSIGHT_CLARIFICATION.json"
tot = {"ridge": 0, "R1": 0, "campaign_best_of": 0}
n = 0
for f in (2, 3, 4):
    r = json.loads((REC / f"E_fold{f}.json").read_text(encoding="utf-8"))["A_B3"]
    for a, b, s in zip(r["ridge"]["unmeasured"]["campaign_hits"], r["R1"]["unmeasured"]["campaign_hits"],
                       r["R1"]["unmeasured"]["campaign_compounds"]):
        if s != 64:
            continue
        n += 1
        tot["ridge"] += a
        tot["R1"] += b
        tot["campaign_best_of"] += max(a, b)
res = {"complete_campaigns": n, "hits": tot,
       "reading": "campaign-level choice of the better complete ridge/R1 list by realised hits is an unavailable hindsight "
                  "diagnostic; the predecessor's D_hindsight chose models per compound by squared error (a fit criterion), "
                  "so its hindsight_gate/best_of figures are not terminal-decision ceilings."}
if not out.exists():
    out.write_bytes((json.dumps(res, indent=1) + "\n").encode())
print(res)
