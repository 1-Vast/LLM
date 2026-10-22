# Identity-only continuation after dictionary inspection

The data dictionary is authenticated: per-sample/per-assay records contain
normalised experimental dose responses data0..14, matching conc0..14 in molar
units, curve fits, chemical sample IDs and SMILES. Replicate/plate/time/raw-control
columns are not defined. Normalised response values are real released observations
but cannot by themselves authenticate matched cultures, raw QC or assay causality.

Before acquiring the full CSV, permit ONE bounded <=40 MB download of the pinned
38,887,216-byte Zenodo file, inside this continuation's <=100 MB coordinator cap.
Store it in sealed_source. A separate worker reads only explicit identity,
structure, library/supplier and concentration columns; it must NOT select data*,
activity, fitted potency, efficacy, AUC, curve-class or quality-of-fit columns.
Return assay membership/coverage, chemical/dose identities, duplicates and
intersection counts only. No activity rate, shortlist, threshold or model fit.

Purpose: establish whether AlphaLISA, TruHit and an orthogonal/functional assay
have a sufficiently matched menu to test the proposed error-source distinction.
Complete assay names and broad public access are insufficient. Selected-only
orthogonal follow-up must remain flagged. No new virtual-cell or RSI claim is
licensed by a successful overlap. Stop acquisition/inspection at 10 additional
minutes; preserve source hash and status. Data dictionary/initial ledger remain
unchanged. No reserve outcomes or morphological values are opened.
