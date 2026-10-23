targets <- c("affy", "affyio", "frma", "frmaTools", "hgu133plus2cdf", "hgu133plus2frmavecs", "hgu133plus2.db", "preprocessCore", "Biobase", "BiocGenerics", "AnnotationDbi", "BiocManager", "oligo", "limma")
ip <- installed.packages()
cat("R_VERSION\t", R.version.string, "\n", sep = "")
cat("R_LIBPATHS\t", paste(.libPaths(), collapse = "|"), "\n", sep = "")
for (package in targets) {
  if (package %in% rownames(ip)) {
    cat("PACKAGE\t", package, "\t", ip[package, "Version"], "\t", ip[package, "LibPath"], "\n", sep = "")
  } else {
    cat("PACKAGE\t", package, "\tNOT_INSTALLED\n", sep = "")
  }
}
if ("affy" %in% rownames(ip)) {
  ns <- asNamespace("affy")
  for (fun in c("rma", "bg.correct.rma", "normalize.AffyBatch.quantiles", "expresso")) {
    cat("FUNCTION\t", fun, "\t", paste(deparse(args(get(fun, envir = ns))), collapse = " "), "\n", sep = "")
  }
}
