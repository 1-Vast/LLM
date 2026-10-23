"""Independent preparation reconstruction; never import the experiment fitter."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'log/20261023/depmap_state_increment'
SOURCE=ROOT/'log/20261023/functional_source_bridge/root'


def main():
    assert (OUT/'FREEZE.json').exists()
    assert (OUT/'prepared.npz').exists(), 'Await root-confirmed preparation completion'
    with (OUT/'pseudobulk.csv').open(newline='',encoding='utf-8') as handle:
        reader=csv.reader(handle)
        first=next(reader);second=next(reader)
        pairs=list(zip(first[1:],second[1:]))
        transcripts=[];rows=[]
        for row in reader:
            assert len(row)==len(pairs)+1
            transcripts.append(row[0])
            rows.append([float(x) if x else np.nan for x in row[1:]])
    counts=np.asarray(rows,dtype=np.float64).T
    del rows
    assert len(set(pairs))==len(pairs) and len(set(transcripts))==len(transcripts)
    lines=np.array([x[0] for x in pairs]);genes=np.array([x[1] for x in pairs])
    padding={}
    for line in sorted(set(lines)):
        row_ids=np.where(lines==line)[0]
        missing=np.isnan(counts[row_ids])
        per_column=missing.sum(axis=0)
        assert ((per_column==0)|(per_column==len(row_ids))).all()
        padding[line]=int(per_column.sum())
        zero_columns=np.where(per_column==len(row_ids))[0]
        counts[np.ix_(row_ids,zero_columns)]=0.
    assert np.isfinite(counts).all() and (counts>=0).all()
    assert (counts==np.trunc(counts)).all()
    library=np.sum(counts,axis=1)
    assert (library>0).all()
    expression=np.log(1.+(counts/library.reshape(-1,1))*1_000_000.)
    panel=np.zeros_like(expression)
    for line in sorted(set(lines)):
        ids=np.where(lines==line)[0]
        panel[ids]=np.sum(expression[ids],axis=0)/len(ids)
    residual=expression-panel
    quality=np.column_stack((np.log(1.+library),np.count_nonzero(counts,axis=1)/counts.shape[1]))
    with (SOURCE/'crispr_table.csv').open(newline='',encoding='utf-8') as handle:
        lookup={}
        for row in csv.DictReader(handle):
            key=(row['cell_line'],row['guide']);assert key not in lookup
            try: lookup[key]=float(row['gene_effect'])
            except ValueError: lookup[key]=float('nan')
    function=np.array([lookup[x] for x in pairs])
    keep=np.isfinite(function)
    design=json.loads((SOURCE/'IDENTITY_JOIN.json').read_text())['cell_line_design']
    batchmap={row['cell_line']:row['batch'] for row in design}
    expected=dict(y=function[keep],genes=genes[keep],lines=lines[keep],
                  groups=np.array([batchmap[x] for x in lines[keep]]),
                  qc=quality[keep],log=expression[keep],context=panel[keep],relative=residual[keep],
                  transcripts=np.array(transcripts))
    prepared=np.load(OUT/'prepared.npz',allow_pickle=False)
    comparison={}
    for name,value in expected.items():
        actual=prepared[name]
        assert actual.shape==value.shape,(name,actual.shape,value.shape)
        if value.dtype.kind in 'US':
            assert np.array_equal(actual,value),name
            comparison[name]=dict(shape=list(value.shape),exact=True)
        else:
            maximum=float(np.max(np.abs(actual-value)))
            assert np.allclose(actual,value,rtol=1e-12,atol=1e-12),(name,maximum)
            comparison[name]=dict(shape=list(value.shape),max_absolute_error=maximum)
    report=json.loads((OUT/'PREPARED.json').read_text())
    assert padding==report['padding_cells']
    gram_checks={}
    ids=np.array([0,len(expected['y'])//2,len(expected['y'])-1])
    for name in ['log','context','relative']:
        one=expected[name][ids]@expected[name][ids].T
        two=prepared[name][ids]@prepared[name][ids].T
        delta=float(np.max(np.abs(one-two)))
        assert np.allclose(one,two,rtol=1e-11,atol=1e-10)
        gram_checks[name]=dict(indices=ids.tolist(),max_absolute_error=delta)
    result=dict(status='PASS',scope='Independent preparation reconstruction; no new biological evidence',
                csv_parser='Python csv, independent of pandas prepare',comparisons=comparison,
                original_pairs=len(pairs),finite_pairs=int(keep.sum()),transcripts=len(transcripts),
                padding_cells=padding,representative_grams=gram_checks,
                prepared_sha256=hashlib.sha256((OUT/'prepared.npz').read_bytes()).hexdigest())
    destination=OUT/'methods/PREPARATION_AUDIT.json'
    assert not destination.exists()
    destination.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
