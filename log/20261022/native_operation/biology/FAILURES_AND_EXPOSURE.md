# Failures and exposure

- Europe PMC fullTextXML request returned HTTP500,150-byte JSON. Parsing it as XML raised `xml.etree.ElementTree.ParseError: not well-formed (invalid token): line 1, column 0`. Body and receipt retained; it was not fulltext evidence.
- PMC HTML alternative returned a127-byte403 page. The shell invocation was started through exec and its session metadata was not retained when only output was printed; the local body persists. Do not count this as a successful article read or claim a retained response-header receipt.
- BioC alternative returned HTTP429,899bytes; body/receipt retained.
- First local HTML extraction attempted BeautifulSoup and failed `ModuleNotFoundError: No module named 'bs4'`. No dependency was installed. A subsequent standard-library HTMLParser extracted the public paragraphs successfully.
- Successful Nature page is subscription preview, not complete main text. Abstract, public captions and availability statements were read. Published qualitative CD58 conclusion is designer-exposed.
- One public3,771,230-byte supplementary workbook downloaded. All sheets' first-row strings and Table2 rows1–3 strings were inspected; no biological numerical scalar was cast, displayed or fitted. Serialized XML numeric tokens existed in memory during metadata parsing. Counts of rows and coordinates/shared-string indices are metadata, not assay outcomes.
- SCP1064 portal HTML and author GitHub top-level directory metadata were read. Portal requires sign-in to download; no expression matrices or source code contents were read.
- No DeepSeek call, new wet-lab experiment, predictive fit or protected reserve access. Code and evidence only in the assigned research/native_biological_20261022 and log/20261022/native_operation/biology directories.
