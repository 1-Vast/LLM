# MAP-KG knowledge-layer validation

This audit separates structured knowledge retrieval, learned molecular content,
cross-modal alignment, response prediction and decision value. It restores three
official MAP-KG tables plus pinned Tahoe drug metadata, binds full structures to
the prior official molecule/knowledge feature cache, and compares fixed top-five
neighbors with molecular and Morgan fingerprint controls. It fits no RNA model,
opens no new biological outcomes and does not recreate the removed MAP runtime.

The primary sources and paper/code differences are recorded in `SOURCE_AUDIT.json`.
Canonical conclusions belong in [EVIDENCE.md](../EVIDENCE.md). The experiment's
original protocol, source/cache hashes and independent verifier are retained here;
results belong in `outputs/knowledge_layer_validation_20261009` and execution
records in `log/20261009`.

Using the maestro environment (NumPy, pandas, pyarrow, requests and RDKit):

```powershell
D:/anaconda/envs/maestro/python.exe -m pytest research/knowledge_layer_validation_20261009/test_benchmark.py
D:/anaconda/envs/maestro/python.exe research/knowledge_layer_validation_20261009/audit.py
D:/anaconda/envs/maestro/python.exe research/knowledge_layer_validation_20261009/verify.py
```

`audit.py` restores about 67.8 MB of public tables at pinned revisions and checks
their sizes and published LFS digests where available. It refuses to overwrite
an existing audit. Reproduction also requires `FEATURES.npz` and `IDENTITIES.json`
from the original released-weight audit, with the hashes in `FREEZE.json`. These
generated caches are local ignored assets, not guaranteed by a clean checkout.
Full checkpoint and protein projector assets are absent here; the molecule-protein
shared-space test must remain explicitly blocked rather than be approximated.

Missing annotations are unknown, not negative biology. The conservative predicate
table deliberately leaves many relation phrases unparsed, including explicit
binding phrasing. Its `unknown` values describe parser coverage, not absence of
source knowledge. Original relation text and source rows remain available for
typed evidence interpretation. Agonism and antagonism do not become generic
up/down cell-response signs. Similar vectors retrieve possible evidence; exact
typed assertions supply identity and meaning.

The retained graph may have been used to train the cached encoder. This is a
content-retrieval audit, not unseen-drug/edge generalization, target engagement,
response calibration, a functional bridge, a risk certificate or agent advantage.
No current production interface or STATE inference path is modified.
