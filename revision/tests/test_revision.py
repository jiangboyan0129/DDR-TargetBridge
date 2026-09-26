import unittest,sys,json,tempfile
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'code'))
from revise_existing_outputs import weighted_mixture,module_values,theta_from_samples,verify_sources

class MathTests(unittest.TestCase):
 def test_mixture(self):self.assertAlmostEqual(weighted_mixture(23,.5,68,3.5),(23*.5+68*3.5)/91)
 def test_mixture_identity(self):
  for a,b in [(.5,3.5),(-2,0),(1,1)]:self.assertAlmostEqual(weighted_mixture(23,a,68,b)-a,68/91*(b-a))
 def test_invalid_group(self):
  with self.assertRaises(ValueError):weighted_mixture(0,0,2,2)
 def test_ties_and_whole_background(self):
  f=pd.DataFrame({'gene':['a','b','c','d'],'raw_score':[-2,0,0,2]})
  t,m,z=module_values(f,['b','c']);self.assertEqual(t,0);self.assertEqual(m,0)
  self.assertAlmostEqual(module_values(f,['a'])[0],.3)
 def test_no_member_only_rank(self):
  f=pd.DataFrame({'gene':['a','b','c'],'raw_score':[-1,0,1]})
  self.assertEqual(module_values(f,['a'])[0],.25)
 def test_duplicates(self):
  with self.assertRaises(ValueError):module_values(pd.DataFrame({'gene':['a','a'],'raw_score':[1,2]}),['a'])
 def test_absent_member(self):
  with self.assertRaises(ValueError):module_values(pd.DataFrame({'gene':['a'],'raw_score':[1]}),['b'])
 def test_nonfinite(self):
  with self.assertRaises(ValueError):module_values(pd.DataFrame({'gene':['a'],'raw_score':[np.nan]}),['a'])
 def test_sample_count(self):
  f=pd.DataFrame({'sample_id':['A549_parent__vehicle__rep1'],'M':[1]})
  with self.assertRaises(ValueError):theta_from_samples(f,'M')

class SnapshotTests(unittest.TestCase):
 def test_source_integrity(self):self.assertEqual(verify_sources(ROOT),15)
 def test_six_unchanged_results(self):
  a=pd.read_csv(ROOT/'data/terminal/decision_grid.tsv',sep='\t');b=pd.read_csv(ROOT/'results/revision/six_frozen_results_UNCHANGED.tsv',sep='\t')
  pd.testing.assert_frame_equal(a,b,check_exact=False,rtol=0,atol=1e-12)
 def test_mixture_disclosed(self):
  f=pd.read_csv(ROOT/'results/revision/retained_added_mixture.tsv',sep='\t');e=f[(f['transform']=='zero_only_0.5')&(f.pathway=='C')].iloc[0]
  self.assertEqual(e.n_added,68);self.assertEqual(e.n_retained,23);self.assertAlmostEqual(e.added_theta,3.574050986,places=6)
 def test_primary_crossing_still_fails(self):
  f=pd.read_csv(ROOT/'results/revision/R2_contrasts_reranked.tsv',sep='\t').set_index('condition')
  self.assertGreater(f.loc['PARPi','contrast_HR_minus_metabolic'],0);self.assertGreater(f.loc['WEE1i','contrast_HR_minus_metabolic'],0)
 def test_reproduction_scope_honest(self):
  r=json.loads((ROOT/'results/revision/REVISION_RECEIPT.json').read_text());self.assertFalse(r['whole_study_reproduction']);self.assertFalse(r['source_R2_XLSX_reparsed'])
if __name__=='__main__':unittest.main()
