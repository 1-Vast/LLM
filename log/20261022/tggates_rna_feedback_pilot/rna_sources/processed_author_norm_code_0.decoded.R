#!/usr/bin/env Rscript
# Stage 41a: RMA normalization with BrainArray ENTREZG v22 CDFs.
#
# Reproduces Eastman & Pande 2019 (arXiv:1907.03041) normalization exactly:
#   - Rat CELs   -> Rat2302_Rn_ENTREZG_22.0.0   -> 14,075 rat genes
#   - Human CELs -> HGU133Plus2_Hs_ENTREZG_22.0.0 -> 20,352 human genes
#
# Usage:
#   Rscript 41a_rma_brainarray.R rat   data/cel/rat_in_vitro   data/rma/rat.tsv
#   Rscript 41a_rma_brainarray.R human data/cel/human          data/rma/human.tsv
#
# Output: tab-separated matrix with genes as rows (Entrez IDs) and CEL barcodes
# as columns. Values are log2 RMA expression (matches E&P's input space).

suppressPackageStartupMessages({
  library(affy)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) {
  stop("Usage: Rscript 41a_rma_brainarray.R <rat|human> <cel_dir> <out_tsv>")
}
species <- args[1]
cel_dir <- args[2]
out_tsv <- args[3]

cdf_name <- switch(species,
  rat   = "rat2302rnentrezgcdf",
  human = "hgu133plus2hsentrezgcdf",
  stop(sprintf("unknown species: %s (expected rat|human)", species))
)
suppressPackageStartupMessages(library(cdf_name, character.only = TRUE))

cel_files <- list.files(cel_dir, pattern = "\\.CEL(\\.gz)?$",
                        ignore.case = TRUE, full.names = TRUE, recursive = TRUE)
message(sprintf("[41a] %s: %d CEL files found under %s",
                species, length(cel_files), cel_dir))
if (length(cel_files) == 0) stop("no CEL files found")

t0 <- Sys.time()
eset <- justRMA(filenames = cel_files, cdfname = cdf_name)
dt  <- as.numeric(difftime(Sys.time(), t0, units = "mins"))
message(sprintf("[41a] RMA done in %.1f min", dt))

expr <- exprs(eset)                                    # genes x samples, log2
rownames(expr) <- sub("_at$", "", rownames(expr))      # bare Entrez IDs
colnames(expr) <- sub("\\.CEL(\\.gz)?$", "",
                      basename(colnames(expr)),
                      ignore.case = TRUE)              # barcodes

message(sprintf("[41a] matrix: %d genes x %d samples",
                nrow(expr), ncol(expr)))

dir.create(dirname(out_tsv), showWarnings = FALSE, recursive = TRUE)
write.table(round(expr, 4), out_tsv,
            sep = "\t", quote = FALSE, col.names = NA)
message(sprintf("[41a] wrote %s", out_tsv))
