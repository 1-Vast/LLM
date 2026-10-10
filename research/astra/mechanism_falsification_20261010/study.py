"""Shared construction for block M: tier-guarded data, basis, noise, compilers, calibration.

Only reference drugs fit anything (basis, prototypes, noise, potency prior, knowledge slopes,
calibration scores, simulation residuals). Query drugs (development or confirmation) are only ever
scored. The confirmation file is refused by name (``TIER_SEALED``) until FREEZE.json exists.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import falsify as F
import knowledge as KN

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DERIVED = ROOT / "data/external/lincs_l1000_gse92742/derived"


def load_tier(tier: str) -> dict:
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    if tier == "open":
        path = DERIVED / "block_m_landmark_open.npz"
    elif tier == "sealed":
        if not (HERE / "FREEZE.json").exists():
            raise SystemExit("TIER_SEALED: confirmation drugs open only after FREEZE.json")
        path = DERIVED / "block_m_landmark_sealed.npz"
    else:
        raise ValueError(tier)
    # the extraction stored gene symbols as an object array; the file is checked against the
    # extraction receipt's digest before that one key is read with pickling allowed
    receipt = json.loads((HERE / "EXTRACT_RECEIPT.json").read_text(encoding="utf-8"))
    want = receipt["output_sha256" if tier == "open" else "sealed_sha256"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != want:
        raise SystemExit(f"TIER_DIGEST_MISMATCH: {path.name}")
    with np.load(path, allow_pickle=False) as f:
        d = {k: f[k] for k in f.files if k != "gene"}
    with np.load(path, allow_pickle=True) as f:
        d["gene"] = np.array([str(g) for g in f["gene"]])
    d["moa"] = np.array([split["drugs"][x]["moa"] for x in d["drug"]])
    d["role"] = np.array([split["drugs"][x]["role"] for x in d["drug"]])
    d["options"] = [str(o) for o in d["option"]]
    d["genes"] = [str(g) for g in d["gene"]]
    d["split"] = split
    return d


@dataclass
class Config:
    k: int = 64              # basis dimension
    kappa: float = 1.0       # shrinkage weight toward the generic or knowledge prototype
    alpha: float = 0.10
    compile: str = "data"    # data | hybrid | knowledge  (how classes WITH references are represented)
    emh_variant: str = "lit" # which agent hypotheses represent classes (and serve as hybrid targets)
    permute_classes: bool = False  # control: shuffle class labels among reference drugs
    permute_emh: bool = False      # control: shuffle EMHs across classes
    knowledge_for_unreferenced: bool = True  # False = world model only (C2): unreferenced classes cannot be rejected
    kcal: str = "mateless"   # knowledge-bucket calibration rows: mateless | small (classes of <= 3 drugs) | all
    score: str = "absolute"  # absolute | relative (NLL minus the best NLL in the hypothesis set)
    n_bins: int = 1          # Mondrian bins by observed energy (1 = none)
    tau2: float = 0.0        # potency prior variance; 0 = estimated from reference potencies (floored at 0.05)
    calib: str = "set"       # set = exact-option-set calibration | episode = calibrate the whole adaptive procedure
    knowledge: str = "emh"   # how agent knowledge becomes a prediction: emh (gene programs) | analogy
                             # (agent-chosen analog classes' reference means) | analogy_permuted | generic
    seed: int = 20261010


@dataclass
class Built:
    cfg: Config
    basis: F.Basis
    Z_open: np.ndarray       # projected open-tier signatures (n_open, n_opt, K)
    models: list
    model_index: dict
    cal: F.Calibration
    resid_pool: np.ndarray
    option_order: np.ndarray
    slopes: dict
    emh_classes: set
    lam_pool: np.ndarray | None = None  # fitted potencies of reference drugs (data buckets), for simulation


def all_classes(split: dict) -> list[str]:
    return sorted({v["moa"] for v in split["drugs"].values()})


def build(data: dict, cfg: Config) -> Built:
    X, moa, role = data["x"], data["moa"].copy(), data["role"]
    options, genes, split = data["options"], data["genes"], data["split"]
    ref = role == "reference"
    rng = np.random.default_rng(cfg.seed)
    if cfg.permute_classes:
        idx = np.where(ref)[0]
        moa[idx] = moa[idx][rng.permutation(len(idx))]
    basis = F.Basis.fit(X[ref], cfg.k)
    Z = np.where(np.isnan(X[..., :1]), np.nan, basis.project(np.nan_to_num(X)))
    classes = all_classes(split)

    # agent hypotheses -> knowledge prototypes (gene space, slopes fitted on reference drugs)
    emhs = KN.load_emhs(HERE, cfg.emh_variant, classes)
    if cfg.permute_emh:
        keys = sorted(emhs)
        vals = [emhs[k] for k in keys]
        perm = rng.permutation(len(keys))
        emhs = {k: dict(vals[perm[i]], mechanism=k) for i, k in enumerate(keys)}
    slopes = KN.fit_slopes(X, moa, ref, emhs, genes, options)
    kg = KN.compile_gene_space(emhs, genes, options, slopes)
    kproto = {c: basis.project(v) for c, v in kg.items()}

    # generic prototype per option (all reference drugs) and data prototypes
    generic = np.nanmean(Z[ref], axis=0)
    data_mean = F.class_prototypes(Z, moa, ref, None, 0.0)
    if cfg.knowledge in ("analogy", "analogy_permuted"):
        an = KN.load_analogies(HERE, classes)
        if cfg.knowledge == "analogy_permuted":  # control: analog lists shuffled across classes
            keys = sorted(an)
            perm = np.random.default_rng(cfg.seed + 1).permutation(len(keys))
            an = {k: an[keys[perm[i]]] for i, k in enumerate(keys)}
        kproto = KN.compile_analogies(an, data_mean, generic)
    elif cfg.knowledge == "generic":
        kproto = {c: generic.copy() for c in classes}
    elif cfg.knowledge != "emh":
        raise ValueError(cfg.knowledge)

    def proto_for(c: str, n: int, mean: np.ndarray | None) -> tuple[np.ndarray, str]:
        if n == 0 or mean is None:
            if c in kproto and cfg.knowledge_for_unreferenced:
                return kproto[c], "knowledge"
            return np.full_like(generic, np.nan), "knowledge"
        target = kproto.get(c, generic) if cfg.compile in ("hybrid",) else generic
        filled = np.where(np.isnan(mean), target, mean)
        if cfg.compile == "knowledge" and c in kproto:
            return kproto[c], "knowledge"
        # shrink: (n * mean + kappa * target) / (n + kappa), per option with the option's own count
        return (n * filled + cfg.kappa * target) / (n + cfg.kappa), cfg.compile if cfg.compile != "knowledge" else "data"

    models, index = [], {}
    for c in classes:
        mean, n = data_mean.get(c, (None, 0))
        proto, kind = proto_for(c, n, mean)
        index[c] = len(models)
        models.append(F.HypothesisModel(name=c, proto=proto, n=n if kind != "knowledge" else 0, kind=kind))

    # leave-self-out own-class prototypes for calibration drugs (reference drugs only)
    ref_idx = np.where(ref)[0]
    own = np.full((len(ref_idx),) + Z.shape[1:], np.nan)
    bucket = np.empty(len(ref_idx), dtype=object)
    for j, i in enumerate(ref_idx):
        c = moa[i]
        mates = ref & (moa == c)
        mates[i] = False
        n = int(mates.sum())
        mean = None
        if n > 0:
            sub = Z[mates]
            cnt = (~np.isnan(sub[..., 0])).sum(axis=0)
            mean = np.where(cnt[:, None] > 0, np.nansum(sub, axis=0) / np.maximum(cnt, 1)[:, None], np.nan)
        proto, kind = proto_for(c, n, mean)
        own[j] = proto
        bucket[j] = F.bucket_of(n if kind != "knowledge" else 0, kind)

    # noise: per-option, per-dimension variance of reference residuals around own-class LOO prototypes (lambda fitted)
    Zr = Z[ref_idx]
    var = np.ones(Z.shape[1:])
    resid = np.full_like(Zr, np.nan)
    for _ in range(2):  # one refinement of lambda with the updated variance
        noise_tmp = F.NoiseModel(var=var, tau2=1.0)
        lam = np.ones(len(ref_idx))
        for j in range(len(ref_idx)):
            o = np.where(~np.isnan(Zr[j, :, 0]) & ~np.isnan(own[j, :, 0]))[0]
            if len(o) == 0:
                continue
            _, l = F.score_batch(Zr[j:j + 1, o], own[j:j + 1, o], noise_tmp, o)
            lam[j] = l[0]
            resid[j, o] = Zr[j, o] - l[0] * own[j, o]
        data_rows = bucket != "K"  # knowledge-only calibration drugs do not set the noise scale
        var = np.nanmean(resid[data_rows] ** 2, axis=0)
        var = np.where(np.isfinite(var) & (var > 1e-6), var, np.nanmedian(var))
    tau2 = float(np.var(lam[(bucket != "K") & np.isfinite(lam)]))
    noise = F.NoiseModel(var=var, tau2=cfg.tau2 if cfg.tau2 > 0 else max(tau2, 0.05))
    # knowledge-bucket calibration: reference drugs scored against their own class's compiled agent
    # hypothesis. "mateless" keeps only drugs with no other reference drug in their class (rows above);
    # "small" adds every reference drug of a class with <= 3 drugs in the universe; "all" adds all.
    Zc, oc, bc = [Zr], [own], [bucket.astype(str)]
    cc = [np.array([index[moa[i]] for i in ref_idx])]
    if cfg.kcal in ("small", "all"):
        size = {}
        for v in split["drugs"].values():
            size[v["moa"]] = size.get(v["moa"], 0) + 1
        extra = [j for j, i in enumerate(ref_idx) if bucket[j] != "K" and moa[i] in kproto
                 and (cfg.kcal == "all" or size.get(moa[i], 0) <= 3)]
        if extra:
            Zc.append(Zr[extra])
            oc.append(np.stack([kproto[moa[ref_idx[j]]] for j in extra]))
            bc.append(np.full(len(extra), "K"))
            cc.append(np.array([index[moa[ref_idx[j]]] for j in extra]))
    elif cfg.kcal != "mateless":
        raise ValueError(cfg.kcal)
    cal = F.Calibration(Z=np.concatenate(Zc), own_proto=np.concatenate(oc), bucket=np.concatenate(bc), noise=noise,
                        P=np.stack([m.proto for m in models]), cal_class=np.concatenate(cc), mode=cfg.score, n_bins=cfg.n_bins)
    pool = []
    for o in range(Z.shape[1]):
        r = resid[:, o]
        pool.append(r[~np.isnan(r[:, 0])])
    m = min(len(p) for p in pool)
    resid_pool = np.stack([p[:m] for p in pool])
    # fixed design order: options by mean reference response norm (largest first), ties by name
    norms = np.nanmean(np.linalg.norm(Z[ref], axis=2), axis=0)
    order = np.array(sorted(range(len(options)), key=lambda o: (-norms[o], options[o])))
    return Built(cfg=cfg, basis=basis, Z_open=Z, models=models, model_index=index, cal=cal, resid_pool=resid_pool,
                 option_order=order, slopes=slopes, emh_classes=set(emhs),
                 lam_pool=lam[(bucket != "K") & np.isfinite(lam)].copy())


def falsifier(b: Built) -> F.Falsifier:
    return F.Falsifier(b.models, b.cal, b.resid_pool, b.cfg.alpha, b.option_order, rng_seed=b.cfg.seed)


def available(data: dict, i: int) -> list[int]:
    return [j for j in range(len(data["options"])) if not np.isnan(data["x"][i, j, 0])]
