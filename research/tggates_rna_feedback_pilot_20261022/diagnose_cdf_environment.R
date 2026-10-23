# Inspect supported affy environment lookup before any CEL access.
.libPaths(c("D:/anaconda/envs/maestro/r-library-bioc322",.libPaths()))
suppressPackageStartupMessages(library(affy))
print(getOption("BioC"))
print(getFromNamespace("cdfFromEnvironment","affy"))
print(getFromNamespace("cdfFromLibPath","affy"))
