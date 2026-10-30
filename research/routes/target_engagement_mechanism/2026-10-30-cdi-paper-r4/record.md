# Round record — paper-informed CDI revision

Date: 2026-10-30. The parent objective remains `ACTIVE / NOT_ACHIEVED`.

## Roles and actual outputs

* `/root/doi_paper_virtual_cell_audit`: independent paper evidence audit;
  requested `gpt-6-astra/xhigh`, effective model unknown. Output:
  `../2026-10-30-cdi-r3/doi_paper_audit_astra.md`.
* `/root/public_engagement_resource_scout`: public target-engagement and
  genetic-resource audit; requested `gpt-6.1-sol/high`, effective model
  unknown. Output:
  `../2026-10-30-cdi-r3/engagement_resource_scout.md`.
* `/root/doi_cdi_transfer_challenger`: fresh candidate challenge; requested
  model/effort as delegated, effective model unknown. Output:
  `../2026-10-30-cdi-r3/doi_cdi_transfer_challenge.md`.
* `/root/target_engagement_overlap_search`: independent 2025–2026 cellular
  engagement overlap search; output `target_engagement_overlap_search.md`.
  It found CellEKT and a live-cell kinase-probe study as near-overlap
  templates, but no verified PRISM/DepMap/GDSC row-level crosswalk.
* `/root/gene_reference_challenger`: fresh independent challenge of the
  corrected GeneEffect join and candidate; output `gene_reference_challenge.md`.
  Requested `gpt-6-astra/max` (effective model unknown). It rejected the first
  repeated-row tertile definition, required unique-cell freezing, and downgraded
  the candidate to a conditional diagnostic pilot.
* Coordinator independently checked the DOI metadata, source boundaries,
  existing r3 results and the returned resource fields. No sealed data were
  opened and no scientific result was delegated to DeepSeek.

## Auxiliary Harness boundary

The latest formal DeepSeek task was DS044 and is closed. DS043 accepted only
fixed paper fields and arithmetic after coordinator review. No new Harness
call was needed for this revision; the existing default remains to check new
formal tasks first and to delegate only fixed metadata/units/arithmetic.

## Budget and execution state

No wet-lab work, model training, protected-data access, external scientific
model API, or core-code change occurred. No new `maestro` effect run was
authorized because the intervention data gate failed. All proposed gains and
mechanism claims remain conditional.

The coordinator completed a bounded metadata-only acquisition of the PRISM and
DepMap release records (about 2.65 MB; no response matrix). The downloaded
resource files and deterministic census are under `raw/resource_metadata/`;
the manifest distinguishes downloaded files from generated snapshots.

After that metadata pass, a separately budgeted GeneEffect stream was completed:
413,544,937 source bytes (under the 500 MB/10-minute cap), matching MD5, with
only the 1,208-row FLT3 extraction retained. The exact join to the existing
PRISM 19Q4/MTS010 pair table was independently re-counted as 409,428 rows,
395 cells, 153 pairs and eight doses. An independent challenge corrected the
tertile unit from repeated rows to unique cells: the corrected interaction was
`rho = 0.0642`; pair-level mean-over-dose `rho = 0.1116` was dose-unstable,
and cell-level mean direct rho was `-0.0706`. The direct repeated-row
correlation was `rho = -0.0056`; the rejected row-weighted interaction was
`rho = 0.0717`. The separate arithmetic/identity check is retained in
`raw/resource_metadata/gene_reference_independent_check.json`. This is a
genetic-reference concordance check only and does not change the
`data_unavailable` gate.

The independent target-engagement overlap search audited CellEKT and a
live-cell kinase probe assay as the strongest 2025 near-overlap resources.
Both have useful dose/time/repeat fields but lack a verified PRISM/DepMap/GDSC
row-level crosswalk; no large PRIDE file was downloaded. The detailed audit is
`target_engagement_overlap_search.md`.

## Coordinator source snapshots

The DOI metadata responses used for this round are preserved in `raw/`:
`doi_crossref.json`, `doi_openalex.json`, `doi_biorxiv.json`,
`doi_semanticscholar.json`, and `doi_europepmc.json`. They are metadata and
abstract evidence only; they do not establish the inaccessible CellQ method or
the biological claims.
