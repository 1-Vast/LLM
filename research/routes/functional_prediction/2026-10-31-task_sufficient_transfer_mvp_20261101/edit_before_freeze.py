from pathlib import Path
p=Path(__file__).parent/'mvp_run.py'
s=p.read_text(encoding='utf-8-sig')
s=s.replace('METHODS = ["raw_k5", "gat_d5_k20"]', 'METHODS = ["raw_k5", "raw_k20", "chemistry_k20", "gat_d5_k20", "global_residual_diagnostic"]')
s=s.replace('def metrics(pred:', '''def selection_regret(pred: np.ndarray, obs: np.ndarray, generic: np.ndarray) -> float:
    a, b = residualise(pred, generic), residualise(obs, generic)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 40 or np.std(a[ok]) < 1e-12 or np.std(b[ok]) < 1e-12:
        return float("nan")
    m = max(1, int(round(0.10 * ok.sum())))
    pa, true_sensitivity = -a[ok], -b[ok]
    chosen = np.argsort(-pa, kind="stable")[:m]
    oracle = np.argsort(-true_sensitivity, kind="stable")[:m]
    return float(true_sensitivity[oracle].mean() - true_sensitivity[chosen].mean())


def metrics(pred:''')
s=s.replace('if freeze["data_sha256"] != sha256(DATA):', 'if (STUDY / "RUN").exists():\n        raise RuntimeError("RUN exists; single launch only")\n    if freeze["code_sha256"] != sha256(Path(__file__).resolve()):\n        raise RuntimeError("code hash differs from freeze")\n    if freeze["data_sha256"] != sha256(DATA):')
s=s.replace('lines = d["line"].astype(str)', 'lines = d["line"].astype(str)\n    fp = d["fingerprint"].astype(float)')
s=s.replace('raw_sets = raw_nb', '''predictions["raw_k20"][q], raw_sets = knn(raw_sim, Yr, 20)
        qfp, rfp = fp[q], fp[r]
        inter = qfp @ rfp.T
        union = qfp.sum(1)[:, None] + rfp.sum(1)[None, :] - inter
        chem_sim = inter / np.maximum(union, 1e-12)
        chem_sim[qfp.sum(1) == 0] = np.nan
        chem_sim[:, rfp.sum(1) == 0] = np.nan
        predictions["chemistry_k20"][q], chem_nb = knn(chem_sim, Yr, 20)
        for i, nbi in enumerate(raw_nb):
            neighbor_overlap["raw_k5"][np.flatnonzero(q)[i]] = jaccard(raw_sets[i], nbi)
        neighbor_overlap["raw_k20"][q] = 1.0
        for i, nbi in enumerate(chem_nb):
            neighbor_overlap["chemistry_k20"][np.flatnonzero(q)[i]] = jaccard(raw_sets[i], nbi)''')
s=s.replace('predictions["gat_d5_k20"][q] = gat_pred', '''predictions["gat_d5_k20"][q] = gat_pred
        # Exact target decomposition with line-wise missingness retained; reassembly is ordinary GAT.
        means = np.nanmean(Yr, axis=1)
        g = generic - np.nanmean(generic)
        denom = np.nansum(np.where(np.isfinite(Yr), g[None, :] ** 2, np.nan), axis=1)
        beta = np.nansum((Yr - means[:, None]) * g[None, :], axis=1) / np.maximum(denom, 1e-12)
        global_part = means[:, None] + beta[:, None] * g[None, :]
        global_part[~np.isfinite(Yr)] = np.nan
        residual_part = Yr - global_part
        gp, _ = knn(gat_sim, global_part, KNN_K)
        rp, _ = knn(gat_sim, residual_part, KNN_K)
        predictions["global_residual_diagnostic"][q] = gp + rp''')
s=s.replace('proj = rng.normal(size=(Rrf.shape[1], max(PCA_KS))).astype(np.float64) / np.sqrt(max(PCA_KS))', 'proj, _ = np.linalg.qr(rng.normal(size=(Rrf.shape[1], max(PCA_KS))).astype(np.float64), mode="reduced")')
s=s.replace('"method": name, "hit_precision": hp, "regret": (1.0 - hp) if np.isfinite(hp) else np.nan,', '"method": name, "hit_precision": hp, "miss_rate": (1.0 - hp) if np.isfinite(hp) else np.nan,\n                             "regret": selection_regret(predictions[name][idx], Y[idx], generic),')
s=s.replace('ss = sub[pop.to_numpy()]', 'ss = sub[np.asarray(pop)]')
s=s.replace('("hit_precision", "regret", "selective_r", "raw_r", "raw_mae", "neighbor_overlap_vs_raw")', '("hit_precision", "miss_rate", "regret", "selective_r", "raw_r", "raw_mae", "neighbor_overlap_vs_raw")')
p.write_text(s,encoding='utf-8')
protocol=Path(__file__).parent/'PROTOCOL.md'
s=protocol.read_text(encoding='utf-8-sig')
s=s.replace('Date: 2026-11-01 (Asia/Shanghai)', 'Date: 2026-10-31 (client date; actual UTC/local timestamps in FREEZE.json)')
s=s.replace('2. `gat_d5_k20`:', '2. `raw_k20`: raw mean cosine and k=20, controlling neighbor count.\n3. `chemistry_k20`: Morgan fingerprint Tanimoto with k=20 and no transcriptomic input.\n4. `global_residual_diagnostic`: decompose each reference outcome into compound mean plus generic-profile projection plus residual; transfer both components with the same GAT weights and reassemble. This is an algebraic diagnostic and should equal GAT within floating-point error.\n5. `gat_d5_k20`:')
s=s.replace('- Primary companion: selective top-10% regret, defined as `1 - hit_precision`.', '- Primary companion: selective top-10% selection regret = observed oracle top-m mean sensitivity minus observed mean sensitivity of the predicted top-m set, using the same reference-generic residuals. `1 - hit_precision` is separately named miss rate.')
s=s.replace('neighbor overlap with `raw_k5` for kNN arms (`top-20` Jaccard)', 'neighbor overlap with `raw_k20` for kNN arms (Jaccard; raw_k5 has five neighbors)')
s=s.replace('A candidate is retained for a future frozen external test only if, across fixed folds, it is non-inferior to `gat_d5_k20` on selective-r and does not reduce selective top-10% precision, while showing a stable dimension-performance curve.', 'The pilot describes paired changes and dimension-performance curves against `gat_d5_k20`; no non-inferiority claim is made because no formal margin or confirmatory confidence procedure is specified. Any retained candidate requires a separately frozen external test.')
s=s.replace('This pilot is non-confirmatory and cannot promote code or establish the core innovation.', 'This pilot is non-confirmatory and cannot promote code or establish the core innovation. Existing NCI-60 and PRISM 24Q2 outcomes were already exposed in GAT and would only support retrospective checks, never pristine confirmation for this new candidate.')
protocol.write_text(s,encoding='utf-8')
