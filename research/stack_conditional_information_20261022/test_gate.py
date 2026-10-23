"""Synthetic boundary/meaning tests; never reads any real response cells."""
import copy
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

import gate as g


def xml(body):
    return BytesIO(('<worksheet xmlns="'+g.NS[1:-1]+'"><sheetData><row r="2">'+body+
                    '</row></sheetData></worksheet>').encode())


class Boundaries(unittest.TestCase):
    def test_closed_values_formulas_and_future_are_inert(self):
        visible='<c r="AC2"><v>5</v></c><c r="C2"><v>0</v></c>'
        closed=['<c r="AU2"><v>99999</v></c>',
                '<c r="AU2" t="s"><v>not an index</v></c>',
                '<c r="AU2"><f>1/0</f><v>bad</v></c>',
                '<c r="BB2" t="e"><v>#REF!</v></c><c r="AC601"><v>-999</v></c>']
        expected=g.project_numeric(xml(visible),{'AC2','C2'})
        for body in closed:
            self.assertEqual(expected,g.project_numeric(xml(visible+body),{'AC2','C2'}))

    def test_numeric_domain_cached_formula_and_absence(self):
        body=''.join(f'<c r="{a}"{kind}>{extra}<v>{v}</v></c>' for a,kind,extra,v in [
            ('A2','','','0'),('B2','','','-1'),('C2','','','NaN'),('D2','','','inf'),
            ('E2','','','nonsense'),('F2',' t="e"','','#N/A'),('G2',' t="s"','','4'),
            ('H2',' t="b"','','1'),('I2','','<f>some_formula</f>','3.25')])
        body+='<c r="J2"><f>cached_missing</f></c>'
        out=g.project_numeric(xml(body),{f'{c}2' for c in 'ABCDEFGHIJK'})
        self.assertEqual([out[f'{c}2']['status'] for c in 'ABCDEFGHIJK'],[
            'valid','negative','nonfinite','nonfinite','unparsable','non_numeric_type',
            'non_numeric_type','non_numeric_type','formula_disallowed','formula_disallowed','absent'])
        self.assertEqual(out['A2']['value'],0)
        self.assertTrue(out['I2']['formula'])
        self.assertIsNone(out['I2']['value'])

    def test_metadata_roles_collision_and_exact_maps(self):
        manifest=g.make_manifest()  # frozen identity projection only, file-byte hashes
        records=manifest['records']
        self.assertEqual(len(records),5499)
        roles={r['name']:r for r in records}
        self.assertEqual(roles['Doxycycline Hyclate']['group'],roles['E-64']['group'])
        grouped={r['group']:r['role'] for r in records}
        self.assertEqual(dict(g.Counter(grouped.values())),{'train':1099,'validate':366,'test':367})
        for name in roles:
            rr=[r for r in records if r['name']==name]
            self.assertEqual(len(rr),3)
            self.assertEqual(len({r['role'] for r in rr}),1)
        for screen in range(3):
            r=next(r for r in records if r['screen']==screen)
            row=str(r['row'])
            expectedL=['AC','AD','AE','AF','AG','AH','AI'] if screen<2 else ['BL','BN','BP','BR','BT','BV','BX']
            expectedD=['C','D','E','F','G','H','I'] if screen<2 else ['C','E','G','I','K','M','O']
            self.assertEqual(r['L'],[a+row for a in expectedL])
            self.assertEqual(r['D'],[a+row for a in expectedD])
            self.assertEqual(r['target'],('AU' if screen<2 else 'CV')+row)
            for c in r['L']+r['D']:
                header=next(m for m in g.load(g.OLD/'IDENTITY_PROJECTION.json')['files'][1:] if m['filename']==manifest['sources'][screen]['filename'])['cells']
                self.assertIn(header[''.join(filter(str.isalpha,c))+'1']['metadata_literal'],['0','4','8','12','16','20','24'])

    def test_authorization_and_target_cannot_change_features(self):
        records=[{'key':f'0:{i+2}','screen':0,'row':i+2,'name':str(i),'role':role,'group':str(i),
                  'L':[f'L{j}_{i}' for j in range(7)],'D':[f'D{j}_{i}' for j in range(7)],'target':f'T{i}'}
                 for i,role in enumerate(g.ROLES)]
        manifest={'records':records}
        prefix={'0':{a:{'status':'valid','value':j+1} for r in records for j,a in enumerate(r['L']+r['D'])}}
        self.assertEqual(g.authorized(manifest,'train_validate_target')[0],{'T0','T1'})
        self.assertEqual(g.authorized(manifest,'test_target')[0],{'T2'})
        self.assertEqual(len(g.authorized(manifest,'prefix')[0]),42)
        L,D,y=g.observations(manifest,prefix,{})
        self.assertTrue(np.isnan(y).all())
        targets={'0':{'T2':{'status':'valid','value':1234567}}}
        LL,DD,yy=g.observations(manifest,prefix,targets)
        for a in g.ARMS:
            assert_array_equal(g.features(L,D,np.array([0,0,0]))[a],g.features(LL,DD,np.array([0,0,0]))[a])
        self.assertTrue(np.isfinite(yy[2]))

    def test_features_nesting_and_exact_slopes(self):
        s=np.array([2+.1*g.TIMES,5-.05*g.TIMES,1+.2*g.TIMES])
        z=np.arange(21).reshape(3,7)/10
        X=g.features(2**s-1,2**z-1,np.array([0,1,2]))
        self.assertEqual([X[a].shape[1] for a in g.ARMS],[19,20,20,21,26])
        assert_allclose(X['live_only'][:,:7],s)
        assert_allclose(X['live_only'][:,13:16],np.array([[.1]*3,[-.05]*3,[.2]*3]))
        assert_allclose(X['live_only'][:,16:],np.eye(3))
        for a in g.ARMS[1:]:
            assert_allclose(X[a][:,:19],X['live_only'])
        assert_allclose(X['dead_endpoints'][:,19:],X['dead_history'][:,[19,25]])
        assert_allclose(X['dead_initial'][:,19],X['dead_history'][:,19])
        assert_allclose(X['dead_snapshot'][:,19],X['dead_history'][:,25])

    def test_weights_macro_and_fixed_budget(self):
        screens=np.array([0,0,0,1,2,2])
        w=g.weights(screens)
        assert_allclose(w,[2/3,2/3,2/3,2,1,1])
        self.assertAlmostEqual(w.mean(),1)
        error=np.array([1,2,3,4,7,9])
        self.assertAlmostEqual(np.average(error,weights=w),g.macro(error,screens)['macro'])
        grid=g.configs()
        self.assertEqual(len(grid),14)
        self.assertEqual(dict(g.Counter(c[0] for c in grid.values())),{'extra':4,'hgb':4,'ridge':6})
        self.assertEqual((len(grid)+1)*len(g.ARMS),75)
        for config in grid.values():
            model=g.estimator(config)
            if config[0]=='hgb':
                self.assertEqual(model.max_iter,300)
                self.assertFalse(model.early_stopping)
            elif config[0]=='extra':
                self.assertEqual(model.n_estimators,300)
                self.assertEqual(model.n_jobs,1)

    def test_coverage_fixed_denominator_and_all_member_guard(self):
        records=[]
        for i in range(200):
            for screen in range(3):
                records.append({'role':'test','screen':screen,'group':str(i)})
        # The collision group's additional member must qualify in every context too.
        records += [{'role':'test','screen':s,'group':'0'} for s in range(3)]
        n=len(records)
        L,D,y=np.ones((n,7)),np.ones((n,7)),np.ones(n)
        good,dual,complete=g.coverage({'records':records},L,D,y,('test',))
        self.assertTrue(good['passed'])
        D[-1,0]=np.nan
        result,dual,complete=g.coverage({'records':records},L,D,y,('test',))
        self.assertFalse(result['passed'])  # 199 fully contributing groups, though coverage>95%
        self.assertEqual(result['fully_contributing_groups']['test'],199)
        self.assertEqual(result['tables'][2]['denominator'],201)
        self.assertEqual(result['tables'][2]['D_additional_prefix_failure'],1)
        self.assertEqual(result['tables'][2]['live_prefix_valid'],201)
        self.assertEqual(result['tables'][2]['dual_prefix_valid'],200)
        self.assertEqual(int(complete.sum()),602)  # other five rows in collision group retained

    def test_bootstrap_multiplicity_and_zero_observation_groups(self):
        # Unequal group sizes expose the error from averaging group means equally.
        groups=['a']*6+['b']*3+['c']*3
        screens=np.array([0,1,2]*4)
        errors=np.array([0.,0,0,2,2,2,8,8,8,4,4,4])
        # Frozen group d has no complete observations; it must still be resampled.
        out=g.bootstrap(errors,screens,groups,['a','b','c','d'])
        self.assertEqual(out['groups'],4)
        rng=np.random.default_rng(g.SEED)
        manual=[]
        while len(manual)<10000:
            selected=rng.integers(0,4,4)
            multiplicity=np.bincount(selected,minlength=4)
            rowweights=np.array([multiplicity['abcd'.index(k)] for k in groups])
            if rowweights.sum():
                manual.append(np.mean([np.average(errors[screens==s],weights=rowweights[screens==s]) for s in range(3)]))
        assert_allclose(out['percentile95'],np.percentile(manual,[2.5,97.5]))
        self.assertGreater(out['empty_screen_draws_redrawn'],0)

    def test_prediction_seal_blocks_missing_incomplete_tampered_and_wrong_keys(self):
        manifest={'records':[{'key':'a','role':'test'},{'key':'b','role':'test'},{'key':'x','role':'train'}]}
        with tempfile.TemporaryDirectory(dir=g.LOG) as tmp:
            path=Path(tmp)/'forecast.json'
            predictions=[{'key':key,'status':'prefix_abstention','predictions':{a:None for a in g.ARMS+g.ANCHORS}} for key in ('a','b')]
            g.write(path,{'records':predictions})
            seal={'path':str(path),'sha256':g.sha(path)}
            g.verify_predictions(manifest,seal)
            with self.assertRaises(AssertionError):
                g.verify_predictions(manifest,seal,{'a':True,'b':False})
            with self.assertRaises(AssertionError):
                g.verify_predictions(manifest,None)
            path.write_text('{}',encoding='utf-8')
            with self.assertRaises(AssertionError):
                g.verify_predictions(manifest,seal)
            for mutate in ('missing_arm','wrong_key','missing_record','nan'):
                p=copy.deepcopy(predictions)
                if mutate=='missing_arm': del p[0]['predictions']['dead_history']
                if mutate=='wrong_key': p[0]['key']='x'
                if mutate=='missing_record': p.pop()
                if mutate=='nan': p[0]['status']='predicted'
                path.write_text(json.dumps({'records':p}),encoding='utf-8')
                seal['sha256']=g.sha(path)
                with self.assertRaises(AssertionError):
                    g.verify_predictions(manifest,seal)

    def test_standard_scaler_does_not_fit_validation(self):
        X=np.arange(18).reshape(6,3).astype(float)
        model=g.estimator(('ridge',{'alpha':1}))
        g.fit(model,('ridge',{'alpha':1}),X[:3],np.array([1,2,3]),np.ones(3))
        assert_allclose(model[0].mean_,X[:3].mean(axis=0))
        before=model[0].mean_.copy()
        self.assertTrue(np.isfinite(model.predict(X[3:]+10000)).all())
        assert_array_equal(model[0].mean_,before)


if __name__=='__main__':
    unittest.main(verbosity=2)
