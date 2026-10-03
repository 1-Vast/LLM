# Prediction binding, multi-result audit and checkout reproducibility

Date: 2026-10-03. Review base: `16eed5142ff817535b37a004a6ff7280e7a658b8`.
Evidence: `results/20261003_prediction_audit_fix_v1/`.

## Findings and implementation

The supplied review is correct. Relocation and responsibility consolidation did
not repair two pre-existing contract defects. Eight new regression cases failed
before the production edits; `before.xml` and `before.txt` retain those failures.

`virtual_cell.panel.run_panel` now calls the existing `safe_predict` once per
condition. Prediction identity, serving version and required readouts use the same
checks as the tool/orchestrator paths. Refusals remain panel rows with no usable
values or artifact, and request/model/readout violations enter the panel ledger.
Backend exceptions become explicit refusal rows. Unsupported biological scope is
still a refusal, not a fabricated response. No backend or threshold was changed.

`RunLogger` now writes result records as
`<session>.result.<SHA256(result_id)>.json`. The full result identity stays in the
payload and event. Exclusive creation prevents overwrite; an identical retry is
allowed, conflicting bytes are rejected. Original plan records remain separate.
The orchestrator retains each result view under its session and result identity,
instead of replacing the session's plan with the latest execution. Run review
examines every result and counts distinct session/round pairs. It reports result
record count separately; a revision in either result order survives the summary.
Shared readout names do not overwrite another result's metrics. QC failures with
no numeric metrics still count as received results. CaseStore facts, budget and
evidence admission remain unchanged. The in-process caches do not restore a run
summary after restart; persisted individual records remain readable.

The child collection test now passes an explicit independent pytest configuration
and checks the collected node identity, not terminal-summary wording. Its temporary
directory was exercised inside a clean checkout and outside the repository.

## Byte identities and restoration

The old 2,058-file inventory describes original working-tree bytes. It is not a
promise that all checkout bytes equal those records. Our original environment
matches 2,058; a clean LF checkout matches 2,057. The difference is exactly
`research/identifiability_audit/intervention.py`: Git retains LF, the registered
working-tree hash corresponds to CRLF. Its Git blob equals the base version.
Likewise Git stores LF `pack.json`, whereas the frozen pack expects CRLF.
`pack_arrays.npz` was not distributed in Git. `clean_bytes.json` records original
raw, Git blob and explicitly computed CRLF-candidate hashes separately. Normalized
equivalence is diagnostic and never satisfies a raw experimental-asset checksum.
No old manifest, hash, protocol or historical source was rewritten.

The frozen LINCS pack was rebuilt into a new directory from existing registered
source files. Both output SHA256 values equal the originals exactly:

| Asset | Frozen raw SHA256 | Reconstruction |
|---|---|---|
| `pack.json` | `5e4100852551e8945f88dda92cc60fcf21960e1034320ea90ca8a714b178c120` | Exact match in maestro/Windows |
| `pack_arrays.npz` | `c603e70e7f8bf6264d0d469bdf9210f4c605e54383423be4855764100a5f0a4b` | Exact match |

This re-extracts frozen data; it does not train a new model or tune against test
outcomes. On an LF platform, restoration can reconstruct CRLF only if the resulting
bytes equal the original frozen hash. The tool retains the original manifest and
refuses corrupt inputs or an existing fresh-pack destination.

`replay_fixture_bundle.zip` contains 392 original replay/regression assets: the
evaluation public/private case packages, costing and capability declarations,
frozen pack and development-study metadata. It is about 3.24 MB. Its companion
manifest lists every member, raw hash and size; restoration verifies the entire
archive before writing. Existing differing content is refused, except a verified
line-ending representation that is restored to the registered raw bytes.
Private result members are evaluator-only; distributing them for reproducibility
does not grant a planner access before the registered purchase. These are historical
fixtures, not newly measured outcomes or inputs for training.

The additional `legacy_fixtures_v3/` bundle supplies all originally frozen
denominator inputs and archived fold/source-linkage declarations. Its 16 entries
include the original CRLF `research/case_memory_integration/freeze_protocol.json`:
its registered raw hash also differs from the Git LF blob. This gap was exposed
only after the pack had been restored. The v3 manifest registers both identities;
restoration writes the old raw bytes in the prepared replay checkout, without
changing the old frozen value or the maintained Git source. Earlier incomplete
v1/v2 bundles and their failing test receipts remain visible.

The last legacy replay dependency is a 17-file, 126,841,252-byte prepared dataset
cache. `legacy_dataset_cache_manifest.json` lists exact paths/hashes and records
the verified local-cache restoration. The single offline ReferenceWorld replay
contract then passes. An exact public download of these prepared bytes is not
published; independent raw-source reconstruction remains a separate undertaking.
This is a source-cache-assisted reproduction on clean code, not an independently
downloaded or different-OS biological replication.

Large originals remain outside that bundle. The PISA supplement is 377,658,784
bytes, with its original URL/hash in `pisa_cache_restoration.json` and the source
provenance. The clean prepared run used a hash-verified copy of the local original,
not a fresh network download. LINCS Level5 is 35,518,405,386 bytes and is needed for
source reconstruction, not pack-based regression. `asset_inventory.json` names its
public URL and source hash; the rebuild recomputed that hash. Optional model assets
and legacy protocol replay outputs are not bundled and remain explicit dependencies.

We also re-downloaded the small GEO phase-1 metadata and Hallmark GMT; raw hashes
match. Phase-2's public dated gzip differs from the old local alias at the compressed
byte level, while decoded bytes have the same SHA256. Both representations and the
failed raw match are retained in `source_url_checks.json` and
`phase2_alias_diagnosis.json`. The bundle restores the old alias exactly. A fresh
source reconstruction may use the separately registered dated download under the
builder's alias path, but must still pass the original pack-output checks. It must
not claim to have downloaded the old gzip bytes.

## Reproduction

Use maestro or an environment with the declared optional dependencies. Start with
a fresh checkout. The scope here is a fresh worktree on the same Windows/maestro
interpreter; an independent Linux or dependency-version evaluation was not run.

```powershell
$py = 'D:/anaconda/envs/maestro/python.exe'
$receipts = 'research/astra/results/20261003_prediction_audit_fix_v1'
& $py -m research.astra.reproducibility_audit --out NEW_OUTPUT/checkout_bytes.json
& $py -m pytest tests/test_virtual_cell_panel.py tests/test_handoff.py tests/test_case_control_loop.py tests/test_research_validation.py research/astra/test_reproducibility_audit.py -o addopts= -q --junitxml NEW_OUTPUT/focused.xml
& $py -m research.astra.reproducibility_audit --restore-fixtures-from "$receipts/replay_fixture_bundle.zip" --out NEW_OUTPUT/restored_bytes.json
& $py -m research.astra.reproducibility_audit --restore-fixtures-from "$receipts/legacy_fixtures_v3/replay_fixture_bundle.zip" --out NEW_OUTPUT/legacy_bytes.json
& $py -m pytest research/case_memory_integration/test_external_evaluation.py tests/test_real_case_memory_denominator.py -o addopts= -q --junitxml NEW_OUTPUT/lincs.xml
```

Every output filename must be new. For an alternative original cache or fresh
source rebuild, create a new verified pack rather than altering its manifest:

```powershell
& $py -c 'from pathlib import Path; from tools.datasets.lincs_pack import build_pack; build_pack(Path("NEW_OUTPUT/rebuilt_pack"), workspace=Path("SOURCE_WORKSPACE"))'
& $py -m research.astra.reproducibility_audit --restore-pack-from NEW_OUTPUT/rebuilt_pack --restore-pack-to NEW_OUTPUT/verified_pack --out NEW_OUTPUT/restoration.json
```

The expected hashes always come from the checkout's original frozen manifest,
not a newly generated manifest. `SOURCE_WORKSPACE` must contain the original
LINCS2020 metadata/GCTX, the two development-study compound tables and Hallmark
GMT at the paths in `asset_inventory.json`. Acquire missing files from those
URLs, verify their registered raw hashes, and retain any mismatch as a new receipt.
Do not substitute a different build or update the frozen expectations.

For full legacy replay, restore the prepared cache only from an original verified
cache, and acquire PISA from its original URL or a verified original cache:

```python
import hashlib, json, shutil
from pathlib import Path

cache = Path('ORIGINAL_ASSET_CACHE')
checkout = Path('FRESH_CHECKOUT')
manifest = json.loads((checkout / 'research/astra/results/20261003_prediction_audit_fix_v1/legacy_dataset_cache_manifest.json').read_text())
for name, identity in manifest['files'].items():
    assert hashlib.sha256((cache / name).read_bytes()).hexdigest() == identity['sha256'], name
for name in manifest['files']:
    destination = checkout / name
    if destination.exists():
        assert destination.read_bytes() == (cache / name).read_bytes(), name
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cache / name, destination)
```

The PISA original must equal
`e026b27cc88dd82f0d033605af9e01ce8aa07377fc521f82df9040f0684aa3ea`.
Place it at `data/external/pisa_living_cells/PMC11554310_supplementary.zip`.
Its acquisition URL is
`https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11554310/supplementaryFiles`.
Optional assets behind skipped tests need their own source contracts; this replay
cache is not a distribution of every registered model or dataset.

Full aggregate command (asset-dependent, deliberately not made silently green):

```powershell
& $py -m pytest tests research/astra research/scientific_optimization/test_population_flow.py research/scientific_optimization/test_response_training.py research/case_memory_integration/test_external_evaluation.py -o addopts= -q --junitxml NEW_OUTPUT/full.xml
```

## Verification scope and scientific boundary

Exact final counts and source revisions are recorded in `receipt.json` and the
day log. `full_clean_unprepared.xml` is retained: 1,898 passed, 43 failed,
8 errors, 16 skipped. That is an asset-preparation failure, not a green clean
checkout. Targeted corrected contracts passed 40 in that checkout before asset
restoration. Aggregate and focused scopes overlap and must not be summed.

The final original-environment aggregate passes 1,966 tests, with no failures,
errors or skips; the final focused scope passes 41. The first prepared clean run
retains 1,945 passed, 2 failed, 4 errors and 14 skipped. Further restoration fixes
the frozen-schema/source and prepared-data blockers rather than suppressing them;
later scopes and final clean counts are listed separately in the receipt.

Two verification-command mistakes are retained: the first broad local collector
encountered the temporary nested fixture tree left by our inside-repository test;
it was moved outside the collection tree before retry. The first clean focused
command specified a basetemp whose parent did not exist; creating that parent
fixed the command, without changing code. Neither failed receipt is discarded.
Supplemental fixture enumeration initially omitted registry entries expressed as
constant names, then missed the original freeze-schema bytes. Full registry-based
enumeration corrected those omissions; the intermediate receipts remain.

No new STATE inference, API science, biological model fitting, physical experiment
or decision-utility comparison ran. Neither the green engineering tests nor exact
pack reconstruction supplies biological state gain, calibrated mechanism likelihoods
or agent utility. The existing scientific designs remain research-only.
