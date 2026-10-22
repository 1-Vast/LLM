"""Episode sets for the research-program experiments: stage x world-model version -> list of episodes (cached as pickles in RUN/episodes)."""
from __future__ import annotations
import pickle, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import ptv_tasks as T, ptv_direct as X, ptv_episodes as EP, eval_R as R

HERE = Path(__file__).parent
CACHE = HERE / "RUN" / "episodes"


def w_from_npz(rundir, stage, variant, epoch, seed=0):
    parts = []
    for f in sorted(Path(rundir).glob(f"{stage}_*_{variant}_s{seed}.npz")):
        z = np.load(f, allow_pickle=True)
        parts.append(pd.DataFrame({"cell": z["cell"], "perts": z["perts"], "single": z["single"], "w": z[f"p_e{epoch}"]}))
    d = pd.concat(parts); return d[d.single][["cell", "perts", "w"]]


def build(stage, w1_table, tag):
    """Episodes with W0 = M0 (logistic direct predictor), W1 = given table, B1 = strongest conventional prior; molecular tool included."""
    P = T.Prep(); dr = X.Direct(P)
    sc = R.direct_scores(P, dr, stage, None)
    out = {}
    for name, ws in (("W0", sc[["cell", "perts", "m0_lr"]].rename(columns={"m0_lr": "w"}).dropna()), ("W1", w1_table), ("B1", sc[["cell", "perts", "b1"]].rename(columns={"b1": "w"}).dropna())):
        out[name] = EP.build_episodes(P, dr, stage, ws, with_mol=(name != "B1"))
    CACHE.mkdir(parents=True, exist_ok=True)
    pickle.dump(out, open(CACHE / f"{stage}_{tag}.pkl", "wb"))
    return out


def load(stage, tag):
    return pickle.load(open(CACHE / f"{stage}_{tag}.pkl", "rb"))
