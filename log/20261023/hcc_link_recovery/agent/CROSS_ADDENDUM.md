# Independent BioStudies attachment-identity challenge

2026-10-23. New addendum; prior 15-file FINAL_SEAL.json remains unchanged. This check made no new network requests. Root-supplied raw metadata, source JATS and retrieved DOCX were inspected independently with standard-library XML/ZIP/hash parsing. No statistical assay response rows were read or fitted; DOCX text inspection was restricted to the first three nonempty paragraphs.

The saved EPMC labsLinks explicitly links the matching article title to BioStudies S-EPMC12205652. The BioStudies record accession and title agree with the HCC paper. Thus root did follow an authentic official metadata link; it is not a guessed CDN path. However article-level metadata identity does not authenticate the attached bytes.

All four BioStudies listed file sizes disagree with original JATS processing instructions:

| Object | BioStudies listed bytes | Original JATS bytes |
|---|---:|---:|
|mmc1.pdf|3449107|2439020|
|mmc2.docx|15923|65340|
|mmc3.pdf|11172242|1968126|
|mmc4.pdf|28887472|5643190|

The actual downloaded DOCX is15923 bytes, matching the BioStudies list. Its SHA256 is f6d73e4c7c8c4dd5c519a3ce35de80e6d3bf3a2b1d5d2caeb06670b4d4c3b653; MD5 bd655e2b385c09101e4592a8d61f9ff4 differs from original JATS mmc2 MD5 31b73eb3fd2aa42c679bb87fbac135c0. Its first paragraph is exactly **Table S2. PRDEGs in the PPI network ranked with the MCC method**, followed by Rank and Name. The original authenticated HCC mmc2 was the methods/resources table, and the sought HCC response matrix is Table S7 in a separate Excel workbook. The first paragraph is incompatible with treating this DOCX as either of those target artifacts.

The receipt records the official file service URL redirecting to the accession-specific ftp.ebi.ac.uk path, status200, same15923bytes/SHA256. This eliminates a simple accidental local wrong-file substitution relative to that receipt, but does not prove which upstream system caused the mapping discrepancy. Do not label it BioStudies misconduct, infer corruption of all BioStudies records, or claim another paper's identity without additional evidence.

**REJECT_AS_HCC_ASSAY_SOURCE.** Quarantine these listed/downloaded attachment identities from HCC task construction. Do not substitute their contents into a same-title HCC dataset, and do not download the three PDFs merely hoping to obtain the Excel matrix. The title/accession match and HTTP200 are insufficient against direct attachment identity conflict. Original JATS plus previously byte-matched EPMC supplements remain the current authenticated source boundary; workbook still not recovered. NO_NUMERICAL_GO remains unchanged.

Independent machine-check detail: BIOSTUDIES_INDEPENDENT.json. No diagnosis beyond the observed source mapping discrepancy is established. A future source correction or separately authenticated publisher workbook could resolve the task, but the present metadata mismatch cannot.
