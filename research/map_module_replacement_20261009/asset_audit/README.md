# Original MAP asset subset and protein content assay

This work acquires genuine pretrained MAP-KG gene and molecule projectors plus
an exact symbol-indexed subset of the released ESM vectors. It keeps the original
raw storage members under `data/external/map_module_replacement_20261009` and
does not restore a full MAP runtime. `PARTIAL_ASSET_RECEIPTS.json` binds source
file IDs/revisions, member CRC values, byte ranges, local SHA256 values and the
strict projector/cache checks. Whole-file GB-scale SHA256 values remain
unverified from these partial downloads.

The fixed gallery contains 241 unambiguous menu target genes and 1,000 globally
sampled protein-symbol distractors. Twenty-one raw target stable IDs remain
documented mapping exclusions. All 146 drug-dose candidates are represented by
the existing frozen molecule/knowledge cache; scoring deduplicates them to 111
molecular identities and retains all 44 known-assertion drug queries. This is a
target-enriched known-graph content assay, not genome-wide retrieval or held-out
biological validation.

`protein_score.py` requires the parent-created `PROTEIN_FREEZE.json` before
running. The protocol fixes ordinary 1024-dimensional molecule/protein cosine,
protein and molecule identity shuffles, molecule-neighbor target votes and
query-excluded target popularity. It opens no RNA or functional outcomes.
Projected-protein cosine is narrower than the full relation-conditioned MAP
objective; `NATIVE_FEASIBILITY.json` records the additional assets and semantic
requirements for that experiment and the separate native RNA reproduction.

`PARTIAL_ASSET_VERIFIED.json` reports a second complete local size/CRC/SHA check
of all 1,261 raw members plus an independent projector recomputation at three
fixed gallery indices. The smiles projector reproduces the historical cached
knowledge vectors from their original molecule vectors with a maximum absolute
gap of 1.9073486328125e-6. These checks establish subset integrity and cache
compatibility, not whole-checkpoint byte identity or biological validity.

Fresh public metadata confirms that `epoch_3.pt` still uses the older
`PrimeKG_ver1` drug hierarchy and has `hvg_info: null`. No exact 2,000-output
gene list was found in the inspected official folder, source tree, checkpoint
metadata or author replies. The historical compatible-forward audit remains
qualified: current public causal first-CLS semantics produced drug-independent
outputs, while replacing the mask is a disclosed new forward. Neither new
gene names nor a new HVG selection can authenticate the missing decoder axis.
