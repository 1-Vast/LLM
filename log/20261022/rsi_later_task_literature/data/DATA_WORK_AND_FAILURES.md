# Data-source audit work and failures

2026-10-22. Independent source review; no peer new drafts read, no AZ/reserve access and no fitting. All fetches use unauthenticated public HTTP; each response or request failure retains URL/status/body hash/time in a paired .http.json receipt. HTML/markdown/source metadata only; no expression/HDF5 datasets downloaded.

Initial guessed ArcInstitute/virtual-cell-challenge README and virtualcellchallenge.org/data paths returned 404. The repo tree then identified the actual ArcInstitute/arc-virtual-cell-atlas/virtual-cell-challenge path. The Biomni-R0 report URL linked by the author README returned 404; that README assertion is not treated as a verified technical-report result.

The first local HTML extraction attempted BeautifulSoup and failed because maestro lacks bs4 (ModuleNotFoundError). No install or environment change was made during the live AZ fit. The extractor was corrected to use Python's standard HTMLParser; this is a local document-processing correction, not a model/experimental retry.

The first Next.js payload text extraction succeeded for datasets but failed on a home-page token containing an unescaped newline (JSONDecodeError). The local derived-text decoder was corrected to allow control characters; captured original HTTP bytes remain unchanged. No website script was executed.

During cross-review, an inline multiline `python -c` binding calculation was rejected by conda's Windows wrapper before Python execution (AssertionError: arguments contain newlines). No source/experiment file changed and no report was submitted. Moved the calculation into the external `data_commit_binding.py` script, consistent with keeping research code in research/.
