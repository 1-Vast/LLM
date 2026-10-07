"""Retrieve supported short directed gene paths, with provenance and missing context.

This is evidence retrieval, not an indication that a drug combination is effective.
It deliberately cannot output an unqualified clinical or cell-specific action.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from .build_knowledge import OUT


def paths(source, target, max_hops=2, limit=10):
    if max_hops not in (1,2):
        raise ValueError('only bounded 1- or 2-hop paths are supported')
    db = sqlite3.connect(f'file:{OUT / "knowledge.sqlite"}?mode=ro', uri=True)
    db.row_factory = sqlite3.Row

    def outgoing(gene):
        rows = db.execute('''SELECT dataset,source_gene,target_gene,sign,source_resources,
                 references_raw,species,tissue,cell_line,dose,time,evidence_note FROM claim c
                 WHERE source_gene=? AND usable_before_gene_conflict_check=1
                 AND NOT EXISTS (SELECT 1 FROM claim x WHERE x.source_gene=c.source_gene
                     AND x.target_gene=c.target_gene AND x.sign=-c.sign
                     AND x.usable_before_gene_conflict_check=1)
                 ORDER BY target_gene,dataset''', (gene,)).fetchall()
        return [dict(r) for r in rows]
    found = []
    for first in outgoing(source):
        if first['target_gene'] == target:
            found.append([first])
        elif max_hops == 2:
            # Protein influence may feed transcription; do not propagate an
            # inferred change in RNA instantaneously back into protein activity.
            if first['dataset'] != 'omnipath':
                continue
            for second in outgoing(first['target_gene']):
                if second['target_gene'] == target:
                    found.append([first,second])
    db.close()
    return dict(source=source,target=target,paths=found[:limit],total_paths=len(found),
                applicability='Human aggregate; requested cell/dose/time not established',
                interpretation='Path sign is topological composition, not a measured drug-combination effect',
                usable_as='Mechanistic prior / evidence pointer; requires context and intervention evidence')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('target')
    args = ap.parse_args()
    print(json.dumps(paths(args.source,args.target),indent=2))
