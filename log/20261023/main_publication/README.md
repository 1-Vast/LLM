# Main-branch publication and branch cleanup

Completed: content commit `f96f209d7e6b6f0ae08cf581a3d5fb45d378ff61` was pushed to `main`; the incorporated report branch was deleted. Remote and local branch checks showed only `main`. A subsequent receipt-only commit records the operation. See [receipt](RECEIPT.json) and [verification](VERIFICATION.json).

The user requested publication of all relevant accumulated work to `main` and deletion of other branches. The compact report branch is first incorporated into `main`; retained reports, result summaries, experimental code, storage documentation and authorized record/data-layout changes are then included in a reviewed commit. Raw datasets, model checkpoints, downloaded source bodies and disposable run artifacts remain local under the existing storage policy.

The five current experimental/maintenance working areas are listed separately in `research/STUDIES.json`, preserving the 39 registered studies and their frozen records. Working-area registration is not scientific completion or promotion to `src/` or `tools/`.

The publication plan records included and excluded paths. Verification checks repository structure, relevant experiment contracts, tracked-deletion preservation and staged-file scope. Delete a non-main branch only after its head is incorporated into published `main`. No force-push or history rewrite is required. The final receipt records the resulting remote heads.

Publication also corrects the compact package's line-ending binding: JSON files created with Windows default newlines had raw-byte hashes that differed from the LF content delivered by the earlier API upload. The builder now writes canonical LF before hashing, and regenerates only the compact package bindings. Original experimental freezes and source records are unchanged. The staged Git blobs are checked against the corrected package manifest before publishing.

Git attributes preserve raw bytes for `log/` records and the five current research working areas, preventing upload-time newline conversion from invalidating their existing content hashes. Core runtime source formatting is unchanged. This transport correction does not repair historical provenance drift or supply missing dataset files.

A repeated staging pass initially failed because it named deleted paths that were already absent from the index. No file was deleted by that failed command. The helper now stages only existing or still-indexed paths and reapplies attributes to the reviewed file set. The migration-preservation checks still cover all 883 deletions independently.

Key operation records stay here; maintenance code lives in `research/report_consolidation_20261023/`. This operation changes publication and storage, not experiment scores, frozen scientific decisions or the overall research goal.
