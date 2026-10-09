"""Dose-matched full-dimensional kernels replace residual-sharing covariance."""
import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator

ARMS = ("molecule", "knowledge", "Morgan", "permutedknowledge")


def candidate_kernels(records, features):
    groups = {}
    for index, record in enumerate(records):
        molecule = Chem.MolFromSmiles(record["smiles"])
        if molecule is None or Chem.MolToSmiles(molecule, isomericSmiles=True) != record["smiles"]:
            raise ValueError("canonical_fullstructure_required")
        groups.setdefault((record["cid"], record["smiles"]), []).append(index)
    identities = sorted(groups)
    first = [groups[identity][0] for identity in identities]
    for key in ("molecule256", "knowledge1024"):
        values = features[key]
        if len(values) != len(records) or not np.isfinite(values).all():
            raise ValueError("feature_alignment_or_finiteness")
        for rows in groups.values():
            if not np.allclose(values[rows], values[rows[0]], atol=1e-5, rtol=0):
                raise ValueError("same_structure_dose_vectors_differ")
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fingerprints = []
    for record in records:
        bits = np.zeros(2048)
        DataStructs.ConvertToNumpyArray(generator.GetFingerprint(Chem.MolFromSmiles(record["smiles"])), bits)
        fingerprints.append(bits)
    permutation = np.random.default_rng(20261009).permutation(len(identities))
    permuted = np.empty_like(features["knowledge1024"])
    for group, source in enumerate(permutation):
        permuted[groups[identities[group]]] = features["knowledge1024"][first[source]]
    representations = {"molecule": features["molecule256"], "knowledge": features["knowledge1024"],
                       "Morgan": np.array(fingerprints), "permutedknowledge": permuted}
    conditions = np.array([[float(a["dose"] == b["dose"] and a["unit"] == b["unit"])
                            for b in records] for a in records])
    kernels = {}
    for arm, values in representations.items():
        values = np.asarray(values, dtype=float)
        norms = np.linalg.norm(values, axis=1)
        if np.any(norms == 0):
            raise ValueError("zero_vector_has_no_authenticated_cosine")
        normalized = values/norms[:, None]
        kernels[arm] = (normalized @ normalized.T)*conditions
        np.fill_diagonal(kernels[arm], 1.)
    return kernels, dict(identities=[list(identity) for identity in identities], permutation=permutation.tolist())


def covariances(error_B, error_A, kernels):
    errors = np.concatenate([error_B, error_A], axis=1)
    moment = errors.T @ errors/len(errors)
    sd = np.sqrt(np.diag(moment))
    standardized = np.divide(errors, sd, out=np.zeros_like(errors), where=sd > 0)
    n = error_B.shape[1]
    rho = float(np.clip(np.mean(standardized[:, :n]*standardized[:, n:]), -1., 1.))
    matrices = {"empirical": moment}
    for arm, candidate_kernel in kernels.items():
        role_kernel = np.block([[candidate_kernel, rho*candidate_kernel],
                                [rho*candidate_kernel, candidate_kernel]])
        matrices[arm] = role_kernel*sd[:, None]*sd[None, :]
    for arm, matrix in matrices.items():
        matrices[arm] = .5*matrix+.5*np.diag(np.diag(matrix))+np.eye(2*n)*1e-12
    return matrices, rho


def blend(empirical, kernel, eta):
    return empirical.copy() if eta == 0 else (1-eta)*empirical+eta*kernel


def boundary_schedule(mean):
    order = np.lexsort((np.arange(len(mean)), -mean))
    midpoint = .5*(mean[order[4]]+mean[order[5]])
    return np.lexsort((np.arange(len(mean)), abs(mean-midpoint)))[:8].tolist()


def conditional_mean(prior, offset, covariance, schedule, observations):
    """Exact batch B mean after the specified eight A values, no B outcomes."""
    n = len(prior)
    coordinates = n+np.array(schedule)
    innovation = np.asarray(observations)-prior[schedule]-offset[schedule]
    return prior+covariance[:n, coordinates] @ np.linalg.solve(covariance[np.ix_(coordinates, coordinates)], innovation)
