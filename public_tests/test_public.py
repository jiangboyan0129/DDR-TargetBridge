import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('publiccore',R/'workflows/reproduce_public_core.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixture():
 rows=[]
 for bg in ['parent','PRDX1KO']:
  for cond,n in [('T0',2),('vehicle',3),('DNAPKi',3)]:
   value={'parent':{'T0':1,'vehicle':2,'DNAPKi':3},'PRDX1KO':{'T0':1,'vehicle':4,'DNAPKi':10}}[bg][cond]
   for i in range(n):
    for arm in ['M','C']:rows.append({'transform':'synthetic','support':'fixed','pathway':arm,'gene':arm,'sample_id':f'A549_{bg}__synthetic__{cond}__rep{i+1}','value':value if arm=='M' else 0})
 return pd.DataFrame(rows)
class PublicTests(unittest.TestCase):
 def test_known_factorial_contrast(self):self.assertAlmostEqual(m.calculate(fixture())[1].iloc[0].theta_KO_minus_WT,5)
 def test_duplicate_identity_rejected(self):
  f=fixture()
  with self.assertRaises(ValueError):m.calculate(pd.concat([f,f.iloc[:1]]))
 def test_missing_value_not_zero(self):
  f=fixture();f.loc[0,'value']=np.nan
  with self.assertRaises(ValueError):m.calculate(f)
 def test_missing_endpoint_sample_rejected(self):
  f=fixture();f=f[~f.sample_id.eq('A549_parent__synthetic__DNAPKi__rep3')]
  with self.assertRaises(ValueError):m.calculate(f)
 def test_missing_pathway_rejected(self):
  with self.assertRaises(ValueError):m.calculate(fixture().query("pathway=='M'"))
 def test_protected_output_rejected(self):
  p=subprocess.run([sys.executable,'tools/run.py','core','--output','results/new'],cwd=R,capture_output=True,text=True);self.assertNotEqual(p.returncode,0);self.assertIn('Refusing output',p.stderr)
 def test_three_exact_external_sources(self):
  rows=json.loads((R/'data_metadata/external_inputs.json').read_text());self.assertEqual(len(rows),3)
  for r in rows:self.assertEqual(len(r['sha256']),64);self.assertTrue(r['url'].startswith('https://'))
 def test_full_negative_grid_retained(self):
  f=pd.read_csv(R/'results/canonical/support_views/decision_grid.tsv',sep='\t');self.assertEqual(len(f),6);self.assertEqual(sum(f.theta_KO_minus_WT<0),2)
if __name__=='__main__':unittest.main()
