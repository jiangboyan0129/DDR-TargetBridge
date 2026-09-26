import unittest,sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from execute_decision import transformed,group_gene_values,contrasts,group_indices
class DecisionTests(unittest.TestCase):
    def test_zero_only(self):np.testing.assert_equal(transformed([0,1,2,4],'zero_only_0.5'),[-1,0,1,2])
    def test_plus_one(self):np.testing.assert_allclose(transformed([0,1,3,7],'count_plus_1'),[0,1,2,3])
    def test_positive_unchanged(self):np.testing.assert_equal(transformed([2,4,8],'zero_only_0.5'),[1,2,3])
    def test_invalid_counts(self):
        for x in [[-1],[.5],[np.nan],[np.inf]]:
            with self.assertRaises(ValueError):transformed(x,'zero_only_0.5')
    def test_unknown_transform(self):
        with self.assertRaises(ValueError):transformed([1],'other')
    def test_equal_transcript_weights(self):
        df=pd.DataFrame({'target':['G','G','G','H'],'transcript':['T1','T1','T2','T1'],'s':[0,2,9,4]})
        units,genes=group_gene_values(df,['s']);self.assertEqual(genes.loc['G','s'],5);self.assertEqual(genes.loc['H','s'],4)
    def test_center_cancellation(self):
        x=np.array([[1,2,3],[4,5,6.]]);y=np.array([[7,8,9.]]);off=np.array([42,-5,.5]);np.testing.assert_allclose((x+off).mean(0)-(y+off).mean(0),x.mean(0)-y.mean(0))
    def test_factorial_sign(self):
        ix={('parent','T0'):[0,1],('parent','vehicle'):[2,3,4],('parent','DNAPKi'):[5,6,7],('PRDX1KO','T0'):[8,9],('PRDX1KO','vehicle'):[10,11,12],('PRDX1KO','DNAPKi'):[13,14,15]}
        a=np.array([0,0,1,1,1,3,3,3,0,0,4,4,4,9,9,9]);r=contrasts(a,ix);self.assertEqual(r['beta_WT'],2);self.assertEqual(r['beta_KO'],5);self.assertEqual(r['theta_KO_minus_WT'],3)
    def test_invalid_sample_groups(self):
        with self.assertRaises(ValueError):group_indices(['invented'])
    def test_saved_grid_complete(self):
        d=pd.read_csv(Path(__file__).resolve().parents[1]/'results/decision_grid.tsv',sep='\t');self.assertEqual(len(d),6);self.assertEqual(d[['transform','support']].duplicated().sum(),0)
if __name__=='__main__':unittest.main()
