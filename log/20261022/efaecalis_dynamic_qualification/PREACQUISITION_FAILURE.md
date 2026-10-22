# Retained synthetic failure

Before the first source request, nine synthetic tests ran and one failed: a regex intended to match `class`/`classes` matched only plural forms, allowing synthetic `Class A` to pass as unclassified text. No source workbook was acquired or opened. Corrected the guard to `class(?:es)?`; the original test result is retained and the corrected run is recorded in a separate directory. This is a pre-exposure repair, not source-dependent category filtering.
