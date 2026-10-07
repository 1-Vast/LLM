"""Combine frozen network, public context and later action annotations for retrieval.

Creates a NEW database; never changes the frozen model-feature database. Phenotype
outcomes and benchmark campaign results are deliberately excluded from this store.
"""
from __future__ import annotations
import json
import shutil
import sqlite3
import pandas as pd
from .acquire import HERE,digest


def main():
    target=HERE/'biological_knowledge.sqlite'
    shutil.copyfile(HERE/'knowledge/knowledge.sqlite',target)
    db=sqlite3.connect(target)
    db.executescript('''
      CREATE TABLE context_release(kind TEXT PRIMARY KEY, method TEXT, source_url TEXT,
        source_sha256 TEXT, data_context TEXT, evidence_kind TEXT);
      CREATE TABLE context_activity(sidm TEXT, kind TEXT, feature TEXT, value REAL,
        PRIMARY KEY(sidm,kind,feature));
      CREATE TABLE drug_identity(drug_id TEXT PRIMARY KEY, chembl_id TEXT, preferred_name TEXT,
        matching_rule TEXT, benchmark_structure_verified INTEGER);
      CREATE TABLE curated_drug_mechanism(id INTEGER PRIMARY KEY, drug_id TEXT,
        molecule_chembl_id TEXT, target_chembl_id TEXT, action_type TEXT, mechanism_text TEXT,
        direct_interaction_curated INTEGER, mechanism_references_json TEXT, original_record_json TEXT,
        provenance TEXT, used_in_models INTEGER DEFAULT 0);
      CREATE TABLE chembl_target(target_chembl_id TEXT PRIMARY KEY, name TEXT, entity_type TEXT,
        organism TEXT, component_metadata_json TEXT, original_record_json TEXT);
      CREATE TABLE database_note(name TEXT PRIMARY KEY, value TEXT);
      CREATE INDEX mechanism_drug ON curated_drug_mechanism(drug_id);
    ''')
    sources=json.loads((HERE/'context/pinned_sources.json').read_text())
    for kind,name in [('pathway','GDSC_progeny_activities.csv'),('tf','GDSC_TF_activities.csv')]:
        source=next(s for s in sources if s['path'].endswith(name))
        db.execute('INSERT INTO context_release VALUES (?,?,?,?,?,?)',
          (kind,'ULM with '+('PROGENy top100' if kind=='pathway' else 'CollecTRI regulons'),
           source['url'],source['sha256'],'untreated basal RNA; no within-line perturbation trajectory',
           'upstream computationally derived activity score'))
        matrix=pd.read_csv(HERE/f'context/{kind}_125_lines.csv',index_col=0)
        db.executemany('INSERT INTO context_activity VALUES (?,?,?,?)',
          [(sidm,kind,feature,float(v)) for sidm,row in matrix.iterrows() for feature,v in row.items()])
    bundles=json.loads((HERE/'supplement/chembl_actions.json').read_text())
    for bundle in bundles:
        molecule=bundle.get('molecule')
        if molecule:
            db.execute('INSERT INTO drug_identity VALUES (?,?,?,?,?)',
             (bundle['drug_id'],molecule['molecule_chembl_id'],molecule.get('pref_name'),
              'unique exact normalised preferred name or synonym',None))
        provenance=json.dumps(bundle.get('source_requests',[]),sort_keys=True)
        for mechanism in bundle.get('mechanisms',[]):
            db.execute('''INSERT INTO curated_drug_mechanism(drug_id,molecule_chembl_id,
              target_chembl_id,action_type,mechanism_text,direct_interaction_curated,
              mechanism_references_json,original_record_json,provenance) VALUES (?,?,?,?,?,?,?,?,?)''',
              (bundle['drug_id'],mechanism.get('molecule_chembl_id'),mechanism.get('target_chembl_id'),
               mechanism.get('action_type'),mechanism.get('mechanism_of_action'),
               mechanism.get('direct_interaction'),json.dumps(mechanism.get('mechanism_refs',[])),
               json.dumps(mechanism,sort_keys=True),provenance))
        for tid,t in bundle.get('targets',{}).items():
            db.execute('INSERT OR IGNORE INTO chembl_target VALUES (?,?,?,?,?,?)',
             (tid,t.get('pref_name'),t.get('target_type'),t.get('organism'),
              json.dumps(t.get('target_components',[])),json.dumps(t,sort_keys=True)))
    notes={
      'purpose':'Provenance-preserving retrieval and reusable public features; not a complete causal model',
      'benchmark_outcomes':'Excluded from this database',
      'frozen_experiments':'Use knowledge/knowledge.sqlite and its frozen kernels; later ChEMBL enrichment was never used',
      'unknown_context':'Unknown tissue/cell/dose/time is not evidence of a matching condition',
      'complexes':'Keep complexes, protein families and nucleic acid targets distinct; no all-subunits-binding inference',
      'dependence':'Multiple resources may reuse the same paper; resource count is not independent evidence',
      'licenses':'Retain each original resource license. OmniPath commercial filter is not a blanket license grant.',
    }
    db.executemany('INSERT INTO database_note VALUES (?,?)',notes.items())
    db.commit()
    counts={table:db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            for table in ('gene','drug','drug_target_annotation','claim','context_activity',
                          'drug_identity','curated_drug_mechanism','chembl_target')}
    integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
    db.close()
    result=dict(file=target.name,sha256=digest(target),bytes=target.stat().st_size,
                counts=counts,sqlite_integrity=integrity,benchmark_outcome_rows=0)
    (HERE/'assembled_knowledge_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
