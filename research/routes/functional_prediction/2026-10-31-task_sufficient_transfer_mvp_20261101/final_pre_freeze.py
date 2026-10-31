from pathlib import Path
from datetime import datetime,timezone
p=Path(__file__).parent/'mvp_run.py'
s=p.read_text(encoding='utf-8-sig')
s=s.replace('import platform\n', 'import platform\nimport time\n')
s=s.replace('"global_residual_diagnostic"]', '"global_residual_diagnostic", "full_flat_residual_k20", "gat_permuted_null"]')
s=s.replace('Rrf = flatten_centered(Rr)\n        Rqf = flatten_centered(Rq)', '''Rrf = flatten_centered(Rr)
        Rqf = flatten_centered(Rq)
        flat_sim = (Rqf @ Rrf.T) / np.maximum(np.linalg.norm(Rqf, axis=1)[:, None] * np.linalg.norm(Rrf, axis=1)[None, :], 1e-12)
        predictions["full_flat_residual_k20"][q], flat_nb = knn(flat_sim, Yr, KNN_K)
        for i, nbi in enumerate(flat_nb):
            neighbor_overlap["full_flat_residual_k20"][np.flatnonzero(q)[i]] = jaccard(raw_sets[i], nbi)
        perm = np.random.default_rng(SEED + 1000 + f).permutation(len(Yr))
        predictions["gat_permuted_null"][q], _ = knn(gat_sim, Yr[perm], KNN_K)''')
s=s.replace('PCA(n_components=max(PCA_KS), svd_solver="randomized", random_state=SEED + f)', 'PCA(n_components=max(PCA_KS), svd_solver="randomized", iterated_power=3, n_oversamples=10, power_iteration_normalizer="QR", random_state=SEED + f)')
s=s.replace('Pr = pca.fit_transform(Rrf)', 'pca.fit(Rrf)\n        Pr = pca.transform(Rrf)')
s=s.replace('Ridge(alpha=100.0, fit_intercept=True, solver="lsqr")', 'Ridge(alpha=100.0, fit_intercept=True, solver="cholesky")')
s=s.replace('def main() -> None:\n', 'def main() -> None:\n    started = time.perf_counter()\n')
s=s.replace('"environment": env_info(),', '"environment": env_info(), "elapsed_seconds": time.perf_counter() - started,')
p.write_text(s,encoding='utf-8')
protocol=Path(__file__).parent/'PROTOCOL.md'
s=protocol.read_text(encoding='utf-8-sig')
s=s.replace('reference-only randomized PCA basis fitted at 100 components;', 'reference-only randomized PCA basis fitted at 100 components (`iterated_power=3`, `n_oversamples=10`, QR normalization, seed=20261101+fold); both reference and query states use `.transform` after fitting;')
s=s.replace('`alpha=100`, `solver=lsqr`', '`alpha=100`, `solver=cholesky` (dual system for n_features > n_samples)')
s=s.replace('## Endpoints', '7. `full_flat_residual_k20`: full flattened GAT residual cosine, controlling the geometry change from option-mean cosine to flattened cosine.\n8. `gat_permuted_null`: GAT similarities with reference viability rows permuted using `seed=20261101+1000+fold`.\n\n## Endpoints')
s += '\n## Final pre-freeze corrections\n\nActual receipt UTC: '+datetime.now(timezone.utc).isoformat()+'. Before freeze: corrected date label; distinguished miss rate from true selective selection regret; removed formal non-inferiority language; added raw k20, chemistry k20, target-decomposition identity diagnostic, full flattened residual geometry control and reference-target permutation null; fixed PCA/random settings; chose cholesky ridge to avoid repeated LSQR target solves. All are final pre-run choices. No model grid was executed before freeze.\n'
protocol.write_text(s,encoding='utf-8')
