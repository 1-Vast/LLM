# Offline identity projection, registered after code I/O evidence

2026-10-22. `Calculation.m` line 23 requires exactly the CSV columns `Time`,
`Dose_A`, `Dose_B`, `Growth`, `Dosing_Type`; its line 29 names `A+B`, `A-B`, `B-A`.
The first schema stage redacted the fifth header because it was not in that
stage's allowlist. This amendment permits **only** that header and these three
category labels, and aggregate counts of distinct `(dose A, dose B, type)`
trajectories and time/trajectory identity keys from the already retained CSV.
Do not refetch; do not export or summarise Growth, fitted parameters or results.

Count duplicate identity rows without deleting them. Numerical time/dose values
are parsed only to check identity and finite keys; their units and real drug
identities remain unauthenticated. The absence of run/chamber/drug-name columns
in this particular table is a schema fact, not proof the paper never measured
them. No outcome-based split, hypothesis tuning or numerical model follows.
