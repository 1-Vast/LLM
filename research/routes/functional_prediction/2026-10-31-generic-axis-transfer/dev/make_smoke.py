"""Fake confirmation sets drawn from the exposed development pool only (code-path smoke test, no real outcomes)."""
import sys
import numpy as np
d = np.load(sys.argv[1] + "/dev_pool.npz", allow_pickle=True)
rng = np.random.default_rng(0)
Y, X, fp = d["profile"], d["signature"], d["fingerprint"]
idx = rng.choice(len(Y), 400, replace=False)
cols = rng.choice(Y.shape[1], 60, replace=False)
act = np.nanmean(Y[idx] <= -1.0, axis=1) >= 0.05
np.savez_compressed(sys.argv[1] + "/nci60.npz", key=d["drug"][idx], line=d["line"][cols], profile=-Y[idx][:, cols],
                    signature=X[idx], option=d["option"], fingerprint=fp[idx], active=act,
                    killed_lines=np.zeros(400, int), fold=np.arange(400) % 10)
q = rng.choice(len(Y), 80, replace=False)
lines = d["line"][:450]
np.savez_compressed(sys.argv[1] + "/prism24q2.npz", key=d["drug"][q], line=lines, profile=Y[q][:, :450],
                    signature=X[q], option=d["option"], fingerprint=fp[q],
                    active=np.nanmean(Y[q][:, :450] <= -1.0, axis=1) >= 0.05, parsed_treatments=80,
                    dropped_in_pool=np.array([], dtype=str))
print("smoke sets written", int(act.sum()))
