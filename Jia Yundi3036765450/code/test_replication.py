"""Meaningful tests of missingness, closure handling and estimator algebra."""
import unittest
import numpy as np
import pandas as pd
from analysis import construct, fit

class ReplicationTests(unittest.TestCase):
    def fake(self):
        d=pd.DataFrame({'STATE':[0,1,1,1], 'CHAIN':[1,2,3,4], 'CO_OWNED':[0,1,0,1],
            'EMPFT':[5.,5.,5.,np.nan], 'EMPPT':[10.,10.,10.,10.], 'NMGRS':[2.,2.,2.,2.],
            'EMPFT2':[6.,np.nan,np.nan,6.], 'EMPPT2':[10.,np.nan,np.nan,10.], 'NMGRS2':[2.,np.nan,np.nan,2.],
            'STATUS2':[1,3,2,1], 'WAGE_ST':[4.25,4.25,5.5,np.nan], 'WAGE_ST2':[4.25,np.nan,np.nan,5.05]})
        return d
    def test_missing_component_is_not_zero(self):
        d=construct(self.fake()); self.assertTrue(np.isnan(d.fte0.iloc[3]))
    def test_closure_distinction(self):
        d=construct(self.fake()); self.assertEqual(d.fte1.iloc[1],0); self.assertTrue(np.isnan(d.fte1.iloc[2]))
        z=construct(self.fake(),temporary_zero=True); self.assertEqual(z.fte1.iloc[2],0)
    def test_gap_eligibility(self):
        d=construct(self.fake()); np.testing.assert_allclose(d.gap.iloc[:3],[0,.8/4.25,0]); self.assertTrue(np.isnan(d.gap.iloc[3]))
    def test_managers_and_parttime(self):
        d=construct(self.fake()); self.assertEqual(d.fte0.iloc[0],12)
        d=construct(self.fake(),alpha=.4,managers=False); self.assertEqual(d.fte0.iloc[0],9)
    def test_closed_proportional_special_convention(self):
        d=construct(self.fake()); self.assertEqual(d.sym_change.iloc[1],-1)
    def test_regression_did_sign(self):
        d=pd.DataFrame({'STATE':[0,0,1,1],'delta':[-1.,-1.,2.,2.]})
        r,_=fit(d,'delta',['STATE']); self.assertAlmostEqual(r.params.STATE,3.)

if __name__=='__main__': unittest.main()
