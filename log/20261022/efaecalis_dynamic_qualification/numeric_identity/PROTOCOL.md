# Exact E. faecalis identity and challenge-design census

Preregistered 2026-10-22 after schema/coordinate discovery and before finite source numerical values are interpreted. Root explicitly authorizes day/lineage/concentration design metadata, without OD/IC50/AUC values. Prior nonfinite-string guard failure, all author methods/design and schema remain exposed; no sealed performance claim is made. This census is offline, no source requests/model/API calls.

## Exact value scope

Use unmodified `redirect_followup/pbio.3002970.s001.raw.xlsx`, matching its NETWORK SHA256. Decode value text only for the following exact coordinates, no formulas/caches:

- **Fig4B replicate IDs:** B9:B28, J9:J28, Q9:Q28, X9:X28, AE9:AE28, AL9:AL28, AS9:AS28. The safe row8 labels explicitly say Replicate; row6 strings label days2/4/6/8/10/12/14, respectively. Check each is the same full set of twenty unique IDs and row-order equality; do not assume IDs from row position.
- **Fig4B DOX challenge concentrations:** C4:H4, immediately below C3=`Concentration DOX`. These six values are assay-design metadata, not CRO evolution exposure/history. Units are authenticated separately by primary caption/provenance, not guessed from numbers. A zero value, if present, is a candidate no-drug challenge control, not proof of normalization provenance. Concentrations may reflect the designer's prior knowledge/feedback and are DESIGN/PRIOR-FEEDBACK-EXPOSED, not random interventions or agent-free knowledge.
- **Fig4B embedded ID/day labels:** D34:W34 (twenty `strain` column IDs), C35:C48 (fourteen Day row IDs), and D31:R31 (fifteen Days labels for AUC summary). No corresponding response cells are decoded. Determine daily/even-day identity menus and equality with top-panel IDs; do not assume these embedded regions are raw IC50 trajectories or redefine a gate without explicit preregistration.
- **Fig1B main-clone dates:** the B cell of each of the eighty rows whose existing approved A string matches `(CIP|DAP|DOX|CRO|LZD) [1-4]`. The exact coordinate list is generated and frozen from the safe string JSON before source-value access. Check precisely 5drug×4lineage×day{2,4,6,8}, 80unique clone/time records. Drug-response columns C:G/I:M remain excluded. Mean/SEM schema authenticates five assay slots per record, not response completeness/quality or independent biological samples.

All other numerical cells, other worksheets' bodies, formulas/caches and response arrays remain unread/unexported. Reading enclosing XML bytes for coordinate routing is unavoidable; the parser must never retrieve/interpret their numeric text. Strict failure on missing/duplicate/typed-string/formula/invalid authorized cells, retain failure without expanding scope.

## Verification and outputs

Use maestro Python `-B`; code/tests only under `research/efaecalis_dynamic_qualification_20261022/`, all records/test artifacts here under `log/`. Freeze protocol/code/tests, exact allowlist, successful synthetic-test result, source workbook/NETWORK and safe JSON hashes before real census. Tests verify adversarial response values outside scope are ignored, identity type/integer guards, missing/duplicate cells, set/order comparisons and unchanged bytes. Output `CENSUS.json` with only allowed design/identity values, exact access trace and provenance checks.

Success: authenticated main-clone drug/lineage/day keys, top DOX-challenge twenty-ID equality, exact observed day menus and assay dose grid; retain gaps between clone and population experiments, mother→sample IDs, controls and technical replicates. No independence increase from repeated days/doses. Numeric model evaluations, outcome-dependent gating and speculative serial-switch claims are outside scope. Proposed alternative even-day gates must be separately recorded before outcome access; no numeric outcome gate has yet been executed.
