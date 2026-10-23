"""Full24/7 synthetic execution checks real loop/selection/seal and exact fit accounting."""
import contextlib,json,sys,unittest,uuid
from pathlib import Path
from unittest.mock import patch
import numpy as np
from threadpoolctl import threadpool_limits
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_pilot
from pilot_core import configurations
from linear_models import COUNTERS

class FullPipelineTest(unittest.TestCase):
    def test_full_nested24_source7_development_execution_with_no_high_targets(self):
        dest=run_pilot.P/'synthetic_tests'/('full_pipeline_'+uuid.uuid4().hex)
        inputs=dest/'numeric_inputs';inputs.mkdir(parents=True)
        rng=np.random.default_rng(41434336);n,p=31,9
        y=1+.1*rng.normal(size=(n,3,2));y[24:,[0,2]]=np.nan
        xh=rng.normal(size=(n,p));xh[24:]=np.nan
        np.savez(inputs/'DATA.npz',chem=rng.integers(0,2,size=(n,12)),units=np.eye(2)[np.arange(n)%2],
            dose=np.tile([1.,3.,10.],(n,1)),y=y,sd=np.ones((n,3,2))*.1,xm=rng.normal(size=(n,p)),xh=xh)
        metadata=dict(source=list(range(24)),development=list(range(24,31)),
            gene_indices=[[0,1],[2],[3],[4,5]],rows=[dict(compound_label=f'synthetic_{i:02d}') for i in range(n)])
        (inputs/'METADATA.json').write_text(json.dumps(metadata))
        freeze=dict(configurations=sorted(configurations(),key=run_pilot.key),artifacts_sha256={})
        for name in COUNTERS:COUNTERS[name]=0
        with patch.object(run_pilot,'P',dest),threadpool_limits(limits=1),\
             (dest/'EXECUTION.log').open('w') as stream,contextlib.redirect_stdout(stream):
            run_pilot.execute(freeze)
        receipt=json.loads((dest/'NUMERICAL_RECEIPT.json').read_text())
        self.assertEqual(receipt['estimator_fits'],4336)
        self.assertEqual(receipt['operations']['coefficient_fits'],4336)
        self.assertEqual(receipt['pipeline_evaluations'],1552)
        predictions=json.loads((dest/'DEVELOPMENT_RNA_PREDICTIONS.json').read_text())
        self.assertEqual(len(predictions['predictions']),9)
        self.assertFalse(predictions['development_high_function_read'])
        self.assertEqual(set(predictions['route_masks']),{'00','01','10','11'})
        self.assertEqual(json.loads((dest/'PREDICTION_SEAL.json').read_text())['status'],
                         'SEALED_BEFORE_SEPARATE_DEVELOPMENT_SCORING')
        (dest/'TEST_ASSERTIONS.json').write_text(json.dumps(dict(status='PASS',actual_fits=4336,
            pipelines=1552,development_high_missing=True,synthetic_only=True)))

if __name__=='__main__':unittest.main()
