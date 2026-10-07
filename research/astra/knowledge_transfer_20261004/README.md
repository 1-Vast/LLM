# Public biological knowledge and cheap context prototype

Read `REPORT_ZH.md` for the Chinese analysis and all negative/positive results.
All analyses are exploratory. No production model promotion, no Vis outcome access,
no paid model calls. This folder is an addition to MAESTRO, not a replacement repository.

## Environment

Repository base: https://github.com/1-Vast/LLM at
`0f7a99928857dbbc93e2aebb85ecca6c95517389`.
Use Python 3.12, numpy 2.3.5, pandas 2.2.3 and scipy 1.17.0 for closest numeric reproduction.
Run commands at repository root with `PYTHONPATH=src:.` on Linux.

```bash
python -m pip install numpy==2.3.5 pandas==2.2.3 scipy==1.17.0
PYTHONPATH=src:. python -m research.astra.knowledge_transfer_20261004.check_invariants
PYTHONPATH=src:. python -m research.astra.knowledge_transfer_20261004.context.check_context
PYTHONPATH=src:. python -m research.astra.knowledge_transfer_20261004.interaction.check_interaction
python -m research.astra.knowledge_transfer_20261004.verify_receipts
PYTHONPATH=src:. python -m research.astra.knowledge_transfer_20261004.query_knowledge BRAF MAPK1
```

The above receipt verification reconstructs all reported totals from 49,424 records
and checks history exclusion, costs and frozen files. It does not require the raw
198.9 MB Jaaks outcome CSV. Knowledge retrieval does not read phenotype outcomes.

## Use the delivered knowledge without model experiments

```python
import sqlite3
from pathlib import Path

root = Path('research/astra/knowledge_transfer_20261004')
db = sqlite3.connect(f'file:{root / "biological_knowledge.sqlite"}?mode=ro', uri=True)

# SIDM-keyed, publicly derived baseline state; not direct protein activity.
state = db.execute('''SELECT feature, value FROM context_activity
                      WHERE sidm=? AND kind=? ORDER BY feature''',
                   ('SIDM00097', 'pathway')).fetchall()

# Curated action annotations preserve distinct target entity types.
actions = db.execute('''SELECT d.name, m.action_type, t.name, t.entity_type
    FROM curated_drug_mechanism m JOIN drug d USING(drug_id)
    LEFT JOIN chembl_target t USING(target_chembl_id)
    WHERE d.name=?''', ('Alpelisib',)).fetchall()
print(state)
print(actions)
```

`biological_knowledge.sqlite` is assembled from the frozen network plus context and
post-evaluation ChEMBL annotations. `knowledge/knowledge.sqlite` is the unchanged
snapshot actually used to create the model kernels. Do not confuse them.

## Rebuild versus replay

`acquire.py` downloads original network/HGNC/Jaaks data; `build_knowledge.py` creates
a new knowledge snapshot. These commands are for a NEW study copy. Current public
endpoints may update; source hashes and downloaded releases, not a URL alone, define
the archived experiment. Do not regenerate manifests or change a completed freeze.

For numeric replay, work in a separate copy at the exact repository base. Preserve
the delivered frozen files and matrices. Download only the original Jaaks CSV to
`assets/jaaks.csv` (https://ndownloader.figshare.com/files/34006655), then verify
SHA256 `1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278`.
The raw CSV is excluded from the delivery archive.

In that replay copy, move the three `results` directories to backup names, keeping
the archive originals safe. Run the three scripts in order. Each stage rebuilds
the exact prior summary needed by the next stage's freeze. A differing hash must
be investigated, not bypassed by rewriting the freeze.

```bash
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m research.astra.knowledge_transfer_20261004.evaluate
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m research.astra.knowledge_transfer_20261004.context.evaluate_context
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m research.astra.knowledge_transfer_20261004.interaction.evaluate_interaction
```

The scripts intentionally refuse to overwrite completed E results or refreeze.
The two later trials are adaptive follow-ups, not additional untouched test sets.

## Attribution and limitations

Retain the upstream README, R source and GPL-3.0 license in `context/raw/` for the
GDSC footprints. Original network and ChEMBL source terms also continue to apply;
this package does not grant a new unified data license. Source URLs, hashes and
curated references are included. Structures, dose-matched engagement and cell-specific
mechanism evidence remain unknown unless explicitly provided in a source record.
