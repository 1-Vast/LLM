# Environment status

**Checked:** 2026-10-30 with the project CPU environment.

## Canonical environments

- `D:\MAESTRO\.venv` is now a fresh Python 3.11.16 `--copies` environment built from `D:\anaconda\envs\maestro\python.exe`. The previous broken launcher was retained outside the project at `D:\MAESTRO-organization-20261030\venv-broken-20261030`.
- The project environment has an editable install with the `test` and `preparation` extras. `agent`, `maestro`, `virtual_cell`, `tools`, `pandas`, `xlrd`, and `docx` import successfully.
- The conda `maestro` environment remains the GPU/ARC State environment. It now has `cell-eval`, `cell-load`, and `ipykernel`; `pip check` reports no broken requirements.

## Compatibility repair

The ARC State dependency `polars` raised a false CPU-feature error on this Windows host (`unknown feature flag: 'sse3'`) even though the package was installed. The conda environment persists `POLARS_SKIP_CPU_CHECK=1`, and imports of `polars 2.1.0`, `cell_eval`, and `cell_load` succeed under that setting. This bypasses only the package's detection guard; ARC State model execution still requires its own declared checkpoint, GPU, and data contract.

## Verification boundary

These checks certify environment installation and imports. They do not certify ARC State inference, model quality, dataset licensing, or any scientific claim. Heavy GPU inference and protected outcome access were not run during organization.


Activation scripts were corrected to the actual `.venv` location after relocation, and pip was reinstalled to regenerate its launchers. Direct `pip.exe --version` and `python -m pip check` succeed. When invoking the conda interpreter directly without activation, explicitly set `POLARS_SKIP_CPU_CHECK=1`; activation is what normally supplies the persisted environment variable. GPU inference remains unverified.
