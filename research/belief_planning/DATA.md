# Data provenance for belief-planning-1

All downloads were made on 2026-09-27 (+0800) from NCBI GEO over HTTPS. For large files a
parallel range downloader resumed and joined the parts (12 connections, about 20 MB/s). Every
file was checked against the series' own `SHA512SUMS` list. `data/` is not tracked by git, so this
file is the record.

## External study: GSE70138 (LINCS L1000 Phase II), `data/external/lincs_l1000_phase2/`

Source: `https://ftp.ncbi.nlm.nih.gov/geo/series/GSE70nnn/GSE70138/suppl/`

| File | Bytes | Downloaded | SHA-512 check |
|---|---|---|---|
| `GSE70138_SHA512SUMS.txt.gz` | 1,071 | 03:07 | (the reference list) |
| `GSE70138_Broad_LINCS_README.pdf` | 26,382 | 03:07 | not listed |
| `GSE70138_Broad_LINCS_cell_info_2017-04-28.txt.gz` | 2,528 | 03:07 | match |
| `GSE70138_Broad_LINCS_gene_info_2017-03-06.txt.gz` | 216,692 | 03:07 | match |
| `GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz` | 82,376 | 03:07 | match |
| `GSE70138_Broad_LINCS_pert_info.txt.gz` | 83,669 | 03:07 | not listed (an older copy; unused) |
| `GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz` | 1,943,865 | 03:07 | match |
| `GSE70138_Broad_LINCS_sig_metrics_2017-03-06.txt.gz` | 3,137,083 | 03:07 | match |
| `GSE70138_Broad_LINCS_inst_info_2017-03-06.txt.gz` | 4,783,200 | 03:07 | match |
| `GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx.gz` | 5,365,179,698 | 03:11-03:16 (313 s) | match `9d078903...975c9f` |

- The Level 5 file was decompressed to `.gctx` (5,824,120,558 bytes; HDF5,
  `0/DATA/0/matrix` 118,050 x 12,328 float32).
- Its uncompressed SHA-256 is registered in `freeze.json`.
- Measured genes: the 978 landmark genes (`pr_is_lm == 1`), the same set as GSE92742 and the
  development cache.

## Development study: GSE92742 (Phase I) Level 5, `data/external/lincs_l1000_phase1/`

| File | Bytes | Downloaded | SHA-512 check |
|---|---|---|---|
| `GSE92742_Broad_LINCS_Level5_COMPZ.MODZ_n473647x12328.gctx.gz` | 21,328,033,748 | 03:17-03:36 (1,115 s) | match `6a3115cf...0208a2a` |

- It was decompressed to `.gctx` (23,380,287,022 bytes).
- It was used only for the feasibility check of the strict cross-study design
  (`l1000_level5.phase1_line_task_feasibility`), which was not run.
- The development L1000 tiers still read the existing `subset48` cache, unchanged.

## Licence and terms

- **GEO.** NCBI places no restrictions on use or distribution of GEO data. Its disclaimer notes
  that submitters may claim rights in the data.
- **Series README.** The GSE70138 README carries no licence text. It points to
  `https://clue.io/GEO-guide`.
- **Use here.** Non-commercial research, with the data cited to Subramanian et al., Cell 2017
  (the LINCS L1000 resource).
- **Annotations.** Mechanism labels come from the Drug Repurposing Hub files already in the
  repository (`data/raw/sciplex3/repurposing_{samples,drugs}_20200324.txt`), through the frozen
  `lincs_flow.annotation_map` join.

## Access to the external study before the freeze

- **Metadata:** `sig_info`, `pert_info`, `cell_info`, `gene_info` and `inst_info` were read to
  define the task, the reference arm and the test compounds (`external_phase2.manifest`).
- **Schema:** the gctx dataset names, shapes and id vectors were read.
- **`sig_metrics`:** loaded once, at 03:10, to list its column names.
- **Nothing else.** No expression value, QC metric value or test-compound label was read before
  `freeze.json` (04:35:20). The vault opened at 04:35:44 and the replay ran once (04:38:53-04:40:39),
  as recorded in `outputs/belief_planning_20260927/external/vault_access.jsonl`.

## Overlap audit (`manifests/gse70138_p2ld.json`, `audit`)

- **Reference arm:** 1,053 Phase II compounds already known to development:
  - 880 by Broad ID in GSE92742;
  - 151 by InChIKey block in GSE92742;
  - 22 by InChIKey block in SciPlex3.
- **Test compounds:** 673 new compounds with a parsable structure, measured at all 12 conditions
  (613 identity/scaffold components); 13 more were excluded as not measured at all 12.
  - Identity overlap with development: 0.
  - Batch overlap with GSE92742: none. The test batches are Phase II `REP.*` plates.
  - Scaffold overlap: 152 test compounds share a Murcko scaffold with a GSE92742 compound, and
    112 with the reference arm. Results are stratified by maximum Tanimoto similarity to the
    references.
  - Cell lines: MCF7, HT29 and PC3 are also development L1000 lines. The external task does not
    claim a new cell context, only new compounds in a new study.
- **Opened in the vault:**
  - 516 of the 673 test compounds carry a single-mechanism annotation, and 38 fall in the
    11-class pool built from the references. The external evaluation has 38 independent units
    and 380 forced-choice episodes.
  - The reference arm supplies about 100 pool-class references.

## Costs

No language-model or other paid API was called: provider spend was $0. No laboratory work was
done: 0 wells. Compute ran on the local workstation.
