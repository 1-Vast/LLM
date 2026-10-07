import numpy as np
import pandas as pd
from .raw_endpoint import plate_endpoint

def fixture():
    return pd.DataFrame([
        ['1','1','B',None,None,10.],['1','2','NC-1',None,None,110.],['1','3','NC-0',None,None,110.],
        ['1','4','A1-S','10','1',60.],['1','5','L1-D1-S','20','10',90.],
        ['1','6','A1-C','10','1',30.],['1','6','L1-D1-C','20','10',30.]
    ],columns=['BARCODE','POSITION','TAG','DRUG_ID','CONC','INTENSITY'])

def test_plate_local_bliss_arithmetic():
    z,error=plate_endpoint(fixture())
    assert error is None and len(z)==1
    assert np.isclose(z.raw_y.iloc[0],.2) and np.isclose(z.mixed_control_y.iloc[0],.2)

def test_background_translation_and_scale_invariance():
    f=fixture();a,_=plate_endpoint(f)
    f.INTENSITY=2*f.INTENSITY+17;b,_=plate_endpoint(f)
    assert np.allclose(a.raw_y,b.raw_y)
