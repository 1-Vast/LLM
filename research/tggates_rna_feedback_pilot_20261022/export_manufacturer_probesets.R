# Annotation only. Independent coordinate reference, no CEL or expression read.
base <- "D:/MAESTRO/log/20261022/tggates_rna_feedback_pilot"
definition <- new.env()
load(file.path(base,"r_dependencies/cdf_diagnostic_source/hgu133plus2cdf/data/hgu133plus2cdf.rda"),envir=definition)
ids <- sort(ls(definition$hgu133plus2cdf),method="radix")
stopifnot(length(ids)==54675L,!anyDuplicated(ids))
dest <- file.path(base,"annotation/MANUFACTURER_PROBESETS.txt")
stopifnot(!file.exists(dest))
writeLines(ids,dest,useBytes=TRUE)
cat("MANUFACTURER_COORDINATES_EXPORTED",length(ids),"\n")
