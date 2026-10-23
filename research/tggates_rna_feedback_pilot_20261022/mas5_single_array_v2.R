args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args) == 4L)
cel <- normalizePath(args[1], mustWork=TRUE)
barcode <- args[2]
allow <- read.delim(args[3], colClasses="character", check.names=FALSE)
out <- args[4]
stopifnot(sum(allow$barcode == barcode) == 1L,
          basename(cel) == paste0(barcode, ".CEL"))
lib <- "D:/anaconda/envs/maestro/r-library-bioc322"
.libPaths(c(lib, .libPaths()))
suppressPackageStartupMessages(library(affy))
# Use the unmodified manufacturer CDF environment via affy's documented lookup.
# The original annotation-only package fails installation during lazy loading.
cdf_path <- "D:/MAESTRO/log/20261022/tggates_rna_feedback_pilot/r_dependencies/cdf_diagnostic_source/hgu133plus2cdf/data/hgu133plus2cdf.rda"
definition <- new.env()
stopifnot(setequal(load(cdf_path,envir=definition),c("hgu133plus2cdf","hgu133plus2dim")),
          length(ls(definition$hgu133plus2cdf)) == 54675L)
registry <- new.env()
registry[["HG-U133_Plus_2"]] <- definition$hgu133plus2cdf
registry[["hgu133plus2cdf"]] <- definition$hgu133plus2cdf
bioc <- getOption("BioC")
bioc$affy$probesloc <- list(list(what="environment",where=registry))
options(BioC=bioc)
stopifnot(as.character(packageVersion("affy")) == "1.88.0",
          as.character(packageVersion("affyio")) == "1.80.0",
          as.character(packageVersion("preprocessCore")) == "1.72.0")
started <- proc.time()
raw <- ReadAffy(filenames=cel)
stopifnot(length(sampleNames(raw)) == 1L, cdfName(raw) == "HG-U133_Plus_2")
fit <- mas5(raw, normalize=TRUE, sc=500)
signal <- exprs(fit)[,1]
stopifnot(length(signal) == 54675L, !anyDuplicated(names(signal)), all(is.finite(signal)))
calls <- mas5calls(raw, alpha1=.04, alpha2=.06, tau=.015)
stopifnot(identical(rownames(exprs(calls)), names(signal)))
order_ids <- order(names(signal), method="radix")
result <- data.frame(probeset=names(signal), signal=as.numeric(signal),
                     log2_signal=log2(pmax(signal, 1)),
                     detection=as.character(exprs(calls)[,1]),
                     detection_p=as.numeric(assayDataElement(calls,"se.exprs")[,1]))
write.table(result[order_ids,], paste0(out,".tsv"), sep="\t", quote=FALSE, row.names=FALSE)
qc <- c(barcode=barcode, probesets=length(signal), nonfinite=sum(!is.finite(signal)),
        nonpositive=sum(signal<=0), floored=sum(signal<1),
        setNames(quantile(signal,c(0,.01,.25,.5,.75,.99,1)), c("min","q01","q25","median","q75","q99","max")),
        detection_present=sum(exprs(calls)=="P"), detection_marginal=sum(exprs(calls)=="M"),
        detection_absent=sum(exprs(calls)=="A"), elapsed_seconds=(proc.time()-started)["elapsed"])
write.table(data.frame(metric=names(qc),value=unname(qc)),paste0(out,".qc.tsv"),
            sep="\t",quote=FALSE,row.names=FALSE)
writeLines(capture.output(sessionInfo()), paste0(out,".session.txt"))
cat("SINGLE_ARRAY_MAS5_COMPLETE\n")
