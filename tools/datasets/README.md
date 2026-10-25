# Dataset Tools

The maintained commands are dataset discovery and explicitly scoped data builders. Discovery
does not qualify a source as evaluation data. Acquisition requires a caller-selected URL,
declared hash and byte limit; `--help` performs no network request.

```bash
python -m tools.datasets.catalog --help
python -m tools.datasets.catalog candidates
python -m tools.datasets.catalog source sciplex3
python -m tools.datasets.combination_screens --help
```

`catalog` reads `candidates.json` and `sources.json`. It distinguishes recorded hashes from
verified local files and preserves missing or unqualified status. `condition_sources` resolves
only exact registered context, drug, dose and provenance identities; it does not infer absent
measurements.

`lincs_pack` builds the case-memory data pack from the registered LINCS inputs. The builder,
case-memory audit and validation commands require those source assets. A missing pack or source
is an asset blocker and must not be represented as an empty dataset.

`tahoe_phenotypes` builds same-spheroid relative-survival and phase-shift endpoints from Tahoe-100M
per-cell obs codes. It refuses lines below the declared median treated-cell count as
`CONTEXT_UNDERCOUNTED`; absolute survival is not identified because spheroid totals did not
replicate. See the [current source and endpoint qualifications](../../data/INVENTORY.md#source-identity-conditions-and-lineage). The historical phenotype-anchor verdict is source identity `ef49d423fcaa:research/EVIDENCE.md`, section "Phenotype-anchored dual core — 2026-10-10"; it is not a live current-report anchor.

`combination_screens` and `evaluation.discovery_replay` remain importable release entry points.
The former historical parity test is archived because its frozen `research/certified_discovery`
package is not included. The production `virtual_cell.combination_world` contracts remain in the
default asset-free test suite.

Other historical dataset auditors and benchmark builders are recoverable from Git history; they
are not current release commands. Large scientific data and generated outputs are not bundled.

## Verified O'Neil originals

Use the project-local Python from `log/20261020/PREPARATION.md`:

```powershell
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m tools.datasets.oneil_sources
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m tools.datasets.oneil_sources --verify-only
```

Acquisition uses three official AACR/Figshare article/file identities, bounded public GET retries,
complete byte size and published MD5, ZIP integrity and SHA-256 receipts. Existing mismatched
files are refused, never overwritten. Interrupted `.part` files are retained for inspection;
verify their identity before removing or renaming them. `curl.exe` is required for public range GETs.
The combination's `.xls` extension contains OOXML. Read [the structural receipt](../../data/ONEIL_STRUCTURE.json)
and [source receipts](../../data/ONEIL_SOURCES.json) before selecting a research observation unit.
The historical builder merges batches and can use cross-batch monotherapy fallback; its cell-target
replay does not implement the new pair-level protocol. No cache was rebuilt during preparation.
