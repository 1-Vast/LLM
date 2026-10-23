# Official lexical identity authentication

2026-10-22. Public compound metadata only; no molecular/functional experimental responses read. Exact official bodies and URL/status/header/time/byte/SHA256 receipts are saved inreview/lexical_sources/. No broad fuzzy normalization is authorized.

## Authenticated pair 1: Carboplatin / Carboplatine

Official ChEBI record **CHEBI:31355**, name`carboplatin`, names.INN explicitly lists:

- `carboplatin`, language`en`, source`WHO MedNet`.
- `carboplatine`, language`fr`, source`WHO MedNet`.

This is a direct language-specific name bridge in one official entry, rather than edit-distance inference. A SYNONYM entry also spells`Carboplatin` (KEGG DRUG). Archived response:lexical_sources/CHEBI31355.body; receipt:CHEBI31355.receipt.json. Exact endpoint:[official ChEBI entry API](https://www.ebi.ac.uk/chebi/backend/api/public/compound/31355/).

Important negative search result retained: official PubChemname/Carboplatin/synonyms resolvedCID426756 and did not include bareCarboplatine; name/Carboplatine/synonyms resolvedCID10339178, which includesCarboplatine andCARBOPLATIN [INN]/[USAN] etc. Do **not** claim these queries returned one CID or silently equate their structural encodings. The direct ChEBI bilingual name evidence authenticates the lexical bridge without relying on that erroneous shortcut.

## Authenticated pair 2: Cyclophosphamide / Cyclophosphamid

Official PubChem **CID2907** synonym response contains both exact strings`cyclophosphamide` and`Cyclophosphamid` within the same compoundInformation entry. Case alone is ignored in matching; no letters are inserted/deleted algorithmically. Archived response:Cyclophosphamide.body.json; receipt:Cyclophosphamide.receipt.json. Endpoint:[official PubChem synonyms](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Cyclophosphamide/synonyms/JSON).

The exact metadata supports an explicitCyclophosphamid→Cyclophosphamide lexical rule. It does not independently certify the publisher's physical material, batch, salt or laboratory treatment; the retained author-file/condition identity contract still applies.

## Allowed disposition and limits

The two exact spelling pairs may be added as individually documented aliases before selective numeric extraction. They are unlike unresolvedCHDI: no corresponding authoritative bridge has been found forCHDI-0046593-0000-003→CHDI00465983. Do not generalize from these two examples to remove arbitrary trailinge, collapse punctuation or repair near names. Partitions and sensitivity plans remain unchanged. Inventory can retain strict raw-name mismatch flags while separately marking these two resolved lexical discrepancies.

## Actual request accounting and source retention limitation

Actual calls:5PubChem HTTP requests (two initial canonical queries, then the same two repeated plus theCarboplatine query after correcting case-only matching), and1ChEBI HTTP request. All completedHTTP200; no failed retrieval was hidden. The first matcher wrongly required canonical case exactly and therefore markedCyclophosphamide pair false despite displayingCyclophosphamid; correctedcasefoldmatching authenticates exact lexical strings apart from capitalization. Initial prints and later body show the same reported synonym counts, but the two first responses were overwritten by second retrievals at the same filename rather than separately archived. Current bodies/receipts authenticate the later responses; do not claim all6original bodies are separately retained. This small provenance gap is disclosed instead of inventing timestamps or hashes for lost first-response receipts. No source performance claim rests on these metadata.

Scripts:research/decrypte_molecular_increment_20261022/lexical_identity.py andchebi_identity.py. The latter also printed a large chemical entry including ontology/metadata fields; these are compound metadata, not newly read experimental response data. No supplementary molecularbodywas displayed.
