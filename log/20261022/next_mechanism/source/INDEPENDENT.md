# Independent FM03 source qualification

2026-10-22. Decision: **STOP the presently proposed longitudinal FM03 numerical route under the accessible source contract.** This is a scoped source decision, not a proof of absent observations and not a rejection of FateMap biology. No response counts, expression matrix, FASTQ, raw image, or biological count array was decoded. No prediction, fitting, or author performance replication occurred.

I read the full objective, prior continuation and same-source completion decision. I did not read other new-role conclusions or exchange conclusions before this report and its seal. The supplied calibration code and prior endpoint metadata are accepted as existing evidence; I did not rerun prior synthetic falsifiers.

## New attainable facts

The publisher's Supplementary Table 7 supplies explicit standard barcode identities. In the archived workbook, cells A3/B3 are **Clone D8** and its 100-base sequence; A4/B4 are **Clone C8** and its 100-base sequence. Exact reverse-complement comparison establishes that D8 is the FM03 analysis code's `spikeBC1`, and C8 is `spikeBC2`. Both sequence checks pass in `STANDARD_IDENTITY.json`. This closes the sequence-to-code-identifier part of the standard identity gate. It does not authenticate the physical amounts, their sample-specific fraction meaning, or the correspondence between code file order and actual experimental sample identity.

There is a primary-source naming discrepancy: the paper's Methods names **D8 and F8**, while Supplementary Table 7 labels the matching second sequence **C8**. I preserve both rather than silently renaming C8 to F8. The matching sequences permit deterministic sequence-key matching independent of this nomenclature. There is no demonstrated calibration error.

Supplementary Table 11 explicitly annotates FM03 as WM989, BRAFV600E, sample 1 `(1uM PLX, DMSO)` and sample 2 `(1uM PLX, DOT1Li)`, both resistant samples. It provides no four-gDNA-branch chronology in its inspected text annotations. Numeric worksheet cells were deliberately not decoded. Thus this primary sample annotation supports the two endpoint conditions but does not authenticate `FM03_Naive_DMSO` or `FM03_Naive_DOT1Li` harvest time, ancestry or pre-decision availability.

The newly acquired Supplementary Discussion explicitly calls these inhibitor-pretreated versus DMSO-pretreated conditions and says vemurafenib followed pinometostat pretreatment. This agrees with the already available Methods (five-day pretreatment, general WM989 treatment interval 3–4 weeks). It supplies **no exact naive-harvest time or FM03-specific day count**. A generic 3–4-week protocol must not become an exact FM03 observation timestamp. Descriptive author statements about more resistant clones are published results, not new measured performance here.

## Precise qualification matrix

| Required fact | Current primary evidence | Disposition |
|---|---|---|
| Code barcode to standard sequence | Table 7 sequences exactly reverse-complement-match spikeBC1 and spikeBC2 | VERIFIED sequence binding |
| Standard clone name | Methods F8 versus Table 7 C8 for second standard | Unresolved nomenclature, sequence binding survives |
| Four sample names and nominal standard amounts | Existing static FM03 code | Already supplied; do not claim quantities wholly absent |
| `nFraction` meaning | Code multiplies standard totals by fractions and separately divides unique-barcode numbers by those fractions; no explicit inspected definition | NOT_QUALIFIED; do not guess gDNA aliquot, GFP fraction or capture probability |
| Endpoint split identities | Table 11 + existing GEO endpoint records | Supported for two resistant conditions |
| Naive harvest before/after five-day pretreatment | Neither inspected supplement text nor sample annotations defines it | NOT_QUALIFIED |
| Authoritative four-branch common ancestral pool/sample mapping | General split-population description; four code names; no actual four-branch timing/pool record | NOT_QUALIFIED for proposed paired longitudinal inference |
| FM03-specific endpoint interval and assay availability | Generic 3–4-week method, no exact four-branch dates | NOT_QUALIFIED |

The missing record is scientifically consequential. Post-pretreatment baseline would permit conditional later abundance prediction under the shared main drug; pre-pretreatment baseline would instead permit complete-regimen prediction. Endpoint sampling mislabeled as a baseline would invalidate prospective evaluation. Data values cannot establish which interpretation applies.

I therefore do not recommend downloading or decoding FM03 count tables to infer chronology. Do not initiate another generic inventory, inspect more endpoints, or repeat this source search merely because the full goal remains active. Reopen this narrow route only upon a concrete newly identified primary sample sheet, laboratory timeline, fraction definition or sample/pool mapping that resolves these facts. No author contact was made. Missing evidence within inspected records is not global nonexistence.

## Acquisition and reading boundary

Five direct HTTP requests: one PMC supplement binary returned 403 (134 response bytes), and four publisher supplement requests succeeded (**49,286,949 body bytes** total). Raw bodies, final URLs, headers, timestamps, sizes and SHA-256 are stored in adjacent receipts. No retry was used for the PMC failure; authenticated publisher links in saved Nature HTML supplied the alternate route.

The four successes are Supplementary Figures/Discussion DOCX (26,069,799 bytes), Reporting Summary PDF (74,635 bytes; four pages), Peer Review File PDF (23,041,901 bytes; 108 pages), and Supplementary Tables XLSX (100,614 bytes). Full PDF text was extracted locally; relevant keyword pages and the first-page document titles were inspected. DOCX text was extracted from OOXML, including the complete DOT1L discussion. Embedded figure pixels were not visually inspected, so no assertion of complete supplement-content absence is justified. The table workbook was inspected for structure/shared text and text cells in Table 7 and Table 11 only, without numerical worksheet-cell decode. A targeted lookup of existing archive/code names found the previously known four FM03 branches and relevant existing static code; no new archive download or biological data decompression followed.

Code is `research/next_mechanism_source_20261022/qualify_source.py`; all downloaded data and records are in this source directory. Maestro Python was used. Initial extraction failed because `bs4` was unavailable; it was replaced with standard-library `HTMLParser`, without installing dependencies. PDF text extraction used existing `pypdf`; OOXML and sequence comparison use standard libraries. No stochastic routine or seed, model/API call, training compute, or wet experiment was used. The documents skill was read to check relevance; its container artifact authoring workflow was not applied to this static source qualification, and no deliverable DOCX was authored or edited.

## Next action for the scientific goal

The standard-sequence binding is useful reusable primary evidence, but it does not supply a world-model/agent/RSI mechanism, separate contributions, useful-gain result or later-task inheritance. Move research effort to another distinct evidence-backed mechanism/data contract unless a specific missing FM03 source record is newly found. The full goal remains ACTIVE / NOT_ACHIEVED.
