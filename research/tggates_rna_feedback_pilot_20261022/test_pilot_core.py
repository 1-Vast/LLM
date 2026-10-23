"""Synthetic ownership and end-to-end comparator tests; no real RNA loaded."""
import copy,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pilot_core import Data,Base,select_record,histories,training_targets,configurations,feedback_fit_predict,ordinary_refit,derange_history


class PilotTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(9321);n,p=7,9
        y=rng.normal(size=(n,3,2));y[-1,[0,2]]=np.nan
        xh=rng.normal(size=(n,p));xh[-1]=np.nan
        self.data=Data(rng.integers(0,2,size=(n,12)),np.eye(2)[np.arange(n)%2],
            np.tile([1.,3.,10.],(n,1)),y,np.full((n,3,2),.1),rng.normal(size=(n,p)),xh,
            range(6),[[0,1],[2],[3],[4,5]])

    def make(self,data,outer=0):
        train=[i for i in data.source if i!=outer];records=[]
        for j in train:
            pack=Base(data,[i for i in train if i!=j],.1).export([j])
            records.append(select_record(pack,j))
        h=histories(data,train,records,[outer]);t=training_targets(data,train,h)
        pack=Base(data,train,.1).export([outer]);q=histories(data,[outer],[select_record(pack,outer)])
        return train,h,t,pack,q

    def test_all64_configurations_and_expected_source_fit_count(self):
        counts={}
        for c in configurations():counts[c['family']]=counts.get(c['family'],0)+1
        self.assertEqual(set(counts.values()),{8});self.assertEqual(len(counts),8)
        source_fits=24*(3*8*2+4*8+8*3)
        final_fits=3*2+3+7*3+1+3
        self.assertEqual(301*2*3+source_fits+final_fits,4336)

    def test_heldout_high_sentinel_changes_no_comparator_forecast(self):
        a=self.make(self.data)
        changed=copy.deepcopy(self.data);changed.y[0,2]=1e15;changed.xh[0]=1e15
        b=self.make(changed)
        for config in configurations():
            if config['alpha']!=.1:continue
            led={'estimator_fits':0}
            if config['family']=='refit':
                pa=ordinary_refit(self.data,a[0],0,.1,config['weight'],a[3]['transforms'],led)
                pb=ordinary_refit(changed,b[0],0,.1,config['weight'],b[3]['transforms'],led)
            else:
                pa,_=feedback_fit_predict(a[1],a[2],a[4],config,led)
                pb,_=feedback_fit_predict(b[1],b[2],b[4],config,led)
            np.testing.assert_allclose(pa,pb,atol=1e-11,err_msg=str(config))

    def test_real_no_observed_rna_family_ignores_queried_rna(self):
        a=self.make(self.data)
        changed=copy.deepcopy(self.data);changed.xm[0]*=1e7
        b=self.make(changed)
        config=dict(family='no_rna',alpha=.1,penalty=.1)
        pa,_=feedback_fit_predict(a[1],a[2],a[4],config,{'estimator_fits':0})
        pb,_=feedback_fit_predict(b[1],b[2],b[4],config,{'estimator_fits':0})
        np.testing.assert_allclose(pa,pb,atol=1e-11)

    def test_g_derivative_matches_actual_composition_and_mask_identity(self):
        train,h,t,pack,q=self.make(self.data)
        base=Base(self.data,train,.1)
        config=dict(family='rho_0',alpha=.1,penalty=.1,rank=2,rho=0.)
        prediction,extra=feedback_fit_predict(h,t,q,config,{'estimator_fits':0})
        actual=base.g(pack['fh']+extra['dx'],[0],[2])
        delta_function=extra['masks']['01']-extra['masks']['00']
        np.testing.assert_allclose(prediction,actual+delta_function,atol=1e-11)
        np.testing.assert_allclose(extra['masks']['11']-extra['masks']['10'],delta_function,atol=1e-11)

    def test_bad_fold_owner_is_rejected(self):
        train,h,t,pack,q=self.make(self.data)
        bad=copy.deepcopy(h['records']);bad[0]['owner_train']+=(0,)
        with self.assertRaises(AssertionError):histories(self.data,train,bad,[0])

    def test_inner_heldout_high_cannot_change_its_nuisance_prediction(self):
        train=[2,3,4,5]
        a=Base(self.data,train,.1).export([1])
        changed=copy.deepcopy(self.data);changed.xh[1]=1e18;changed.y[1,2]=1e18
        b=Base(changed,train,.1).export([1])
        for name in ['fm','fh','gm','gmp','g0','bm','bh','slope']:
            np.testing.assert_allclose(a[name],b[name],atol=1e-12)

    def test_development_high_absent_yet_all_methods_forecast(self):
        d=self.data;train=list(d.source);records=[]
        for j in train:
            p=Base(d,[i for i in train if i!=j],.1).export([j]);records.append(select_record(p,j))
        h=histories(d,train,records);t=training_targets(d,train,h)
        pack=Base(d,train,.1).export([6]);q=histories(d,[6],[select_record(pack,6)])
        for config in configurations():
            if config['alpha']!=.1:continue
            led={'estimator_fits':0}
            if config['family']=='refit':p=ordinary_refit(d,train,6,.1,config['weight'],pack['transforms'],led)
            else:p,_=feedback_fit_predict(h,t,q,config,led)
            self.assertTrue(np.isfinite(p).all(),str(config))

    def test_diagnostic_derangement_moves_paired_bundle_only(self):
        _,h,_,_,_=self.make(self.data)
        moved,order=derange_history(h)
        self.assertTrue(np.all(order!=np.arange(len(order))))
        for name in ['um','vm','ym','xm']:
            np.testing.assert_array_equal(moved[name],h[name][order])
        for name in ['fh','fm','g0','bm','bh','design']:
            np.testing.assert_array_equal(moved[name],h[name])

if __name__=='__main__':unittest.main()
