"""Independent finite/tie/singular-control equivalence, no target outcome reads."""
from types import SimpleNamespace
import numpy as np
from .benchmark import study
from .kernel import kg_values


def main():
    normals = np.random.default_rng(42).standard_normal(64)
    rng = np.random.default_rng(7)
    checked = 0
    for count in (5, 12, 146):
        matrix = rng.standard_normal((count, 8))
        cov = matrix @ matrix.T / 8
        for mean, covariance in ((rng.standard_normal(count), cov), (np.zeros(count), np.eye(count)),
                                 (np.zeros(count), np.zeros((count, count)))):
            belief = SimpleNamespace(mean=mean, cov=covariance, obs_var=np.ones(count))
            original = (mean.copy(), covariance.copy(), belief.obs_var.copy())
            for indices in (list(range(count)), list(reversed(range(count))), []):
                before = study.kg_values(belief, 5, indices, normals)
                after = kg_values(belief, 5, indices, normals)
                assert before == after
                if indices:
                    assert max(before, key=lambda i: (before[i], -i)) == max(after, key=lambda i: (after[i], -i))
                assert all(np.array_equal(a,b) for a,b in zip(original, (belief.mean, belief.cov, belief.obs_var)))
                checked += 1
    print(f"PASS: {checked} exact score/choice/input-preservation cases")


if __name__ == "__main__":
    main()
