# Daily record: 2026-10-20

Preparation and workspace maintenance only; the new scientific experiment was not run.

## Post-cleanup readiness review and revised execution handoff

Reviewed on 2026-10-20 after both cleanup passes. The new research experiment has still NOT run.
This section supersedes the earlier pending-presentation and final-test-failure caveats below.
The user clarified that execution must test the reviewed EvoPharm functional-rule-revision idea
and supplied the original English execution brief. [NEXT_RESEARCH_PROMPT.md](NEXT_RESEARCH_PROMPT.md)
was updated from that supplied brief, preserving its primary question, restricted edits,
globally held-out pairs, and decisive same-information comparators.

Current decision: READY to execute the bounded internal-development study, with the functional
transfer-rule hypothesis intact. Independent biological validation and physical-cost claims
remain outside what these assets support. Missing cost identifiers do not block this model study.

Rechecked facts:

- Branch `codex/workspace-preparation`, HEAD `f4e37615`, with uncommitted preparation changes.
  Neither the working changes nor the newly added source receipts are captured by HEAD alone.
- Project-local Python 3.11.16: every preparation-lock version matches; `pip check` passes;
  maintained CLI help passes. The full default suite passed all 940 tests, exit 0, using
  `D:/MAESTRO/.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider --basetemp D:/MAESTRO_maintenance_backups/20261020_readiness_review_pytest`.
  This is software readiness, not evidence for the research hypothesis.
- All three canonical O'Neil files pass the existing verify-only command, including published
  size/MD5, local SHA-256, and OOXML ZIP integrity. No redownload is required.
- All 1,080 original research files in the first-pass research inventory, excluding the three
  intentionally consolidated central indexes, match their recorded hashes. All 30 registered
  studies' protocol, evidence, and verifier targets exist. Separately, all 1,066 Git-tracked
  files inside those study roots match the pre-cleanup baseline.
- Recovery hashes and sizes match for 122 first-pass archived files (31,638,875 bytes),
  1,174 second-pass archived files (86,037,847 bytes), and 41 backed-up old log files.
  These are manifest scopes, not an additive claim about distinct reclaimed bytes.
  Active log had five files at review; checked live Markdown links resolve. No further cleanup
  or study deletion was performed. Same-drive archival still reclaims zero drive capacity.
- One user-authorized, synthetic JSON API connectivity check passed through the existing
  DeepSeek client: returned model `deepseek-flash`, 57 input tokens, 11 output tokens,
  one HTTP attempt, 0.88 seconds, no scientific payload. Monetary cost was not independently
  priced. API keys and authorization headers were not printed or persisted. TypeSafe was not
  called. This establishes connectivity only, not Agent value.

Additional identity/dose-only checks (no outcome summaries, model fits, or scientific tests):

| Source batch | Combination rows | Same-batch monotherapy curves for both drugs | Both doses within curve ranges | Both doses match within tolerance |
|---|---:|---:|---:|---:|
| 1 | 358,560 | 358,560 | 358,560 | 23,251 |
| 2 | 5,232 | 5,232 | 5,232 | 344 |
| 3 | 5,040 | 5,040 | 5,040 | 270 |

Dose matching used relative tolerance 1e-7 and absolute tolerance 1e-12. Primary batches 1/2
jointly cover exactly 583 unordered pairs by 39 cells: 22,737 pair-cell groups. Each group occurs
in one primary batch, has 16 distinct points, and forms a complete 4x4 dose grid. Most primary
rows require interpolation to calculate a same-dose monotherapy reference; 23,595/363,792
match both doses within tolerance. Structural completeness does not certify numerical validity
or biological independence. Batch 3 is a selected repeat and is excluded from the primary design.

Handoff changes are operational: verified environment/data replace stale availability claims;
the primary study must save executable before/after sharing rules and their effects on unseen
pairs; a frozen activity-shortlist utility supplies a concrete default while reference-adjusted
effects remain separately labeled; conventional models get comparable S+C tuning; a failed G
retention gate falls back without inventing a new edit; API testing has a small explicit budget
and a separate optional secondary arm. DBP remains separate. No full world-model evolution,
acquisition-policy benefit, molecular mechanism, or autonomous-discovery claim is authorized by
these readiness checks. Only this receipt and the existing execution prompt were edited in review.

## Second cleanup (supersedes earlier pending-cleanup notes below)

- Archived the completed `.build-1024-reposition` presentation, retired pytest fixture trees,
  exploratory tmp debug scripts/logs and `tmp/smoke_fp`, with SHA256 verification after every move.
- Moved 1174 physical files (86,037,847 bytes) out of the active workspace;
  removed 1472 empty directories and archived 30 one-off code files including the old log audit.
- Reduced log from 41 files to five: one index, one old-direction history and three dated files.
  The original log files and review packages are recoverable byte-for-byte outside the workspace.
- Seven `outputs/local_verification/upstream/dataset` junctions pointed at canonical data.
  They were relocated with the empty verification scaffolding; their targets were not traversed or moved.
  The earlier claim of independent duplicate workbook copies was incorrect: these were aliases.
- Kept all 30 registered study packages, their frozen code and required tmp caches. Production code
  remains unchanged because absence of static callers does not prove a frozen/dynamic consumer absent.
- Recovery: `D:/MAESTRO_maintenance_backups/20261020_deep_cleanup/`; original log paths are recorded in CLEANUP_FILES.json.
  Same-drive recoverable moves reclaim zero drive capacity. This is active-workspace reduction.
- Current handoff: [NEXT_RESEARCH_PROMPT.md](NEXT_RESEARCH_PROMPT.md).
  Future experiment records belong in `log/YYYYMMDD/`; historical directions belong in `log/archive/`.

## Original preparation record (historical measurements)

The following records earlier checks. Its pending-cleanup, layout and duplicate-copy notes are
superseded by the second-cleanup section above. Final verification is recorded at the end.

# MAESTRO preparation receipt — 2026-10-20

Preparation completed on `codex/workspace-preparation`, starting from clean Git revision
`f4e37615d29a90657f58600f1de36c25300249db`. No new scientific experiment, provider call,
model fitting, cache rebuild or final-evaluation read was performed. ALMANAC outcome vault
and sealed PRISM files were not opened. Scientific feasibility is not established.

## Separate readiness judgments

| Area | Judgment | Evidence / remaining limit |
|---|---|---|
| Environment | READY for core and CPU ONeil preparation | Python 3.11.16; editable install, pip check, core/data imports and CLI help passed. Both environments passed 940 tests earlier; final local check is 939 passed / 1 shape failure from a concurrently created presentation folder. Clean reconstruction passed. |
| Data access | READY for original ONeil response workbooks | Three full official files, 40,518,420 bytes total, published size/MD5 and SHA-256, OOXML ZIP CRC verified. Data/ONEIL_SOURCES.json and source metadata are reviewable. |
| Historical cleanup | COMPLETED for verified scope; ambiguous assets retained | 17 duplicate summaries consolidated/archived; original 105-file presentation package archived. All 30 study closures intact. Newly created concurrent .build-1024-reposition is retained pending producer completion; final repository-shape check remains blocked. |
| Research-input structure | RAW RESPONSE ROWS AVAILABLE; design qualification remains | Technical replicate columns and dose/batch/identity fields recovered. No plate/well/control/date/stock identifiers: real acquisition costs and culture independence NOT qualified. New pair partitions and matched single-agent contrasts still need protocol qualification. |

The next agent can begin from raw-level normalized response workbooks rather than aggregate-only
fallback. The route is still exposed internal development. Physical-cost claims are blocked by
missing identifiers; independent biological confirmation is unavailable. No need to reopen or
restore unrelated historical datasets for this pilot.

## Environment diagnosis and reproduction

Available interpreters checked: `C:/Python314/python.exe` 3.14.4 (global default, not selected),
`D:/anaconda/python.exe` 3.9.13 (below project minimum), existing conda `maestro`
`D:/anaconda/envs/maestro/python.exe` 3.11.16 (base for project-local environment).
Other discovered conda environments were listed but not modified. Project-local `.venv` is
selected to isolate old scientific dependencies without changing the legacy environment.

Legacy maestro `pip check` initially reported arc-state 0.11.3 missing cell-eval, cell-load and
ipykernel. It was not necessary to repair that heavy historical stack for a CPU ONeil study.
The supported `.venv` has no broken requirements. Both environments pass the core tests after
removing the pre-existing unrelated `.build-1024` artifact tree. Default global Python, CUDA,
proxies, user configuration and other environments were not changed.

```powershell
Set-Location D:\MAESTRO
& 'D:\anaconda\envs\maestro\python.exe' -m venv .venv
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m pip install -r requirements-preparation.lock
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m pip install --no-deps --no-build-isolation -e '.[test,preparation]'
& 'D:\MAESTRO\.venv\Scripts\Activate.ps1'
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m pip check
& 'D:\MAESTRO\.venv\Scripts\maestro.exe' --help
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m pytest
& 'D:\anaconda\envs\maestro\python.exe' -m pytest
& 'D:\MAESTRO\.venv\Scripts\python.exe' -m tools.datasets.oneil_sources --verify-only
```

Activation is optional when using these explicit executables. Run creation/installation only
when rebuilding an absent or unhealthy environment. The single Windows x64 / CPython 3.11
[lock](../../requirements-preparation.lock) pins all installed transitive packages including build
and test tools. No existing pins were removed: pytest 9.1.1 installed successfully. The
`preparation` extra separates the focused stack from the broad optional research stack.
Import inspection also found `anndata` and `matplotlib` in retained optional code; these are
now declared in the broad research extra, but are not needed/installed for this CPU preparation.
Torch/RDKit/ARC inference and old scientific pickle reproduction remain optional and may need
original per-study environments; FAR's saved sklearn-1.6.1 pickle is not portable to newer sklearn.
No GPU dependency was installed.

Hardware observed: 28 logical CPUs, 16,944,848,896 bytes RAM; starting D: free space
118,254,407,680 bytes. Streaming the 38.8 MB workbook is practical on this machine; metadata
census used the maintained streaming reader. Use modest fitting grids and thread counts on this
16 GB machine. This is a practical preparation assessment, not a full experiment resource estimate.
`curl.exe`, Git and PowerShell are available. Acquisition uses normal public GETs with small
ranges and bounded retries; HEAD is not used to establish availability. Early large transfers
timed out or received expiring-link 403 responses; smaller public ranges completed and the
assembled full-file published MD5 authenticated the result. Regenerable download scratch was removed.

A fresh temporary environment was built from this lock, editable installed with the same commands,
passed pip check and core/numerical/reader imports, then was removed. Logs remain under
`D:/MAESTRO_maintenance_backups/20261020_preparation/` (`reconstruction_install.txt`).
A scratch script named inspect.py initially shadowed the standard library during one schema-check
startup; it was renamed and the structural census rerun successfully. This was a resolved
maintenance-script issue, not a defect in the selected environment or source workbooks.

## Data receipt and reuse boundaries

[Authoritative inventory](../../data/INVENTORY.md), [file-level observations](../../data/ASSETS.json),
[source receipts](../../data/ONEIL_SOURCES.json) and [schema/protocol receipt](../../data/ONEIL_STRUCTURE.json)
are tracked-size reviewable documents. Original workbooks remain ignored in
`D:/MAESTRO/data/raw/oneil2026_qualification/`; each source metadata response is retained there.
All three are AACR/Figshare v1 for DOI `10.1158/1535-7163.MCT-15-0843`.

| File ID | Bytes | Published MD5 | Actual format |
|---|---:|---|---|
| 39962566 combination | 38,829,879 | d1b914b83d7ef475795731bec1d1e36e | OOXML, despite .xls extension |
| 39962560 single agent | 1,678,111 | 26c8ccbe68837d9c3bba967bb421e9fd | OOXML/xlsx |
| 39962563 legends | 10,430 | 6992447cee5b60ee9f15efa209cc3bfe | OOXML/xlsx |

Single-agent: 16,752 rows, BatchID 1/2/3 counts 11,856 / 2,736 / 2,160; 39 lines, 38 drugs,
6 nonempty technical viability columns. Combination: 368,832 rows, batch counts
358,560 / 5,232 / 5,040; 583 unordered pairs, 4 nonempty technical columns.
Dose headers are micromolar; legends specify 96 h. Batches 1/2 are primary screen; batch 3
is a partial selected-drug repeat. These are not three independent experiments.

`mu/muMax` and `X/X0` are derived normalized growth responses. DMSO normalization was performed
by the publisher; raw control IDs/muMax linkage are not exported. Technical replicates do not
identify independent cultures or priced acquisition bundles. No synergy, performance effect,
favorable subset, model or new scientific result was computed in preparation.

The existing `oneil_v1.npz` is retained byte-identical (368,620 bytes; SHA-256
`2edc5e7a351e7ded3daf6a37dcf6a32f76d442216bf2cb1a9feff5f97baeeb1f`). Its JSON's combination
and single-agent source hashes match the recovered originals. This authenticates source identity,
not its aggregation semantics. Its recorded build had zero single-batch fallbacks; the maintained
historical loader nevertheless CAN fall back across batches and averages primary batches.
`virtual_cell.combination_world` and old discovery replay use a cell-history split, not the new
global pair split. They do not establish pair isolation or real physical costs. Nothing historical
was modified to make the new protocol appear ready.

55 local dataset/version directories were reconciled against files and retained source/study
references; 17 catalog path claims are missing. Empty old raw/source directories are explicitly
EMPTY_DIRECTORY_NOT_DATA. The populated data includes LINCS (~56 GB), PRISM, Beat AML,
Jaaks, GCP, Tahoe and retained model assets. Previously evaluated or exposed statuses persist.
ALMANAC has its historical cache but an empty original-source directory; its outcomes were not
read. GDSC2/CTRP and old evaluation-case source paths remain unavailable where recorded.
Do not restore them merely to run old asset-dependent suites. The old September external archive
path does not exist; no `D:/MAESTRO_data_archive_*` directory was observed. `MAESTRO-retained`
and `MAESTRO_TMP` were preserved without asserting verified archive identity.

## Research consolidation and cleanup

The question/units/comparator/final-decision map is [research/REPORT.md](../../research/REPORT.md).
Numerical authority and exact audit pointers remain in [EVIDENCE](../../research/EVIDENCE.md).
The machine registry now carries evidence paths and closure decisions for all 30 retained studies.
Later seed-attribution, FAR, action-substitution P0 and identifiability-audit corrections override
earlier positive claims. RSD D1 does not establish D2; heavy tails failed to repair progression.
The decoupled study actually has FREEZE and DEV_RESULT: its calibration-only development result
and unchanged decisions are now recorded centrally, correcting the stale unrun direction note.

[Cleanup manifest](#original-cleanup-and-recovery-narrative) and [per-file actions](CLEANUP_FILES.json) give exact paths,
reasons, original hashes and recovery locations. The external package at
`D:/MAESTRO_maintenance_backups/20261020_preparation/` preserves complete presentation sources,
outputs, removed summaries, previous mutable reports and baseline inventories. Representative
report restoration matched SHA-256. Four obsolete presentation generators left active code;
no unused production module was guessed from static search alone. Ambiguous tmp/reference/user
material and unique scientific originals stay in place with explicit keep reasons.

[Preservation check](CLEANUP_FILES.json): all 616 pinned research files match their baseline
bytes; all tracked files in the 30 study closures remain unchanged. No freeze hash was regenerated
and no frozen record was rewritten. Cross-study imports make partial study-package relocation
unsafe without redesign, so their minimal complete evidence closures remain in place.

## Verification and pre-existing limits

- Initial maestro test run: 939 passed, 1 pre-existing repository-shape failure caused by `.build-1024`.
  After archival, maestro: **940 passed in 127.20 s**. No assertion was weakened or test excluded.
- Project-local environment earlier: **940 default tests passed**; focused repository-shape plus synthetic
  combination-builder/vault tests: **27 passed in 11.62 s**. Synthetic vault checks use temporary
  fixtures, not real ALMANAC access.
- **Final local test:** 939 passed, 1 failed in 94.68 s. During preparation, a different active
  presentation task created `.build-1024-reposition` (created 14:10:37 Asia/Shanghai, modified
  after creation). The existing repository-shape assertion rejects all `.build-*` directories.
  This new user-work tree was preserved, not moved while its producer may still be writing.
  Original `.build-1024` cleanup is verified; no test assertion was weakened. The final default
  suite is therefore NOT fully green. Once that producer completes, keep its outputs outside
  the checkout or archive the complete package, then rerun the same test command. This is a
  concurrent filesystem blocker, not a numerical/runtime failure or scientific qualification.
- pip check, editable installation, core/numerical/document-reader imports and maintained help
  commands passed; [command receipt](CLEANUP_FILES.json). HTML masquerading as a workbook
  and incorrect size/checksum were both refused by the acquisition verifier.
- RSD verifier was inspected before running without --replay: all declared source/text hashes,
  saved stage rules and saved verdict checks passed (`VERIFY OK`). No model or study reran.
- Generic research preflight without explicit study remains expected exit 2, BLOCKED/ASSET_MISSING:
  no active protocol is released. Historical cases/metadata missing in the inventory remain
  explicit research-asset blockers; no hidden tier was opened to make old tests pass.
- Registry evidence paths, active document links, Python syntax and git diff whitespace were checked.
  No unrelated tracked file change or unexpected deletion was found. New concurrent ignored files are retained and separately noted.

Concurrent final review also found copies under
`outputs/local_verification/upstream/dataset/raw/oneil2026_qualification/`, created outside the
preparation commands. The three workbooks are SHA-256-identical to the recovered originals;
these are copies, not independent evidence. They and accompanying metadata are retained while
the concurrent consumer is unknown, and counted separately from preparation additions.

## Measured accounting

Snapshot: 2026-10-20 14:19:58 Asia/Shanghai; concurrent work may change after this observation. Consistent scope
excludes `.git`, `.venv`, `__pycache__` and `.pytest_cache`; no symlinks followed.
Before: **9,682 files / 136,062,933,729 bytes**.
After snapshot: **9,605 files / 136,120,452,537 bytes**.
Original paths no longer active: **122 files / 31,638,875 bytes**, all recoverably archived
(105 presentation files plus 17 redundant summaries).
New preparation files (including editable-install metadata): **24 / 42,085,366 bytes**.
Concurrent presentation and dataset-copy additions: **21 / 47,069,048 bytes**,
preserved user work outside this maintenance. Consolidated existing prose also changed size.
The net workspace-byte change includes both kinds of additions and is not reported as savings.

Original-content drive capacity reclaimed: **0 bytes**, because recovery packages remain on D:.
Active original content reduced by **31,638,875 bytes (~30.17 MiB)**. Temporary reconstruction
environment and redundant maintenance download fragments were removed; these are not counted as
reclaimed original scientific content. The selected local environment adds installation space and
is excluded consistently from both counts. Sizes are logical file lengths, not allocation deltas.

## Handoff

[Complete revised English execution prompt](NEXT_RESEARCH_PROMPT.md). It preserves the objective,
known constituent drugs and globally held-out unordered pairs, four isolated roles, no final-label
access for fitting/edit/continuation, one challenge and one edit, same-data fixed refit, the fixed
all-gates sparse comparator, strong conventional nonlinear learning, model/Agent separation,
resource-selected aggregate fallback and scoped cost/claim limits. It is NOT EXECUTED.


## Original cleanup and recovery narrative

# Cleanup manifest: 2026-10-20

Baseline: clean `main`, Git revision `f4e37615d29a90657f58600f1de36c25300249db`.
Working branch: `codex/workspace-preparation`. No user changes were present at start.
Recovery root: `D:/MAESTRO_maintenance_backups/20261020_preparation/`.
[Every affected file](CLEANUP_FILES.json) records original path, bytes, SHA-256, reason,
replacement and recovery path. External archive manifests record SHA-256 before and after moves.
Native PowerShell moves were restricted to literal paths within this workspace, with reparse points refused.

| Original path | Action | Reason / replacement | Recovery / integrity |
|---|---|---|---|
| `.build-1024/` (105 files; 31,627,005 bytes) | Archive complete tree | Unrelated presentation generators, drafts, renders and deliverables; no retained consumers. Removes obsolete `build_deck.py`, `build_guide.py`, `render_deck.ps1`, `render_guide.ps1` from active code. No unique asset discarded. | Backup `.build-1024/`, original layout; every SHA-256 checked after move; `presentation_backup_manifest.json`. |
| `log/studies/` (17 files) | Consolidate and archive | Central research map/EVIDENCE and original dated study roots preserve all useful material. Old program-revision positives and proposed fresh tiers are superseded by seed-attribution/P0 audits. | Backup `log_studies/`; every hash checked; `report_backup_manifest.json`; exact replacement per file in CLEANUP_FILES. |
| `log/EXPERIMENT_REGISTER.md` | Consolidate | Repeated numeric table replaced by authoritative map/registry pointers. | Original at backup `previous_EXPERIMENT_REGISTER.md` and baseline Git revision. |
| `research/REPORT.md` | Consolidate | Duplicate opening chronology removed; new question/units/comparator/correction/closure map. Original detailed study records and EVIDENCE retained. | Backup `previous_REPORT.md` and Git baseline. |
| `log/DIRECTIONS.md` | Correct live index | Decoupled RSD freeze and development result actually exist; later decisions override old proposed continuations. | Git baseline; original study records untouched. |
| `data/INVENTORY.md` | Replace stale claims | Actual file states/sizes and source registrations in data/ASSETS.json. Prior September archive is absent. | Backup `previous_DATA_INVENTORY.md`; unique prior history preserved. |
| All 30 registered study packages | Keep complete evidence closures | Cross-study imports and hashes require exact relative layout. Preserve protocols, negative results, deviations, records, cache pins and reproductions. | Baseline Git revision plus retained files; CLEANUP_FILES.json (previous_preservation_check). |
| Large scientific originals and all external archives | Keep | Unneeded for ONeil does not mean obsolete. No data removed or relocated; no ALMANAC vault opened. | In place; source receipts and inventory distinguish missing paths from invalid files. |
| `.build-1024-reposition/` (created during preparation) | Retain pending producer completion | Concurrent presentation work; actively changed after baseline. Preserve user changes. Causes final default repository-shape check to fail; move only after producer completion. | In place, outside the original cleanup baseline; no content opened or changed by preparation. |
| `outputs/local_verification/upstream/dataset/raw/oneil2026_qualification/` (created during preparation) | Retain pending consumer identification | Concurrent copies, not generated by preparation commands. Workbook SHA-256 matches source receipts; not independent evidence. | In place; duplicate identities in data/ASSETS.json. |
| `.env`, `.claude`, `.workbuddy`, `tmp`, external `D:/MAESTRO-retained`, `D:/MAESTRO_TMP` | Retain pending clarification | Unrelated/private or ambiguous material, not proven obsolete. Secret values were not read. | Unchanged. |
| Historical verifiers / production modules without callers | Keep pending specific evidence | Static absence of references alone is insufficient; frozen and dynamic reproduction dependencies remain. | In place; no speculative code deletion. |

## Recovery

For an archived report, first compare `Get-FileHash -Algorithm SHA256` with CLEANUP_FILES,
then `Copy-Item -LiteralPath 'D:\MAESTRO_maintenance_backups\20261020_preparation\log_studies\NAME.md' -Destination 'D:\MAESTRO\log\studies\NAME.md'`
after creating the destination directory. Presentation package restoration is the analogous
Copy-Item of `.build-1024` with `-Recurse`, after verifying target is exactly within the workspace.
Tracked prose/code can be extracted from the identified baseline Git revision without resetting user work.
A representative report was restored to an external verification file and its hash matched.

## Space accounting

Archival moves reduce active workspace content but reclaim **zero drive capacity**, because
recovery packages remain on D:. Measured file-content counts/bytes before and after (excluding
Git, local environments, bytecode and pytest caches consistently) are recorded in PREPARATION.md.
No claim of reclaimed drive capacity is made. New dataset and environment installations add space.

## Previous maintenance record (preserved verbatim)

# Cleanup Manifest (2026-10-16)

This cleanup removed only regenerable content. Frozen research materials, results, external data, and referenced caches were retained.

| Category | Scope | Pre-cleanup estimate | Reason |
|---|---|---:|---|
| Python bytecode | Repository-wide `__pycache__/` | 218 files / 4,130,544 bytes | Automatically regenerated by the interpreter; contains no experimental content |
| pytest cache | Repository-wide `.pytest_cache/` | Included in the scan above | Automatically regenerated after tests; contains no scientific conclusions |
| dry-run cache | `research/knowledge_transfer_20261012/cache/dryrun_*` and `dryrun_phase1.log` | About 2.23 MB | No full-text references; simulation runs only |

Not removed: `data/external/`, frozen research files, arrays and models in `knowledge_transfer/cache` referenced by FREEZE/input audits/replays, historical results in `outputs` referenced by `EVIDENCE.md`, and duplicate test snapshots that remain independently replayable.


## Final second-pass verification

- Existing conda `maestro` interpreter: 940 default software tests passed, exit code 0.
  Command: `D:/anaconda/envs/maestro/python.exe -B -m pytest -q -p no:cacheprovider --basetemp D:/MAESTRO_maintenance_backups/20261020_deep_cleanup/pytest_tmp`.
  Full output is in the recovery root's `pytest.txt`; pytest fixtures remain outside the workspace.
- 1,080 original study files match the first-pass SHA256 inventory exactly; all 30 study closures are retained.
- All checked live Markdown links resolve; all three canonical O'Neil workbook SHA256 values match their receipts.
- All seven archived Windows junctions still point to their original canonical data targets.
- 19 regenerable bytecode/pytest cache directories were moved outside the workspace after testing.
  Exact file counts and bytes are in CLEANUP_FILES.json; no drive-space recovery is claimed.
- Old-direction log originals and scientific frozen records remain recoverable. No new scientific experiment ran.
