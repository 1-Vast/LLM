# Released MAP test: reproduction

The scientific result and limitations have one canonical narrative:
[EVIDENCE.md](../../EVIDENCE.md#map-released-weights-20261008).

Run from `D:/MAESTRO` with `D:/anaconda/envs/maestro/python.exe` (Python 3.11,
torch 2.7.0+cu126, CUDA-capable GPU, NumPy, RDKit, pandas, pyarrow, scikit-learn,
threadpoolctl, OmegaConf and safetensors). This run uses an RTX 4060 Laptop GPU.
Raw weights and generated outputs are external/ignored assets; research code,
protocol, freeze and asset manifest define their identities.

1. Restore the existing boundary-acquisition `packet2`, predecessor MAP pilot
   inputs and Tahoe basal observations at the paths in `FREEZE.json` and
   `compare.py`. Preserve their existing hashes; missing inputs are blockers.
2. Run `python research/astra/map_release_test_20261008/acquire.py` for the five
   official weights/embedding files. Verify their recorded SHA256 against
   `ASSET_MANIFEST.json`; Drive has no publisher checksum. HF downloads use a
   revision and published LFS checksum.
3. Download the pinned official source ZIP from the manifest, unpack its root
   contents into `data/external/map_release_20261008/official_source`, and verify
   every original file against `official_source_hashes`. Obtain the three Tahoe
   metadata files from `tahoebio/Tahoe-100M` at the manifest revision (drug/gene
   parquet under `metadata/`, gene vocabulary under `metadata/gene_vocabulary.json`).
   Obtain the MoleculeSTM vocabulary from its manifest URL. Check all four
   `small_asset_hashes`; do not reinterpret raw Tahoe token IDs as ESM indices.
4. Install compatibility dependencies without altering global packages:
   `python -m pip install --target data/external/map_release_20261008/compat --no-deps transformers==4.30.1 tokenizers==0.13.3 huggingface_hub==0.25.2`.
5. For original-result verification, run
   `python research/astra/map_release_test_20261008/verify.py`, then
   `python research/astra/map_release_test_20261008/repeat.py`. The repeat runs
   in a temporary directory and compares exact saved results, preserving them.
6. `features.py` and `compare.py` deliberately refuse to overwrite original
   representation/prediction files. A new extraction or scientific comparison
   must use a separately registered output location and freeze; do not delete
   original outputs merely to rerun.
7. `native.py` strictly loads the checkpoint-compatible hierarchy and runs the
   public basal fixture. `forward_probe.py` separately diagnoses causal masking.
   Both refuse to overwrite their audit JSON. Neither authenticates the old
   training forward or supplies the missing HVG output map. They are not native
   biological outcome evaluations. See their JSON receipts before reuse.
8. Run the existing default core scope with `python -m pytest`; this scope is
   distinct from the real-asset verification and inference above.

The standalone acquisition helper retrieves the large weights only; steps 1,
3 and 4 are explicit prerequisites, not silently fabricated substitute assets.
No production module or official source is changed by these commands.
