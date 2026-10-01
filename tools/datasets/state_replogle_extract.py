"""Reacquire bounded same-record raw and processed RNA slices from pinned originals."""
import argparse
from pathlib import Path

import h5py
import numpy as np

from src.virtual_cell.state_runner import _column
from tools.datasets.state_prospective_input import write_json
from tools.datasets.state_remote_h5 import RangeFile


def read_obs(handle, rows):
    result={}
    for name in ['cell_barcode','UMI_count','gem_group','cell_line','gene']:
        obj=handle['obs'][name]
        if isinstance(obj,h5py.Group):
            result[name]=obj['categories'][:].astype(str)[obj['codes'][rows]].tolist()
        else:
            result[name]=obj[rows].astype(str).tolist()
    return result


def run(out):
    out.mkdir(parents=True,exist_ok=False)
    processed='https://huggingface.co/datasets/arcinstitute/State-Replogle-Filtered/resolve/d790193bb2c93726541a75ca3fa873a92ed44da5/replogle_concat.h5ad'
    raw='https://huggingface.co/datasets/arcinstitute/Replogle-Nadig-Preprint/resolve/833d2be9f604dd656ebaddf875d9ad3fbf5dda0d/GSE264667_hepg2_raw_singlecell_01.h5ad'
    with RangeFile(processed,out/'processed_ranges') as remote:
        with h5py.File(remote,'r') as h:
            axis=_column(h['var'],h['var'].attrs['_index'])
            metadata=read_obs(h,slice(0,32))
            if set(metadata['cell_line'])!={'hepg2'}:raise ValueError('unexpected processed context')
            matrix=h['X'][:32,:]
            write_json(out/'replogle_remote_axis.json',axis.tolist())
            # Historical filename; exactly32 rows are sufficient for reconstruction.
            write_json(out/'replogle_first1000_obs.json',metadata)
            np.save(out/'replogle_first32.npy',matrix)
    with RangeFile(raw,out/'raw_ranges') as remote:
        with h5py.File(remote,'r') as h:
            ensembl=_column(h['var'],h['var'].attrs['_index'])
            symbols=_column(h['var'],'gene_name')
            ids=h['obs'][h['obs'].attrs['_index']][:2000].astype(str).tolist()
            desired=[x.removesuffix('-hepg2') for x in metadata['cell_barcode']]
            rows=[ids.index(x) for x in desired]
            if len(set(rows))!=32:raise ValueError('ambiguous raw/processed barcode join')
            values=h['X'][rows,:]
            if not np.equal(values,np.floor(values)).all():raise ValueError('source is not raw UMI')
            write_json(out/'hepg2_raw_axis.json',ensembl.tolist())
            write_json(out/'hepg2_raw_symbols.json',symbols.tolist())
            write_json(out/'raw_processed_join.json',{'processed_rows':list(range(32)),'raw_rows':rows,
                       'raw_ids':desired,'rule':'context verified hepg2; remove exact concat cell-line suffix, preserve native barcode/gem group'})
            np.save(out/'hepg2_raw32.npy',values)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out.resolve())
