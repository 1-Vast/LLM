# Preserved execution failure

Initial proposer_inspect.py invocation failed before parsing with ModuleNotFoundError: No module named 'bs4'. Exit code 1. Replaced the optional third-party HTML parser with Python standard-library HTMLParser. No package was installed, no assay was accessed, and no scientific result was produced by that failed invocation.

The initial rg invocation passed a wildcard-containing path directly on Windows and failed with OS error123. Corrected to rg -g DECISION.md over the existing directory. No scientific conclusion came from the failed search.

EuropePMC PMC3501264/fullTextXML returned HTTP500,150bytes. The returned body and receipt are preserved. It is not qualified full text or assay data.
