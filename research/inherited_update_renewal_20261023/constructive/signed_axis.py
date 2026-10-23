"""Predeclared exact two-case signed-axis cancellation check."""
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "log/20261023/inherited_update_renewal/constructive"
q = [Q(0),Q(0),Q(0),Q(0),Q(1),Q(2)]
feedback = [Q(0),Q(0),Q(0),Q(0),Q(1),Q(1)]
query = [Q(0),Q(0),Q(0),Q(0),Q(0),Q(1)]
epsilon = Q(1,10)

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def scale(a,v): return [a*x for x in v]
def fit(v):
    response = dot(feedback,v)
    alpha = Q(3)/response if response else Q(0)
    pred = scale(alpha,v)
    return {"alpha":alpha,"feedback_prediction":dot(feedback,pred),
            "held_prediction":dot(query,pred),"held_squared_error":(dot(query,pred)-2)**2}

results = {}
for name,amps in [("same_signed_mean",[Q(1),Q(3)]),("opposite_signed_shared_axis",[Q(1),Q(-1)])]:
    histories = [scale(a,q) for a in amps]
    mean_direction = [sum(h[i] for h in histories)/(len(histories)+epsilon) for i in range(6)]
    assert mean_direction[:4] == [0]*4
    second_moment = [[sum(h[i]*h[j] for h in histories) for j in range(6)] for i in range(6)]
    coefficient = sum(a*a for a in amps)
    assert second_moment == [[coefficient*q[i]*q[j] for j in range(6)] for i in range(6)]
    action_on_q = [dot(row,q) for row in second_moment]
    assert action_on_q == scale(coefficient*dot(q,q),q)
    assert coefficient*dot(q,q)>0
    # Select a nonzero column of the source-only rank-one second moment.
    basis = next([row[j] for row in second_moment] for j in range(6) if any(row[j] for row in second_moment))
    candidate,ordinary = fit(mean_direction),fit(basis)
    assert ordinary["held_squared_error"] == 0
    if name == "same_signed_mean":
        assert candidate["held_squared_error"] == 0
        assert candidate["feedback_prediction"] == 3
    else:
        assert mean_direction == [0]*6
        assert candidate["held_squared_error"] == 4
        assert candidate["feedback_prediction"] == 0
    results[name] = {"history_amplitudes":amps,"mean_direction":mean_direction,
                     "source_second_moment_basis":basis,"candidate":candidate,"ordinary_rank_one":ordinary}

def serial(v):
    if isinstance(v,Q): return {"exact":str(v),"float":float(v)}
    if isinstance(v,list): return [serial(x) for x in v]
    if isinstance(v,dict): return {k:serial(x) for k,x in v.items()}
    return v

payload = {"protocol_sha256":hashlib.sha256((OUT/"SIGNED_AXIS_PROTOCOL.md").read_bytes()).hexdigest(),
           "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "epsilon":epsilon,"lambda_R":0,"cases":results,
           "scope":"two exact synthetic cases; root check unread; not biological replication or RSI"}
(OUT/"SIGNED_AXIS_RESULT.json").write_text(json.dumps(serial(payload),indent=2),encoding="utf-8")
print(json.dumps(serial(payload),indent=2))
