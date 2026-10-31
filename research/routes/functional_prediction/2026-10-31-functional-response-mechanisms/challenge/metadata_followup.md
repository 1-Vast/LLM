# Post-snapshot metadata verification

After preserving `initial_review.md`, I ran the reviewer-owned `verify_metadata.py`. It hashes the supplied originals and projects exactly `cell_line` and `condition` with PyArrow. It never deserializes `growth_rate` or computes any response statistics. This is a metadata audit, not a scientific-model run. Output: `metadata_verification.json`.

All four freeze-manifest hashes match, including the question, root audit source/output and original LaValle PDF. The underlying summary SHA256 also matches the declared 3b4b9e451eab1106b7e47aac1b68d5181f0e684c021c88fc63f0dca01d7cc5c9.

Independent metadata projection confirms 4,992 rows, 52 lines, 93 label identities and 93 canonical unordered condition identities, 4,836 unique line-condition keys, multiplicities {1:4784,4:52}, combination orders {2:41,3:3,4:3}, 16 combination families and exact-single-matched orders {2:17}. Thus this projection finds no extra canonical condition identity obtained by treating tuple ordering as meaningful. Schedule/preparation fields are absent from the three-field summary schema. These findings authenticate design metadata only and do not authenticate administration timing or independent preparations.

This strengthens the metadata provenance in the initial review without changing its scientific qualification. No response/model numerical access, downloaded-code execution, HTTP requests, installation, global edits, shared-file edits or subdelegation occurred. Requested setting remains gpt-6.1-sol/high; effective settings, usage and cost remain unknown.
