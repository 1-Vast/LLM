# Local data

`data/` holds MAESTRO's local datasets and third-party assets. Only this README is tracked;
everything else is git-ignored and staged per machine. Code, tests, tools and registries name
assets by `data/...` paths relative to the repository root.

Until 2026-09-26 this directory was named `dataset/`, and `data` was a directory junction to it,
so every asset was reachable under two names. The two were merged into this one real directory:
the junction was removed, `dataset/` was renamed `data/`, and four byte-identical duplicates were
moved out of the tree, not deleted, to `D:/MAESTRO_data_archive_20260926/`. Each is listed there
with its SHA-256 and the path of the twin kept here, in `_ARCHIVE_MANIFEST.json`.

## Layout

| Path | Contents |
|---|---|
| `raw/` | Primary public measurements: SciPlex3, DepMap, PRISM, kinobeads, ontology and combination sources |
| `external/` | Third-party releases, model weights and source checkouts: State, a LINCS L1000 subset, chemCPA and others |
| `evaluation/` | Case packages, capability registries, cost tables and pre-registrations |
| `knowledge/` | Retained, hash-checked knowledge packages |
| `virtual_cell/` | The virtual-cell asset registry and feature identities |
| `INVENTORY.md` | What the tree keeps, what was archived on 2026-09-14, and the rule that decided each case |

## Pinned assets used by the E0-DIR and virtual-cell work

- `raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad`
  - source: Figshare file 43381398 / article 24681285, CC BY 4.0
  - MD5: `d1f51b9f8de35ca07638132539da9a99`
  - SHA256: `bde2420ce24c8aad00d4b0fcbeb0351334e7cd6945d06030ce47be6bcc63b35f`
  - **Its feature labels are offset by one row.** The first entry of `var/ensembl_id` is a
    stray header, `id gene_short_name`, so the gene in column j is the label in row j + 1, and
    the `gene_symbol` column is unusable. Read labels through
    `virtual_cell.identity_markers.resolve_label_offset`, which confirms the alignment with
    cell-line markers (12 of 12 at offset +1, 5 of 11 as published) or refuses. The chemCPA
    subset `raw/sciplex3/sciplex_complete_middle_subset.h5ad` is correctly aligned.
- `external/chemCPA/` is a pinned source checkout at commit
  `43e830eb0958c54e4aa64442c17ec0fed19b3f15`.

## Added 2026-09-26

- `external/hgnc/hgnc_complete_set.txt`: HGNC approved symbols with Entrez and Ensembl
  identifiers, used to name genes and to join SciPlex3, DepMap and Reactome.
- `external/msigdb/h.all.v2024.1.Hs.symbols.gmt`: MSigDB Hallmark gene sets, used for the
  pre-registered pathway anchors and the served pathway readouts.
- Each carries a `.provenance.json` with its URL, retrieval time, size and SHA-256.

## Staging on a fresh machine

Create `data/` as an ordinary directory and stage assets under the paths above. Do not recreate
a `dataset/` directory or a junction between the two names: one asset reachable under two paths
is how the duplicate copies above accumulated.
