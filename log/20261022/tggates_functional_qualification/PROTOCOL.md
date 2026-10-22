# TG-GATEs outcome-blind functional-menu qualification

Registered 2026-10-22, Asia/Shanghai, before new acquisition or DNA/LDH payload inspection. This follows source/identity qualification in `log/20261022/tggates_source_qualification/`; that evidence remains unchanged and is not downloaded again. Absence of lot metadata does not invalidate a narrower temporal-condition question.

## Source, limits, and access contract

Acquire exactly one official object: `https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/open_tggates_cell_viability.zip`, previously advertised as approximately 51 KB. Store original bytes in this directory's `sealed_source/`. Record URL, status, headers, SHA256, bytes, UTC receipt and elapsed time. <=2,000,000 new HTTP response-body bytes, one writer, initial <=20 minutes. No CEL, expression, images, other functional datasets, model API or GPU. Runtime: `D:/anaconda/envs/maestro/python.exe`.

All new experimental/test code is in `research/tggates_functional_qualification_20261022/`; all outputs, temporary test files, receipts, failures, freezes and source files are under this log directory. No old source or research output is overwritten.

Acquisition does not print or parse CSV rows. After meaningful synthetic tests and a pre-open freeze of code/protocol/inputs, a separate worker process may decode only the source table's header-approved identity fields and DNA/LDH fields for missingness/equality. Its allowed export is identity fields (`EXP_ID`, `GROUP_ID`, `INDIVIDUAL_ID`, compound, species, sex, dose, unit, level, time) plus DNA/LDH missing booleans and duplicate conflict booleans. No observed response, numerical extrema/means/distribution, potency/activity label, shortlist, model fit, rank or per-drug activity rate may leave the worker.

CSV identity is preserved as strings (including leading zeros); no name-to-structure guesses or unit conversion. Response missingness uses explicit string tokens after trimming/casefold: empty, `na`, `n/a`, `nan`, `null`, `none`, `-`, `--`, `no data`, `no_data`, `not available`; genuinely zero-valued strings are nonmissing. Unknown nonmissing response strings are counted as nonmissing, not cast to outcomes or silently dropped; the census does not claim numerical validity. Source headers and parser dtype policy are allowed metadata. Duplicate sample keys are retained as groups, require exact identity agreement, and compare nonmissing raw response strings only to export conflict booleans; never choose a larger response.

Mixed content is isolated by independent worker and restricted data flow, not OS encryption or file permissions. No process outside that worker is to open response rows. Error messages must identify stages/field names without echoing any raw response or full source row.

## Frozen questions and outcome-blind decision

1. Authenticate source and exact sample keys; join human functional rows to previous 2,610 human cell samples and 2,605 CEL attributes. Verify compound, concentration, original unit, dose level and time as well as experiment/group/individual keys; report keys absent from either side and conflicts.
2. Explain the five previously unlinked sample/CEL records from identity and availability fields only. Do not infer they have valid expression or functional outcomes from a count match.
3. Count human functional coverage, DNA/LDH nulls, duplicate-key identity/response conflicts and complete measurement menus. Preserve failed/missing observations; no missing-to-negative conversion.
4. Reproduce same compound-dose-unit 2/8/24 h menu counts from old identity data, then count which conditions have matching source sample/CEL availability and nonmissing DNA/LDH flags. Multiple time samples are not longitudinal observations of the same cells or certified independent lots.

GO only to a new dev-only opening protocol if necessary exact keys and paired functional/CEL availability can be authenticated without value-based filtering. This census is not a claim of signal strength, biological replication, dose independence, world-model value or RSI. Any conflicts/missing menus remain explicit exclusions or blockers defined by identity/null flags, never response magnitude. Later numerical analysis requires separate chemical grouping/reservation, exact early-state/late-functional task units, dose-selection prior-feedback policy, normalization provenance, allowed dev-only endpoints/roles, and frozen success/stop criteria. No opening is authorised by a green coverage count alone.
