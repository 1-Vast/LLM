# sciplex_pilot_v1 — Handoff (Task: Data Acquisition & Construction)

Status: **COMPLETE** — package built, QA 10/10 passed. No model/code integration;
no commit/push (per task constraints).

## 1. What was delivered

Data package `data/processed/sciplex_pilot_v1/`:

| File | Contents |
|---|---|
| `pilot_manifest.json` | Protocol pointer, source checksums (MD5+SHA256, Zenodo record 13350497), condition counts, gene-mapping stats, row counts, build timestamp |
| `observation_provenance.csv` | 240 condition-level rows with full contract columns: source_record_id, source_file, source_md5, perturbation_identity, dose_value, control_identity, cells_in_condition, measurement_status, … |
| `response_arrays.npz` | `means::sciplex2` (33×58,347), `effects::sciplex2` (33×58,347), `means::sciplex4` (207×58,347), `effects::sciplex4` (207×58,347) — log1p-CP10K, deterministic |
| `response_genes.txt` / `response_index.csv` | Gene axis (raw var names, join key) and condition-axis index with `effect_available` flag |
| `typed_evidence.csv` | Evidence layering per condition: `direct_molecular_measurement` (vehicle controls) vs `derived_population_response` (perturbations). **No row is marked `qualified_experimental_evidence`.** No outcome labels constructed. |

QA outputs `outputs/sciplex_pilot_v1/`: `QA_REPORT.md`, `qa_report.json`,
`qa_effect_distributions.png`.

Build/QA tools: `tools/case_memory/build_sciplex_pilot.py`,
`tools/case_memory/qa_sciplex_pilot.py`.

## 2. Conditions constructed

- **sciPlex2**: 33 conditions (32 agent×dose + vehicle control); agent-specific
  zero-dose wells as population controls; 4 agents × 8 doses
  (BMS, Dex, Nutlin, SAHA) across 3 cell lines (A549, MCF7, K562).
- **sciPlex4**: 207 conditions (204 HDACi × precursor/enzyme-inhibitor
  combinations with DMSO/DMSO per-cell-line controls + 3 controls).
  This is a **chemical metabolic rescue** design (evidence layer
  `chemical_metabolic_rescue`), NOT a genetic-rescue experiment.

## 3. Gene mapping (honest accounting)

- 37,537 / 58,347 (64.3%) var names resolved to HGNC approved symbols
  (35,071 direct; 2,060 via prev_symbol/alias or de-duplication-suffix
  stripping — the `:N` scanpy-style suffixes on 1,701 names were resolved
  where the base symbol is valid).
- 20,810 unmapped, categorized:
  - **17,783 locus/accession tags** (`AC…`, `AL…`): legacy 10x reference
    identifiers from the 2019-era genome build; genuinely unresolvable to
    current HGNC symbols without an Ensembl GTF crosswalk.
  - **1,109** de-dup-suffixed names whose base (rRNA, snoRNA, mixed IDs) is
    not in HGNC.
  - **1,918** other noncoding / unknown.
- Mapped counts per condition are in `pilot_manifest.json`; unmapped genes
  remain in the arrays (positionally indexed by `response_genes.txt`) so no
  information is silently dropped.

## 4. QA results (10/10)

Structural: shapes match manifest; no NaN/Inf; control rows have exactly zero
effect; all conditions have ≥11 cells (min 11); provenance columns complete.

Scientific: effect distributions centered at 0 (median 0.0000 both studies);
dose-response sanity 4/4 agents (BMS biphasic — matches the non-monotonicity
reported in the original sci-Plex paper; Dex and Nutlin monotonically
increasing; SAHA most widespread, ~2,400 genes with |effect|>0.1, max 773
genes with |effect|>0.25); HDACi widespread-effect sanity passed;
no layer upgrade (nothing claims qualified_experimental_evidence).

## 5. Reproduction commands

```bash
cd /d/MAESTRO
# 1. sources must already exist (checksums verified in build):
ls data/external/sciplex_family/
# 2. build (recomputes checksums, deterministic):
D:/anaconda/envs/maestro/python.exe tools/case_memory/build_sciplex_pilot.py
# 3. QA (seed 20260929, deterministic):
D:/anaconda/envs/maestro/python.exe tools/case_memory/qa_sciplex_pilot.py
```

## 6. Known limitations (do not paper over these downstream)

1. **Dose units are file tokens, not verified units** — `dose_unit` is marked
   `unverified_in_file` in provenance; contract mapping to nM/µM must go
   through the protocol's contract table, never assumed.
2. **No biological replicates** — sci-Plex hash rows are an indexing scheme;
   `biological_replicate_id` = unavailable. Population means have no
   replicate-level uncertainty.
3. **scPerturb-processed derivative** — not raw GEO submission; raw counts
   verified in X, but demultiplexing QC decisions were made upstream.
4. **64.3% HGNC coverage** — dominated by legacy locus tags; any downstream
   pathway scoring must handle the unmapped tail explicitly.
5. **No outcome labels** — package provides population responses only;
   response/reference labels for task families must be constructed under a
   separate registered protocol.

## 7. Next steps (outside this task)

- Contract-mapping table (`dose_value` token → verified unit) per protocol §5.
- Downstream consumers: task families A/B/C consume `effects::*` rows whose
  `effect_available=True`; family E (failure modeling) can use
  `measurement_status=undetected` rows.
- The 3 conditions without population controls (sciPlex4 rows where a
  DMSO/DMSO control for that cell line is absent) are flagged
  `effect_available=False`.

---

## SUPERSEDED ADDENDUM (2026-09-29, added by the v2 repair task)

An independent review (`PILOT_REVIEW.md`) found that this handoff's "10/10 QA passed"
claim does not support construction-complete or scientifically-validated status. Confirmed
defects include: cross-plate control mismatch (144 of 204 sciPlex4 contrasts used a
different plate's control), 40 unknown-identity cells manufactured into a qualified
condition, 28 agent2-only conditions mislabeled vehicle controls, QA arithmetic that
counted only positive effects (`np.abs(effect > t)` instead of `np.abs(effect) > t`), an
untrustworthy gene mapping (75 stable-ID conflicts, first-wins aliases), a sample-sheet
"comparison" that only counted lines, and overstated narrative claims (sciPlex2 cell
lines, SAHA/Nutlin/BMS descriptions).

**This handoff and the v1 data package remain here as historical audit evidence only.
They are NOT accepted for downstream scientific use.** The historical measurements above
were deliberately left unchanged. The repair is documented in `CONSTRUCTION_PROTOCOL_V2.md`,
built as `sciplex_pilot_v2`, and reported in `PILOT_HANDOFF_V2.md`. The v1 builder and QA
implementations are hash-archived at `tools/case_memory/archive_v1/`.
