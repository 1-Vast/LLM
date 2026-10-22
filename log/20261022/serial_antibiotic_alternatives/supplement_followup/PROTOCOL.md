# Tripartite supplementary-material read qualification

2026-10-22. The retained primary CC-BY article identifies
`msaf115_supplementary_data.pdf`. Fetch the official Europe PMC supplementary
archive once from `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12164588/supplementaryFiles`.
At most one request, 20,000,000 decoded body bytes, no retries or redirects.
Retain the body/status/hash even on failure. If a ZIP is returned, export its
directory and unpack only the exact named PDF into this log directory, after
checking the uncompressed size <=20MB and no path traversal. Do not execute any
source code or fetch figures/FASTQ/genome/function matrices separately.

This block first authenticates the supplement's identity. If obtained, use the
PDF skill for read-only page/text review. Store extracted text/renders under log,
all scripts under research. User-required locations override the skill's generic
tmp/output conventions. No artifact authoring marker is needed for read-only use.

Source inspection may encounter published numerical result figures. Record such
pages as designer-exposed literature; do not claim an evaluation on those values
is a blind confirmation. Until a separate scope amendment, only manifest/page
count/title/heading and table-caption projections leave the extraction worker;
no response arrays or figure images are shown to root. A later relevant-page
review must specify the evidence required and record its exposure boundary.

Success: determine whether the archive actually contains the referenced PDF and
whether the PDF advertises individual lineage/functional/genomic mapping tables,
versus figure-only summaries. Source absence or download failure alone does not
establish that data do not exist. No candidate implementation or performance
experiment is authorised by a successful supplement download.
