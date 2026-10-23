# Metadata-only lexical name bridges before selective values

2026-10-22. The metadata inventory found Carboplatine and Cyclophosphamid in author files assigned Carboplatin and Cyclophosphamide. Independent official-source authentication is recorded in review/LEXICAL_IDENTITIES.md and raw source receipts. ChEBI CHEBI:31355 records carboplatin (English) and carboplatine (French) in one INN entry, sourced to WHO MedNet. PubChem CID2907 lists cyclophosphamide and Cyclophosphamid together. These two explicit nominal-substance spelling bridges are allowed in preparation; no edit-distance or fuzzy identity inference is used. They do not certify batch purity, stereochemistry or analytical measurements.

PubChem's default Carboplatin and Carboplatine name requests returned different CIDs; do not claim matching PubChem CID evidence. The explicit ChEBI INN mapping is the stated bridge. Preserve failed/redundant source accesses rather than hiding them.

CHDI remains unresolved and is not covered by this lexical rule. Its weaker author-file-assignment contract and mandatory47refit are unchanged. Any other unmatched internal name must stop for its own metadata review before scientific extraction; no automatic generalization from these cases.
