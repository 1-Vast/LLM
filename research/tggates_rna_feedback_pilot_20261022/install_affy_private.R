args <- commandArgs(trailingOnly=TRUE)
lib <- "D:/anaconda/envs/maestro/r-library-bioc322"
logs <- "D:/MAESTRO/log/20261022/tggates_rna_feedback_pilot/r_dependencies"
dir.create(lib, recursive=TRUE, showWarnings=FALSE)
dir.create(logs, recursive=TRUE, showWarnings=FALSE)
.libPaths(c(lib, .libPaths()))
Sys.setenv(R_LIBS_USER=lib)
options(timeout=300)
stopifnot(getRversion() >= "4.5", getRversion() < "4.6")
repos <- c(BioCsoft="https://bioconductor.org/packages/3.22/bioc",
           BioCann="https://bioconductor.org/packages/3.22/data/annotation",
           CRAN="https://cloud.r-project.org")
ap <- available.packages(contriburl=contrib.url(repos, type="win.binary"), type="win.binary")
targets <- c("affy", "hgu133plus2cdf", "AnnotationDbi")
deps <- unique(c(targets, unlist(tools::package_dependencies(targets, db=ap,
  which=c("Depends", "Imports", "LinkingTo"), recursive=TRUE))))
deps <- deps[deps %in% rownames(ap)]
already <- installed.packages(lib.loc=lib)
deps <- deps[!vapply(deps, function(p) p %in% rownames(already) && already[p,"Version"] == ap[p,"Version"], logical(1))]
print(ap[deps, intersect(c("Package","Version","Depends","Imports","Repository"), colnames(ap)), drop=FALSE])
write.table(ap[deps, , drop=FALSE], file.path(logs,"package_metadata.tsv"), sep="\t", row.names=FALSE)
# Pin all required non-base packages in the private library, even when global copies exist.
if (length(deps)) {
  downloaded <- download.packages(deps, destdir=logs, available=ap, repos=repos, type="win.binary")
  write.table(downloaded, file.path(logs,"downloaded.tsv"), sep="\t", row.names=FALSE)
  install.packages(downloaded[,2], repos=NULL, type="win.binary", lib=lib)
}
# Annotation data packages are distributed as source archives without compilation.
missing <- setdiff(targets, rownames(installed.packages(lib.loc=lib)))
if (length(missing)) {
  src <- available.packages(contriburl=contrib.url(repos["BioCann"], type="source"), type="source")
  stopifnot(all(missing %in% rownames(src)))
  write.table(src[missing,,drop=FALSE], file.path(logs,"annotation_metadata.tsv"), sep="\t", row.names=FALSE)
  dl <- download.packages(missing, destdir=logs, available=src, repos=repos["BioCann"], type="source")
  write.table(dl, file.path(logs,"annotation_downloaded.tsv"), sep="\t", row.names=FALSE)
  install.packages(dl[,2], repos=NULL, type="source", lib=lib)
}
suppressPackageStartupMessages(library(affy))
suppressPackageStartupMessages(library(hgu133plus2cdf))
write.table(installed.packages(lib.loc=lib)[,c("Package","Version","LibPath")],
            file.path(logs,"installed.tsv"), sep="\t", row.names=FALSE)
sink(file.path(logs,"function_sources.txt"))
print(affy::mas5)
print(affy::mas5calls)
print(affy::normalize.AffyBatch.constant)
print(sessionInfo())
sink()
cat("PRIVATE_INSTALL_OK\n")
