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
replicate. See the [phenotype-anchor evidence](../../research/EVIDENCE.md#phenotype-anchored-dual-core--2026-10-10).

`combination_screens` and `evaluation.discovery_replay` remain importable release entry points.
The former historical parity test is archived because its frozen `research/certified_discovery`
package is not included. The production `virtual_cell.combination_world` contracts remain in the
default asset-free test suite.

Other historical dataset auditors and benchmark builders are recoverable from Git history; they
are not current release commands. Large scientific data and generated outputs are not bundled.
