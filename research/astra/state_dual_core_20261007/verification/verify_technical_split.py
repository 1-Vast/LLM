"""Verify disjoint technical split and exact archived source extraction."""
from pathlib import Path
import hashlib,json,time
import numpy as np,h5py
B=Path(__file__).resolve().parents[1];W=B/'world';O=B/'verification';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();start=time.perf_counter();f=read(W/'technical_screen_freeze.json');p=read(W/'metadata_freeze.json');r=read(W/'technical_screen_receipt.json');old={x['condition_id']:x for x in p['conditions']};assert sha(W/'technical_screen_freeze.json')==r['freeze_sha256']==read(W/'technical_screen_freeze_receipt.json')['sha256'];assert sha(W/'technical_screen.py')==f['source_code_sha256']
assert len(f['rows'])==48;screen=set();validation=set();control=set(sum([x['basal_rows']+x['reference_rows'] for x in p['controls'].values()],[]))
with h5py.File(read(W/'contract.json')['hashes']['dataset']['path'],'r') as h:
 index=h['obs'][h['obs'].attrs['_index']].asstr()[:];matrix=h['obsm']['X_hvg'];ref={plate:np.asarray(matrix[v['reference_rows']]).mean(0) for plate,v in p['controls'].items()}
 for which in ['screen','validation']:
  saved=np.load(W/('technical_'+which+'_values.npz'));assert sha(W/('technical_'+which+'_values.npz'))==r[which+'_sha256']
  assert np.array_equal(saved['condition_id'],[x['condition_id'] for x in f['rows']])
  for i,row in enumerate(f['rows']):
   a,b=row['screen_rows'],row['validation_rows'];screen.update(a);validation.update(b);assert not set(a)&set(b);assert set(a)|set(b)==set(old[row['condition_id']]['treated_rows'])
   ordering=sorted(old[row['condition_id']]['treated_rows'],key=lambda j:hashlib.sha256(('technical-screen-v1:'+str(index[j])).encode()).hexdigest());assert a==sorted(ordering[::2]) and b==sorted(ordering[1::2])
   ix=row[which+'_rows'];assert list(index[ix])==row[which+'_cell_ids'];delta=np.asarray(matrix[ix]).mean(0)-ref[row['plate']];np.testing.assert_array_equal(delta,saved[which+'_delta'][i]);np.testing.assert_allclose(np.sqrt((delta**2).mean()),saved[which+'_magnitude'][i],rtol=1e-7)
assert not screen&validation and not (screen|validation)&control
receipt={'status':'PASS','conditions':48,'screen_cells':len(screen),'validation_cells':len(validation),'all_source_rows_and_cell_ids_reconstructed':True,'row_halves_disjoint':True,'control_rows_disjoint_from_treated':True,'shared_reference_controls':True,'split_values_reconstructed_without_policy_choice_access':True,'scope':'Technical split of previously exposed source only. Conditional on surviving/QC-passing cells; source population and shared denominator are not independent biological repeats. H1 unchanged.','wall_seconds':time.perf_counter()-start};(O/'technical_split_verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
