# Public-input knowledge: current maintenance entry

The supplied study is preserved at
[`../knowledge_transfer_20261004/REPORT_ZH.md`](../knowledge_transfer_20261004/REPORT_ZH.md).
This successor owns read-only verification, retrieval contracts and the next
pretraining design. It does not replace the frozen study or activate a new model.

| Material | Role |
|---|---|
| [REPORT_ZH.md](REPORT_ZH.md) | This iteration's changes, findings and verification |
| [PRETRAINING_PROTOCOL.json](PRETRAINING_PROTOCOL.json) | Staged single-drug supervision design; metadata inspected, model not trained |
| [model_review.md](model_review.md), [data_review.md](data_review.md), [maintenance_review.md](maintenance_review.md) | Independent agent analyses |
| [verify_import.py](verify_import.py) | Archive bytes, dependency differences and saved-campaign accounting; read-only by default |
| [test_knowledge.py](test_knowledge.py) | Original 14 synthetic contracts plus independent retrieval boundary tests |
| `../knowledge_transfer_20261004/knowledge/knowledge.sqlite` | Frozen network actually used in the experiments |
| `../knowledge_transfer_20261004/biological_knowledge.sqlite` | Later assembled retrieval snapshot: network, basal features and ChEMBL annotations |

The two databases have different scientific roles. Neither is redundant.
Original build/acquire/assemble/receipt scripts can overwrite their outputs;
run those historical commands only in a separate replay copy. Do not execute
them to refresh the supplied snapshot or its hashes.

## Read-only use in maestro

Run from the repository root with `D:/anaconda/envs/maestro/python.exe`:

```powershell
python -m tools.datasets.biological_knowledge --database research/astra/knowledge_transfer_20261004/biological_knowledge.sqlite context SIDM00097 --kind pathway
python -m tools.datasets.biological_knowledge --database research/astra/knowledge_transfer_20261004/biological_knowledge.sqlite drug Alpelisib
python -m tools.datasets.biological_knowledge --database research/astra/knowledge_transfer_20261004/biological_knowledge.sqlite paths AR CASP2 --hops 1
python -m research.astra.knowledge_optimization_20261004.verify_import
python -m pytest -o addopts= research/astra/knowledge_optimization_20261004/test_knowledge.py -q
```

The verification command writes no files unless `--output NEW_PATH` is supplied;
an existing receipt cannot be overwritten. It verifies 49,424 saved campaigns
without reading the raw Jaaks CSV or changing the original receipt. It records
the external partition's CRLF/LF difference separately; original hashes stay
unchanged. These checks authenticate artifacts and accounting, not biological
independence or predictor benefit.

## Restore and replay boundaries

The local original package is `research/MAESTRO_biological_knowledge_20261004.zip`,
SHA256 `185a1b02e1fba74cee48d1831c0275ad8b734d3e01c69f24dd6a4aa91f3190c1`.
Its 83 entries were extracted at their original repository-relative paths,
without replacing an existing differing file. Verify its digest first; refuse
absolute/traversal entries or differing destinations when restoring elsewhere.
The package and canonical report retain their original bytes.

Source snapshots needed to rebuild the network are not all in this package.
`../knowledge_transfer_20261004/download_manifest.json` records six asset hashes;
restore those exact bytes into an isolated study copy for full reconstruction.
Mutable current endpoints may not return the original releases. A newly fetched
different snapshot needs a new study identity, not a rewritten freeze. Footprint
score snapshots are supplied; recomputing ULM also needs its upstream RNA and
network/software versions. ChEMBL annotations are retained, but their full raw
HTTP responses/version chronology are incomplete.

GDSC footprint code/data attribution and its supplied GPL-3.0 file, network
resource terms and ChEMBL terms remain separate. The SQLite database grants no
blanket data licence or scientific permission. Public cell-line profiles are
retrospective basal covariates, not certified dynamic state of a current culture.

## Successor research

The proposed mono experiment has since been executed; see
[its preserved results](../mono_pretraining_20261005/REPORT_ZH.md).
`PRETRAINING_PROTOCOL.json` remains the original design, not the current task.
The [repeat maintenance entry](../repeat_optimization_20261006/README.md)
owns the latest review and first-screen design. Neither design authorizes
opening Vis outcomes or equates mono sensitivity with synergy.

This navigation update is recorded by the 2026-10-06 manifest. The earlier
run manifest retains the hash of the README as it existed in that run.
