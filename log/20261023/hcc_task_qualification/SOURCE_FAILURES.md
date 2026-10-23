# Source access and revised retrieval scope

Two PMC attachment routes returned HTTP403 and the same134-byte diagnostic HTML, despite a .docx target name. They are retained as failed bodies, never used as a document. The canonical-route fallback did not solve access. No authentication or access control was bypassed.

Official EPMC fullTextXML succeeded (137492bytes), providing attachment sizes and MD5 provenance. The source request was issued as an inline read command; subsequent receipt reconstruction is explicitly retrospective and cannot reconstruct original request start time. JATS identifies mmc2.docx size65340 and MD5 31b73eb3fd2aa42c679bb87fbac135c0. This does not identify its table contents.

The official EPMC supplementaryFiles API returns an archive rather than a selected attachment. Revised scope: acquire the entire supplement archive bytes if available, inventory filenames/sizes only; decode mmc2.docx only via the caption/header reader. Other PDFs/response bytes are acquired but uninspected, not described as unopened or unacquired. Any later PDF schema extraction needs a separate narrow protocol. This is source qualification, not numerical assay analysis.

PDF caption extraction initially failed before any parsing because fitz is absent. pypdf was already available and substituted; no package installed. DOCX assay-keyword read returned no matches, so a separately scoped supplementary-method-page read was used. Publisher responses were403, preserved without retry or inferring absent data. Method agent disclosed an overly broad single-line XML search emitted a truncated large text output; its own failure log distinguishes visible text contact from response-table numerical access. No table response file exists in the retrieved archive.
