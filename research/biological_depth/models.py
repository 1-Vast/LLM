"""Arms for the biological-depth audit: baselines, the current learned rung and latent world models.

File summary
- Path: research/biological_depth/models.py
- Purpose: fit every pre-registered arm on one training fold and predict held-out compounds, so
  all arms see identical inputs, splits and cost.
- Core points:
  - No arm reads a held-out compound's cells, shifts or annotation except where its declaration
    says so (the annotation-conditioned family).
  - The latent arms share one pharmacological transition head; only the encoder differs, so a
    difference between them is attributable to the representation.
  - The transition is exactly zero at vehicle dose by construction.
- Depends on: numpy, torch, sklearn, rdkit, src/virtual_cell/learned_response.py
"""
from __future__ import annotations

import copy
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
LOG_DOSE_SCALE = math.log1p(10000.0)


# ---------------------------------------------------------------------------------------------
# Inputs shared by all arms
# ---------------------------------------------------------------------------------------------
@dataclass
class FoldData:
    """Everything an arm may read for one fold; test rows carry no response."""

    lines: tuple[str, ...]
    cond_line: np.ndarray          # (n_cond,) line index
    cond_compound: np.ndarray      # (n_cond,) compound index
    cond_dose: np.ndarray          # (n_cond,) nM
    shift: np.ndarray              # (n_cond, G) observed rep-averaged shift; test rows must not be read
    train: np.ndarray              # condition indices used for fitting
    val: np.ndarray                # inner-validation condition indices (subset of the training fold)
    test: np.ndarray               # held-out condition indices
    fp2048: np.ndarray             # (n_compounds, 2048) binary Morgan r2
    fp512: np.ndarray              # (n_compounds, 512) binary Morgan r2
    moa: np.ndarray                # (n_compounds,) pathway_level_2 index, 0 = unknown
    n_moa: int
    chunk_mean: np.ndarray         # (n_chunks, G)
    chunk_group: np.ndarray        # (n_chunks,)
    group_line: np.ndarray         # (n_groups,) line index
    group_compound: np.ndarray     # (n_groups,) compound index, -1 for vehicle
    group_dose: np.ndarray
    group_rep: np.ndarray          # (n_groups,) replicate index
    group_mean: np.ndarray         # (n_groups, G)
    train_compounds: np.ndarray    # compound indices whose cells the fold may use
    extras: dict = field(default_factory=dict)

    def fit_rows(self) -> np.ndarray:
        """Training rows for fitting: the training fold minus the inner-validation rows."""

        return np.setdiff1d(self.train, self.val)


def gate(dose: np.ndarray) -> np.ndarray:
    return (np.log1p(np.asarray(dose, dtype=np.float64)) / LOG_DOSE_SCALE).astype(np.float32)


def tanimoto(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a, b = a.astype(np.float32), b.astype(np.float32)
    inter = a @ b.T
    union = a.sum(1)[:, None] + b.sum(1)[None, :] - inter
    return np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)


def morgan(smiles: list[str], bits: int) -> np.ndarray:
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator

    RDLogger.DisableLog("rdApp.*")
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=bits)
    return np.array([generator.GetFingerprintAsNumPy(Chem.MolFromSmiles(s)) for s in smiles], dtype=np.float32)


# ---------------------------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------------------------
def predict_zero(d: FoldData) -> dict:
    return {"prediction": np.zeros((len(d.test), d.shift.shape[1]), dtype=np.float32)}


def systematic_reference(d: FoldData, rows: np.ndarray) -> dict[tuple[int, float], np.ndarray]:
    reference = {}
    for key in {(int(d.cond_line[i]), float(d.cond_dose[i])) for i in rows}:
        members = rows[(d.cond_line[rows] == key[0]) & (d.cond_dose[rows] == key[1])]
        reference[key] = d.shift[members].mean(0)
    return reference


def predict_systematic(d: FoldData) -> dict:
    reference = systematic_reference(d, d.train)
    return {"prediction": np.stack([reference[(int(d.cond_line[i]), float(d.cond_dose[i]))] for i in d.test])}


def _ridge_design(d: FoldData, rows: np.ndarray) -> np.ndarray:
    fp = d.fp2048[d.cond_compound[rows]]
    onehot = np.eye(len(d.lines), dtype=np.float32)[d.cond_line[rows]]
    crossed = (fp[:, None, :] * onehot[:, :, None]).reshape(len(rows), -1)
    return np.hstack([crossed, onehot]) * gate(d.cond_dose[rows])[:, None]


def _ridge_dual(x: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    gram = x @ x.T
    return x.T @ np.linalg.solve(gram + alpha * np.eye(len(x)), y)


def predict_ridge(d: FoldData) -> dict:
    fit, val = d.fit_rows(), d.val
    x_fit, x_val = _ridge_design(d, fit), _ridge_design(d, val)
    scores = {}
    for alpha in (1.0, 10.0, 100.0, 1000.0):
        w = _ridge_dual(x_fit, d.shift[fit], alpha)
        scores[alpha] = float(np.square(x_val @ w - d.shift[val]).mean())
    alpha = min(scores, key=lambda a: (scores[a], -a))
    w = _ridge_dual(_ridge_design(d, d.train), d.shift[d.train], alpha)
    return {"prediction": (_ridge_design(d, d.test) @ w).astype(np.float32), "selected_alpha": alpha,
            "validation_mse": scores}


def predict_knn(d: FoldData, k: int = 5) -> dict:
    train_compounds = np.unique(d.cond_compound[d.train])
    lookup = {(int(d.cond_compound[i]), int(d.cond_line[i]), float(d.cond_dose[i])): i for i in d.train}
    sims = tanimoto(d.fp2048, d.fp2048[train_compounds])
    out, spread = [], []
    for i in d.test:
        row = sims[d.cond_compound[i]]
        order = np.argsort(-row)
        vectors, weights = [], []
        for j in order:
            key = (int(train_compounds[j]), int(d.cond_line[i]), float(d.cond_dose[i]))
            if key in lookup:
                vectors.append(d.shift[lookup[key]])
                weights.append(max(float(row[j]), 1e-6))
            if len(vectors) == k:
                break
        weights = np.asarray(weights) / np.sum(weights)
        out.append(np.tensordot(weights, np.asarray(vectors), axes=1))
        spread.append(1.0 - float(np.sort(row)[-1]))
    return {"prediction": np.asarray(out, dtype=np.float32), "spread": np.asarray(spread, dtype=np.float32)}


def predict_mlp_existing(d: FoldData, seeds: list[int]) -> dict:
    """The repository's current learned rung, trained exactly as evaluation/model_validation.py does."""

    from sklearn.decomposition import TruncatedSVD
    from sklearn.preprocessing import StandardScaler
    from virtual_cell.learned_response import fit_response

    fit, val = d.fit_rows(), d.val
    dose = gate(d.cond_dose)
    onehot = np.eye(len(d.lines), dtype=np.float32)[d.cond_line]
    raw = np.c_[d.fp512[d.cond_compound], onehot, dose]
    scaler = StandardScaler().fit(raw[fit])
    x = scaler.transform(raw).astype(np.float32)
    svd = TruncatedSVD(n_components=64, random_state=11).fit(d.shift[fit])
    target_fit = svd.transform(d.shift[fit]).astype(np.float32)
    target_val = svd.transform(d.shift[val]).astype(np.float32)
    predictions = []
    for seed in seeds:
        result = fit_response(x[fit], dose[fit], target_fit, x[val], dose[val], target_val, seed=seed, device=DEVICE)
        predictions.append(result.predict(x[d.test], dose[d.test]) @ svd.components_)
    stack = np.asarray(predictions, dtype=np.float32)
    return {"prediction": stack.mean(0), "spread": np.linalg.norm(stack.std(0), axis=1)}


# ---------------------------------------------------------------------------------------------
# Latent world models
# ---------------------------------------------------------------------------------------------
class Encoder(nn.Module):
    def __init__(self, genes: int, hidden: int, latent: int):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(genes, hidden), nn.LayerNorm(hidden), nn.GELU(),
                                 nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU(),
                                 nn.Linear(hidden, latent))

    def forward(self, x):
        return self.net(x)


class Standardiser:
    """Gene-wise centering on training vehicle minibulks with a damped scale."""

    def __init__(self, vehicle: np.ndarray):
        self.mean = vehicle.mean(0)
        var = vehicle.var(0)
        self.scale = np.sqrt(var + np.median(var)).astype(np.float32)

    def __call__(self, x: np.ndarray) -> np.ndarray:
        return ((x - self.mean) / self.scale).astype(np.float32)


class ViewSampler:
    """Two disjoint-cell views of one group: each view averages 1, 2 or 4 of its chunks.

    Up to eight distinct chunks of a group are drawn per sample; the first half feeds view a and
    the second half view b, so the two views never share a cell. Chunks are pre-standardised and
    held on the device, and a batch is gathered with index arithmetic rather than a Python loop.
    """

    def __init__(self, chunks: torch.Tensor, chunk_group: np.ndarray, groups: set[int], rng: np.random.Generator):
        self.chunks = chunks
        self.rng = rng
        members: dict[int, list[int]] = {}
        for index, g in enumerate(chunk_group):
            if int(g) in groups:
                members.setdefault(int(g), []).append(index)
        kept = {g: v for g, v in members.items() if len(v) >= 2}
        self.keys = np.array(sorted(kept))
        width = max(len(v) for v in kept.values())
        self.padded = np.full((len(self.keys), width), -1, dtype=np.int64)
        for row, g in enumerate(self.keys):
            self.padded[row, :len(kept[g])] = kept[g]
        self.counts = np.array([len(kept[g]) for g in self.keys])
        self.weights = self.counts / self.counts.sum()
        self.total = int(self.counts.sum())

    def epoch_steps(self, batch: int) -> int:
        return max(1, self.total // batch)

    def batch(self, size: int) -> tuple[torch.Tensor, torch.Tensor]:
        rows = self.rng.choice(len(self.keys), size=size, p=self.weights)
        ids = self.padded[rows]
        keys = self.rng.random(ids.shape)
        keys[ids < 0] = 2.0
        order = np.argsort(keys, axis=1)[:, :8]
        picked = np.take_along_axis(ids, order, axis=1)
        available = np.minimum(self.counts[rows], 8)
        half = available // 2
        ra = np.minimum(self.rng.choice((1, 2, 4), size=size), half)
        rb = np.minimum(self.rng.choice((1, 2, 4), size=size), available - half)
        position = np.arange(8)[None, :]
        wa = ((position < ra[:, None]) / ra[:, None]).astype(np.float32)
        wb = (((position >= half[:, None]) & (position < (half + rb)[:, None])) / rb[:, None]).astype(np.float32)
        gathered = self.chunks[torch.as_tensor(np.maximum(picked, 0), device=self.chunks.device)]
        a = (torch.as_tensor(wa, device=self.chunks.device)[:, :, None] * gathered).sum(1)
        b = (torch.as_tensor(wb, device=self.chunks.device)[:, :, None] * gathered).sum(1)
        return a, b


def gene_modules(x: np.ndarray, k: int) -> np.ndarray:
    from sklearn.cluster import KMeans

    genes = (x - x.mean(0)) / (x.std(0) + 1e-6)
    return KMeans(n_clusters=k, n_init=4, random_state=0).fit_predict(genes.T.astype(np.float64))


def _mask(modules: torch.Tensor, k: int, fraction: float, size: int,
          generator: torch.Generator) -> tuple[torch.Tensor, torch.Tensor]:
    module_mask = (torch.rand((size, k), generator=generator, device=modules.device) < fraction).float()
    return module_mask, module_mask[:, modules]


def pretrain_jepa(sampler: ViewSampler, modules: np.ndarray, cfg: dict, seed: int) -> Encoder:
    torch.manual_seed(seed)
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    genes = len(modules)
    k = int(modules.max()) + 1
    modules_t = torch.as_tensor(modules, device=DEVICE, dtype=torch.long)
    encoder = Encoder(genes, cfg["hidden"], cfg["latent_dim"]).to(DEVICE)
    target = copy.deepcopy(encoder)
    for p in target.parameters():
        p.requires_grad_(False)
    predictor = nn.Sequential(nn.Linear(cfg["latent_dim"] + k, cfg["predictor_hidden"]), nn.GELU(),
                              nn.Linear(cfg["predictor_hidden"], cfg["latent_dim"])).to(DEVICE)
    params = list(encoder.parameters()) + list(predictor.parameters())
    optimiser = torch.optim.AdamW(params, lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"])
    for _ in range(cfg["pretrain_epochs"]):
        for _ in range(sampler.epoch_steps(cfg["batch_size"])):
            a, b = sampler.batch(cfg["batch_size"])
            module_mask, gene_mask = _mask(modules_t, k, cfg["mask_module_fraction"], len(a), generator)
            z = encoder(a * (1.0 - gene_mask))
            predicted = predictor(torch.cat([z, module_mask], 1))
            with torch.no_grad():
                goal = target(b)
            loss = nn.functional.smooth_l1_loss(predicted, goal)
            std = torch.sqrt(z.var(0) + 1e-4)
            loss = loss + cfg["variance_hinge_weight"] * torch.relu(1.0 - std).mean()
            optimiser.zero_grad(set_to_none=True)
            loss.backward()
            optimiser.step()
            with torch.no_grad():
                for online, ema in zip(encoder.parameters(), target.parameters()):
                    ema.mul_(cfg["ema_momentum"]).add_(online, alpha=1 - cfg["ema_momentum"])
    target.eval()
    return target


def pretrain_mae(sampler: ViewSampler, modules: np.ndarray, cfg: dict, seed: int) -> Encoder:
    torch.manual_seed(seed)
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    genes = len(modules)
    k = int(modules.max()) + 1
    modules_t = torch.as_tensor(modules, device=DEVICE, dtype=torch.long)
    encoder = Encoder(genes, cfg["hidden"], cfg["latent_dim"]).to(DEVICE)
    decoder = nn.Sequential(nn.Linear(cfg["latent_dim"] + k, cfg["hidden"]), nn.GELU(),
                            nn.Linear(cfg["hidden"], genes)).to(DEVICE)
    optimiser = torch.optim.AdamW(list(encoder.parameters()) + list(decoder.parameters()),
                                  lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"])
    for _ in range(cfg["pretrain_epochs"]):
        for _ in range(sampler.epoch_steps(cfg["batch_size"])):
            a, b = sampler.batch(cfg["batch_size"])
            module_mask, gene_mask = _mask(modules_t, k, cfg["mask_module_fraction"], len(a), generator)
            recon = decoder(torch.cat([encoder(a * (1.0 - gene_mask)), module_mask], 1))
            loss = nn.functional.mse_loss(recon, b)
            optimiser.zero_grad(set_to_none=True)
            loss.backward()
            optimiser.step()
    encoder.eval()
    return encoder


class PCAEncoder:
    def __init__(self, x: np.ndarray, latent: int):
        from sklearn.decomposition import PCA

        self.pca = PCA(n_components=latent, random_state=0).fit(x)

    def encode(self, x: np.ndarray) -> np.ndarray:
        return self.pca.transform(x).astype(np.float32)


def encode(encoder, x: np.ndarray) -> np.ndarray:
    if isinstance(encoder, PCAEncoder):
        return encoder.encode(x)
    with torch.no_grad():
        out = [encoder(torch.as_tensor(x[i:i + 4096], device=DEVICE)).cpu().numpy() for i in range(0, len(x), 4096)]
    return np.concatenate(out).astype(np.float32)


class TransitionHead(nn.Module):
    """delta_z = sum_k g_k(dose) v_k(compound, line) with g_k(0) = 0 exactly."""

    def __init__(self, latent: int, lines: int, n_moa: int | None):
        super().__init__()
        self.chem = nn.Sequential(nn.Linear(2048, 256), nn.GELU(), nn.Dropout(0.2))
        self.line = nn.Embedding(lines, 16)
        self.moa = nn.Embedding(n_moa, 16, padding_idx=0) if n_moa else None
        width = 256 + 16 + (16 if n_moa else 0)
        self.body = nn.Sequential(nn.Linear(width, 256), nn.GELU(), nn.Linear(256, 2 * latent + 2))
        self.latent = latent

    def forward(self, fp, line, dose, moa=None):
        parts = [self.chem(fp), self.line(line)]
        if self.moa is not None:
            parts.append(self.moa(moa))
        out = self.body(torch.cat(parts, 1))
        v1, v2 = out[:, :self.latent], out[:, self.latent:2 * self.latent]
        log_ec50 = 1.0 + 4.0 * torch.sigmoid(out[:, 2 * self.latent:])
        g = dose[:, None] / (dose[:, None] + torch.pow(10.0, log_ec50))
        return g[:, :1] * v1 + g[:, 1:] * v2, log_ec50


def fit_head(d: FoldData, latent_delta: np.ndarray, gene_target: np.ndarray, decoder_w: np.ndarray,
             cfg: dict, seed: int, moa: np.ndarray | None) -> TransitionHead:
    torch.manual_seed(seed)
    t = cfg["transition"]
    head = TransitionHead(latent_delta.shape[1], len(d.lines), d.n_moa if moa is not None else None).to(DEVICE)
    optimiser = torch.optim.AdamW(head.parameters(), lr=t["learning_rate"], weight_decay=t["weight_decay"])
    w = torch.as_tensor(decoder_w, device=DEVICE)

    def tensors(rows):
        items = [torch.as_tensor(d.fp2048[d.cond_compound[rows]], device=DEVICE),
                 torch.as_tensor(d.cond_line[rows], device=DEVICE, dtype=torch.long),
                 torch.as_tensor(d.cond_dose[rows], device=DEVICE, dtype=torch.float32),
                 torch.as_tensor(moa[d.cond_compound[rows]], device=DEVICE, dtype=torch.long) if moa is not None else None]
        return items

    fit, val = d.fit_rows(), d.val
    x_fit, x_val = tensors(fit), tensors(val)
    zf = torch.as_tensor(latent_delta[fit], device=DEVICE)
    yf, yv = torch.as_tensor(gene_target[fit], device=DEVICE), torch.as_tensor(gene_target[val], device=DEVICE)
    best, stale, state = float("inf"), 0, None
    for _ in range(t["max_epochs"]):
        head.train()
        delta, _ = head(*x_fit)
        loss = nn.functional.mse_loss(delta, zf) + nn.functional.mse_loss(delta @ w, yf)
        optimiser.zero_grad(set_to_none=True)
        loss.backward()
        optimiser.step()
        head.eval()
        with torch.no_grad():
            value = float(nn.functional.mse_loss(head(*x_val)[0] @ w, yv))
        if value < best:
            best, stale, state = value, 0, copy.deepcopy(head.state_dict())
        else:
            stale += 1
            if stale >= t["patience"]:
                break
    head.load_state_dict(state)
    head.eval()
    return head


def latent_arms(d: FoldData, cfg: dict, seeds: list[int], moa_shuffled: np.ndarray, log=print) -> dict:
    """Fit PCA, MAE and JEPA encoders plus the shared head; returns every latent arm's prediction."""

    from sklearn.linear_model import Ridge

    allowed = set(d.train_compounds.tolist())
    train_groups = np.flatnonzero((d.group_compound < 0) | np.isin(d.group_compound, list(allowed)))
    vehicle_chunks = np.isin(d.chunk_group, np.flatnonzero(d.group_compound < 0))
    standardise = Standardiser(d.chunk_mean[vehicle_chunks])
    fit_chunks = np.isin(d.chunk_group, train_groups)
    x_chunks = standardise(d.chunk_mean[fit_chunks])
    modules = gene_modules(x_chunks[np.random.default_rng(0).permutation(len(x_chunks))[:8000]], cfg["gene_modules"])
    x_groups = standardise(d.group_mean)
    target = (d.shift / standardise.scale).astype(np.float32)

    # latent shift targets for training-fold conditions only: mean over replicates of
    # f(treated) - f(matched vehicle). Held-out rows stay zero and are never read.
    def latent_targets(z_groups: np.ndarray) -> np.ndarray:
        vehicle = {(int(l), int(r)): z_groups[g] for g, (l, r, c) in
                   enumerate(zip(d.group_line, d.group_rep, d.group_compound)) if c < 0}
        index = {}
        for g, (l, c, dose, r) in enumerate(zip(d.group_line, d.group_compound, d.group_dose, d.group_rep)):
            if c in allowed and (int(l), int(r)) in vehicle:
                index.setdefault((int(l), int(c), float(dose)), []).append(z_groups[g] - vehicle[(int(l), int(r))])
        out = np.zeros((len(d.cond_line), z_groups.shape[1]), dtype=np.float32)
        for i in d.train:
            key = (int(d.cond_line[i]), int(d.cond_compound[i]), float(d.cond_dose[i]))
            if key in index:
                out[i] = np.mean(index[key], axis=0)
        return out

    results: dict[str, list] = {}
    encoders = {"latent_pca": [PCAEncoder(x_chunks, cfg["latent_dim"])] * len(seeds)}
    allowed_groups = set(train_groups.tolist())
    chunks_device = torch.as_tensor(standardise(d.chunk_mean), device=DEVICE)

    def sampler(seed: int) -> ViewSampler:
        # A fresh sampler per seed, so MAE and JEPA see identical views and masks for one seed.
        return ViewSampler(chunks_device, d.chunk_group, allowed_groups, np.random.default_rng(seed))

    encoders["latent_mae"] = [pretrain_mae(sampler(s), modules, cfg, s) for s in seeds]
    log("mae pretrained")
    encoders["latent_jepa"] = [pretrain_jepa(sampler(s), modules, cfg, s) for s in seeds]
    log("jepa pretrained")
    del chunks_device
    diagnostics = {}
    for name, members in encoders.items():
        for seed, encoder in zip(seeds, members):
            z_chunks = encode(encoder, x_chunks)
            decoder = Ridge(alpha=1.0, fit_intercept=True).fit(z_chunks, x_chunks)
            w = decoder.coef_.T.astype(np.float32)
            z_groups = encode(encoder, x_groups)
            delta_target = latent_targets(z_groups)
            diagnostics.setdefault(name, []).append({
                "seed": seed, "latent_std_mean": float(z_chunks.std(0).mean()),
                "decoder_r2_chunks": float(decoder.score(z_chunks, x_chunks))})
            variants = [(name, None)]
            if name == "latent_jepa":
                variants += [("latent_jepa_moa", d.moa), ("latent_jepa_moa_shuffled", moa_shuffled)]
            for arm, moa in variants:
                head = fit_head(d, delta_target, target, w, cfg, seed, moa)
                rows = d.test
                with torch.no_grad():
                    args = [torch.as_tensor(d.fp2048[d.cond_compound[rows]], device=DEVICE),
                            torch.as_tensor(d.cond_line[rows], device=DEVICE, dtype=torch.long),
                            torch.as_tensor(d.cond_dose[rows], device=DEVICE, dtype=torch.float32),
                            torch.as_tensor(moa[d.cond_compound[rows]], device=DEVICE, dtype=torch.long) if moa is not None else None]
                    delta, log_ec50 = head(*args)
                    genes = (delta @ torch.as_tensor(w, device=DEVICE)).cpu().numpy() * standardise.scale
                results.setdefault(arm, []).append((genes.astype(np.float32), log_ec50.cpu().numpy()))
        log(f"{name} heads fitted")
    out = {}
    for arm, members in results.items():
        stack = np.asarray([m[0] for m in members])
        out[arm] = {"prediction": stack.mean(0), "spread": np.linalg.norm(stack.std(0), axis=1),
                    "log10_ec50": np.asarray([m[1] for m in members]).mean(0)}
    out["_diagnostics"] = diagnostics
    return out
